# LAUNCHER SISTEM PEGAWAI AI (HERMES MULTI-AGENT)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
Clear-Host
$Host.UI.RawUI.WindowTitle = "SISTEM PEGAWAI AI - PT AI TOP TRENDS"
python "$PSScriptRoot\pegawai_ai_cli.py"
