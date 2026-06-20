"""
Halaman untuk Owner menambahkan akun Customer baru.
Setiap customer adalah member yang dibuat oleh owner.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox, QSpinBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from controllers.auth_controller import add_customer
from utils.worker import DataWorker

# ─────────────────────────────────────────────────────────────────────────────
#  FORM FIELD
# ─────────────────────────────────────────────────────────────────────────────

class FormField(QFrame):
    """Input field dengan label dan styling."""
    
    def __init__(self, label: str, placeholder: str = "", input_type: str = "text"):
        super().__init__()
        self.setObjectName("formField")
        self.setStyleSheet("""
            #formField {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #2A2A2A;"
        )
        layout.addWidget(label_widget)
        
        # Input
        if input_type == "text":
            self.input = QLineEdit()
            self.input.setPlaceholderText(placeholder)
        elif input_type == "password":
            self.input = QLineEdit()
            self.input.setPlaceholderText(placeholder)
            self.input.setEchoMode(QLineEdit.Password)
        elif input_type == "email":
            self.input = QLineEdit()
            self.input.setPlaceholderText(placeholder)
        elif input_type == "phone":
            self.input = QLineEdit()
            self.input.setPlaceholderText(placeholder)
        
        self.input.setMinimumHeight(40)
        self.input.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1px solid #ECEAE6;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #2A2A2A;
            }
            QLineEdit:focus {
                border: 2px solid #0F6E56;
                padding: 9px 11px;
            }
            QLineEdit::placeholder {
                color: #C5C3BD;
            }
        """)
        layout.addWidget(self.input)
    
    def value(self):
        return self.input.text().strip()
    
    def set_value(self, value: str):
        self.input.setText(value)
    
    def clear(self):
        self.input.clear()


# ─────────────────────────────────────────────────────────────────────────────
#  ADD CUSTOMER PAGE
# ─────────────────────────────────────────────────────────────────────────────

class AddCustomerPage(QWidget):
    """Halaman untuk menambahkan customer baru."""
    
    back_clicked = Signal()
    customer_added = Signal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("addCustomerPage")
        self.setStyleSheet("background: #F8F7F4;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ─ HEADER ─
        header = self._create_header()
        main_layout.addWidget(header)
        
        # ─ FORM CONTAINER ─
        form_container = self._create_form()
        main_layout.addWidget(form_container, 1)
    
    def _create_header(self) -> QFrame:
        """Header dengan tombol kembali dan judul."""
        header = QFrame()
        header.setObjectName("header")
        header.setStyleSheet("""
            #header {
                background: #ffffff;
                border-bottom: 1px solid #ECEAE6;
            }
        """)
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # Tombol kembali
        back_btn = QPushButton("← Kembali")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedSize(120, 36)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ECEAE6;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                color: #2A2A2A;
            }
            QPushButton:hover {
                background: #F5F4F0;
                border-color: #D4D2CD;
            }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        # Judul
        title = QLabel("Tambah Customer Baru")
        title.setFont(QFont("", 16, QFont.Bold))
        title.setStyleSheet("color: #1A1A1A; background: transparent;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        return header
    
    def _create_form(self) -> QFrame:
        """Form untuk input data customer."""
        container = QFrame()
        container.setObjectName("formContainer")
        container.setStyleSheet("""
            #formContainer {
                background: #F8F7F4;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(0)
        
        # ─ SCROLL AREA ─
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #D4D2CD;
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A8A6A2;
            }
        """)
        
        scroll_content = QFrame()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # ─ INFO BOX ─
        info_box = QFrame()
        info_box.setStyleSheet("""
            QFrame {
                background: #E8F0EE;
                border: 1px solid #0F6E5640;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(16, 12, 16, 12)
        
        info_text = QLabel(
            "Isi form di bawah untuk membuat akun customer (member) baru. "
            "Username akan menggunakan email, dan password akan diatur oleh Anda."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(
            "font-size: 12px; color: #0F6E56; background: transparent; line-height: 1.5;"
        )
        info_layout.addWidget(info_text)
        scroll_layout.addWidget(info_box)
        
        # ─ FORM FIELDS ─
        scroll_layout.addSpacing(10)
        
        # Nama
        self.field_name = FormField("Nama Lengkap", "Masukkan nama customer")
        scroll_layout.addWidget(self.field_name)
        
        # Email
        self.field_email = FormField("Email (Username)", "customer@example.com", "email")
        scroll_layout.addWidget(self.field_email)
        
        # Password
        self.field_password = FormField("Password", "Minimal 6 karakter", "password")
        scroll_layout.addWidget(self.field_password)
        
        # Konfirmasi Password
        self.field_password_confirm = FormField("Konfirmasi Password", "Ulangi password", "password")
        scroll_layout.addWidget(self.field_password_confirm)
        
        # No. Telpon (opsional)
        self.field_phone = FormField("No. Telpon (Opsional)", "+62 812 3456 7890", "phone")
        scroll_layout.addWidget(self.field_phone)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # ─ BUTTON AREA ─
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.setSpacing(12)
        
        # Tombol Batal
        cancel_btn = QPushButton("Batal")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ECEAE6;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                color: #2A2A2A;
            }
            QPushButton:hover {
                background: #F5F4F0;
                border-color: #D4D2CD;
            }
        """)
        cancel_btn.clicked.connect(self._cancel)
        button_layout.addWidget(cancel_btn)
        
        # Tombol Tambah
        add_btn = QPushButton("Tambah Customer")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setMinimumHeight(40)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #0F6E56;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                color: #ffffff;
            }
            QPushButton:hover {
                background: #0D5A48;
            }
            QPushButton:pressed {
                background: #0A4839;
            }
        """)
        add_btn.clicked.connect(self._add_customer)
        button_layout.addWidget(add_btn)
        
        layout.addWidget(button_frame)
        
        return container
    
    def _validate_form(self) -> tuple[bool, str]:
        """Validasi form input."""
        name = self.field_name.value()
        email = self.field_email.value()
        password = self.field_password.value()
        password_confirm = self.field_password_confirm.value()
        phone = self.field_phone.value()
        
        if not name:
            return False, "Nama tidak boleh kosong"
        
        if not email:
            return False, "Email tidak boleh kosong"
        
        if "@" not in email or "." not in email:
            return False, "Format email tidak valid"
        
        if not password:
            return False, "Password tidak boleh kosong"
        
        if len(password) < 6:
            return False, "Password minimal 6 karakter"
        
        if password != password_confirm:
            return False, "Password tidak sesuai"
        
        return True, ""
    
    def _add_customer(self):
        """Proses penambahan customer."""
        # Validasi
        valid, msg = self._validate_form()
        if not valid:
            QMessageBox.warning(self, "Validasi Gagal", msg)
            return
        
        # Ambil data
        name = self.field_name.value()
        email = self.field_email.value()
        password = self.field_password.value()
        phone = self.field_phone.value()
        
        # Simpan dengan worker thread
        self.worker = DataWorker(
            lambda: add_customer(name, email, password, phone)
        )
        self.worker.finished.connect(self._on_add_customer_finished)
        self.worker.start()
    
    def _on_add_customer_finished(self, result):
        """Handle hasil penambahan customer."""
        success, message = result
        
        if success:
            QMessageBox.information(
                self, "Berhasil",
                f"✓ {message}\n\nCustomer siap menggunakan akun mereka."
            )
            self._clear_form()
            self.customer_added.emit()
        else:
            QMessageBox.critical(self, "Gagal", f"✗ {message}")
    
    def _cancel(self):
        """Batalkan dan kembali."""
        self._clear_form()
        self.back_clicked.emit()
    
    def _clear_form(self):
        """Bersihkan semua field."""
        self.field_name.clear()
        self.field_email.clear()
        self.field_password.clear()
        self.field_password_confirm.clear()
        self.field_phone.clear()
