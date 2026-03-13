#!/bin/bash

# Nextral Terminal - macOS Build Script
# Requirements: Python 3.8+, pip

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================================"
echo "  NEXTRAL TERMINAL - macOS BUILD"
echo "============================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found!${NC}"
    echo "Please install Python 3.8+ from python.org or brew install python3"
    exit 1
fi

python3 --version

# Check pip
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${RED}Error: pip not found!${NC}"
    exit 1
fi

# Install dependencies
echo ""
echo "[1/4] Installing Python dependencies..."
python3 -m pip install --upgrade pip > /dev/null 2>&1
python3 -m pip install pyinstaller textual rich psutil pyperclip pillow jinja2 aiohttp httpx markdown uvicorn fastapi pyfiglet > /dev/null 2>&1

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Clean previous builds
echo ""
echo "[2/4] Cleaning previous builds..."
rm -rf dist build __pycache__ 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned${NC}"

# Build
echo ""
echo "[3/4] Building executable..."
python3 -m PyInstaller nextral.spec --clean --noconfirm

# Verify
echo ""
echo "[4/4] Verifying build..."
if [ -f "dist/Nextral" ]; then
    echo ""
    echo "============================================================"
    echo -e "  ${GREEN}BUILD SUCCESSFUL!${NC}"
    echo "============================================================"
    echo ""
    echo "Output: dist/Nextral"
    ls -lh dist/Nextral
    
    # Make executable
    chmod +x dist/Nextral
    echo ""
    echo "Run with: ./dist/Nextral"
else
    echo -e "${RED}Error: Executable not found!${NC}"
    exit 1
fi

echo ""
