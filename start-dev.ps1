# Starts the shared backend (port 8080) and the frontend (port 5173, or 5174 with -Mock),
# each in its own window, then opens the browser once both answer.
# Usage: .\start-dev.ps1 [-Mock] [-NoBrowser]
param(
    [switch]$Mock,
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$backendDir = Join-Path $PSScriptRoot 'local_setup\backend_template'
$frontendDir = Join-Path $PSScriptRoot 'frontend'
$python = Join-Path $backendDir '.venv\Scripts\python.exe'
$port = if ($Mock) { 5174 } else { 5173 }
$frontendUrl = "http://localhost:$port/"

function Test-Url($url) {
    try { (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch { $false }
}

function Wait-Url($url, $seconds) {
    for ($i = 0; $i -lt $seconds; $i++) {
        if (Test-Url $url) { return $true }
        Start-Sleep -Seconds 1
    }
    $false
}

# Backend setup: the venv and the key file must exist before the server can run a task.
if (-not (Test-Path $python)) {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv tidak ditemukan. Pasang uv, atau buat .venv di local_setup\backend_template secara manual.' }
    Write-Host 'Membuat .venv backend dengan uv...' -ForegroundColor Yellow
    Push-Location $backendDir
    try {
        uv venv .venv
        uv pip install --python .venv\Scripts\python.exe -r requirements.txt pillow
    } finally { Pop-Location }
}
if (-not (Test-Path (Join-Path $backendDir '.env'))) {
    Write-Warning '.env backend belum ada. Salin .env.example menjadi .env; tanpa key, tugas akan gagal.'
}

# Frontend setup.
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm tidak ditemukan. Pasang Node.js 22 atau lebih baru.' }
if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host 'Memasang dependensi frontend...' -ForegroundColor Yellow
    Push-Location $frontendDir
    try { npm ci } finally { Pop-Location }
}

# Backend. Reused if something already answers on 8080.
if (Test-Url 'http://127.0.0.1:8080/health') {
    Write-Host 'Backend sudah berjalan di port 8080.' -ForegroundColor Green
} else {
    Write-Host 'Menyalakan backend di port 8080...' -ForegroundColor Cyan
    Start-Process powershell -WorkingDirectory $backendDir -ArgumentList '-NoExit', '-Command', "`$host.UI.RawUI.WindowTitle='Pegawai AI backend'; & '$python' server.py"
    if (-not (Wait-Url 'http://127.0.0.1:8080/health' 30)) { throw 'Backend tidak menjawab dalam 30 detik. Lihat jendela "Pegawai AI backend".' }
}

# Frontend.
if (Test-Url $frontendUrl) {
    Write-Host "Frontend sudah berjalan di port $port." -ForegroundColor Green
} else {
    $mode = if ($Mock) { ' --mode mock' } else { '' }
    Write-Host "Menyalakan frontend di port $port..." -ForegroundColor Cyan
    # npm.cmd, not npm: PowerShell drops the "--" before npm.ps1 sees it, so vite would get "5173" as its root folder.
    Start-Process powershell -WorkingDirectory $frontendDir -ArgumentList '-NoExit', '-Command', "`$host.UI.RawUI.WindowTitle='Pegawai AI frontend'; npm.cmd run dev -- --port $port --strictPort$mode"
    if (-not (Wait-Url $frontendUrl 60)) { throw 'Frontend tidak menjawab dalam 60 detik. Lihat jendela "Pegawai AI frontend".' }
}

Write-Host "Siap: $frontendUrl" -ForegroundColor Green
if ($Mock) { Write-Host 'Mode data contoh: tidak memanggil model.' -ForegroundColor Yellow }
Write-Host 'Untuk berhenti, tutup jendela "Pegawai AI backend" dan "Pegawai AI frontend".'
if (-not $NoBrowser) { Start-Process $frontendUrl }
