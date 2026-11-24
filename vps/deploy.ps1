#Requires -Version 5.1
<#
.SYNOPSIS
    Deploy Pegawai AI ke VPS dengan satu perintah, dari laptop Windows.

.DESCRIPTION
    Alur: ambil commit dari origin/main -> bangun rilis dari git archive di folder
    sementara di luar repo -> uji backend -> build frontend -> rakit
    bff/ + www/ + SHA + MANIFEST.sha256 -> kirim ke /home/ubuntu/releases/<sha> ->
    jalankan /home/ubuntu/deploy-pegawai-ai.sh <sha> (backup, restart, health,
    rollback otomatis di server).

    Berkas .env tidak pernah dibaca, dikirim, atau dicetak.

.PARAMETER Ref
    Commit atau branch yang mau dideploy. Hanya boleh commit yang sudah menjadi
    bagian dari origin/main (deploy hanya dari main).

.PARAMETER Rollback
    Kembalikan server ke rilis sebelumnya (satu langkah sebelum CURRENT_RELEASE).

.PARAMETER DryRun
    Kerjakan semua tahap lokal (uji, build, rakit, arsip, verifikasi) dan periksa
    status server, tetapi jangan unggah dan jangan jalankan deploy.

.PARAMETER SkipTests
    Lewati uji backend. Hanya untuk keadaan mendesak; keluar peringatan.

.PARAMETER Yes
    Jangan minta konfirmasi pada -Rollback.

.PARAMETER KeyPath
    Kunci SSH. Default: ~/.ssh/pegawai-ai.pem

.PARAMETER ServerHost
    Alamat VPS. Default: 139.190.107.151

.PARAMETER ServerUser
    Pengguna SSH. Default: ubuntu

.EXAMPLE
    .\vps\deploy.ps1 -DryRun

.EXAMPLE
    .\vps\deploy.ps1

.EXAMPLE
    .\vps\deploy.ps1 -Rollback
#>
[CmdletBinding()]
param(
    [string]$Ref,
    [switch]$Rollback,
    [switch]$DryRun,
    [switch]$SkipTests,
    [switch]$Yes,
    [string]$KeyPath = ([IO.Path]::Combine($HOME, '.ssh', 'pegawai-ai.pem')),
    [string]$ServerHost = '139.190.107.151',
    [string]$ServerUser = 'ubuntu'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- konstanta
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RemoteReleases = '/home/ubuntu/releases'
$RemoteScript = '/home/ubuntu/deploy-pegawai-ai.sh'
$RemoteCurrent = '/home/ubuntu/CURRENT_RELEASE'
$RemoteLock = '/home/ubuntu/.deploy-pegawai-ai.lock'
$SshTarget = "$ServerUser@$ServerHost"
$Utf8NoBom = [Text.UTF8Encoding]::new($false)
$TotalSteps = 7
$TempRoot = $null
$Stopwatch = [Diagnostics.Stopwatch]::StartNew()

$SshArgs = @(
    '-i', $KeyPath,
    '-o', 'BatchMode=yes',
    '-o', 'ConnectTimeout=20',
    '-o', 'StrictHostKeyChecking=accept-new',
    '-o', 'ServerAliveInterval=30',
    '-o', 'ServerAliveCountMax=10'
)
$ScpArgs = @(
    '-i', $KeyPath,
    '-o', 'BatchMode=yes',
    '-o', 'ConnectTimeout=20',
    '-o', 'StrictHostKeyChecking=accept-new'
)

# ---------------------------------------------------------------- tampilan
function Write-Head([string]$Text) {
    Write-Host ''
    Write-Host $Text -ForegroundColor White
}
function Write-Step([int]$Number, [int]$Total, [string]$Text) {
    Write-Host ''
    Write-Host ("[{0}/{1}] {2}" -f $Number, $Total, $Text) -ForegroundColor Cyan
}
function Write-Info([string]$Text) {
    Write-Host "    $Text"
}
function Write-Ok([string]$Text) {
    Write-Host "    OK: $Text" -ForegroundColor Green
}
function Write-Warn([string]$Text) {
    Write-Host "    PERINGATAN: $Text" -ForegroundColor Yellow
}
function Write-FailNote([string]$Text) {
    Write-Host "    GAGAL: $Text" -ForegroundColor Red
}

function Format-Duration([TimeSpan]$Span) {
    if ($Span.TotalMinutes -ge 1) {
        return ('{0} menit {1} detik' -f [int][Math]::Floor($Span.TotalMinutes), $Span.Seconds)
    }
    return ('{0} detik' -f [int]$Span.TotalSeconds)
}

# ------------------------------------------------------- pemanggilan proses
function Invoke-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [string[]]$Arguments = @()
    )
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $lines = & $File @Arguments 2>&1 | ForEach-Object { "$_" }
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previous
    }
    return [pscustomobject]@{
        Output   = (($lines | Out-String).TrimEnd())
        ExitCode = $code
    }
}

function Invoke-Stream {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory = $true)][string]$What
    )
    & $File @Arguments
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "$What gagal (kode $code). Lihat keluaran di atas."
    }
}

function Invoke-InDir {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$File,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory = $true)][string]$What
    )
    Push-Location -LiteralPath $Directory
    try {
        & $File @Arguments
        $code = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    if ($code -ne 0) {
        throw "$What gagal (kode $code). Lihat keluaran di atas."
    }
}

function ConvertTo-RemoteBash {
    param([Parameter(Mandatory = $true)][string]$ScriptText)
    $normalized = $ScriptText -replace "`r`n", "`n"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($normalized))
    return "echo '$encoded' | base64 -d | bash"
}

