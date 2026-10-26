@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Installing DC AI Java agent into Project Zomboid...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-agent.ps1"
echo.
pause
