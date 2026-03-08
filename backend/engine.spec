# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect torch data files and submodules
torch_datas = collect_data_files('torch')
torch_binaries = [] # Usually handled by hooks but can be explicit

# Collect safpy
safpy_datas = collect_data_files('safpy')
safpy_binaries = [('venv/lib/python3.13/site-packages/_safpy.abi3.so', '.')]

a = Analysis(
    ['engine.py'],
    pathex=['.'],
    binaries=safpy_binaries,
    datas=torch_datas + safpy_datas,
    hiddenimports=['torch', 'safpy', 'websockets', 'pythonosc', 'sounddevice', 'soundfile', 'numpy'],
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
    [],
    exclude_binaries=True,
    name='engine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='engine',
)
