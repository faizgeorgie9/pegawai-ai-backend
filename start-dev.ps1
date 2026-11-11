# Starts the Hermes gateway (8642), the BFF (8090) and the frontend (5173) with no extra windows:
# each runs hidden and writes its log to .dev-logs\. This window stays as the one control window;
# press Enter (or Ctrl+C) here to stop everything it started. Needs Postgres and bff\.env (see README, "Menjalankan BFF").
# Usage: .\start-dev.ps1 [-NoBrowser] [-NoWait]
#   -NoWait  start the services and return at once (stop them later with .\stop-dev.ps1)
param(
    [switch]$NoBrowser,
    [switch]$NoWait
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$host.UI.RawUI.WindowTitle = 'Pegawai AI'

$bffDir = Join-Path $PSScriptRoot 'bff'
$frontendDir = Join-Path $PSScriptRoot 'frontend'
$logDir = Join-Path $PSScriptRoot '.dev-logs'
$port = 5173
$frontendUrl = "http://localhost:$port/"
$healthUrl = 'http://127.0.0.1:8090/api/health'
$hermesUrl = 'http://127.0.0.1:8642/health'
New-Item -ItemType Directory -Force $logDir | Out-Null

function Test-Url($url) {
    try { (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 } catch { $false }
}

function Wait-Url($url, $seconds) {
    for ($i = 0; $i -lt $seconds; $i++) {
        if (Test-Url $url) { return $true }
        Start-Sleep -Seconds 1
    }
    $false
}

# Runs a command hidden, stdout and stderr to .dev-logs\<name>.log and .err.log. Returns the process.
function Start-Hidden($name, $dir, $command) {
    $out = Join-Path $logDir "$name.log"
    $err = Join-Path $logDir "$name.err.log"
    Start-Process powershell -WorkingDirectory $dir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err `
        -ArgumentList '-NoProfile', '-Command', $command
}

# Setup checks.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv tidak ditemukan. Pasang uv terlebih dahulu.' }
if (-not (Test-Path (Join-Path $bffDir '.env'))) { throw 'bff\.env belum ada. Salin bff\.env.example dan isi sesuai README, bagian "Menjalankan BFF".' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm tidak ditemukan. Pasang Node.js 22 atau lebih baru.' }
if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host 'Memasang dependensi frontend...' -ForegroundColor Yellow
    Push-Location $frontendDir
    try { npm ci } finally { Pop-Location }
}

$started = @()

# Hermes gateway. Reused when something already answers on 8642.
if (Test-Url $hermesUrl) {
    Write-Host 'Hermes gateway sudah berjalan (8642).' -ForegroundColor Green
} else {
    Write-Host 'Menyalakan Hermes gateway (8642)...' -ForegroundColor Cyan
    $started += Start-Hidden 'hermes' $PSScriptRoot 'hermes gateway run'
    if (-not (Wait-Url $hermesUrl 30)) { Write-Warning "Hermes gateway belum menjawab. Lihat $logDir\hermes.err.log." }
}

# BFF. The loop flag is needed on Windows: psycopg cannot use the default ProactorEventLoop.
if (Test-Url $healthUrl) {
    Write-Host 'BFF sudah berjalan (8090).' -ForegroundColor Green
} else {
    Write-Host 'Menyalakan BFF (8090)...' -ForegroundColor Cyan
    $started += Start-Hidden 'bff' $bffDir 'uv run uvicorn bff.main:app --host 127.0.0.1 --port 8090 --loop asyncio:SelectorEventLoop'
    if (-not (Wait-Url $healthUrl 60)) { throw "BFF tidak menjawab dalam 60 detik. Lihat $logDir\bff.err.log (biasanya DATABASE_URL atau Postgres)." }
}

# Frontend. npm.cmd, not npm: PowerShell drops the "--" before npm.ps1 sees it, so vite would get "5173" as its root folder.
if (Test-Url $frontendUrl) {
    Write-Host "Frontend sudah berjalan ($port)." -ForegroundColor Green
} else {
    Write-Host "Menyalakan frontend ($port)..." -ForegroundColor Cyan
    $started += Start-Hidden 'frontend' $frontendDir "npm.cmd run dev -- --port $port --strictPort"
    if (-not (Wait-Url $frontendUrl 60)) { throw "Frontend tidak menjawab dalam 60 detik. Lihat $logDir\frontend.log." }
}

Write-Host "Siap: $frontendUrl   (log: $logDir)" -ForegroundColor Green
if (-not $NoBrowser) { Start-Process $frontendUrl }
if ($NoWait) { Write-Host 'Untuk berhenti: .\stop-dev.ps1'; return }

# Stays open as the single control window; Enter or Ctrl+C stops what this script started.
# Closing the window with X skips this: then run .\stop-dev.ps1.
try {
    Write-Host 'Tekan Enter untuk menghentikan semua layanan.'
    [void](Read-Host)
} finally {
    foreach ($p in $started) {
        # /T stops the whole tree (powershell -> uv -> python, npm -> node).
        & taskkill.exe /PID $p.Id /T /F 2>$null | Out-Null
    }
    Write-Host 'Semua layanan dihentikan.' -ForegroundColor Yellow
}
