@echo off
rem Double-click to start the backend and frontend. Pass -Mock for sample data.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
pause
