# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all data files from pygame and our project
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect pygame data (fonts, etc.)
pygame_datas = collect_data_files('pygame')

# Collect all game modules
games_modules = collect_submodules('games')

# Collect all game data files
games_datas = []
try:
    from games import __path__ as games_path
    for path in games_path:
        games_datas.extend(collect_data_files('games', include_py_files=False))
except Exception:
    games_datas = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=pygame_datas + games_datas,
    hiddenimports=['pygame', 'pygame._sdl2'] + [m for m in games_modules if 'test' not in m],
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
    name='ClassicArcade',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
