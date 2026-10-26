@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Testing the file link WITHOUT a network / API key.
echo Start the game (with DC_AIVoice enabled) in another window, then watch this console.
echo.
python bridge.py --offline
pause
