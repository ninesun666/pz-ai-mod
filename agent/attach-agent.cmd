@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 游戏如果是提权运行的，非管理员 attach 会“拒绝访问”，所以先要管理员
net session >nul 2>&1
if not "%errorlevel%"=="0" (
  echo Requesting administrator rights...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

set "JDK=%JAVA_HOME%"
if "%JDK%"=="" if exist "C:\Users\gjx\Desktop\workspace\workspace\envronment\jdk1.8.0_181\bin\javac.exe" set "JDK=C:\Users\gjx\Desktop\workspace\workspace\envronment\jdk1.8.0_181"
if "%JDK%"=="" (
  echo [!] JAVA_HOME not set and no known JDK found.
  echo     Set JAVA_HOME to a JDK 8+ folder, then run this again.
  pause & exit /b 1
)

set "PID="
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "(Get-Process ProjectZomboid64 -ErrorAction SilentlyContinue | Select-Object -First 1).Id"') do set "PID=%%i"
if "%PID%"=="" ( echo [!] Project Zomboid is not running. & pause & exit /b 1 )
echo Target PID: %PID%

set "AGENT=%~dp0dcaiv-agent.jar"
if not exist "%AGENT%" ( echo [!] dcaiv-agent.jar not found & pause & exit /b 1 )

if not exist "%~dp0Attach.class" (
  "%JDK%\bin\javac.exe" -cp "%JDK%\lib\tools.jar" -d "%~dp0" "%~dp0Attach.java" || goto :fail
)
"%JDK%\jre\bin\java.exe" -cp "%~dp0;%JDK%\lib\tools.jar" Attach %PID% "%AGENT%"

echo.
echo Check: %%USERPROFILE%%\Zomboid\dcagent.log
pause
exit /b 0

:fail
echo [!] compile failed
pause
exit /b 1
