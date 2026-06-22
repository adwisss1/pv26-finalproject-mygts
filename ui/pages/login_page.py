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
        self.setObjectName("loginPage")
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(0)
        
        # Force primary button styling on card (cascade to children)
        card.setStyleSheet("""
            QFrame#loginCard QPushButton#primary {
                background: #0F6E56;
                color: #ffffff;
                border: none;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
                border-radius: 8px;
                min-height: 40px;
            }
            QFrame#loginCard QPushButton#primary:hover {
                background: #0A5A45;
            }
            QFrame#loginCard QPushButton#primary:pressed {
                background: #08463a;
            }
        """)

        logo = QFrame()
        logo.setFixedSize(56, 56)
        logo.setObjectName("loginLogo")
        logo_layout = QVBoxLayout(logo)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_icon = QLabel("M")
        logo_icon.setObjectName("logoIcon")
        logo_layout.addWidget(logo_icon)

        layout.addWidget(logo, 0, Qt.AlignCenter)
        layout.addSpacing(12)

        title = QLabel("MyGTS")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(6)

        subtitle = QLabel("Sistem Manajemen Inventaris Sanggar")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("loginSubtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(28)

        # --- KOLOM EMAIL ---
        email_group = QVBoxLayout()
        email_group.setSpacing(6)
        lbl_email = QLabel("Email")
        lbl_email.setObjectName("formLabel")
        email_group.addWidget(lbl_email)

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("nama@email.com")
        self.login_email.setObjectName("input")
        email_group.addWidget(self.login_email)
        layout.addLayout(email_group)

        layout.addSpacing(16)

        # --- KOLOM KATA SANDI ---
        pw_group = QVBoxLayout()
        pw_group.setSpacing(6)
        lbl_password = QLabel("Kata Sandi")
        lbl_password.setObjectName("formLabel")
        pw_group.addWidget(lbl_password)

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setObjectName("input")
        
        # Kata sandi sekarang masuk langsung ke grup vertikal (sejajar dengan email)
        pw_group.addWidget(self.login_password)
        layout.addLayout(pw_group)

        layout.addSpacing(24)

        btn_login = QPushButton("Masuk")
        btn_login.setObjectName("primary")
        btn_login.clicked.connect(self._handle_login)
        layout.addWidget(btn_login)

        layout.addSpacing(20)

        footnote = QLabel("Belum punya akun? Hubungi pemilik sanggar.")
        footnote.setAlignment(Qt.AlignCenter)
        footnote.setObjectName("muted")
        layout.addWidget(footnote)

        outer.addStretch()
        outer.addWidget(card, 0, Qt.AlignCenter)
        outer.addStretch()

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