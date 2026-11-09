@echo off
rem Double-click to start the BFF and the frontend. Pass -NoBrowser to skip opening the browser.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
pause
