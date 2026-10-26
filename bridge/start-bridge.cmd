@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist config.json (
  echo [!] config.json not found.
  echo     Copy config.example.json to config.json, then fill in api_key.
  echo     Or run test-bridge-offline.cmd to test the file link without a key.
  pause
  exit /b 1
)
echo Starting DC_AIVoice bridge... (Ctrl+C to stop)
python bridge.py
pause
