from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QMessageBox, QFormLayout, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor, QLinearGradient

from src.auth.user_manager import authenticate, create_user, init_db


class LoginWindow(QDialog):
    login_success = pyqtSignal(dict)  # emits user dict on success

    def __init__(self, parent=None):
        super().__init__(parent)
        init_db()
        self.setWindowTitle('通信原理仿真软件 — 登录')
        self.setFixedSize(480, 560)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self._build_ui()

    # ── drag support for frameless window ─────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── UI construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame(self)
        card.setObjectName('card')
        card.setStyleSheet('''
            QFrame#card {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #1a1f3a, stop:1 #0d1226);
                border-radius: 16px;
                border: 1px solid #2a3060;
            }
        ''')
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(16)

        # ── header bar (close btn) ─────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.addStretch()
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet('''
            QPushButton { background:#c0392b; color:white; border-radius:14px;
                          font-size:12px; border:none; }
            QPushButton:hover { background:#e74c3c; }
        ''')
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(close_btn)
        layout.addLayout(hdr)

        # ── logo / title ───────────────────────────────────────────────────
        title_lbl = QLabel('通信原理仿真软件')
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet('color:#4fc3f7; font-size:22px; font-weight:bold; letter-spacing:2px;')
        layout.addWidget(title_lbl)

        sub_lbl = QLabel('Communications Simulation Lab')
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet('color:#607d8b; font-size:11px; margin-bottom:8px;')
        layout.addWidget(sub_lbl)

        # ── tab widget ─────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setStyleSheet('''
            QTabWidget::pane { border: 1px solid #2a3060; border-radius:8px;
                               background: #111629; }
            QTabBar::tab { background:#1a1f3a; color:#90a4ae; padding:8px 24px;
                           border-radius:6px 6px 0 0; margin-right:4px; font-size:13px; }
            QTabBar::tab:selected { background:#4fc3f7; color:#0d1226; font-weight:bold; }
            QTabBar::tab:hover { background:#263060; }
        ''')
        layout.addWidget(tabs)

        # Login tab
        login_tab = QWidget()
        self._build_login_tab(login_tab)
        tabs.addTab(login_tab, '  登  录  ')

        # Register tab
        reg_tab = QWidget()
        self._build_register_tab(reg_tab)
        tabs.addTab(reg_tab, '  注  册  ')

        # ── hint ──────────────────────────────────────────────────────────
        hint = QLabel('默认账号 admin / 密码 admin123')
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet('color:#455a64; font-size:11px;')
        layout.addWidget(hint)

    # ── Login tab ─────────────────────────────────────────────────────────────
    def _build_login_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText('用户名')
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText('密码')
        self.login_pass.setEchoMode(QLineEdit.Password)

        for w in (self.login_user, self.login_pass):
            w.setStyleSheet(self._input_style())
            w.setFixedHeight(40)
            layout.addWidget(w)

        self.remember_cb = QCheckBox('记住用户名')
        self.remember_cb.setStyleSheet('color:#90a4ae; font-size:12px;')
        layout.addWidget(self.remember_cb)

        btn = QPushButton('登  录')
        btn.setFixedHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._btn_style())
        btn.clicked.connect(self._do_login)
        self.login_pass.returnPressed.connect(self._do_login)
        layout.addWidget(btn)

        layout.addStretch()

    # ── Register tab ──────────────────────────────────────────────────────────
    def _build_register_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self.reg_user = QLineEdit(); self.reg_user.setPlaceholderText('用户名 *')
        self.reg_pass = QLineEdit(); self.reg_pass.setPlaceholderText('密码 *')
        self.reg_pass.setEchoMode(QLineEdit.Password)
        self.reg_pass2 = QLineEdit(); self.reg_pass2.setPlaceholderText('确认密码 *')
        self.reg_pass2.setEchoMode(QLineEdit.Password)
        self.reg_name = QLineEdit(); self.reg_name.setPlaceholderText('真实姓名')
        self.reg_sid = QLineEdit(); self.reg_sid.setPlaceholderText('学号')

        for w in (self.reg_user, self.reg_pass, self.reg_pass2, self.reg_name, self.reg_sid):
            w.setStyleSheet(self._input_style())
            w.setFixedHeight(38)
            layout.addWidget(w)

        btn = QPushButton('注  册')
        btn.setFixedHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._btn_style('#26a69a', '#00897b'))
        btn.clicked.connect(self._do_register)
        layout.addWidget(btn)

        layout.addStretch()

    # ── actions ───────────────────────────────────────────────────────────────
    def _do_login(self):
        username = self.login_user.text().strip()
        password = self.login_pass.text()
        if not username or not password:
            self._msg('请输入用户名和密码', warning=True)
            return
        user = authenticate(username, password)
        if user:
            self.login_success.emit(user)
            self.accept()
        else:
            self._msg('用户名或密码错误', warning=True)
            self.login_pass.clear()
            self.login_pass.setFocus()

    def _do_register(self):
        u = self.reg_user.text().strip()
        p = self.reg_pass.text()
        p2 = self.reg_pass2.text()
        name = self.reg_name.text().strip()
        sid = self.reg_sid.text().strip()
        if not u or not p:
            self._msg('用户名和密码不能为空', warning=True)
            return
        if p != p2:
            self._msg('两次输入的密码不一致', warning=True)
            return
        if len(p) < 6:
            self._msg('密码至少需要6位', warning=True)
            return
        ok = create_user(u, p, real_name=name, student_id=sid)
        if ok:
            self._msg(f'注册成功！请使用账号 "{u}" 登录')
        else:
            self._msg(f'用户名 "{u}" 已存在', warning=True)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _msg(self, text, warning=False):
        mb = QMessageBox(self)
        mb.setText(text)
        mb.setWindowTitle('提示')
        if warning:
            mb.setIcon(QMessageBox.Warning)
        else:
            mb.setIcon(QMessageBox.Information)
        mb.exec_()

    @staticmethod
    def _input_style():
        return '''
            QLineEdit {
                background:#1e2545; color:#e0e0e0; border:1px solid #2a3060;
                border-radius:6px; padding:0 12px; font-size:13px;
            }
            QLineEdit:focus { border:1px solid #4fc3f7; }
            QLineEdit::placeholder { color:#546e7a; }
        '''

    @staticmethod
    def _btn_style(c1='#1565c0', c2='#0d47a1'):
        return f'''
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {c1}, stop:1 {c2});
                color:white; border:none; border-radius:8px;
                font-size:15px; font-weight:bold; letter-spacing:4px;
            }}
            QPushButton:hover {{ background: {c1}; }}
            QPushButton:pressed {{ background: {c2}; }}
        '''
