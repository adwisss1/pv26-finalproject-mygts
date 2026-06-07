from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from controllers.auth_controller import login
from utils.validators import is_empty


class LoginPage(QWidget):
    login_successful = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #F8F7F4;")
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)
        card.setStyleSheet("""
            #loginCard {
                background: #ffffff;
                border: 0.5px solid #E0DDD8;
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(0)

        logo = QFrame()
        logo.setFixedSize(56, 56)
        logo.setStyleSheet("""
            background: #0F6E56; border-radius: 28px;
        """)
        logo_layout = QVBoxLayout(logo)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_icon = QLabel("M")
        logo_icon.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff; background: transparent;")
        logo_layout.addWidget(logo_icon)

        layout.addWidget(logo, 0, Qt.AlignCenter)
        layout.addSpacing(12)

        title = QLabel("MyGTS")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #1A1A1A; letter-spacing: -0.5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(6)

        subtitle = QLabel("Sistem Manajemen Inventaris Sanggar")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #8C8A86;")
        layout.addWidget(subtitle)

        layout.addSpacing(28)

        email_group = QVBoxLayout()
        email_group.setSpacing(6)
        lbl_email = QLabel("Email")
        lbl_email.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A;")
        email_group.addWidget(lbl_email)

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("nama@email.com")
        self.login_email.setStyleSheet("""
            QLineEdit {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 14px;
                background: #ffffff; color: #1A1A1A;
                min-height: 22px;
            }
            QLineEdit:focus {
                border-color: #0F6E56;
            }
            QLineEdit::placeholder {
                color: #A8A6A2;
            }
        """)
        email_group.addWidget(self.login_email)
        layout.addLayout(email_group)

        layout.addSpacing(16)

        pw_group = QVBoxLayout()
        pw_group.setSpacing(6)
        lbl_password = QLabel("Kata Sandi")
        lbl_password.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A;")
        pw_group.addWidget(lbl_password)

        pw_container = QWidget()
        pw_container.setStyleSheet("background: transparent;")
        pw_layout = QHBoxLayout(pw_container)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(0)

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet("""
            QLineEdit {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 14px;
                background: #ffffff; color: #1A1A1A;
                min-height: 22px;
            }
            QLineEdit:focus {
                border-color: #0F6E56;
            }
            QLineEdit::placeholder {
                color: #A8A6A2;
            }
        """)

        btn_toggle = QPushButton()
        btn_toggle.setFixedSize(36, 36)
        btn_toggle.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 18px; color: #8C8A86;
            }
            QPushButton:hover { color: #1A1A1A; }
        """)
        btn_toggle.setText("\u25c9")
        btn_toggle.clicked.connect(lambda: self._toggle_password(self.login_password, btn_toggle))

        pw_layout.addWidget(self.login_password)
        pw_layout.addWidget(btn_toggle)
        pw_group.addWidget(pw_container)
        layout.addLayout(pw_group)

        layout.addSpacing(24)

        btn_login = QPushButton("Masuk")
        btn_login.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 12px; font-size: 14px; font-weight: 600;
                color: #ffffff; min-height: 22px;
            }
            QPushButton:hover { background: #0A5A45; }
            QPushButton:pressed { background: #08503A; }
        """)
        btn_login.clicked.connect(self._handle_login)
        layout.addWidget(btn_login)

        layout.addSpacing(20)

        footnote = QLabel("Belum punya akun? Hubungi pemilik sanggar.")
        footnote.setAlignment(Qt.AlignCenter)
        footnote.setStyleSheet("font-size: 12px; color: #A8A6A2;")
        layout.addWidget(footnote)

        outer.addStretch()
        outer.addWidget(card, 0, Qt.AlignCenter)
        outer.addStretch()

    def _toggle_password(self, field, button):
        if field.echoMode() == QLineEdit.Password:
            field.setEchoMode(QLineEdit.Normal)
            button.setText("\u25c8")
        else:
            field.setEchoMode(QLineEdit.Password)
            button.setText("\u25c9")

    def _handle_login(self):
        email = self.login_email.text().strip()
        password = self.login_password.text()

        if is_empty(email) or is_empty(password):
            QMessageBox.warning(self, "Login Gagal", "Email dan kata sandi harus diisi.")
            return

        user = login(email, password)
        if user:
            self.login_email.clear()
            self.login_password.clear()
            self.login_successful.emit(user)
        else:
            QMessageBox.warning(self, "Login Gagal", "Email atau kata sandi salah.")
