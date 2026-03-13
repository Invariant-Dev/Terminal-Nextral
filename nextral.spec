import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None
cwd = os.getcwd()

# Collect all submodules and data for complex libraries
rich_submodules = collect_submodules('rich')
rich_datas = collect_data_files('rich')
textual_submodules = collect_submodules('textual')
textual_datas = collect_data_files('textual')

a = Analysis(
    ['launcher.py'],
    pathex=[cwd],
    binaries=[],
    datas=[
        ('terminal_config.json', '.'),
    ] + rich_datas + textual_datas,
    hiddenimports=[
        'rich',
        'rich.console',
        'rich.logging',
        'rich.table',
        'rich.panel',
        'rich.live',
        'rich.progress',
        'rich._unicode_data',
        'textual',
        'textual.app',
        'textual.widgets',
        'psutil',
        'pyfiglet',
        'nextral',
        'boot',
        'agent_backend',
        'agent_screen',
        'blackbook',
        'breach_watch',
        'cipher',
        'explorer_screen',
        'geo_globe',
        'hex_ray',
        'obelisk',
        'osint_tool',
        'proxy_chain',
        'sandbox_tool',
        'sentinel',
        'vault_x',
        'xray_tool',
        'valkyrie',
        'exif_ray',
        'email',
        'pkg_resources',
        # External tool modules
        'tools_locator',
        'nmap_screen',
        'netcat_screen',
        'nikto_screen',
        'hydra_screen',
        'tcpdump_screen',
        'stun_analyzer',
        'stun_analyzer_screen',
        'openssl_tool',
        'install_wizard_screen',
    ] + rich_submodules + textual_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Third-Party Heavy Bloat (SAFE TO EXCLUDE)
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'matplotlib', 'pandas', 'sklearn', 
        'scipy', 'nltk', 'statsmodels', 'pygame', 'soundfile', 'librosa',
        'sqlalchemy', 'openpyxl', 'jedi', 'parso', 'zmq', 'jsonschema', 
        'IPython', 'notebook', 'nbformat',
        
        # Standard Library (REDUCED TO ESSENTIALS ONLY)
        'unittest', 'pydoc', 'test', 'doctest', 'tcl', 'tk', 'tkinter'
    ],
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
    name='Nextral',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
