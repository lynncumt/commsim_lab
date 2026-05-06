# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for 通信原理仿真软件"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Qt backends
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.sip',
        # Matplotlib
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'matplotlib._path',
        # Scipy
        'scipy',
        'scipy.signal',
        'scipy.special',
        'scipy.interpolate',
        'scipy.fft',
        # Numpy
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        # SQLite
        'sqlite3',
        # Application modules
        'src',
        'src.auth',
        'src.auth.login_window',
        'src.auth.user_manager',
        'src.ui',
        'src.ui.main_window',
        'src.ui.styles',
        'src.ui.base_module',
        'src.modules',
        'src.modules.signal_sources',
        'src.modules.analog_modulation',
        'src.modules.digitization',
        'src.modules.baseband',
        'src.modules.digital_modulation',
        'src.modules.advanced_modulation',
        'src.modules.error_coding',
        'src.modules.modern_systems',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'IPython', 'jupyter', 'notebook', 'sphinx'],
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
    name='通信原理仿真软件',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,            # Set to 'icon.ico' if you have one
    version=None,
)
