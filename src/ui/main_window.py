from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QScrollArea,
    QSizePolicy, QStatusBar, QToolButton, QAction, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor

from src.auth.user_manager import record_progress, get_progress

# Module imports
from src.modules.signal_sources import SignalSourcesWidget
from src.modules.analog_modulation import AnalogModulationWidget
from src.modules.digitization import DigitizationWidget
from src.modules.baseband import BasebandWidget
from src.modules.digital_modulation import DigitalModulationWidget
from src.modules.advanced_modulation import AdvancedModulationWidget
from src.modules.error_coding import ErrorCodingWidget
from src.modules.modern_systems import ModernSystemsWidget
from src.tools.analysis_panel import AnalysisPanelWidget


# ── Navigation menu data ─────────────────────────────────────────────────────
NAV_GROUPS = [
    {
        'group': '基础实验',
        'icon': '📡',
        'items': [
            ('signal_sources',    '信号源与基础分析',     '实验1',  SignalSourcesWidget),
            ('analog_mod',        '模拟调制解调',         '实验2',  AnalogModulationWidget),
            ('digitization',      '信号数字化与复用',     '实验3/4/6', DigitizationWidget),
            ('baseband',          '基带传输与码型变换',   '实验7/8', BasebandWidget),
            ('digital_mod',       '数字频带调制',         '实验5',  DigitalModulationWidget),
        ]
    },
    {
        'group': '扩展模块',
        'icon': '🔬',
        'items': [
            ('advanced_mod',      '新型频带调制',         'QPSK/QAM/MSK', AdvancedModulationWidget),
            ('error_coding',      '差错控制编码',         'Hamming/LDPC/Polar', ErrorCodingWidget),
            ('modern_systems',    '现代通信系统',         'OFDM/MIMO/DVB-T', ModernSystemsWidget),
        ]
    },
    {
        'group': '综合工具',
        'icon': '🔧',
        'items': [
            ('analysis_tools',    '综合分析工具',         '示波器/频谱/BER/星座图', AnalysisPanelWidget),
        ]
    },
]


