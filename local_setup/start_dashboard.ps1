# PowerShell Launcher for Pegawai AI Web Dashboard
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   MENJALANKAN PEGAWAI AI WEB DASHBOARD (PORT 8080)" -ForegroundColor Yellow
Write-Host "   Engine: Hermes Agent + DeepSeek V4.1 Flash via Opencode" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Membuka browser di http://127.0.0.1:8080 ..." -ForegroundColor White

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:8080/"
& python "$PSScriptRoot\backend_template\server.py"

