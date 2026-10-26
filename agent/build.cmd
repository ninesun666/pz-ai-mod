@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "JAVAC=javac"
set "JAR=jar"

where %JAVAC% >nul 2>nul || (
  echo [!] javac not found in PATH. Install a JDK 8+ or add it to PATH.
  pause
  exit /b 1
)

if exist classes rmdir /s /q classes
mkdir classes

echo [1/3] compiling...
%JAVAC% -encoding UTF-8 -source 8 -target 8 -d classes src\com\dcai\agent\Agent.java || goto :fail

echo [2/3] packaging...
> manifest.txt echo Premain-Class: com.dcai.agent.Agent
>> manifest.txt echo Can-Retransform-Classes: true
%JAR% cfm dcaiv-agent.jar manifest.txt -C classes . || goto :fail

echo [3/3] done: %cd%\dcaiv-agent.jar
echo.
echo Next: run install-agent.cmd (adds -javaagent to ProjectZomboid64.json)
pause
exit /b 0

:fail
echo [!] build failed
pause
exit /b 1