class SidebarButton(QPushButton):
    def __init__(self, key, label, subtitle, parent=None):
        super().__init__(parent)
        self.key = key
        self.setCheckable(True)
        self.setMinimumHeight(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._label = label
        self._sub = subtitle
        self._update_text()

    def _update_text(self):
        self.setText(f'{self._label}\n{self._sub}')
        self.setStyleSheet('''
            QPushButton {
                background: transparent;
                color: #90a4ae;
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0;
                text-align: left;
                padding: 8px 12px 8px 16px;
                font-size: 13px;
                line-height: 1.4;
            }
            QPushButton:hover {
                background: #1a2a4a;
                color: #e3f2fd;
                border-left: 3px solid #1565c0;
            }
            QPushButton:checked {
                background: #0d2040;
                color: #4fc3f7;
                border-left: 3px solid #4fc3f7;
                font-weight: bold;
            }
        ''')


class MainWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle('通信原理仿真软件')
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)

        self._nav_buttons: dict[str, SidebarButton] = {}
        self._module_widgets: dict[str, QWidget] = {}
        self._current_key = None

        self._build_ui()
        self._navigate_to('signal_sources')

        # Status bar update timer
        timer = QTimer(self)
        timer.timeout.connect(self._update_status)
        timer.start(30_000)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # sidebar
        sidebar = self._make_sidebar()
        root.addWidget(sidebar)

        # divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet('color:#1e2545;')
        root.addWidget(div)

        # content area
        content_frame = QFrame()
        content_frame.setStyleSheet('background:#0f1628;')
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._header = self._make_header()
        content_layout.addWidget(self._header)

        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack)
        root.addWidget(content_frame, 1)

        # status bar
        self._status = QStatusBar()
        self._status.setStyleSheet('QStatusBar{background:#0d1226;color:#546e7a;font-size:11px;}')
        self.setStatusBar(self._status)
        self._update_status()

    def _make_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet('background:#0d1226; border:none;')
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # user banner
        banner = QFrame()
        banner.setStyleSheet('background:#111629; padding:4px;')
        banner.setFixedHeight(80)
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(14, 10, 14, 10)
        u_label = QLabel(f'👤  {self.user.get("real_name") or self.user["username"]}')
        u_label.setStyleSheet('color:#e3f2fd; font-size:14px; font-weight:bold;')
        sid_label = QLabel(f'学号: {self.user.get("student_id") or "—"}')
        sid_label.setStyleSheet('color:#607d8b; font-size:11px;')
        b_layout.addWidget(u_label)
        b_layout.addWidget(sid_label)
        layout.addWidget(banner)

        # nav scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('border:none; background:transparent;')
        nav_widget = QWidget()
        nav_widget.setStyleSheet('background:transparent;')
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(0)

        for group_info in NAV_GROUPS:
            grp_lbl = QLabel(f'  {group_info["icon"]}  {group_info["group"]}')
            grp_lbl.setStyleSheet('color:#455a64; font-size:11px; font-weight:bold; '
                                  'padding:10px 0 4px 12px; text-transform:uppercase;')
            nav_layout.addWidget(grp_lbl)
            for key, label, subtitle, _ in group_info['items']:
                btn = SidebarButton(key, label, subtitle)
                btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
                nav_layout.addWidget(btn)
                self._nav_buttons[key] = btn

        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        layout.addWidget(scroll, 1)

        # bottom: progress & logout
        bottom = QFrame()
        bottom.setStyleSheet('background:#111629; border-top:1px solid #1e2545;')
        b2 = QVBoxLayout(bottom)
        b2.setContentsMargins(10, 8, 10, 8)
        b2.setSpacing(6)

        prog_btn = QPushButton('📊  实验进度')
        prog_btn.setStyleSheet('background:#1a2a4a;color:#90caf9;border:none;border-radius:5px;padding:6px;font-size:12px;')
        prog_btn.clicked.connect(self._show_progress)
        b2.addWidget(prog_btn)

        logout_btn = QPushButton('🚪  退出登录')
        logout_btn.setStyleSheet('background:#1a1a2a;color:#ef9a9a;border:none;border-radius:5px;padding:6px;font-size:12px;')
        logout_btn.clicked.connect(self.close)
        b2.addWidget(logout_btn)
        layout.addWidget(bottom)

        return sidebar

    def _make_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet('background:#111629; border-bottom:1px solid #1e2545;')
        layout = QHBoxLayout(hdr)
        layout.setContentsMargins(20, 0, 20, 0)

        self._page_title = QLabel('信号源与基础分析')
        self._page_title.setStyleSheet('color:#e3f2fd; font-size:16px; font-weight:bold;')
        layout.addWidget(self._page_title)
        layout.addStretch()

        self._exp_tag = QLabel('实验1')
        self._exp_tag.setStyleSheet('background:#1565c0; color:white; border-radius:4px; '
                                    'padding:3px 10px; font-size:11px; font-weight:bold;')
        layout.addWidget(self._exp_tag)
        return hdr

    # ── Navigation ────────────────────────────────────────────────────────────
    def _navigate_to(self, key: str):
        if self._current_key == key:
            return
        # uncheck previous
        if self._current_key and self._current_key in self._nav_buttons:
            self._nav_buttons[self._current_key].setChecked(False)

        self._current_key = key
        self._nav_buttons[key].setChecked(True)

        # find label/subtitle
        for group_info in NAV_GROUPS:
            for k, label, subtitle, widget_cls in group_info['items']:
                if k == key:
                    self._page_title.setText(label)
                    self._exp_tag.setText(subtitle)
                    break

        # lazy-load module widget
        if key not in self._module_widgets:
            for group_info in NAV_GROUPS:
                for k, _, _, widget_cls in group_info['items']:
                    if k == key:
                        w = widget_cls(self.user)
                        self._module_widgets[key] = w
                        self._stack.addWidget(w)
                        break

        self._stack.setCurrentWidget(self._module_widgets[key])
        record_progress(self.user['id'], key)
        self._update_status()

    # ── Progress dialog ───────────────────────────────────────────────────────
    def _show_progress(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
        dlg = QDialog(self)
        dlg.setWindowTitle('实验进度记录')
        dlg.resize(560, 360)
        dlg.setStyleSheet('background:#0f1628; color:#cfd8dc;')
        layout = QVBoxLayout(dlg)

        tbl = QTableWidget()
        tbl.setStyleSheet('background:#111629;')
        tbl.setColumnCount(3)
        tbl.setHorizontalHeaderLabels(['实验模块', '最近访问', '访问次数'])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setAlternatingRowColors(True)

        MODULE_NAMES = {k: label for g in NAV_GROUPS for k, label, _, _ in g['items']}
        rows = get_progress(self.user['id'])
        tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            tbl.setItem(i, 0, QTableWidgetItem(MODULE_NAMES.get(r['module'], r['module'])))
            tbl.setItem(i, 1, QTableWidgetItem(r['last_accessed'][:19].replace('T', ' ')))
            tbl.setItem(i, 2, QTableWidgetItem(str(r['times_visited'])))

        layout.addWidget(tbl)
        ok = QPushButton('关闭')
        ok.setFixedWidth(100)
        ok.clicked.connect(dlg.accept)
        lyt = QHBoxLayout()
        lyt.addStretch()
        lyt.addWidget(ok)
        layout.addLayout(lyt)
        dlg.exec_()

    def _update_status(self):
        visited = len(get_progress(self.user['id']))
        total = sum(len(g['items']) for g in NAV_GROUPS)
        self._status.showMessage(
            f'用户: {self.user["username"]}   |   '
            f'已完成模块: {visited}/{total}   |   '
            f'通信原理仿真软件 v1.0'
        )
