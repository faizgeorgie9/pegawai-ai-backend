# One-shot launcher for this machine: temp Postgres -> BFF -> frontend (gateway too).
# Usage: right-click "Run with PowerShell", or: .\start-all.ps1 [-NoBrowser]
param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

$pgPython = Join-Path $root '.pgvenv\Scripts\python.exe'
if (-not (Test-Path $pgPython)) {
    throw "Postgres venv belum ada di .pgvenv. Jalankan: uv python install 3.12; uv venv .pgvenv; uv pip install --python .pgvenv\Scripts\python.exe pgserver==0.1.4"
}

$pgServe = Join-Path $root 'pg_serve.py'
$pgLog = Join-Path $root 'pg_serve.log'
$pgOut = Join-Path $root 'pg_serve.out'
$pgErr = Join-Path $root 'pg_serve.err'
$pgUri = Join-Path $root 'pg_uri.txt'
$running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -like '*pg_serve.py*' }

if ($running) {
    Write-Host 'Postgres (pgserver) sudah berjalan.' -ForegroundColor Green
} else {
    Write-Host 'Menyalakan Postgres (pgserver)...' -ForegroundColor Cyan
    Remove-Item $pgLog, $pgOut, $pgErr -ErrorAction SilentlyContinue
    Start-Process -FilePath $pgPython -ArgumentList @($pgServe) -WorkingDirectory $root `
        -RedirectStandardOutput $pgOut -RedirectStandardError $pgErr -WindowStyle Hidden
    $ok = $false
    for ($i = 0; $i -lt 120; $i++) {
        Start-Sleep -Seconds 1
        if ((Test-Path $pgLog) -and ((Get-Content $pgLog -Raw -ErrorAction SilentlyContinue) -like 'ready:*')) { $ok = $true; break }
    }
    if (-not $ok) {
        Get-Content $pgErr -Tail 15 -ErrorAction SilentlyContinue
        throw "Postgres tidak siap setelah 120 detik. Lihat $pgErr"
    }
    Write-Host ("Postgres siap: " + (Get-Content $pgUri -Raw).Trim()) -ForegroundColor Green
}

& (Join-Path $root 'start-dev.ps1') -NoBrowser:$NoBrowser
