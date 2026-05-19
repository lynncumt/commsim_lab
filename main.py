"""通信原理仿真软件 — 主入口"""
import sys
import os

# Ensure the project root is on the path (needed when frozen by PyInstaller)
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from src.ui.styles import DARK_THEME
from src.auth.login_window import LoginWindow
from src.ui.main_window import MainWindow


def main():
    # Enable High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName('通信原理仿真软件')
    app.setApplicationVersion('1.0.0')
    app.setOrganizationName('CommsimLab')

    # Default font
    font = QFont('Microsoft YaHei', 10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    app.setStyleSheet(DARK_THEME)

    # Show login
    login = LoginWindow()

    main_win = None

    def on_login(user):
        nonlocal main_win
        main_win = MainWindow(user)
        main_win.show()

    login.login_success.connect(on_login)

    result = login.exec_()
    if result != login.Accepted or main_win is None:
        sys.exit(0)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
