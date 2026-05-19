DARK_THEME = '''
/* ── Global ─────────────────────────────────────────────────────── */
QWidget {
    background-color: #0f1628;
    color: #cfd8dc;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── Scroll bars ─────────────────────────────────────────────────── */
QScrollBar:vertical {
    background:#1a1f3a; width:8px; border-radius:4px;
}
QScrollBar::handle:vertical {
    background:#2e3d6e; border-radius:4px; min-height:20px;
}
QScrollBar::handle:vertical:hover { background:#4fc3f7; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }

QScrollBar:horizontal {
    background:#1a1f3a; height:8px; border-radius:4px;
}
QScrollBar::handle:horizontal {
    background:#2e3d6e; border-radius:4px; min-width:20px;
}
QScrollBar::handle:horizontal:hover { background:#4fc3f7; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }

/* ── Buttons ──────────────────────────────────────────────────────── */
QPushButton {
    background: #1a2a4a;
    color: #90caf9;
    border: 1px solid #2a3f6e;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
}
QPushButton:hover { background:#1e3a5f; border-color:#4fc3f7; color:#e3f2fd; }
QPushButton:pressed { background:#0d2040; }
QPushButton:disabled { color:#455a64; border-color:#1a2a3a; }

/* ── Run/Primary buttons ─────────────────────────────────────────── */
QPushButton#run_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1565c0, stop:1 #0288d1);
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 7px 20px;
    font-size: 14px;
}
QPushButton#run_btn:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1976d2, stop:1 #039be5);
}

/* ── Input widgets ───────────────────────────────────────────────── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #1e2545;
    color: #e0e0e0;
    border: 1px solid #2a3060;
    border-radius: 5px;
    padding: 4px 8px;
    selection-background-color: #1565c0;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #4fc3f7;
}
QComboBox::drop-down { border: none; width:20px; }
QComboBox QAbstractItemView {
    background:#1e2545; color:#e0e0e0; selection-background-color:#1565c0;
    border:1px solid #2a3060;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background:#2a3060; border:none; width:18px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background:#1565c0;
}

/* ── Sliders ─────────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    background:#1e2545; height:6px; border-radius:3px;
}
QSlider::handle:horizontal {
    background:#4fc3f7; width:16px; height:16px; margin:-5px 0;
    border-radius:8px;
}
QSlider::handle:horizontal:hover { background:#81d4fa; }
QSlider::sub-page:horizontal { background:#1565c0; border-radius:3px; }

/* ── Labels ──────────────────────────────────────────────────────── */
QLabel#section_title {
    color: #4fc3f7;
    font-size: 15px;
    font-weight: bold;
    padding-bottom: 4px;
    border-bottom: 1px solid #1e3a5f;
}
QLabel#param_label { color:#90a4ae; font-size:12px; }
QLabel#value_label { color:#b0bec5; font-size:12px; }

/* ── GroupBox ────────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    color: #607d8b;
    font-size: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #4fc3f7;
}

/* ── Tab widget ──────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    background: #0f1628;
}
QTabBar::tab {
    background: #1a1f3a;
    color: #78909c;
    padding: 7px 18px;
    border-radius: 5px 5px 0 0;
    margin-right: 3px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background: #1565c0;
    color: white;
    font-weight: bold;
}
QTabBar::tab:hover:!selected { background: #1e2a4a; color:#b0bec5; }

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle { background: #1e2545; width: 2px; }
QSplitter::handle:hover { background: #4fc3f7; }

/* ── Table ───────────────────────────────────────────────────────── */
QTableWidget {
    background: #111629;
    gridline-color: #1e2545;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    alternate-background-color: #151b30;
}
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:selected { background: #1565c0; }
QHeaderView::section {
    background: #1a2a4a;
    color: #90a4ae;
    border: none;
    padding: 6px 8px;
    font-size: 12px;
    font-weight: bold;
}

/* ── Progress bar ────────────────────────────────────────────────── */
QProgressBar {
    background: #1e2545;
    border: 1px solid #2a3060;
    border-radius: 5px;
    text-align: center;
    color: #e0e0e0;
}
QProgressBar::chunk { background: #1565c0; border-radius: 4px; }

/* ── Tooltip ─────────────────────────────────────────────────────── */
QToolTip {
    background: #1a2a4a;
    color: #e0e0e0;
    border: 1px solid #4fc3f7;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ── Status bar ──────────────────────────────────────────────────── */
QStatusBar { background:#0d1226; color:#546e7a; font-size:11px; }
QStatusBar::item { border:none; }
'''
