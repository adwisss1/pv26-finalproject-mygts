from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDialog, QTextEdit, QSpinBox,
    QMessageBox, QFrame, QScrollArea, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QColor

from controllers.inventory_controller import (
    CATEGORIES, get_all_inventory, get_by_category,
    search_inventory, add_inventory, update_inventory, delete_inventory
)
from controllers.rental_controller import get_rentals_by_inventory
from controllers.auth_controller import is_owner

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

STATUS_MAP = {
    "Tersedia": "Tersedia",
    "Semua Disewa": "Semua Disewa",
    "Tidak Aktif": "Tidak Aktif",
}


def _calc_status(item):
    cond = item.get("condition", "Baik")
    stock = item.get("stock", 0)
    if cond == "Rusak Berat":
        return "Tidak Aktif"
    active_rentals = 0
    rentals = get_rentals_by_inventory(item.get("id", "")) or []
    for r in rentals:
        s = r.get("status", "")
        if s in ("pending", "confirmed", "active"):
            active_rentals += 1
    if active_rentals >= stock:
        return "Semua Disewa"
    if stock <= 0:
        return "Semua Disewa"
    return "Tersedia"


class StatusBadge(QFrame):
    def __init__(self, status):
        super().__init__()
        bg, fg = STATUS_STYLES.get(status, ("#EDECE8", "#6B6A66"))
        self.setFixedHeight(24)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)
        dot = QLabel("\u25cf")
        dot.setStyleSheet(f"color: {fg}; font-size: 8px; background: transparent;")
        text = QLabel(status)
        text.setStyleSheet(f"color: {fg}; font-size: 11px; font-weight: 600; background: transparent;")
        layout.addWidget(dot)
        layout.addWidget(text)
        self.setStyleSheet(f"background: {bg}; border-radius: 4px;")


