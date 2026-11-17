@echo off
chcp 65001 > nul
title Pegawai AI — 5-Agent Colorbox Marketing Automation
cls
echo ==============================================================================
echo   MENJALANKAN 5-AGENT AUTOMATION BOT COLORBOX (DEEPSEEK + GEMINI)
echo ==============================================================================
python "%~dp0pegawai_colorbox_bot.py" %*
pause

