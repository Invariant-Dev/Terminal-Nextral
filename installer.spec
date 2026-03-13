# -*- mode: python ; coding: utf-8 -*-
#
# installer.spec  – Nextral Setup builder (Cross-Platform)
#
# HOW TO USE:
#   1. First build the main app:   pyinstaller nextral.spec --clean --noconfirm
#   2. Then build the installer:   pyinstaller installer.spec --clean --noconfirm
#
# The resulting Nextral-Setup (or Nextral-Setup.exe) bundles the main binary
# inside itself so end-users only need to share / run one file.
#

import os
import sys
import platform
from pathlib import Path

block_cipher = None

# ── Cross-platform binary detection ─────────────────────────────────────────
is_windows = platform.system().lower() == "windows"
exe_name   = "Nextral.exe" if is_windows else "Nextral"
setup_name = "Nextral-Setup"

nextral_exe = Path("dist") / exe_name

# ── Bundled data files ──────────────────────────────────────────────────────
bundled_datas = [
    ('terminal_config.json', '.'),
    ('icon.png', '.'),
]
if nextral_exe.exists():
    bundled_datas.append((str(nextral_exe), '.'))

# ── Icon handling ───────────────────────────────────────────────────────────
# PyInstaller on Windows expects .ico; on Linux/macOS .png is fine (or None)
icon_file = None
if is_windows and Path('icon.ico').exists():
    icon_file = 'icon.ico'
elif is_windows and Path('icon.png').exists():
    icon_file = 'icon.png'    # PyInstaller will try its best
elif Path('icon.png').exists():
    icon_file = 'icon.png'

a = Analysis(
    ['nextral_installer.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=bundled_datas,
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.ttk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=setup_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=not is_windows,        # strip symbols on Linux for smaller binary
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=not is_windows,      # console mode on Linux (for Tkinter), GUI on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
