"""Shared base class for all experiment module widgets."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QPushButton, QScrollArea, QSizePolicy, QGroupBox
)
from PyQt5.QtCore import Qt
import platform
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


# ── Chinese font detection ────────────────────────────────────────────────────
def _find_chinese_font() -> str:
    """Return the first available CJK font name for the current platform."""
    system = platform.system()
    if system == 'Windows':
        candidates = [
            'Microsoft YaHei', '微软雅黑',
            'SimHei', '黑体',
            'SimSun', '宋体',
            'FangSong', 'KaiTi',
        ]
    elif system == 'Darwin':
        candidates = [
            'PingFang SC', 'Heiti SC', 'STHeiti',
            'Arial Unicode MS',
        ]
    else:  # Linux / embedded
        candidates = [
            'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
            'Noto Sans CJK SC', 'Noto Sans SC',
            'Source Han Sans SC', 'Droid Sans Fallback',
        ]

    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name

    # Last resort: search font files by common CJK filename patterns
    for f in fm.fontManager.ttflist:
        low = f.name.lower()
        if any(k in low for k in ('cjk', 'chinese', 'heiti', 'yahei', 'noto')):
            return f.name

    return 'DejaVu Sans'   # ASCII fallback — won't show CJK but won't crash


_CN_FONT = _find_chinese_font()

# ── Matplotlib global style (dark theme + Chinese font) ───────────────────────
plt.rcParams.update({
    # Font — put the CJK font first so Chinese chars render correctly
    'font.family':          'sans-serif',
    'font.sans-serif':      [_CN_FONT, 'Microsoft YaHei', 'SimHei',
                             'DejaVu Sans', 'Arial', 'sans-serif'],
    'axes.unicode_minus':   False,   # use ASCII minus instead of U+2212

    # Dark colour scheme
    'figure.facecolor':     '#111629',
    'axes.facecolor':       '#0d1826',
    'axes.edgecolor':       '#2a3a5a',
    'axes.labelcolor':      '#90a4ae',
    'xtick.color':          '#607d8b',
    'ytick.color':          '#607d8b',
    'text.color':           '#cfd8dc',
    'grid.color':           '#1e2a4a',
    'grid.linestyle':       '--',
    'grid.linewidth':       0.5,
    'lines.linewidth':      1.8,
    'legend.facecolor':     '#111629',
    'legend.edgecolor':     '#2a3a5a',
    'legend.fontsize':      9,
    'axes.titlesize':       11,
    'axes.labelsize':       10,
    'xtick.labelsize':      9,
    'ytick.labelsize':      9,
})

# Color palette for signal plots
COLORS = ['#4fc3f7', '#ef5350', '#66bb6a', '#ffa726', '#ab47bc',
          '#26c6da', '#ff7043', '#d4e157', '#ec407a', '#42a5f5']


class PlotCanvas(FigureCanvas):
    """A matplotlib figure canvas with dark theme."""
    def __init__(self, rows=1, cols=1, figsize=(10, 4), parent=None):
        self.fig = Figure(figsize=figsize, tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fig.patch.set_facecolor('#111629')
        self._rows = rows
        self._cols = cols
        self.axes = []
        for i in range(rows * cols):
            ax = self.fig.add_subplot(rows, cols, i + 1)
            ax.grid(True, alpha=0.3)
            self.axes.append(ax)

    def clear_axes(self):
        for ax in self.axes:
            ax.cla()
            ax.grid(True, alpha=0.3)

    def ax(self, idx=0):
        return self.axes[idx]


class BaseModuleWidget(QWidget):
    """
    Base layout:
      left panel  (controls, scrollable, ~280px)  |  right panel (plots)
    """
    def __init__(self, user: dict, rows=2, cols=2, figsize=(10, 6), parent=None):
        super().__init__(parent)
        self.user = user
        self._build_base(rows, cols, figsize)

    def _build_base(self, rows, cols, figsize):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet('QSplitter::handle{background:#1e2545;width:2px;}')

        # ── Left panel (parameter controls) ──────────────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet('border:none; background:#0d1226;')
        left_scroll.setFixedWidth(290)

        self.ctrl_widget = QWidget()
        self.ctrl_widget.setStyleSheet('background:#0d1226;')
        self.ctrl_layout = QVBoxLayout(self.ctrl_widget)
        self.ctrl_layout.setContentsMargins(12, 12, 12, 12)
        self.ctrl_layout.setSpacing(10)
        left_scroll.setWidget(self.ctrl_widget)
        splitter.addWidget(left_scroll)

        # ── Right panel (plot + toolbar) ──────────────────────────────────────
        right_frame = QFrame()
        right_frame.setStyleSheet('background:#111629;')
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(8, 4, 8, 4)
        right_layout.setSpacing(4)

        self.canvas = PlotCanvas(rows=rows, cols=cols, figsize=figsize)
        toolbar = NavigationToolbar(self.canvas, right_frame)
        toolbar.setStyleSheet('background:#111629; color:#90a4ae; border:none;')

        right_layout.addWidget(toolbar)
        right_layout.addWidget(self.canvas)
        splitter.addWidget(right_frame)

        splitter.setSizes([290, 990])
        root.addWidget(splitter)

    def add_section_title(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName('section_title')
        lbl.setStyleSheet('color:#4fc3f7; font-size:14px; font-weight:bold; '
                          'padding-bottom:4px; border-bottom:1px solid #1e3a5f;')
        self.ctrl_layout.addWidget(lbl)

    def add_run_button(self, text='▶  运行仿真', callback=None) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName('run_btn')
        btn.setMinimumHeight(38)
        btn.setStyleSheet('''
            QPushButton#run_btn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1565c0, stop:1 #0288d1);
                color:white; font-weight:bold; border:none;
                border-radius:6px; padding:7px 20px; font-size:14px;
            }
            QPushButton#run_btn:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1976d2, stop:1 #039be5);
            }
        ''')
        btn.setCursor(Qt.PointingHandCursor)
        if callback:
            btn.clicked.connect(callback)
        self.ctrl_layout.addWidget(btn)
        return btn

    def add_param_row(self, label_text: str, widget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel(label_text)
        lbl.setStyleSheet('color:#90a4ae; font-size:12px;')
        lbl.setFixedWidth(110)
        row.addWidget(lbl)
        row.addWidget(widget)
        self.ctrl_layout.addLayout(row)
        return row

    def add_spacer(self):
        from PyQt5.QtWidgets import QSpacerItem
        self.ctrl_layout.addSpacerItem(
            QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed)
        )

    def add_stretch(self):
        self.ctrl_layout.addStretch()
