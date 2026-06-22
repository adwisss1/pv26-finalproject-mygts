from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QComboBox, QDateEdit, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QDate

from controllers.inventory_controller import get_all_inventory
from controllers.rental_controller import create_rental
from controllers.auth_controller import get_current_user, is_owner
from utils.validators import validate_rental_dates


class RentalPage(QWidget):
    """Simplified 1-step rental page for customers.

    Removes photo upload and step wizard. On success navigates to history.
    """
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def refresh(self):
        self._toggle_visibility()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 40)
        layout.setSpacing(20)

        title = QLabel("Penyewaan Baru")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        form = QFrame()
        form = QFrame()
        form.setObjectName("cardFrame")
        fl = QVBoxLayout(form)
        fl.setSpacing(12)

        lbl_style = "font-size: 13px; font-weight: 600; color: #6B6A66;"

        self.item_combo = QComboBox()
        self.item_combo.setObjectName("combo")
        fl.addWidget(QLabel("Pilih Barang", objectName="formLabel"))
        fl.addWidget(self.item_combo)

        dates = QHBoxLayout()
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate().addDays(1))
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        dates.addWidget(QLabel("Tanggal Ambil", objectName="formLabel"))
        dates.addWidget(self.start_date)
        dates.addWidget(QLabel("Tanggal Kembali", objectName="formLabel"))
        dates.addWidget(self.end_date)
        fl.addLayout(dates)

        fl.addWidget(QLabel("Catatan (opsional)", objectName="formLabel"))
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        fl.addWidget(self.notes)

        btn_row = QHBoxLayout()
        self.btn_submit = QPushButton("Ajukan Penyewaan")
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.clicked.connect(self._submit)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_submit)
        fl.addLayout(btn_row)

        layout.addWidget(form)
        scroll.setWidget(container)
        outer.addWidget(scroll)

        self._toggle_visibility()

    def _toggle_visibility(self):
        user = get_current_user()
        if not user:
            self.setVisible(False)
            return
        self.setVisible(not is_owner())
        self.item_combo.clear()
        items = get_all_inventory() or []
        for it in items:
            if it.get("stock", 0) > 0:
                price = it.get("price_per_day", 0)
                price_str = f"Rp {price:,.0f}".replace(",", ".")
                self.item_combo.addItem(f"{it.get('name')} ({price_str}/hari)", it.get("id"))

    def _submit(self):
        inv_id = self.item_combo.currentData()
        if not inv_id:
            QMessageBox.warning(self, "Lengkapi Data", "Pilih barang yang akan disewa.")
            return

        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        valid, msg = validate_rental_dates(start, end)
        if not valid:
            QMessageBox.warning(self, "Tanggal Tidak Valid", msg)
            return

        user = get_current_user()
        if not user:
            QMessageBox.warning(self, "Autentikasi", "Silakan login terlebih dahulu.")
            return

        notes = self.notes.toPlainText().strip()
        res = create_rental(user["id"], inv_id, start, end, notes)
        if res:
            QMessageBox.information(self, "Sukses", "Penyewaan berhasil diajukan. Menunggu konfirmasi pemilik.")
            self.notes.clear()
            self.navigate_to.emit("history")
        else:
            QMessageBox.warning(self, "Gagal", "Gagal mengajukan penyewaan.")
        