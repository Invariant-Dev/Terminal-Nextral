@echo off
title Nextral - Linux Docker Build System
cls
echo ============================================================
echo   NEXTRAL TERMINAL - LINUX DOCKER BUILD
echo ============================================================
echo.
echo This script uses Docker to build a genuine Linux executable
echo while you are on Windows. Make sure Docker Desktop is running!
echo.

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop for Windows and make sure it is running.
    pause
    exit /b 1
)

echo [1/3] Pulling Python 3.10 Linux image (if not already cached)...
echo.
docker pull python:3.10-slim
if errorlevel 1 (
    echo [ERROR] Failed to pull Docker image. Check your internet or Docker daemon.
    pause
    exit /b 1
)

echo.
echo [2/3] Building Nextral for Linux inside Docker...
echo Note: This may take a few minutes as it installs Python dependencies in the container.
echo.

REM Map the current directory into the container and run the build script.
REM We install dos2unix to fix CRLF line endings from Windows checkouts before running the sh script.
docker run --rm -v "%cd%:/app" -w /app python:3.10-slim /bin/bash -c "apt-get update && apt-get install -y dos2unix binutils && dos2unix build_linux.sh && chmod +x build_linux.sh && ./build_linux.sh"

if errorlevel 1 (
    echo.
    echo [ERROR] Docker build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying outputs...
echo.
if exist "dist\Nextral" (
    echo   [OK] dist\Nextral (Linux Binary)
) else (
    echo   [MISSING] dist\Nextral
)

if exist "dist\Nextral-Setup" (
    echo   [OK] dist\Nextral-Setup (Linux Installer)
) else (
    echo   [MISSING] dist\Nextral-Setup
)

echo.
echo ============================================================
echo   DOCKER BUILD COMPLETE
echo ============================================================
echo.
echo The Linux executables are safely located in the 'dist' folder.
echo You can now run or distribute 'dist\Nextral' on any Linux system.
echo.
pause
