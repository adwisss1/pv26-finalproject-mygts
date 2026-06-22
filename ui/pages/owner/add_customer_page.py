"""
Halaman untuk Owner menambahkan akun Customer baru.
Setiap customer adalah member yang dibuat oleh owner.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox, QSpinBox, QScrollArea, QSizePolicy, QDialog
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setObjectName("formLabel")
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
        self.input.setObjectName("input")
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
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # Tombol kembali
        back_btn = QPushButton("← Kembali")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedSize(120, 36)
        back_btn.setObjectName("outline")
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        # Judul
        title = QLabel("Tambah Customer Baru")
        title.setFont(QFont("", 16, QFont.Bold))
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        layout.addStretch()
        
        return header
    
    def _create_form(self) -> QFrame:
        """Form untuk input data customer."""
        container = QFrame()
        container.setObjectName("formContainer")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(0)
        
        # ─ SCROLL AREA ─
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")
        
        scroll_content = QFrame()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # ─ INFO BOX ─
        info_box = QFrame()
        info_box.setObjectName("infoBox")
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(16, 12, 16, 12)
        
        info_text = QLabel(
            "Isi form di bawah untuk membuat akun customer (member) baru. "
            "Username akan menggunakan email, dan password akan diatur oleh Anda."
        )
        info_text.setWordWrap(True)
        info_text.setObjectName("infoText")
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
        cancel_btn.setObjectName("outline")
        cancel_btn.clicked.connect(self._cancel)
        button_layout.addWidget(cancel_btn)
        
        # Tombol Tambah
        add_btn = QPushButton("Tambah Customer")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setMinimumHeight(40)
        add_btn.setObjectName("primary")
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


class AddCustomerDialog(QDialog):
    """Dialog QDialog untuk menambah customer (memenuhi ketentuan form sebagai dialog)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tambah Customer")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)

        # reuse same fields as page
        self.field_name = FormField("Nama Lengkap", "Masukkan nama customer")
        self.field_email = FormField("Email (Username)", "customer@example.com", "email")
        self.field_password = FormField("Password", "Minimal 6 karakter", "password")
        self.field_password_confirm = FormField("Konfirmasi Password", "Ulangi password", "password")
        self.field_phone = FormField("No. Telpon (Opsional)", "+62 812 3456 7890", "phone")

        layout.addWidget(self.field_name)
        layout.addWidget(self.field_email)
        layout.addWidget(self.field_password)
        layout.addWidget(self.field_password_confirm)
        layout.addWidget(self.field_phone)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Batal")
        cancel.clicked.connect(self.reject)
        add = QPushButton("Tambah Customer")
        add.clicked.connect(self._on_add)
        btn_row.addWidget(cancel)
        btn_row.addWidget(add)
        layout.addLayout(btn_row)

    def _validate(self):
        name = self.field_name.value()
        email = self.field_email.value()
        pw = self.field_password.value()
        pw2 = self.field_password_confirm.value()
        if not name:
            return False, "Nama tidak boleh kosong"
        if not email or "@" not in email:
            return False, "Email tidak valid"
        if not pw or len(pw) < 6:
            return False, "Password minimal 6 karakter"
        if pw != pw2:
            return False, "Password tidak cocok"
        return True, ""

    def _on_add(self):
        valid, msg = self._validate()
        if not valid:
            QMessageBox.warning(self, "Validasi Gagal", msg)
            return
        # call add_customer synchronously (controller handles storage)
        name = self.field_name.value()
        email = self.field_email.value()
        pw = self.field_password.value()
        phone = self.field_phone.value()
        ok, message = add_customer(name, email, pw, phone)
        if ok:
            QMessageBox.information(self, "Berhasil", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Gagal", message)
