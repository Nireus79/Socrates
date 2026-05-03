# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Socrates AI

import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all necessary modules
datas = []
binaries = []
hiddenimports = [
    'socratic_system',
    'socratic_system.agents',
    'socratic_system.clients',
    'socratic_system.config',
    'socratic_system.database',
    'socratic_system.events',
    'socratic_system.exceptions',
    'socratic_system.models',
    'socratic_system.orchestration',
    'socratic_system.ui',
    'socratic_system.ui.commands',
    'socratic_system.utils',
    'anthropic',
    'chromadb',
    'sentence_transformers',
    'fastapi',
    'uvicorn',
    'sqlalchemy',
    'redis',
    'pydantic',
    'dotenv',
]

a = Analysis(
    ['socrates_windows_entry.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='socrates',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console visible so users can press Ctrl+C to stop
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='socrates.ico',
)
