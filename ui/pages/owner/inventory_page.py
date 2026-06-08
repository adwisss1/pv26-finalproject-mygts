from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDialog, QTextEdit, QSpinBox,
    QMessageBox, QFrame, QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QColor

from controllers.inventory_controller import (
    CATEGORIES, get_all_inventory, search_inventory, 
    add_inventory, update_inventory, delete_inventory
)
from controllers.rental_controller import get_rentals_by_inventory

CATEGORY_PILL_COLORS = {
    "Kostum": ("#E8F0EE", "#0F6E56"),
    "Aksesoris": ("#FEF3E8", "#BA7517"),
    "Properti": ("#E8F7F2", "#1D9E75"),
    "Alat Musik": ("#EEE8F8", "#5B4B8A"),
    "Make Up": ("#F8E8EF", "#C75B7A"),
    "Lainnya": ("#EDECE8", "#6B6A66"),
}

STATUS_STYLES = {
    "Tersedia": ("#E8F7F2", "#1D9E75"),
    "Semua Disewa": ("#FEF3E8", "#BA7517"),
    "Tidak Aktif": ("#EDECE8", "#6B6A66"),
}

def _calc_status(item):
    cond = item.get("condition", "Baik")
    stock = item.get("stock", 0)
    if cond == "Rusak Berat": return "Tidak Aktif"
    
    active_rentals = 0
    rentals = get_rentals_by_inventory(item.get("id", "")) or []
    for r in rentals:
        if r.get("status", "") in ("pending", "confirmed", "active"):
            active_rentals += 1
            
    if active_rentals >= stock or stock <= 0: return "Semua Disewa"
    return "Tersedia"

class StatusBadge(QFrame):
    def __init__(self, status):
        super().__init__()
        bg, fg = STATUS_STYLES.get(status, ("#EDECE8", "#6B6A66"))
        self.setFixedHeight(26)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)
        
        dot = QLabel("\u25cf")
        dot.setStyleSheet(f"color: {fg}; font-size: 10px; background: transparent;")
        
        text = QLabel(status)
        text.setStyleSheet(f"color: {fg}; font-size: 11px; font-weight: bold; background: transparent;")
        
        layout.addWidget(dot)
        layout.addWidget(text)
        self.setStyleSheet(f"background: {bg}; border-radius: 6px;")

class PhotoUploadZone(QFrame):
    def __init__(self):
        super().__init__()
        self._pixmap = None
        self.setFixedHeight(120)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            PhotoUploadZone {
                border: 1.5px dashed #D4D2CD; border-radius: 8px; background: #FAF9F6;
            }
            PhotoUploadZone:hover { border-color: #0F6E56; background: #F4F3F0; }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        
        icon = QLabel("\u2610")
        icon.setStyleSheet("font-size: 28px; color: #A8A6A2; background: transparent;")
        
        self.label = QLabel("Klik untuk upload foto inventaris")
        self.label.setStyleSheet("font-size: 12px; color: #8C8A86; background: transparent;")
        
        layout.addWidget(icon)
        layout.addWidget(self.label)

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label.setText(path.split("/")[-1])
                self.setStyleSheet("PhotoUploadZone { border: 1.5px solid #0F6E56; border-radius: 8px; background: #E8F0EE; }")

    def get_pixmap(self):
        return self._pixmap

class InventoryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self._data = data
        self.setWindowTitle("Edit Inventaris" if data else "Tambah Inventaris Baru")
        self.setFixedWidth(420)
        self.setStyleSheet("QDialog { background: #ffffff; border-radius: 16px; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Edit Inventaris" if data else "Tambah Inventaris Baru")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1A1A1A;")
        layout.addWidget(title)

        field_style = """
            QLineEdit, QTextEdit, QSpinBox {
                border: 1px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 13px; background: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: #0F6E56; }
        """
        label_style = "font-size: 12px; font-weight: 600; color: #1A1A1A; padding-bottom: 2px;"

        def add_field(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            layout.addWidget(lbl)
            layout.addWidget(widget)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contoh: Gendang Beleq")
        self.name_input.setStyleSheet(field_style)
        add_field("Nama Barang", self.name_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 13px; background: #ffffff;
            }
            QComboBox:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """)
        add_field("Kategori", self.category_combo)

        row_layout = QHBoxLayout()
        
        stock_lay = QVBoxLayout()
        lbl_stock = QLabel("Jumlah Stok")
        lbl_stock.setStyleSheet(label_style)
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 9999)
        self.stock_input.setStyleSheet(field_style)
        stock_lay.addWidget(lbl_stock)
        stock_lay.addWidget(self.stock_input)
        
        price_lay = QVBoxLayout()
        lbl_price = QLabel("Harga Sewa / Hari")
        lbl_price.setStyleSheet(label_style)
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 999999999)
        self.price_input.setPrefix("Rp ")
        self.price_input.setStyleSheet(field_style)
        price_lay.addWidget(lbl_price)
        price_lay.addWidget(self.price_input)

        row_layout.addLayout(stock_lay)
        row_layout.addLayout(price_lay)
        layout.addLayout(row_layout)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Tuliskan deskripsi kondisi atau detail barang...")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(field_style)
        add_field("Deskripsi", self.desc_input)

        lbl = QLabel("Foto Inventaris")
        lbl.setStyleSheet(label_style)
        layout.addWidget(lbl)
        self.photo_zone = PhotoUploadZone()
        layout.addWidget(self.photo_zone)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Batal")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #D4D2CD; border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: bold; color: #6B6A66; }
            QPushButton:hover { background: #EDECE8; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Simpan")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background: #0F6E56; border: none; border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: bold; color: #ffffff; }
            QPushButton:hover { background: #0A5A45; }
        """)
        btn_save.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        if data:
            self.name_input.setText(data.get("name", ""))
            self.category_combo.setCurrentText(data.get("category", ""))
            self.stock_input.setValue(data.get("stock", 0))
            self.price_input.setValue(data.get("price_per_day", 0))
            self.desc_input.setText(data.get("description", ""))

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_combo.currentText(),
            "description": self.desc_input.toPlainText().strip(),
            "stock": self.stock_input.value(),
            "price_per_day": self.price_input.value(),
        }

