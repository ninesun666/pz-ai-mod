@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Installing TTS dependencies (edge-tts + miniaudio)...
python -m pip install --upgrade edge-tts miniaudio
echo.
echo Available voices:
python tts.py --list
echo.
pause