class InventoryCard(QFrame):
    open_detail = Signal(str)

    def __init__(self, item_data):
        super().__init__()
        self._item = item_data
        self._item_id = item_data.get("id", "")
        self.setObjectName("invGridCard")
        self.setStyleSheet("""
            #invGridCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
            #invGridCard:hover { border-color: #0F6E56; }
        """)
        self._build(item_data)

    def _build(self, item):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cat = item.get("category", "")
        stock = item.get("stock", 0)
        cat_bg, cat_fg = CATEGORY_PILL_COLORS.get(cat, ("#EDECE8", "#6B6A66"))

        img_placeholder = QFrame()
        img_placeholder.setFixedHeight(150)
        img_placeholder.setStyleSheet("background: #EDECE8; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        img_layout = QVBoxLayout(img_placeholder)
        img_layout.setAlignment(Qt.AlignCenter)
        camera_icon = QLabel("\u26cc")
        camera_icon.setStyleSheet("font-size: 36px; color: #A8A6A2; background: transparent;")
        img_layout.addWidget(camera_icon)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 12, 16, 16)
        body_layout.setSpacing(8)

        cat_badge = QFrame()
        cat_badge.setStyleSheet(f"background: {cat_bg}; border-radius: 4px;")
        cb_layout = QHBoxLayout(cat_badge)
        cb_layout.setContentsMargins(6, 2, 6, 2)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_label = QLabel(cat)
        cb_label.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {cat_fg}; background: transparent;")
        cb_layout.addWidget(cb_label)
        cat_badge.setFixedWidth(cb_label.fontMetrics().boundingRect(cat).width() + 24)
        body_layout.addWidget(cat_badge)

        name = QLabel(item.get("name", ""))
        name.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A;")
        name.setWordWrap(True)
        body_layout.addWidget(name)

        stock_label = QLabel(f"Tersedia: {stock} unit")
        stock_label.setStyleSheet("font-size: 13px; color: #1D9E75; font-weight: 400;")
        body_layout.addWidget(stock_label)

        price = QLabel(f"Rp {item.get('price_per_day', 0):,}")
        price.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F6E56;")
        per_day = QLabel(" / hari")
        per_day.setStyleSheet("font-size: 12px; font-weight: 400; color: #8C8A86;")
        price_row = QHBoxLayout()
        price_row.setContentsMargins(0, 0, 0, 0)
        price_row.setSpacing(0)
        price_row.addWidget(price)
        price_row.addWidget(per_day)
        price_row.addStretch()
        body_layout.addLayout(price_row)

        detail_btn = QPushButton("Lihat Detail")
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.setFixedHeight(34)
        detail_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: 0.5px solid #0F6E56;
                border-radius: 8px; font-size: 12px; font-weight: 500; color: #0F6E56;
            }
            QPushButton:hover { background: #F8F7F4; }
        """)
        detail_btn.clicked.connect(lambda: self.open_detail.emit(self._item_id))
        body_layout.addWidget(detail_btn)

        layout.addWidget(img_placeholder)
        layout.addWidget(body)

    def mouseDoubleClickEvent(self, event):
        self.open_detail.emit(self._item_id)


class PhotoUploadZone(QFrame):
    def __init__(self):
        super().__init__()
        self._pixmap = None
        self.setFixedHeight(120)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            PhotoUploadZone {
                border: 1.5px dashed #D4D2CD; border-radius: 8px;
                background: #FAF9F6;
            }
            PhotoUploadZone:hover { border-color: #0F6E56; }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        icon = QLabel("\u2610")
        icon.setStyleSheet("font-size: 24px; color: #A8A6A2; background: transparent;")
        self.label = QLabel("Klik untuk upload foto inventaris")
        self.label.setStyleSheet("font-size: 12px; color: #A8A6A2; background: transparent;")
        layout.addWidget(icon)
        layout.addWidget(self.label)

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label.setText(path.split("/")[-1])
                self.setStyleSheet("""
                    PhotoUploadZone {
                        border: 1.5px solid #0F6E56; border-radius: 8px;
                        background: #E8F0EE;
                    }
                """)

    def get_pixmap(self):
        return self._pixmap


class InventoryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self._data = data
        self.setWindowTitle("Edit Inventaris" if data else "Tambah Inventaris Baru")
        self.setFixedWidth(420)
        self.setStyleSheet("""
            QDialog {
                background: #ffffff; border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Edit Inventaris" if data else "Tambah Inventaris Baru")
        title.setStyleSheet("font-size: 18px; font-weight: 500; color: #1A1A1A;")
        layout.addWidget(title)

        field_style = """
            QLineEdit, QTextEdit, QSpinBox {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 14px; background: #ffffff;
                min-height: 20px;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: #0F6E56; }
        """
        label_style = "font-size: 12px; font-weight: 500; color: #1A1A1A; padding-bottom: 4px;"

        def add_field(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            layout.addWidget(lbl)
            layout.addWidget(widget)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nama barang")
        self.name_input.setStyleSheet(field_style)
        add_field("Nama Barang", self.name_input)

        self.category_combo = QComboBox()
        for cat in CATEGORIES:
            self.category_combo.addItem(cat)
        self.category_combo.setStyleSheet("""
            QComboBox {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 14px; background: #ffffff;
            }
            QComboBox:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """)
        add_field("Kategori", self.category_combo)

        self.stock_input = QSpinBox()
        self.stock_input.setMinimum(0)
        self.stock_input.setMaximum(9999)
        self.stock_input.setStyleSheet(field_style)
        add_field("Jumlah Stok", self.stock_input)

        self.price_input = QSpinBox()
        self.price_input.setMinimum(0)
        self.price_input.setMaximum(999999999)
        self.price_input.setPrefix("Rp ")
        self.price_input.setStyleSheet(field_style)
        add_field("Harga Sewa / Hari", self.price_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Deskripsi barang...")
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
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Batal")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent; border: 0.5px solid #D4D2CD;
                border-radius: 8px; padding: 10px 24px;
                font-size: 14px; font-weight: 500; color: #6B6A66;
                min-height: 20px;
            }
            QPushButton:hover { background: #EDECE8; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Simpan")
        btn_save.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 10px 24px; font-size: 14px; font-weight: 600;
                color: #ffffff; min-height: 20px;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        btn_save.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        if data:
            self.name_input.setText(data.get("name", ""))
            idx = self.category_combo.findText(data.get("category", ""))
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
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
        self._build_ui()

    def refresh(self):
        self._load_data()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QHBoxLayout()
        title = QLabel("Kelola Inventaris")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        header.addWidget(title)
        header.addStretch()

        self.btn_add = QPushButton("+ Tambah Inventaris Baru")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                font-size: 13px; font-weight: 600; color: #ffffff;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_add.clicked.connect(self._add_dialog)
        header.addWidget(self.btn_add)

        layout.addLayout(header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama barang...")
        self.search_input.setFixedWidth(280)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 10px 14px; font-size: 14px; background: #ffffff;
            }
            QLineEdit:focus { border-color: #0F6E56; }
            QLineEdit::placeholder { color: #A8A6A2; }
        """)
        self.search_input.textChanged.connect(self._search)
        filter_row.addWidget(self.search_input)

        combo_style = """
            QComboBox {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 13px; background: #ffffff;
                min-width: 160px;
            }
            QComboBox:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """

        self.category_filter = QComboBox()
        self.category_filter.addItem("Semua Kategori")
        for c in CATEGORIES:
            self.category_filter.addItem(c)
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

        self.result_count = QLabel("Menampilkan 0 inventaris")
        self.result_count.setStyleSheet("font-size: 13px; color: #8C8A86;")
        layout.addWidget(self.result_count)

        self.customer_grid = QWidget()
        self.customer_grid.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.customer_grid)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        layout.addWidget(self.customer_grid)

        self.empty_state = QWidget()
        self.empty_state.setStyleSheet("background: transparent;")
        es_layout = QVBoxLayout(self.empty_state)
        es_layout.setAlignment(Qt.AlignCenter)
        es_layout.setSpacing(8)
        es_icon = QLabel("\u2610")
        es_icon.setStyleSheet("font-size: 48px; color: #D4D2CD; background: transparent;")
        es_icon.setAlignment(Qt.AlignCenter)
        es_layout.addWidget(es_icon)
        es_title = QLabel("Tidak ada inventaris ditemukan")
        es_title.setStyleSheet("font-size: 16px; font-weight: 500; color: #6B6A66;")
        es_title.setAlignment(Qt.AlignCenter)
        es_layout.addWidget(es_title)
        es_sub = QLabel("Coba ubah kata kunci atau filter")
        es_sub.setStyleSheet("font-size: 13px; color: #A8A6A2;")
        es_sub.setAlignment(Qt.AlignCenter)
        es_layout.addWidget(es_sub)
        layout.addWidget(self.empty_state)
        self.empty_state.setVisible(False)

        self.owner_table_section = QFrame()
        self.owner_table_section.setObjectName("invTableCard")
        self.owner_table_section.setStyleSheet("""
            #invTableCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
        """)
        table_card_layout = QVBoxLayout(self.owner_table_section)
        table_card_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Foto", "Nama Barang", "Kategori", "Stok Total", "Stok Tersedia", "Status", "Aksi"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 72)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 140)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 100)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 110)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 120)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 100)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)
        self.table.setMouseTracking(True)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none; background: #ffffff; font-size: 14px;
                gridline-color: transparent; outline: none;
            }
            QTableWidget::item { padding: 0px 16px; border-bottom: 0.5px solid #EDECE8; }
            QHeaderView::section {
                background: #F8F7F4; border: none;
                font-size: 12px; font-weight: 500; color: #8C8A86;
                padding: 10px 16px; border-bottom: 0.5px solid #E0DDD8;
            }
        """)
        table_card_layout.addWidget(self.table)

        self.table_footer = QFrame()
        self.table_footer.setStyleSheet("background: #ffffff; border-top: 0.5px solid #E0DDD8; border-radius: 0 0 12px 12px;")
        footer_layout = QHBoxLayout(self.table_footer)
        footer_layout.setContentsMargins(16, 10, 16, 10)

        self.footer_label = QLabel("Menampilkan 0 inventaris")
        self.footer_label.setStyleSheet("font-size: 12px; color: #8C8A86;")
        footer_layout.addWidget(self.footer_label)
        footer_layout.addStretch()

        nav_style = """
            QPushButton {
                background: transparent; border: 0.5px solid #D4D2CD;
                border-radius: 6px; padding: 6px 12px; font-size: 12px;
                color: #6B6A66;
            }
            QPushButton:hover { background: #EDECE8; }
            QPushButton:disabled { color: #D4D2CD; }
        """
        self.btn_prev = QPushButton("\u2039")
        self.btn_prev.setStyleSheet(nav_style)
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next = QPushButton("\u203a")
        self.btn_next.setStyleSheet(nav_style)
        self.btn_next.clicked.connect(self._next_page)
        footer_layout.addWidget(self.btn_prev)
        footer_layout.addWidget(self.btn_next)

        table_card_layout.addWidget(self.table_footer)

        layout.addWidget(self.owner_table_section)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._page = 0
        self._page_size = 10
        self._items_data = []

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

        is_owner_view = is_owner()
        self.customer_grid.setVisible(not is_owner_view)
        self.empty_state.setVisible(not is_owner_view and len(data) == 0)
        self.owner_table_section.setVisible(is_owner_view)
        self.btn_add.setVisible(is_owner_view)

        count_text = f"Menampilkan {len(data)} inventaris"
        self.result_count.setText(count_text)
        self.result_count.setVisible(not is_owner_view)

        if is_owner_view:
            self._populate_table(filtered)
        else:
            self._populate_grid(data)

        self._page = 0

    def _populate_grid(self, data):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if len(data) == 0:
            self.empty_state.setVisible(True)
            return

        self.empty_state.setVisible(False)

        for idx, item in enumerate(data):
            card = InventoryCard(item)
            card.open_detail.connect(self.open_detail.emit)
            row, col = divmod(idx, 3)
            self.grid_layout.addWidget(card, row, col)

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
            name = item.get("name", "")
            cat = item.get("category", "")
            stock = item.get("stock", 0)
            status = _calc_status(item)

            rentals = get_rentals_by_inventory(item.get("id", "")) or []
            active_rentals = sum(1 for r in rentals if r.get("status") in ("pending", "confirmed", "active"))
            available = stock - active_rentals
            if available < 0:
                available = 0

            thumb_wrap = QWidget()
            thumb_wrap.setStyleSheet("background: transparent;")
            twl = QHBoxLayout(thumb_wrap)
            twl.setContentsMargins(0, 0, 0, 0)
            twl.setAlignment(Qt.AlignCenter)
            thumbnail = QFrame()
            thumbnail.setFixedSize(40, 40)
            thumbnail.setStyleSheet("background: #F0EFEB; border: 0.5px solid #E0DDD8; border-radius: 6px;")
            tl = QVBoxLayout(thumbnail)
            tl.setContentsMargins(0, 0, 0, 0)
            tl.setAlignment(Qt.AlignCenter)
            ti = QLabel("\U0001f4f7")
            ti.setStyleSheet("font-size: 14px; color: #A8A6A2; background: transparent;")
            tl.addWidget(ti)
            twl.addWidget(thumbnail)
            self.table.setCellWidget(row, 0, thumb_wrap)

            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            font = name_item.font()
            font.setWeight(QFont.Weight.Medium)
            name_item.setFont(font)
            self.table.setItem(row, 1, name_item)

            cat_bg, cat_fg = CATEGORY_PILL_COLORS.get(cat, ("#EDECE8", "#6B6A66"))
            cat_wrap = QWidget()
            cat_wrap.setStyleSheet("background: transparent;")
            cat_wrap_layout = QHBoxLayout(cat_wrap)
            cat_wrap_layout.setContentsMargins(16, 0, 16, 0)
            cat_wrap_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            cat_badge = QFrame()
            cat_badge.setFixedHeight(24)
            cat_badge.setStyleSheet(f"background: {cat_bg}; border-radius: 4px;")
            cb_layout = QHBoxLayout(cat_badge)
            cb_layout.setContentsMargins(8, 2, 8, 2)
            cb_layout.setSpacing(0)
            cb_label = QLabel(cat)
            cb_label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {cat_fg}; background: transparent;")
            cb_layout.addWidget(cb_label)
            cat_wrap_layout.addWidget(cat_badge)
            cat_wrap_layout.addStretch()
            self.table.setCellWidget(row, 2, cat_wrap)

            stock_item = QTableWidgetItem(str(stock))
            stock_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.table.setItem(row, 3, stock_item)

            avail_item = QTableWidgetItem(str(available))
            avail_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            if available <= 0:
                avail_item.setForeground(Qt.red)
            else:
                avail_item.setForeground(QColor("#1D9E75"))
            self.table.setItem(row, 4, avail_item)

            status_wrap = QWidget()
            status_wrap.setStyleSheet("background: transparent;")
            status_layout = QHBoxLayout(status_wrap)
            status_layout.setContentsMargins(8, 0, 8, 0)
            status_layout.setAlignment(Qt.AlignCenter)
            status_badge = StatusBadge(status)
            status_layout.addWidget(status_badge)
            self.table.setCellWidget(row, 5, status_wrap)

            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(8, 0, 8, 0)
            actions_layout.setSpacing(2)
            actions_layout.setAlignment(Qt.AlignCenter)

            global_row = start + row

            btn_edit = QPushButton("\u270e")
            btn_edit.setFixedSize(30, 30)
            btn_edit.setToolTip("Edit")
            btn_edit.setStyleSheet("""
                QPushButton {
                    background: transparent; border: none; border-radius: 6px;
                    font-size: 16px; color: #6B6A66;
                }
                QPushButton:hover { background: #EDECE8; color: #0F6E56; }
            """)
            btn_edit.clicked.connect(lambda checked, r=global_row: self._edit_row(r))

            btn_delete = QPushButton("\u2716")
            btn_delete.setFixedSize(30, 30)
            btn_delete.setToolTip("Hapus")
            btn_delete.setStyleSheet("""
                QPushButton {
                    background: transparent; border: none; border-radius: 6px;
                    font-size: 16px; color: #6B6A66;
                }
                QPushButton:hover { background: #FDE8E8; color: #E24B4A; }
            """)
            btn_delete.clicked.connect(lambda checked, r=global_row: self._delete_row(r))

            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 6, actions_widget)

        self.footer_label.setText(f"Menampilkan {start + 1}–{end} dari {total} inventaris")
        self.btn_prev.setEnabled(self._page > 0)
        self.btn_next.setEnabled(end < total)

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._populate_table(self._filtered_data if hasattr(self, '_filtered_data') else self._items_data)

    def _next_page(self):
        total = len(self._filtered_data if hasattr(self, '_filtered_data') else self._items_data)
        if (self._page + 1) * self._page_size < total:
            self._page += 1
            self._populate_table(self._filtered_data if hasattr(self, '_filtered_data') else self._items_data)

    def _search(self, text):
        if not text.strip():
            self._load_data()
            return
        results = search_inventory(text)
        self._load_data(results)

    def _get_item_by_global_row(self, row):
        data = self._filtered_data if hasattr(self, '_filtered_data') else self._items_data
        if 0 <= row < len(data):
            return data[row]
        return None

    def _edit_row(self, row):
        if not is_owner():
            return
        item = self._get_item_by_global_row(row)
        if not item:
            return
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
            ok = update_inventory(item["id"], {
                "name": data["name"],
                "category": data["category"],
                "description": data["description"],
                "stock": data["stock"],
                "price_per_day": data["price_per_day"],
            })
            if ok:
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal mengupdate inventaris.")

    def _delete_row(self, row):
        if not is_owner():
            return
        item = self._get_item_by_global_row(row)
        if not item:
            return
        reply = QMessageBox.question(
            self, "Konfirmasi", f"Hapus \"{item['name']}\"?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok = delete_inventory(item["id"])
            if ok:
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal menghapus inventaris.")

    def _add_dialog(self):
        dialog = InventoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            ok = add_inventory(**data)
            if ok:
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal menambah inventaris.")