function Invoke-Remote {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptText,
        [switch]$MustSucceed,
        [string]$What = 'perintah di server'
    )
    $command = ConvertTo-RemoteBash -ScriptText $ScriptText
    $result = Invoke-Capture -File 'ssh' -Arguments ($SshArgs + @($SshTarget, $command))
    if ($MustSucceed -and $result.ExitCode -ne 0) {
        $message = $result.Output
        if ([string]::IsNullOrWhiteSpace($message)) { $message = "(tanpa keluaran)" }
        throw "$What gagal (kode $($result.ExitCode)): $message"
    }
    return $result
}

# ------------------------------------------------------- berkas & manifes
function Copy-FilteredTree {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string[]]$ExcludeDirNames = @(),
        [string[]]$ExcludeFileNames = @()
    )
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    foreach ($item in Get-ChildItem -LiteralPath $Source -Force) {
        if ($item.PSIsContainer) {
            if ($ExcludeDirNames -contains $item.Name) { continue }
            $childDestination = Join-Path $Destination $item.Name
            Copy-FilteredTree -Source $item.FullName -Destination $childDestination `
                -ExcludeDirNames $ExcludeDirNames -ExcludeFileNames $ExcludeFileNames
            continue
        }
        if ($ExcludeFileNames -contains $item.Name) { continue }
        if ($item.Name -like '*.pyc') { continue }
        if ($item.Name -like '*.pem') { continue }
        if ($item.Name -like '*.key') { continue }
        Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $Destination $item.Name) -Force
    }
}

function Convert-TextFilesToLf {
    param([Parameter(Mandatory = $true)][string]$Root)
    $extensions = @(
        '.py', '.sh', '.toml', '.lock', '.sql', '.yaml', '.yml', '.json', '.md',
        '.txt', '.csv', '.html', '.css', '.js', '.ts', '.tsx', '.jsx', '.ini',
        '.cfg', '.example', '.gitignore'
    )
    $latin1 = [Text.Encoding]::GetEncoding(28591)   # bolak-balik byte 1:1
    $changed = 0
    foreach ($file in Get-ChildItem -LiteralPath $Root -Recurse -Force -File) {
        $extension = $file.Extension.ToLowerInvariant()
        if ($file.Name -eq '.gitignore') { $extension = '.gitignore' }
        if ($extensions -notcontains $extension) { continue }
        $text = $latin1.GetString([IO.File]::ReadAllBytes($file.FullName))
        if (-not $text.Contains("`r`n")) { continue }
        [IO.File]::WriteAllBytes($file.FullName, $latin1.GetBytes($text.Replace("`r`n", "`n")))
        $changed++
    }
    return $changed
}

function Get-ReleaseFiles {
    param([Parameter(Mandatory = $true)][string]$ReleaseDirectory)
    $root = (Resolve-Path -LiteralPath $ReleaseDirectory).Path.TrimEnd('\', '/')
    $files = New-Object System.Collections.Generic.List[object]
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -Force -File) {
        $relative = $file.FullName.Substring($root.Length).TrimStart('\', '/') -replace '\\', '/'
        if ($relative -eq 'SHA' -or $relative -eq 'MANIFEST.sha256') { continue }
        $files.Add([pscustomobject]@{ Path = $relative; FullName = $file.FullName })
    }
    return $files
}

function Test-ReleaseManifest {
    param([Parameter(Mandatory = $true)][string]$ReleaseDirectory)
    $manifestPath = Join-Path $ReleaseDirectory 'MANIFEST.sha256'
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        throw "MANIFEST.sha256 tidak ada di $ReleaseDirectory"
    }
    $lines = [IO.File]::ReadAllLines($manifestPath)
    $seen = @{}
    foreach ($line in $lines) {
        $match = [regex]::Match($line, '^([0-9a-f]{64})  (.+)$')
        if (-not $match.Success) {
            throw "baris manifest tidak valid: $line"
        }
        $expected = $match.Groups[1].Value
        $relative = $match.Groups[2].Value
        if ($seen.ContainsKey($relative)) {
            throw "berkas ganda di manifest: $relative"
        }
        $seen[$relative] = $true
        $full = Join-Path $ReleaseDirectory ($relative -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $full)) {
            throw "berkas di manifest tidak ada: $relative"
        }
        $actual = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) {
            throw "hash tidak cocok: $relative"
        }
    }
    $files = Get-ReleaseFiles -ReleaseDirectory $ReleaseDirectory
    if ($files.Count -ne $lines.Count) {
        throw "jumlah berkas ($($files.Count)) tidak sama dengan baris manifest ($($lines.Count))"
    }
    return $lines.Count
}

