"""
MyGTS - My Gangsar Treasure System
Aplikasi manajemen inventaris sanggar berbasis PySide6 + Supabase
"""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MyGTS")
    app.setApplicationDisplayName("My Gangsar Treasure System")
    app.setOrganizationName("Gangsar Sanggar")
    style_path = os.path.join(os.path.dirname(__file__), "assets", "qss", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()