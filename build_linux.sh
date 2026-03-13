#!/bin/bash

# ══════════════════════════════════════════════════════════════════════════════
#  Nextral Terminal — Linux Build System (Full)
#  Builds:  dist/Nextral          (main application)
#           dist/Nextral-Setup    (professional installer)
# ══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  NEXTRAL TERMINAL — LINUX BUILD SYSTEM${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# ── Detect OS ────────────────────────────────────────────────────────────────
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo -e "${BOLD}Detected OS:${NC} $OS"

if [[ "$OS" == "windows" ]]; then
    echo ""
    echo -e "${RED}Error: This script is intended for Linux environments.${NC}"
    echo -e "To build for Windows, use ${YELLOW}${BOLD}build.bat${NC} instead."
    echo -e "To build for Linux from Windows, use ${YELLOW}${BOLD}build_linux_docker.bat${NC}."
    echo ""
    exit 1
fi

# ── Check Python ─────────────────────────────────────────────────────────────
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found!${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_CMD="python3"
PYTHON_VER=$($PYTHON_CMD --version 2>&1)
echo -e "${BOLD}Python:${NC} $PYTHON_VER"
echo ""

# ── Step 1: Install Dependencies ────────────────────────────────────────────
echo -e "${CYAN}[1/5]${NC} Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip > /dev/null 2>&1 || true
$PYTHON_CMD -m pip install pyinstaller textual rich psutil pyperclip pillow \
    jinja2 aiohttp httpx markdown uvicorn fastapi pyfiglet > /dev/null 2>&1
echo -e "${GREEN}  ✓ Dependencies installed${NC}"

# ── Step 2: Clean ───────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[2/5]${NC} Cleaning previous builds..."
rm -rf dist build __pycache__ 2>/dev/null || true
echo -e "${GREEN}  ✓ Cleaned${NC}"

# ── Step 3: Build Main Executable ───────────────────────────────────────────
echo ""
echo -e "${CYAN}[3/5]${NC} Building ${BOLD}Nextral${NC} (main application)..."
$PYTHON_CMD -m PyInstaller nextral.spec --clean --noconfirm 2>&1

if [ ! -f "dist/Nextral" ]; then
    echo -e "${RED}  ✗ dist/Nextral not found after build!${NC}"
    exit 1
fi

chmod +x dist/Nextral
echo -e "${GREEN}  ✓ dist/Nextral built successfully${NC}"
ls -lh dist/Nextral | awk '{print "    Size: "$5}'

# ── Step 4: Build Installer ─────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[4/5]${NC} Building ${BOLD}Nextral-Setup${NC} (professional installer)..."
$PYTHON_CMD -m PyInstaller installer.spec --clean --noconfirm 2>&1

if [ -f "dist/Nextral-Setup" ]; then
    chmod +x dist/Nextral-Setup
    echo -e "${GREEN}  ✓ dist/Nextral-Setup built successfully${NC}"
    ls -lh dist/Nextral-Setup | awk '{print "    Size: "$5}'
else
    echo -e "${YELLOW}  ⚠ dist/Nextral-Setup not found — installer build skipped${NC}"
    echo -e "${YELLOW}    (This may be due to missing tkinter on headless systems)${NC}"
fi

# ── Step 5: Verify ──────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[5/5]${NC} Verifying outputs..."
echo ""

MAIN_OK=false
SETUP_OK=false

if [ -f "dist/Nextral" ]; then
    MAIN_OK=true
    echo -e "  ${GREEN}✓${NC} dist/Nextral"
    ls -lh dist/Nextral
fi

if [ -f "dist/Nextral-Setup" ]; then
    SETUP_OK=true
    echo -e "  ${GREEN}✓${NC} dist/Nextral-Setup"
    ls -lh dist/Nextral-Setup
fi

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
if $MAIN_OK; then
    echo -e "  ${GREEN}${BOLD}BUILD SUCCESSFUL!${NC}"
else
    echo -e "  ${RED}${BOLD}BUILD FAILED!${NC}"
fi
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

if $MAIN_OK; then
    echo -e "  ${BOLD}Run directly:${NC}   ./dist/Nextral"
fi
if $SETUP_OK; then
    echo -e "  ${BOLD}Distribute:${NC}     dist/Nextral-Setup  (includes Nextral inside)"
fi

echo ""
