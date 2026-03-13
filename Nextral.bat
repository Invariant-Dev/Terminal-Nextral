@echo off
title Nextral Terminal Launcher
color 0A
cls

echo ================================================
echo    NEXTRAL TERMINAL - Launching...
echo ================================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
    echo.
    python "%~dp0launcher.py"
) else (
    echo [INFO] Requesting Administrator privileges...
    echo.
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %CD% && python launcher.py' -Verb RunAs"
    exit
)

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo ================================================
    echo    An error occurred
    echo ================================================
    echo.
    echo Check the error message above.
    echo.
    pause
)
