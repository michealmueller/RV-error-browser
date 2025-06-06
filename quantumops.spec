# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all hidden imports for PySide6, qdarktheme, azure, etc.
hidden_imports = []
hidden_imports += collect_submodules('PySide6')
hidden_imports += collect_submodules('qdarktheme')
hidden_imports += collect_submodules('azure')
hidden_imports += collect_submodules('azure.storage')
hidden_imports += collect_submodules('azure.storage.blob')

# Collect all data files for PySide6 (Qt plugins, etc.)
data_files = []
data_files += collect_data_files('PySide6')
data_files += collect_data_files('qdarktheme')

# Add project data files (if present)
project_data = [
    ('app.json', '.'),
    ('eas.json', '.'),
    ('requirements.txt', '.'),
    ('README.md', '.'),
]
for src, dest in project_data:
    data_files.append((src, dest))

block_cipher = None

# Main analysis

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=None,
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
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
    name='QuantumOps',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 