# --------------------------------------------------------- status di server
function Get-RemoteState {
    $script = @'
set -u
CUR_FILE=/home/ubuntu/CURRENT_RELEASE
LOCK=/home/ubuntu/.deploy-pegawai-ai.lock
REL_ROOT=/home/ubuntu/releases

echo "CURRENT=$(cat "$CUR_FILE" 2>/dev/null | tr -d '\r\n' || true)"

if command -v flock >/dev/null 2>&1; then
    if [ ! -e "$LOCK" ]; then
        echo "LOCK=free"
    elif ( flock -n 9 ) 9>>"$LOCK" 2>/dev/null; then
        echo "LOCK=free"
    else
        echo "LOCK=busy"
        echo "LOCKINFO=$(tail -n 1 "$LOCK" 2>/dev/null | tr -d '\r\n' || true)"
    fi
else
    echo "LOCK=noflock"
fi

for d in "$REL_ROOT"/*/; do
    [ -d "$d" ] || continue
    s=$(basename "$d")
    case "$s" in
        .*) continue ;;
    esac
    t=$(stat -c %Y "$d/MANIFEST.sha256" 2>/dev/null || true)
    [ -n "$t" ] || t=$(stat -c %Y "$d" 2>/dev/null || echo 0)
    iso=$(date -u -d "@$t" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "?")
    if [ -f "$d/MANIFEST.sha256" ] && [ -f "$d/SHA" ]; then ok=ok; else ok=incomplete; fi
    echo "REL=$s|$t|$iso|$ok"
done

echo "SCRIPT_SHA=$(sha256sum /home/ubuntu/deploy-pegawai-ai.sh 2>/dev/null | cut -d' ' -f1)"
echo "SCRIPT_LOCK=$(grep -c 'flock -n 9' /home/ubuntu/deploy-pegawai-ai.sh 2>/dev/null || true)"
h=$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:8090/api/health 2>/dev/null || true)
echo "HEALTH=${h:-000}"
'@
    $result = Invoke-Remote -ScriptText $script -MustSucceed -What 'membaca status server'
    $state = [pscustomobject]@{
        Current    = ''
        Health     = '000'
        Lock       = 'unknown'
        LockInfo   = ''
        ScriptHash = ''
        ScriptLock = 0
        Releases   = @()
        Raw        = $result.Output
    }
    $releases = New-Object System.Collections.Generic.List[object]
    foreach ($line in ($result.Output -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $match = [regex]::Match($line, '^CURRENT=(.*)$')
        if ($match.Success) { $state.Current = $match.Groups[1].Value; continue }
        $match = [regex]::Match($line, '^HEALTH=(.*)$')
        if ($match.Success) { $state.Health = $match.Groups[1].Value; continue }
        $match = [regex]::Match($line, '^LOCK=(.*)$')
        if ($match.Success) { $state.Lock = $match.Groups[1].Value; continue }
        $match = [regex]::Match($line, '^LOCKINFO=(.*)$')
        if ($match.Success) { $state.LockInfo = $match.Groups[1].Value; continue }
        $match = [regex]::Match($line, '^SCRIPT_SHA=(.*)$')
        if ($match.Success) { $state.ScriptHash = $match.Groups[1].Value; continue }
        $match = [regex]::Match($line, '^SCRIPT_LOCK=(\d+)$')
        if ($match.Success) { $state.ScriptLock = [int]$match.Groups[1].Value; continue }
        $match = [regex]::Match($line, '^REL=([0-9A-Za-z._-]+)\|(\d+)\|(.+)\|([a-z]+)$')
        if ($match.Success) {
            $releases.Add([pscustomobject]@{
                    Sha      = $match.Groups[1].Value
                    Epoch    = $match.Groups[2].Value
                    Date     = $match.Groups[3].Value
                    Manifest = $match.Groups[4].Value
                })
            continue
        }
    }
    $state.Releases = @($releases | Sort-Object -Property { [int64]$_.Epoch } -Descending)
    return $state
}

function Test-RemoteRelease {
    param([Parameter(Mandatory = $true)][string]$Sha)
    $script = @'
set -u
REL=/home/ubuntu/releases/@@SHA@@
if [ ! -d "$REL" ]; then echo "TIDAK_ADA"; exit 1; fi
cd "$REL" || { echo "TIDAK_BISA_MASUK"; exit 2; }
if [ "$(cat SHA 2>/dev/null)" != "@@SHA@@" ]; then echo "SHA_TIDAK_COCOK"; exit 3; fi
if ! sha256sum -c --quiet MANIFEST.sha256; then echo "MANIFEST_GAGAL"; exit 4; fi
N_MAN=$(wc -l < MANIFEST.sha256)
N_FILES=$(find bff www -type f | wc -l)
if [ "$N_MAN" -ne "$N_FILES" ]; then
    echo "JUMLAH_TIDAK_COCOK manifest=$N_MAN berkas=$N_FILES"
    exit 5
fi
echo "OK"
'@
    $script = $script.Replace('@@SHA@@', $Sha)
    $result = Invoke-Remote -ScriptText $script
    return ($result.ExitCode -eq 0 -and $result.Output -match '(?m)^OK\r?$')
}

function Install-RemoteRelease {
    param(
        [Parameter(Mandatory = $true)][string]$Sha,
        [Parameter(Mandatory = $true)][string]$RemoteTar,
        [Parameter(Mandatory = $true)][string]$TarHash
    )
    if ($Sha -notmatch '^[0-9a-f]{7,40}$') { throw "SHA tidak valid: $Sha" }
    if ($TarHash -notmatch '^[0-9a-f]{64}$') { throw "hash arsip tidak valid" }
    if ($RemoteTar -notmatch '^/home/ubuntu/releases/\.upload-[0-9A-Za-z-]+\.tar\.gz$') {
        throw "nama arsip sementara tidak valid: $RemoteTar"
    }
    $script = @'
set -euo pipefail
SHA=@@SHA@@
TAR=@@TAR@@
TARHASH=@@TARHASH@@
REL_ROOT=/home/ubuntu/releases
REL="$REL_ROOT/$SHA"
LOCK=/home/ubuntu/.deploy-pegawai-ai.lock

exec 9>>"$LOCK"
if ! flock -n 9; then
    echo "TERKUNCI: deploy lain sedang berjalan ($(tail -n 1 "$LOCK" 2>/dev/null | tr -d '\r'))"
    exit 3
fi
printf 'pid=%s at=%s\n' "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >&9

if [ ! -f "$TAR" ]; then echo "GAGAL: arsip $TAR tidak ada"; exit 4; fi
ACTUAL=$(sha256sum "$TAR" | cut -d' ' -f1)
if [ "$ACTUAL" != "$TARHASH" ]; then
    echo "GAGAL: checksum arsip tidak cocok (dapat $ACTUAL)"
    exit 5
fi

WORK=$(mktemp -d "$REL_ROOT/.unpack-XXXXXX")
cleanup() { [ -n "${WORK:-}" ] && rm -rf "$WORK"; }
trap cleanup EXIT

tar xzf "$TAR" -C "$WORK"
if [ ! -f "$WORK/SHA" ]; then echo "GAGAL: arsip tidak memuat SHA"; exit 6; fi
if [ "$(cat "$WORK/SHA")" != "$SHA" ]; then echo "GAGAL: SHA di arsip tidak cocok"; exit 7; fi
( cd "$WORK" && sha256sum -c --quiet MANIFEST.sha256 ) || { echo "GAGAL: verifikasi MANIFEST gagal"; exit 8; }
N_MAN=$(wc -l < "$WORK/MANIFEST.sha256")
N_FILES=$(cd "$WORK" && find bff www -type f | wc -l)
if [ "$N_MAN" -ne "$N_FILES" ]; then
    echo "GAGAL: jumlah berkas ($N_FILES) tidak sama dengan manifest ($N_MAN)"
    exit 9
fi
chmod -R u+rwX,go+rX "$WORK"
if [ -e "$REL" ]; then echo "GAGAL: $REL sudah ada"; exit 10; fi
mv "$WORK" "$REL"
WORK=""
rm -f "$TAR"
echo "OK: rilis $SHA terpasang di $REL ($N_MAN berkas)"
'@
    $script = $script.Replace('@@SHA@@', $Sha).Replace('@@TAR@@', $RemoteTar).Replace('@@TARHASH@@', $TarHash)
    return (Invoke-Remote -ScriptText $script -MustSucceed -What 'memasang rilis di server')
}

function Update-RemoteScript {
    param([Parameter(Mandatory = $true)][string]$LocalServerScript)
    # Hanya menyentuh skrip server bila versi di sana belum punya kunci deploy.
    try {
        $state = Get-RemoteState
        if ($state.ScriptLock -gt 0) { return $false }
        $localHash = (Get-FileHash -LiteralPath $LocalServerScript -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($localHash -eq $state.ScriptHash) { return $false }
        $localText = [IO.File]::ReadAllText($LocalServerScript)
        if (-not $localText.Contains('flock -n 9')) {
            Write-Warn 'versi skrip server di commit ini belum memuat kunci deploy; skrip server tidak diubah'
            return $false
        }

        $remoteNew = '/home/ubuntu/.deploy-pegawai-ai.sh.new'
        Invoke-Stream -File 'scp' -Arguments ($ScpArgs + @($LocalServerScript, "$($SshTarget):$remoteNew")) -What 'unggah skrip deploy baru'
        $script = @'
set -euo pipefail
NEW=/home/ubuntu/.deploy-pegawai-ai.sh.new
TARGET=/home/ubuntu/deploy-pegawai-ai.sh
[ -f "$NEW" ] || { echo "GAGAL: $NEW tidak ada"; exit 1; }
bash -n "$NEW" || { echo "GAGAL: sintaks skrip baru salah"; exit 1; }
grep -q 'flock -n 9' "$NEW" || { echo "GAGAL: skrip baru tidak memuat kunci"; exit 1; }
chmod 755 "$NEW"
if [ -f "$TARGET" ]; then
    cp -p "$TARGET" "$TARGET.bak-$(date -u +%Y%m%dT%H%M%SZ)"
fi
mv -f "$NEW" "$TARGET"
echo "OK: skrip server diperbarui"
'@
        $result = Invoke-Remote -ScriptText $script
        if ($result.ExitCode -ne 0) {
            Write-Warn "skrip server tidak diperbarui: $($result.Output)"
            return $false
        }
        $after = Get-RemoteState
        if ($after.ScriptHash -ne $localHash) {
            Write-Warn 'hash skrip server setelah pembaruan tidak sama dengan versi repo'
            return $false
        }
        return $true
    }
    catch {
        Write-Warn "skrip server tidak diperbarui: $($_.Exception.Message)"
        return $false
    }
}

# ------------------------------------------------------------ pemeriksaan
function Assert-Tools {
    foreach ($tool in @('git', 'tar', 'ssh', 'scp')) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            throw "$tool tidak ditemukan di PATH. Pasang dulu sebelum deploy."
        }
    }
    if (-not (Test-Path -LiteralPath $KeyPath)) {
        throw "kunci SSH tidak ditemukan: $KeyPath. Gunakan -KeyPath untuk menunjuk kunci lain."
    }
}

function Assert-Repo {
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'bff'))) {
        throw "folder repo tidak dikenali: $RepoRoot (jalankan skrip ini dari folder repo)."
    }
    $result = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'rev-parse', '--show-toplevel')
    if ($result.ExitCode -ne 0) {
        throw "folder ini bukan repo git: $RepoRoot"
    }
}

function Resolve-TargetCommit {
    param([string]$RequestedRef)

    $fetch = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'fetch', '--prune', 'origin')
    if ($fetch.ExitCode -ne 0) {
        throw "git fetch origin gagal: $($fetch.Output)"
    }
    if (-not [string]::IsNullOrWhiteSpace($fetch.Output)) {
        Write-Info "git fetch: $($fetch.Output)"
    }

    $originMain = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'rev-parse', '--verify', '--quiet', 'origin/main^{commit}')
    if ($originMain.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($originMain.Output)) {
        throw 'origin/main tidak ditemukan. Pastikan remote origin sudah di-fetch.'
    }
    $originMainSha = $originMain.Output.Trim()

    if (-not [string]::IsNullOrWhiteSpace($RequestedRef)) {
        $resolved = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'rev-parse', '--verify', '--quiet', "$RequestedRef^{commit}")
        if ($resolved.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($resolved.Output)) {
            throw "Ref '$RequestedRef' tidak dikenal. Gunakan commit atau branch yang ada di repo ini."
        }
        $commit = $resolved.Output.Trim()
        $ancestor = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'merge-base', '--is-ancestor', $commit, 'origin/main')
        if ($ancestor.ExitCode -eq 1) {
            $shortBad = (Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'rev-parse', '--short=7', $commit)).Output.Trim()
            throw "Ref '$RequestedRef' ($shortBad) bukan bagian dari origin/main. Deploy hanya boleh dari commit yang sudah ada di main; merge ke main dulu."
        }
        if ($ancestor.ExitCode -ne 0) {
            throw "gagal memeriksa apakah '$RequestedRef' bagian dari origin/main: $($ancestor.Output)"
        }
    }
    else {
        $commit = $originMainSha
    }

    $short = (Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'rev-parse', '--short=7', $commit)).Output.Trim()
    if ($short -notmatch '^[0-9a-f]{7,40}$') {
        throw "tidak bisa membaca SHA pendek untuk commit $commit"
    }
    return [pscustomobject]@{
        Commit     = $commit
        Short      = $short
        OriginMain = $originMainSha
    }
}

# --------------------------------------------------------------- rollback
function Show-Releases {
    param($State, [string]$Active)
    Write-Info 'Rilis di server (terbaru dulu, waktu UTC):'
    foreach ($release in $State.Releases) {
        $marker = ''
        if ($release.Sha -eq $Active) { $marker = '  <- aktif' }
        $integrity = ''
        if ($release.Manifest -ne 'ok') { $integrity = '  (tidak utuh)' }
        Write-Info ('  {0}  {1}{2}{3}' -f $release.Date, $release.Sha, $marker, $integrity)
    }
}

function Invoke-RollbackFlow {
    Write-Head 'Rollback Pegawai AI'
    Write-Info "Server : $SshTarget"
    if ($DryRun) { Write-Info 'Mode   : DRY RUN (tidak ada perubahan di server)' }

    $state = Get-RemoteState
    if ($state.Lock -eq 'busy') {
        throw "deploy lain sedang berjalan di server ($($state.LockInfo)). Tunggu sampai selesai."
    }
    if ([string]::IsNullOrWhiteSpace($state.Current)) {
        throw "CURRENT_RELEASE di server kosong; tidak bisa menentukan rilis sebelumnya."
    }
    Write-Info "Rilis aktif sekarang: $($state.Current)"
    Show-Releases -State $state -Active $state.Current

    $currentIndex = -1
    for ($i = 0; $i -lt $state.Releases.Count; $i++) {
        if ($state.Releases[$i].Sha -eq $state.Current) { $currentIndex = $i; break }
    }
    if ($currentIndex -lt 0) {
        throw "rilis aktif '$($state.Current)' tidak ada di $RemoteReleases. Periksa manual; rollback dibatalkan."
    }
    $previousIndex = $currentIndex + 1
    if ($previousIndex -ge $state.Releases.Count) {
        throw "tidak ada rilis sebelumnya yang tersimpan (housekeeping menyisakan 3 rilis)."
    }
    $previous = $state.Releases[$previousIndex]
    if ($previous.Manifest -ne 'ok') {
        throw "rilis $($previous.Sha) di server tidak utuh (MANIFEST/SHA tidak lengkap). Rollback dibatalkan."
    }

    Write-Info "Rilis tujuan rollback: $($previous.Sha) ($($previous.Date))"
    if (-not (Test-RemoteRelease -Sha $previous.Sha)) {
        throw "verifikasi MANIFEST rilis $($previous.Sha) di server gagal. Rollback dibatalkan."
    }
    Write-Ok "manifest rilis $($previous.Sha) utuh"

    if ($DryRun) {
        Write-Head 'DRY RUN selesai'
        Write-Info "Rencana: jalankan di server: bash $RemoteScript $($previous.Sha)"
        Write-Info 'Tidak ada perintah deploy yang dijalankan.'
        return
    }

    if (-not $Yes) {
        $answer = Read-Host "Ketik 'ya' untuk rollback ke $($previous.Sha)"
        if ($null -eq $answer -or $answer.Trim().ToLowerInvariant() -ne 'ya') {
            Write-Host 'Dibatalkan. Tidak ada perubahan di server.' -ForegroundColor Yellow
            return
        }
    }

    Write-Step 1 3 "Rollback ke rilis $($previous.Sha) di server (keluaran langsung)"
    $remoteCommand = "bash $RemoteScript '$($previous.Sha)'"
    & ssh @SshArgs $SshTarget $remoteCommand
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "rollback di server gagal (kode $code). Keluaran di atas menunjukkan langkah yang gagal."
    }
    Write-Ok 'skrip deploy server selesai'

    Write-Step 2 3 'Perbarui skrip server bila versi lama (tanpa kunci deploy)'
    $originRef = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'rev-parse', '--verify', '--quiet', 'origin/main')
    if ($originRef.ExitCode -eq 0) {
        $serverScriptText = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, '-c', 'core.autocrlf=false', 'show', 'origin/main:vps/deploy_release.sh')
        if ($serverScriptText.ExitCode -eq 0) {
            $tempScript = Join-Path ([IO.Path]::GetTempPath()) ("pegawai-ai-deploy-server-" + [Guid]::NewGuid().ToString('N').Substring(0, 8) + '.sh')
            [IO.File]::WriteAllText($tempScript, (($serverScriptText.Output -replace "`r`n", "`n") + "`n"), $Utf8NoBom)
            try {
                $updated = Update-RemoteScript -LocalServerScript $tempScript
                if ($updated) { Write-Ok 'skrip server diperbarui; kunci deploy aktif untuk deploy berikutnya' }
                else { Write-Info 'skrip server tidak perlu diubah' }
            }
            finally {
                Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    Write-Step 3 3 'Ringkasan'
    $after = Get-RemoteState
    Write-Info "Rilis aktif : $($after.Current)"
    Write-Info "Health      : $($after.Health)"
    Write-Info "Durasi      : $(Format-Duration $Stopwatch.Elapsed)"
    if ($after.Current -ne $previous.Sha) {
        throw "server melaporkan rilis aktif '$($after.Current)', bukan '$($previous.Sha)'."
    }
    if ($after.Health -ne '200') {
        throw "health BFF bukan 200 (dapat $($after.Health)). Periksa journal di server."
    }
    Write-Ok "rollback selesai: rilis $($previous.Sha) aktif dan sehat"
}

# ------------------------------------------------------------------ deploy
function Invoke-DeployFlow {
    $targetInfo = Resolve-TargetCommit -RequestedRef $Ref
    $sha = $targetInfo.Short

    Write-Head 'Deploy Pegawai AI'
    Write-Info "Target      : origin/main = $sha ($($targetInfo.Commit))"
    if ($targetInfo.Commit -ne $targetInfo.OriginMain) {
        Write-Info "Catatan     : commit ini bukan ujung origin/main, tetapi sudah menjadi bagiannya."
    }
    if ($DryRun) { Write-Info 'Mode        : DRY RUN (tidak mengunggah, tidak mendeploy)' }
    Write-Info 'Sumber      : git archive dari commit; perubahan lokal di working tree tidak ikut dibangun.'
    if ($SkipTests) {
        Write-Warn 'uji backend dilewati (-SkipTests). Regresi tidak akan terdeteksi sebelum deploy.'
    }

    # ---- 1. uji backend
    Write-Step 1 $TotalSteps 'Siapkan sumber dan uji backend'
    $tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('pegawai-ai-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    $script:TempRoot = $tempRoot
    if ($tempRoot.StartsWith($RepoRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "folder sementara berada di dalam repo ($tempRoot); deploy dibatalkan."
    }

    $sourceTar = Join-Path $tempRoot 'source.tar'
    $archive = Invoke-Capture -File 'git' -Arguments @(
        '-C', $RepoRoot, '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
        'archive', '--format=tar', "--output=$sourceTar", $targetInfo.Commit
    )
    if ($archive.ExitCode -ne 0) {
        throw "git archive gagal: $($archive.Output)"
    }
    $source = Join-Path $tempRoot 'src'
    New-Item -ItemType Directory -Path $source -Force | Out-Null
    Invoke-Stream -File 'tar' -Arguments @('-xf', $sourceTar, '-C', $source) -What 'ekstrak git archive'

    $bffSource = Join-Path $source 'bff'
    $frontendSource = Join-Path $source 'frontend'
    foreach ($required in @(
            (Join-Path $bffSource 'pyproject.toml'),
            (Join-Path $bffSource 'uv.lock'),
            (Join-Path $frontendSource 'package.json'),
            (Join-Path $frontendSource 'package-lock.json')
        )) {
        if (-not (Test-Path -LiteralPath $required)) {
            throw "commit $sha tidak memuat berkas yang dibutuhkan: $required"
        }
    }

    if ($SkipTests) {
        Write-Warn 'langkah uji dilewati'
    }
    else {
        $uv = Get-Command uv -ErrorAction SilentlyContinue
        if (-not $uv) { throw 'uv tidak ditemukan di PATH. Pasang uv dulu (uji dan deploy butuh uv).' }
        $pytestBase = Join-Path $tempRoot 'pytest-tmp'
        Write-Info 'menjalankan uv run --frozen pytest (keluaran langsung)'
        # Tes lama memakai header X-Pegawai-AI-Key yang nilainya dibaca dari config/.env.
        # Arsip git tidak memuat .env, jadi beri nilai uji (bukan rahasia) selama tes saja.
        $previousKey = $env:BFF_API_KEY
        $env:BFF_API_KEY = 'uji-deploy-lokal'
        try {
            Invoke-InDir -Directory $bffSource -File $uv.Source -Arguments @(
                'run', '--frozen', 'pytest', '-q', '-p', 'no:cacheprovider', "--basetemp=$pytestBase"
            ) -What 'uji backend'
        }
        finally {
            if ($null -eq $previousKey) {
                Remove-Item Env:BFF_API_KEY -ErrorAction SilentlyContinue
            }
            else {
                $env:BFF_API_KEY = $previousKey
            }
        }
        Write-Ok 'uji backend lulus'
    }

    # ---- 2. build frontend
    Write-Step 2 $TotalSteps 'Build frontend di laptop'
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) { throw 'npm tidak ditemukan di PATH. Pasang Node.js/npm dulu.' }
    Write-Info 'npm ci'
    Invoke-InDir -Directory $frontendSource -File $npm.Source -Arguments @('ci', '--no-audit', '--no-fund') -What 'npm ci'
    Write-Info 'npm run build'
    Invoke-InDir -Directory $frontendSource -File $npm.Source -Arguments @('run', 'build') -What 'npm run build'
    $dist = Join-Path $frontendSource 'dist'
    if (-not (Test-Path -LiteralPath (Join-Path $dist 'index.html'))) {
        throw "build frontend tidak menghasilkan $dist\index.html"
    }
    $distFiles = @(Get-ChildItem -LiteralPath $dist -Recurse -Force -File)
    Write-Ok "frontend dibangun: $($distFiles.Count) berkas"

    # ---- 3. rakit rilis
    Write-Step 3 $TotalSteps 'Rakit rilis (bff + www + SHA + MANIFEST)'
    $release = Join-Path $tempRoot 'release'
    New-Item -ItemType Directory -Path $release -Force | Out-Null
    $bffDestination = Join-Path $release 'bff'
    Copy-FilteredTree -Source $bffSource -Destination $bffDestination `
        -ExcludeDirNames @('.venv', '__pycache__', '.pytest_cache', '.ruff_cache', 'node_modules', 'dist', '.git') `
        -ExcludeFileNames @('.env', '.env.local')
    $wwwDestination = Join-Path $release 'www'
    Copy-FilteredTree -Source $dist -Destination $wwwDestination

    $leakedEnv = @(Get-ChildItem -LiteralPath $release -Recurse -Force -File | Where-Object { $_.Name -eq '.env' -or $_.Name -eq '.env.local' })
    if ($leakedEnv.Count -gt 0) {
        throw "berkas rahasia ikut masuk rilis: $($leakedEnv[0].FullName). Deploy dibatalkan."
    }

    # Isi bff harus sama persis dengan commit (kecuali berkas yang sengaja dikecualikan).
    $treeResult = Invoke-Capture -File 'git' -Arguments @('-C', $RepoRoot, 'ls-tree', '-r', '--name-only', $targetInfo.Commit, 'bff')
    if ($treeResult.ExitCode -ne 0) { throw "git ls-tree gagal: $($treeResult.Output)" }
    $expected = @($treeResult.Output -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $actual = @(Get-ReleaseFiles -ReleaseDirectory $bffDestination | ForEach-Object { 'bff/' + $_.Path })
    $missing = @($expected | Where-Object { $actual -notcontains $_ })
    $extra = @($actual | Where-Object { $expected -notcontains $_ })
    if ($missing.Count -gt 0 -or $extra.Count -gt 0) {
        $detail = @()
        if ($missing.Count -gt 0) { $detail += ('hilang: ' + (($missing | Select-Object -First 5) -join ', ')) }
        if ($extra.Count -gt 0) { $detail += ('kelebihan: ' + (($extra | Select-Object -First 5) -join ', ')) }
        throw "isi bff tidak sama dengan commit $sha ($($detail -join '; '))."
    }

    $lfChanged = Convert-TextFilesToLf -Root $bffDestination
    if ($lfChanged -gt 0) {
        Write-Info "$lfChanged berkas teks di bff dinormalisasi ke LF."
    }

    [IO.File]::WriteAllText((Join-Path $release 'SHA'), "$sha`n", $Utf8NoBom)

    $manifestLines = @()
    foreach ($file in (Get-ReleaseFiles -ReleaseDirectory $release | Sort-Object -Property Path)) {
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $manifestLines += "$hash  $($file.Path)"
    }
    if ($manifestLines.Count -eq 0) { throw 'rilis kosong; tidak ada berkas untuk manifest.' }
    $manifestText = ($manifestLines -join "`n") + "`n"
    [IO.File]::WriteAllText((Join-Path $release 'MANIFEST.sha256'), $manifestText, $Utf8NoBom)
    $manifestCount = $manifestLines.Count
    $bffCount = @(Get-ReleaseFiles -ReleaseDirectory $bffDestination).Count
    $wwwCount = @(Get-ReleaseFiles -ReleaseDirectory $wwwDestination).Count
    Write-Ok "$bffCount berkas bff + $wwwCount berkas www; MANIFEST.sha256 $manifestCount entri"

    $verified = Test-ReleaseManifest -ReleaseDirectory $release
    Write-Ok "manifest lokal terverifikasi ($verified entri)"

    # ---- 4. arsip
    Write-Step 4 $TotalSteps 'Buat arsip rilis dan verifikasi ulang'
    $tarPath = Join-Path $tempRoot "pegawai-ai-$sha.tar.gz"
    Invoke-Stream -File 'tar' -Arguments @('-czf', $tarPath, '-C', $release, 'bff', 'www', 'SHA', 'MANIFEST.sha256') -What 'buat arsip rilis'
    $tarInfo = Get-Item -LiteralPath $tarPath
    $tarHash = (Get-FileHash -LiteralPath $tarPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $tarSize = '{0:N0}' -f $tarInfo.Length
    Write-Info "arsip: $tarPath"
    Write-Info "ukuran: $tarSize byte; sha256: $tarHash"

    $verify = Join-Path $tempRoot 'verify'
    New-Item -ItemType Directory -Path $verify -Force | Out-Null
    Invoke-Stream -File 'tar' -Arguments @('-xzf', $tarPath, '-C', $verify) -What 'uji ekstrak arsip rilis'
    foreach ($entry in @('SHA', 'MANIFEST.sha256')) {
        if (-not (Test-Path -LiteralPath (Join-Path $verify $entry))) {
            throw "arsip tidak memuat $entry di akar arsip."
        }
    }
    $verifyCount = Test-ReleaseManifest -ReleaseDirectory $verify
    Write-Ok "arsip terverifikasi: $verifyCount entri, SHA dan MANIFEST sesuai"
    Remove-Item -LiteralPath $verify -Recurse -Force -ErrorAction SilentlyContinue

    # ---- 5. periksa server
    Write-Step 5 $TotalSteps 'Periksa server (kunci deploy, rilis aktif, rilis tujuan)'
    $state = $null
    try {
        $state = Get-RemoteState
    }
    catch {
        if ($DryRun) {
            Write-Warn "status server tidak terbaca: $($_.Exception.Message)"
        }
        else {
            throw
        }
    }

    $releaseReusable = $false
    if ($null -ne $state) {
        Write-Info "Rilis aktif : $($state.Current)"
        Write-Info "Health BFF  : $($state.Health)"
        if ($state.Lock -eq 'busy') {
            if ($DryRun) {
                Write-Warn "deploy lain sedang berjalan di server ($($state.LockInfo)); deploy nyata akan menolak."
            }
            else {
                throw "deploy lain sedang berjalan di server ($($state.LockInfo)). Tunggu sampai selesai; jangan hapus berkas kunci."
            }
        }
        elseif ($state.Lock -eq 'free') {
            Write-Info 'Kunci deploy: bebas'
        }
        else {
            Write-Warn 'flock tidak tersedia di server; kunci deploy tidak bisa diperiksa.'
        }

        $existing = @($state.Releases | Where-Object { $_.Sha -eq $sha })
        if ($existing.Count -gt 0) {
            Write-Info "Rilis $sha sudah ada di server."
            if ($existing[0].Manifest -eq 'ok' -and (Test-RemoteRelease -Sha $sha)) {
                $releaseReusable = $true
                Write-Ok 'manifest rilis yang ada utuh; akan dipakai ulang (tanpa unggah)'
            }
            else {
                Write-Warn "rilis $sha di server tidak utuh (MANIFEST gagal)."
                if (-not $DryRun) {
                    throw "rilis /home/ubuntu/releases/$sha sudah ada tetapi tidak utuh. Hapus dulu di server (pastikan bukan rilis aktif): rm -rf $RemoteReleases/$sha, lalu jalankan ulang."
                }
            }
        }
        else {
            Write-Info "Rilis $sha belum ada di server; akan diunggah."
        }

        if ($state.ScriptLock -gt 0) {
            Write-Info 'Skrip server: sudah memakai kunci deploy (flock).'
        }
        else {
            Write-Info 'Skrip server: versi lama tanpa kunci; akan diperbarui setelah deploy berhasil.'
        }
    }

    # ---- 6/7. unggah + deploy
    if ($DryRun) {
        Write-Step 6 $TotalSteps 'Rencana unggah (dry run)'
        if ($releaseReusable) {
            Write-Info "dilewati: rilis $sha sudah ada dan utuh"
        }
        else {
            $remoteTar = "$RemoteReleases/.upload-$sha-<stempel>.tar.gz"
            Write-Info "scp $tarPath -> $SshTarget`:$remoteTar"
            Write-Info "pasang ke $RemoteReleases/$sha setelah verifikasi sha256 + MANIFEST"
        }
        Write-Step 7 $TotalSteps 'Rencana deploy (dry run)'
        Write-Info "bash $RemoteScript $sha"
        Write-Head 'DRY RUN selesai'
        Write-Info "Rilis $sha siap dideploy ($tarSize byte)."
        Write-Info 'Tidak ada berkas yang diunggah dan tidak ada perintah deploy yang dijalankan.'
        Write-Info "Durasi persiapan: $(Format-Duration $Stopwatch.Elapsed)"
        return
    }

    if ($state -eq $null) {
        throw 'status server tidak terbaca; deploy dibatalkan.'
    }

    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $remoteTarPath = "$RemoteReleases/.upload-$sha-$stamp.tar.gz"

    Write-Step 6 $TotalSteps 'Unggah dan pasang rilis di server'
    if ($releaseReusable) {
        Write-Info "memakai rilis yang sudah ada: $RemoteReleases/$sha"
    }
    else {
        Write-Info "unggah $tarSize byte -> $($SshTarget):$remoteTarPath"
        Invoke-Stream -File 'scp' -Arguments ($ScpArgs + @($tarPath, "$($SshTarget):$remoteTarPath")) -What 'unggah arsip rilis'
        $install = Install-RemoteRelease -Sha $sha -RemoteTar $remoteTarPath -TarHash $tarHash
        Write-Info $install.Output
        if (-not (Test-RemoteRelease -Sha $sha)) {
            throw "rilis $sha terpasang tetapi verifikasi manifest di server gagal."
        }
        Write-Ok "rilis terpasang dan terverifikasi di $RemoteReleases/$sha"
    }

    Write-Step 7 $TotalSteps "Deploy di server: bash $RemoteScript $sha"
    $deployWatch = [Diagnostics.Stopwatch]::StartNew()
    $remoteCommand = "bash $RemoteScript '$sha'"
    & ssh @SshArgs $SshTarget $remoteCommand
    $code = $LASTEXITCODE
    $deployWatch.Stop()
    if ($code -ne 0) {
        throw "deploy di server gagal (kode $code). Bila health gagal, skrip server sudah mencoba rollback otomatis; baca keluaran di atas."
    }
    Write-Ok "skrip deploy server selesai dalam $(Format-Duration $deployWatch.Elapsed)"

    $scriptUpdateSource = Join-Path $source 'vps/deploy_release.sh'
    if (Test-Path -LiteralPath $scriptUpdateSource) {
        $updated = Update-RemoteScript -LocalServerScript $scriptUpdateSource
        if ($updated) { Write-Ok 'skrip server diperbarui; kunci deploy aktif untuk deploy berikutnya' }
        else { Write-Info 'skrip server tidak perlu diubah' }
    }

    Write-Head 'Ringkasan'
    $after = Get-RemoteState
    Write-Info "Rilis aktif : $($after.Current)"
    Write-Info "Health BFF  : $($after.Health)"
    Write-Info "Durasi total: $(Format-Duration $Stopwatch.Elapsed)"
    if ($after.Current -ne $sha) {
        throw "server melaporkan rilis aktif '$($after.Current)', bukan '$sha'."
    }
    if ($after.Health -ne '200') {
        throw "health BFF bukan 200 (dapat $($after.Health)). Periksa journal di server."
    }
    Write-Ok "rilis $sha aktif dan sehat"
}

# ------------------------------------------------------------------- utama
$exitCode = 0
try {
    Assert-Tools
    Assert-Repo

    if ($Rollback) {
        if ($PSBoundParameters.ContainsKey('Ref') -and -not [string]::IsNullOrWhiteSpace($Ref)) {
            throw '-Rollback tidak bisa digabung dengan -Ref.'
        }
        Invoke-RollbackFlow
    }
    else {
        Invoke-DeployFlow
    }
}
catch {
    Write-Host ''
    Write-FailNote $_.Exception.Message
    $exitCode = 1
}
finally {
    if ($null -ne $TempRoot -and (Test-Path -LiteralPath $TempRoot)) {
        try {
            Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction Stop
        }
        catch {
            Start-Sleep -Seconds 1
            & cmd.exe /c "rd /s /q `"$TempRoot`"" 2>$null | Out-Null
        }
        if (Test-Path -LiteralPath $TempRoot) {
            Write-Warn "folder sementara belum terhapus: $TempRoot (hapus manual bila perlu)"
        }
    }
}
exit $exitCode
