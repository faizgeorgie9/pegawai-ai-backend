# Stops whatever listens on the dev ports: frontend (5173), BFF (8090) and the Hermes gateway (8642),
# and closes leftover windows from older start-dev versions. Postgres is left alone.
# Usage: .\stop-dev.ps1
foreach ($port in 5173, 8090, 8642) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($procId in ($conns.OwningProcess | Sort-Object -Unique)) {
        & taskkill.exe /PID $procId /T /F 2>$null | Out-Null
        Write-Host "Port $port dihentikan (PID $procId)."
    }
}
$titles = 'Hermes gateway', 'Hermes Gateway', 'Pegawai AI BFF', 'Pegawai AI frontend'
Get-Process powershell, pwsh -ErrorAction SilentlyContinue | Where-Object { $titles -contains $_.MainWindowTitle } |
    ForEach-Object { Stop-Process -Id $_.Id -Force }
Write-Host 'Selesai.'
