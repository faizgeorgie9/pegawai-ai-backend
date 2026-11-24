# Script Pengujian Live Telegram Bot Pegawai AI (VPS)
param(
    [string]$Pesan = "Halo kak, bagaimana syarat retur barang yang cacat?"
)

$VPS_URL = "https://139.190.107.151.sslip.io/bff/api/telegram/simulate"
$BFF_KEY = "mh6IG_kqNfpu4YJe1Gi8FzM1tzejRPSbWfDSRNFriCI"

# Abaikan self-signed cert jika ada
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  PENGUJIAN LIVE TELEGRAM BOT PEGAWAI AI (VPS 139.190.107.151) " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Kirim Pesan: '$Pesan'" -ForegroundColor Yellow

$Body = @{
    text = $Pesan
    chat_id = 999333222
    sender_name = "User Uji"
} | ConvertTo-Json

try {
    $Response = Invoke-RestMethod -Uri $VPS_URL -Method POST -Headers @{
        "Content-Type" = "application/json"
        "X-Pegawai-AI-Key" = $BFF_KEY
    } -Body $Body

    Write-Host "`n[HASIL RESPON BOT]:" -ForegroundColor Green
    Write-Host "Status    : " -NoNewline; Write-Host $Response.status -ForegroundColor White
    if ($Response.bot_id) {
        Write-Host "Agen Aktif: " -NoNewline; Write-Host $Response.bot_id -ForegroundColor White
    }
    if ($Response.command) {
        Write-Host "Perintah  : " -NoNewline; Write-Host $Response.command -ForegroundColor White
    }
    $Balasan = if ($Response.agent_reply) { $Response.agent_reply } else { $Response.reply }
    Write-Host "`nBalasan Agen:" -ForegroundColor Yellow
    Write-Host $Balasan -ForegroundColor Cyan
} catch {
    Write-Host "`n[ERROR]: $_" -ForegroundColor Red
}

Write-Host "`nTips Perintah Lain yang Bisa Dicoba:" -ForegroundColor Gray
Write-Host "  .\test_telegram.ps1 -Pesan '/start'" -ForegroundColor Gray
Write-Host "  .\test_telegram.ps1 -Pesan '/status'" -ForegroundColor Gray
Write-Host "  .\test_telegram.ps1 -Pesan '/agent bram'" -ForegroundColor Gray
Write-Host "  .\test_telegram.ps1 -Pesan 'buatkan caption IG promo akhir tahun'" -ForegroundColor Gray
