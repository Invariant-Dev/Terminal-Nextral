@echo off
title Nextral - Build System
cls
echo ============================================================
echo   NEXTRAL TERMINAL - BUILD SYSTEM (Full)
echo   [NOTE: This script builds Windows .exe files only]
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check pip / pyinstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [1/5] Installing PyInstaller and dependencies...
    pip install pyinstaller textual rich psutil pyperclip pillow jinja2 aiohttp httpx pyfiglet
) else (
    echo [1/5] Dependencies already present.
)

echo.
echo [2/5] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "build_temp" rmdir /s /q "build_temp"

echo.
echo [3/5] Building Nextral.exe (main application)...
python -m PyInstaller nextral.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] Main application build failed!
    pause
    exit /b 1
)

if not exist "dist\Nextral.exe" (
    echo [ERROR] dist\Nextral.exe not found after build!
    pause
    exit /b 1
)

echo.
echo [4/5] Building Nextral-Setup.exe (installer)...
REM installer.spec will auto-bundle dist\Nextral.exe
python -m PyInstaller installer.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] Installer build failed!
    pause
    exit /b 1
)

echo.
echo [5/5] Verifying outputs...
echo.
if exist "dist\Nextral.exe" (
    for %%F in ("dist\Nextral.exe") do set MAIN_SIZE=%%~zF
    echo   [OK] dist\Nextral.exe
    dir /nh "dist\Nextral.exe" | find "Nextral.exe"
) else (
    echo   [MISSING] dist\Nextral.exe
)

if exist "dist\Nextral-Setup.exe" (
    echo   [OK] dist\Nextral-Setup.exe
    dir /nh "dist\Nextral-Setup.exe" | find "Nextral-Setup.exe"
) else (
    echo   [MISSING] dist\Nextral-Setup.exe
)

echo.
echo ============================================================
echo   BUILD COMPLETE
echo ============================================================
echo.
echo   Share: dist\Nextral-Setup.exe  (includes Nextral.exe inside)
echo.
pause
