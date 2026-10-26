@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Removing DC AI Java agent...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-agent.ps1" -Uninstall
echo.
pause