class InventoryPage(QWidget):
    open_detail = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._page = 0
        self._page_size = 10
        self._items_data = []
        self._build_ui()

    def refresh(self):
        self._load_data()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 16, 28, 28)
        layout.setSpacing(20)

        # ── Header Action (Tombol Tambah) ──
        # Judul "Kelola Inventaris" dihapus karena sudah ada di MainWindow
        header = QHBoxLayout()
        header.addStretch()
        
        self.btn_add = QPushButton("+ Tambah Inventaris Baru")
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet("""
            QPushButton { background: #0F6E56; border: none; border-radius: 8px; font-size: 13px; font-weight: bold; color: #ffffff; padding: 12px 20px; }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_add.clicked.connect(self._add_dialog)
        header.addWidget(self.btn_add)
        layout.addLayout(header)

        # ── Filter Section ──
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama barang...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit { border: 1px solid #D4D2CD; border-radius: 8px; padding: 10px 14px; font-size: 13px; background: #ffffff; }
            QLineEdit:focus { border-color: #0F6E56; }
            QLineEdit::placeholder { color: #A8A6A2; }
        """)
        self.search_input.textChanged.connect(self._search)
        filter_row.addWidget(self.search_input)

        combo_style = """
            QComboBox { border: 1px solid #D4D2CD; border-radius: 8px; padding: 10px 14px; font-size: 13px; background: #ffffff; min-width: 160px; }
            QComboBox:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Semua Kategori"] + CATEGORIES)
        self.category_filter.setStyleSheet(combo_style)
        self.category_filter.currentTextChanged.connect(self._on_filter)
        filter_row.addWidget(self.category_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Semua Status", "Tersedia", "Semua Disewa", "Tidak Aktif"])
        self.status_filter.setStyleSheet(combo_style)
        self.status_filter.currentTextChanged.connect(self._on_filter)
        filter_row.addWidget(self.status_filter)
        filter_row.addStretch()
        
        layout.addLayout(filter_row)

        # ── Table Section ──
        self.table_card = QFrame()
        self.table_card.setStyleSheet("background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px;")
        tc_layout = QVBoxLayout(self.table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Foto", "Nama Barang", "Kategori", "Stok Total", "Stok Tersedia", "Status", "Aksi"])
        
        # Penyesuaian lebar kolom agar lebih proporsional
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Fixed); self.table.setColumnWidth(0, 80)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.Fixed); self.table.setColumnWidth(2, 140)
        header_view.setSectionResizeMode(3, QHeaderView.Fixed); self.table.setColumnWidth(3, 110)
        header_view.setSectionResizeMode(4, QHeaderView.Fixed); self.table.setColumnWidth(4, 110)
        header_view.setSectionResizeMode(5, QHeaderView.Fixed); self.table.setColumnWidth(5, 130)
        header_view.setSectionResizeMode(6, QHeaderView.Fixed); self.table.setColumnWidth(6, 100)
        
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(64)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet("""
            QTableWidget { border: none; background: transparent; font-size: 13px; gridline-color: transparent; outline: none; }
            QTableWidget::item { padding: 0px 16px; border-bottom: 1px solid #F0EFEB; }
            QHeaderView::section { background: #F8F7F4; border: none; font-size: 12px; font-weight: bold; color: #8C8A86; padding: 14px 16px; border-bottom: 1px solid #E0DDD8; }
        """)
        tc_layout.addWidget(self.table)

        # ── Pagination Footer ──
        self.footer = QFrame()
        self.footer.setStyleSheet("background: #ffffff; border-top: 1px solid #E0DDD8; border-radius: 0 0 12px 12px;")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(20, 12, 20, 12)

        self.footer_label = QLabel("Menampilkan 0 inventaris")
        self.footer_label.setStyleSheet("font-size: 12px; color: #8C8A86;")
        f_layout.addWidget(self.footer_label)
        f_layout.addStretch()

        nav_style = """
            QPushButton { background: transparent; border: 1px solid #D4D2CD; border-radius: 6px; padding: 4px 12px; font-size: 14px; font-weight: bold; color: #6B6A66; }
            QPushButton:hover { background: #F0EFEB; }
            QPushButton:disabled { color: #D4D2CD; border-color: #E0DDD8; }
        """
        self.btn_prev = QPushButton("\u2039")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet(nav_style)
        self.btn_prev.clicked.connect(self._prev_page)
        
        self.btn_next = QPushButton("\u203a")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(nav_style)
        self.btn_next.clicked.connect(self._next_page)
        
        f_layout.addWidget(self.btn_prev)
        f_layout.addWidget(self.btn_next)
        
        tc_layout.addWidget(self.footer)
        layout.addWidget(self.table_card)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _on_filter(self):
        self._load_data()

    def _load_data(self, data=None):
        if data is None:
            data = get_all_inventory() or []
        self._items_data = data

        cat_filter = self.category_filter.currentText()
        status_filter = self.status_filter.currentText()

        filtered = list(data)
        if cat_filter != "Semua Kategori":
            filtered = [i for i in filtered if i.get("category", "") == cat_filter]
        if status_filter != "Semua Status":
            filtered = [i for i in filtered if _calc_status(i) == status_filter]

        self._populate_table(filtered)
        self._page = 0

    def _populate_table(self, data):
        self._filtered_data = data
        total = len(data)
        pages = max(1, (total + self._page_size - 1) // self._page_size)
        if self._page >= pages:
            self._page = pages - 1

        start = self._page * self._page_size
        end = min(start + self._page_size, total)
        page_data = data[start:end]

        self.table.setRowCount(len(page_data))

        for row, item in enumerate(page_data):
            name, cat, stock = item.get("name", ""), item.get("category", ""), item.get("stock", 0)
            status = _calc_status(item)

            rentals = get_rentals_by_inventory(item.get("id", "")) or []
            active_rentals = sum(1 for r in rentals if r.get("status") in ("pending", "confirmed", "active"))
            available = max(0, stock - active_rentals)

            # Thumbnail
            thumb_wrap = QWidget()
            twl = QHBoxLayout(thumb_wrap)
            twl.setContentsMargins(0, 0, 0, 0)
            twl.setAlignment(Qt.AlignCenter)
            thumbnail = QFrame()
            thumbnail.setFixedSize(46, 46)
            thumbnail.setStyleSheet("background: #F8F7F4; border: 1px solid #E0DDD8; border-radius: 8px;")
            tl = QVBoxLayout(thumbnail)
            tl.setContentsMargins(0, 0, 0, 0)
            tl.setAlignment(Qt.AlignCenter)
            ti = QLabel("\U0001f4f7")
            ti.setStyleSheet("font-size: 18px; color: #A8A6A2; background: transparent;")
            tl.addWidget(ti)
            twl.addWidget(thumbnail)
            self.table.setCellWidget(row, 0, thumb_wrap)

            # Name
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            font = name_item.font()
            font.setWeight(QFont.Weight.Bold)
            name_item.setFont(font)
            self.table.setItem(row, 1, name_item)

            # Category
            cat_bg, cat_fg = CATEGORY_PILL_COLORS.get(cat, ("#EDECE8", "#6B6A66"))
            cat_wrap = QWidget()
            cat_wrap_layout = QHBoxLayout(cat_wrap)
            cat_wrap_layout.setContentsMargins(16, 0, 16, 0)
            cat_badge = QFrame()
            cat_badge.setFixedHeight(24)
            cat_badge.setStyleSheet(f"background: {cat_bg}; border-radius: 6px;")
            cb_layout = QHBoxLayout(cat_badge)
            cb_layout.setContentsMargins(10, 2, 10, 2)
            cb_label = QLabel(cat)
            cb_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {cat_fg}; background: transparent;")
            cb_layout.addWidget(cb_label)
            cat_wrap_layout.addWidget(cat_badge)
            cat_wrap_layout.addStretch()
            self.table.setCellWidget(row, 2, cat_wrap)

            # Stock Total
            stock_item = QTableWidgetItem(str(stock))
            stock_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.table.setItem(row, 3, stock_item)

            # Available
            avail_item = QTableWidgetItem(str(available))
            avail_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            font_avail = avail_item.font()
            font_avail.setWeight(QFont.Weight.Bold)
            avail_item.setFont(font_avail)
            avail_item.setForeground(Qt.red if available <= 0 else QColor("#1D9E75"))
            self.table.setItem(row, 4, avail_item)

            # Status
            status_wrap = QWidget()
            status_layout = QHBoxLayout(status_wrap)
            status_layout.setContentsMargins(8, 0, 8, 0)
            status_layout.setAlignment(Qt.AlignCenter)
            status_badge = StatusBadge(status)
            status_layout.addWidget(status_badge)
            self.table.setCellWidget(row, 5, status_wrap)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(8, 0, 8, 0)
            actions_layout.setAlignment(Qt.AlignCenter)

            global_row = start + row

            btn_edit = QPushButton("\u270e")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 16px; color: #8C8A86; } QPushButton:hover { color: #0F6E56; background: #E8F0EE; border-radius: 8px; }")
            btn_edit.clicked.connect(lambda checked, r=global_row: self._edit_row(r))

            btn_delete = QPushButton("\u2716")
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.setFixedSize(32, 32)
            btn_delete.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 16px; color: #8C8A86; } QPushButton:hover { color: #E24B4A; background: #FEF2F2; border-radius: 8px; }")
            btn_delete.clicked.connect(lambda checked, r=global_row: self._delete_row(r))

            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 6, actions_widget)

        self.footer_label.setText(f"Menampilkan {start + 1 if total > 0 else 0}–{end} dari {total} inventaris")
        self.btn_prev.setEnabled(self._page > 0)
        self.btn_next.setEnabled(end < total)

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._populate_table(self._filtered_data)

    def _next_page(self):
        total = len(self._filtered_data)
        if (self._page + 1) * self._page_size < total:
            self._page += 1
            self._populate_table(self._filtered_data)

    def _search(self, text):
        if not text.strip():
            self._load_data()
            return
        results = search_inventory(text)
        self._load_data(results)

    def _get_item_by_global_row(self, row):
        if 0 <= row < len(self._filtered_data):
            return self._filtered_data[row]
        return None

    def _edit_row(self, row):
        item = self._get_item_by_global_row(row)
        if not item: return
        current = {
            "name": item.get("name", ""),
            "category": item.get("category", ""),
            "stock": item.get("stock", 0),
            "price_per_day": item.get("price_per_day", 0),
            "description": item.get("description", ""),
        }
        dialog = InventoryDialog(self, current)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if update_inventory(item["id"], data): self._load_data()
            else: QMessageBox.warning(self, "Gagal", "Gagal mengupdate inventaris.")

    def _delete_row(self, row):
        item = self._get_item_by_global_row(row)
        if not item: return
        reply = QMessageBox.question(self, "Konfirmasi", f"Hapus \"{item['name']}\"?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if delete_inventory(item["id"]): self._load_data()
            else: QMessageBox.warning(self, "Gagal", "Gagal menghapus inventaris.")

    def _add_dialog(self):
        dialog = InventoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if add_inventory(**data): self._load_data()
            else: QMessageBox.warning(self, "Gagal", "Gagal menambah inventaris.")