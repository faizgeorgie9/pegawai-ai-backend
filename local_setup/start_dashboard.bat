@echo off
chcp 65001 > nul
title Pegawai AI Web Dashboard (PT AI Top Trends)
echo ======================================================================
echo    MENJALANKAN PEGAWAI AI WEB DASHBOARD (PORT 8080)
echo    Engine: Hermes Agent + DeepSeek V4.1 Flash via Opencode
echo    Perusahaan: PT AI Top Trends (v1.0.0)
echo ======================================================================
echo.
echo Membuka browser di http://127.0.0.1:8080 ...
timeout /t 2 /nobreak > nul
start http://127.0.0.1:8080/
python "%~dp0backend_template\server.py"
pause

