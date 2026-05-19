# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — 通信原理仿真软件
关键修复:
  1. collect_data_files('matplotlib') 包含字体/样式/mpl-data，解决中文乱码
  2. collect_submodules 自动收集 scipy/matplotlib 所有子模块，避免运行时 ImportError
  3. 运行时钩子 runtime_hook_font.py 在 EXE 内部强制注册字体路径
  4. 输出文件名使用 ASCII 避免 CI 路径问题，同时保留中文显示名
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── 数据文件：matplotlib 字体/样式/locale 必须打包 ─────────────────────────
datas = []
datas += collect_data_files('matplotlib')   # mpl-data/fonts, stylelib, etc.
datas += collect_data_files('scipy',        includes=['*.pyx', '*.pxd'])
datas += collect_data_files('pytz',         includes=['*.py', 'zoneinfo/*'])

# ── 隐式导入：一次性收集所有子模块 ───────────────────────────────────────────
hiddenimports = []
hiddenimports += collect_submodules('matplotlib')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('numpy')
hiddenimports += [
    # PyQt5 核心
    'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
    'PyQt5.sip', 'PyQt5.QtPrintSupport',
    # Matplotlib Qt 后端
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_agg',
    'matplotlib.font_manager',
    'matplotlib._path',
    # 标准库
    'sqlite3', 'hashlib', 'platform',
    # 应用模块
    'src',
    'src.auth', 'src.auth.login_window', 'src.auth.user_manager',
    'src.ui',   'src.ui.main_window',    'src.ui.styles',
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
    'src.tools', 'src.tools.analysis_panel',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_font.py'],   # 启动时修复字体路径
    excludes=[
        'tkinter', 'IPython', 'jupyter', 'notebook', 'sphinx',
        'PyQt5.QtWebEngine', 'PyQt5.QtBluetooth', 'PyQt5.QtNfc',
        'test', 'tests',
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
    name='CommSimLab',           # ASCII 文件名，CI 友好；窗口标题仍显示中文
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python3*.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
)
