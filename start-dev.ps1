# Starts the BFF (port 8090) and the frontend (port 5173), each in its own window,
# then opens the browser once both answer. Needs Hermes gateway on 8642 and bff\.env (see README, "Menjalankan BFF").
# Usage: .\start-dev.ps1 [-NoBrowser]
param(
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$bffDir = Join-Path $PSScriptRoot 'bff'
$frontendDir = Join-Path $PSScriptRoot 'frontend'
$port = 5173
$frontendUrl = "http://localhost:$port/"
$healthUrl = 'http://127.0.0.1:8090/api/health'

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

# BFF setup: uv installs the dependencies; bff\.env holds DATABASE_URL and BFF_API_KEY.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv tidak ditemukan. Pasang uv terlebih dahulu.' }
if (-not (Test-Path (Join-Path $bffDir '.env'))) { throw 'bff\.env belum ada. Salin bff\.env.example dan isi sesuai README, bagian "Menjalankan BFF".' }

# Frontend setup.
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm tidak ditemukan. Pasang Node.js 22 atau lebih baru.' }
if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host 'Memasang dependensi frontend...' -ForegroundColor Yellow
    Push-Location $frontendDir
    try { npm ci } finally { Pop-Location }
}

# BFF. Reused if something already answers on 8090. The loop flag is needed on Windows: psycopg cannot use the default ProactorEventLoop.
if (Test-Url $healthUrl) {
    Write-Host 'BFF sudah berjalan di port 8090.' -ForegroundColor Green
} else {
    Write-Host 'Menyalakan BFF di port 8090...' -ForegroundColor Cyan
    Start-Process powershell -WorkingDirectory $bffDir -ArgumentList '-NoExit', '-Command', "`$host.UI.RawUI.WindowTitle='Pegawai AI BFF'; uv run uvicorn bff.main:app --host 127.0.0.1 --port 8090 --loop asyncio:SelectorEventLoop"
    if (-not (Wait-Url $healthUrl 60)) { throw 'BFF tidak menjawab dalam 60 detik. Lihat jendela "Pegawai AI BFF" (biasanya DATABASE_URL atau Postgres).' }
}

# Frontend.
if (Test-Url $frontendUrl) {
    Write-Host "Frontend sudah berjalan di port $port." -ForegroundColor Green
} else {
    Write-Host "Menyalakan frontend di port $port..." -ForegroundColor Cyan
    # npm.cmd, not npm: PowerShell drops the "--" before npm.ps1 sees it, so vite would get "5173" as its root folder.
    Start-Process powershell -WorkingDirectory $frontendDir -ArgumentList '-NoExit', '-Command', "`$host.UI.RawUI.WindowTitle='Pegawai AI frontend'; npm.cmd run dev -- --port $port --strictPort"
    if (-not (Wait-Url $frontendUrl 60)) { throw 'Frontend tidak menjawab dalam 60 detik. Lihat jendela "Pegawai AI frontend".' }
}

Write-Host "Siap: $frontendUrl" -ForegroundColor Green
Write-Host 'Untuk berhenti, tutup jendela "Pegawai AI BFF" dan "Pegawai AI frontend".'
if (-not $NoBrowser) { Start-Process $frontendUrl }
