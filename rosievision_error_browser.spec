# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Add all local Python files
local_files = [
    ('main.py', '.'),
    ('app.py', '.'),
    ('dialogs.py', '.'),
    ('delegates.py', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],  # Use current working directory
    binaries=[],
    datas=collect_data_files('PySide6') + [('version.txt', '.')] + local_files,
    hiddenimports=['app', 'dialogs', 'delegates'],
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
    name='RosieVision-Error-Browser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep True for now to see error messages
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
) 