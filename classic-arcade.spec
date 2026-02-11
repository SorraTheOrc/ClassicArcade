# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all data files from pygame and our project
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import glob
import os

# Collect pygame data (fonts, etc.)
pygame_datas = collect_data_files('pygame')

# Collect all game modules
games_modules = collect_submodules('games')

# Collect all game data files including assets
games_datas = collect_data_files('games', include_py_files=False)

# Manually collect assets
assets = []
for pattern in ['assets/**/*.wav', 'assets/**/*.mp3', 'assets/**/*.ogg', 'assets/**/*.png', 'assets/**/*.jpg', 'assets/**/*.gif']:
    for f in glob.glob(pattern, recursive=True):
        if os.path.isfile(f):
            dest_dir = os.path.dirname(f)
            assets.append((f, dest_dir))

# Build the datas list
datas = []
datas.extend(pygame_datas)
datas.extend(games_datas)
datas.extend(assets)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pygame', 'pygame._sdl2'] + [m for m in games_modules if 'test' not in m],
    hookspath=[],
    hooksconfig={},
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
