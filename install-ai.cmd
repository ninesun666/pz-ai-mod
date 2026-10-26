@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Installing DC_AIVoice into Project Zomboid mods folder...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-ai.ps1"
echo.
pause
