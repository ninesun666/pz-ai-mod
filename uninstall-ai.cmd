@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Removing DC_AIVoice from Project Zomboid mods folder...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-ai.ps1" -Uninstall
echo.
pause
