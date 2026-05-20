"""
PyInstaller runtime hook — 在 EXE 启动时修复 matplotlib 字体路径。

打包后 mpl-data 被解压到 sys._MEIPASS，需要告知 matplotlib 在哪里找字体。
同时强制设置 Microsoft YaHei（Windows 系统内置），确保中文正常显示。
"""
import os
import sys


def _setup():
    # 1. 告知 matplotlib 数据目录
    if hasattr(sys, '_MEIPASS'):
        mpl_data = os.path.join(sys._MEIPASS, 'matplotlib', 'mpl-data')
        if os.path.isdir(mpl_data):
            os.environ.setdefault('MATPLOTLIBDATA', mpl_data)

    # 2. 在 matplotlib 初始化前强制配置中文字体
    try:
        import matplotlib
        matplotlib.rcParams.update({
            'font.family':        'sans-serif',
            'font.sans-serif':    ['Microsoft YaHei', 'SimHei', 'SimSun',
                                   'DejaVu Sans', 'Arial'],
            'axes.unicode_minus': False,
        })
    except Exception:
        pass


_setup()
