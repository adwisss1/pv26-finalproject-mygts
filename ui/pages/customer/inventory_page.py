from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from controllers.inventory_controller import (
    CATEGORIES, get_all_inventory, search_inventory
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

class InventoryCard(QFrame):
    open_detail = Signal(str)

    def __init__(self, item_data):
        super().__init__()
        self._item = item_data
        self._item_id = item_data.get("id", "")
        self.setObjectName("invGridCard")
        self.setStyleSheet("""
            #invGridCard { background: #ffffff; border: 0.5px solid #E0DDD8; border-radius: 12px; }
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
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 12, 16, 16)
        body_layout.setSpacing(8)

        cat_badge = QFrame()
        cat_badge.setStyleSheet(f"background: {cat_bg}; border-radius: 4px;")
        cb_layout = QHBoxLayout(cat_badge)
        cb_layout.setContentsMargins(6, 2, 6, 2)
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
        price_row.addWidget(price)
        price_row.addWidget(per_day)
        price_row.addStretch()
        body_layout.addLayout(price_row)

        detail_btn = QPushButton("Lihat Detail")
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.setFixedHeight(34)
        detail_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 0.5px solid #0F6E56; border-radius: 8px; font-size: 12px; font-weight: 500; color: #0F6E56; }
            QPushButton:hover { background: #F8F7F4; }
        """)
        detail_btn.clicked.connect(lambda: self.open_detail.emit(self._item_id))
        body_layout.addWidget(detail_btn)

        layout.addWidget(img_placeholder)
        layout.addWidget(body)

    def mouseDoubleClickEvent(self, event):
        self.open_detail.emit(self._item_id)

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
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QHBoxLayout()
        title = QLabel("Katalog Inventaris Sanggar")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama barang...")
        self.search_input.setFixedWidth(280)
        self.search_input.setStyleSheet("""
            QLineEdit { border: 0.5px solid #D4D2CD; border-radius: 8px; padding: 10px 14px; font-size: 14px; background: #ffffff; }
            QLineEdit:focus { border-color: #0F6E56; }
            QLineEdit::placeholder { color: #A8A6A2; }
        """)
        self.search_input.textChanged.connect(self._search)
        filter_row.addWidget(self.search_input)

        combo_style = """
            QComboBox { border: 0.5px solid #D4D2CD; border-radius: 8px; padding: 10px 12px; font-size: 13px; background: #ffffff; min-width: 160px; }
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

        self.result_count = QLabel("Menampilkan 0 inventaris")
        self.result_count.setStyleSheet("font-size: 13px; color: #8C8A86;")
        layout.addWidget(self.result_count)

        self.customer_grid = QWidget()
        self.grid_layout = QGridLayout(self.customer_grid)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        layout.addWidget(self.customer_grid)

        self.empty_state = QWidget()
        es_layout = QVBoxLayout(self.empty_state)
        es_layout.setAlignment(Qt.AlignCenter)
        es_icon = QLabel("\u2610")
        es_icon.setStyleSheet("font-size: 48px; color: #D4D2CD;")
        es_icon.setAlignment(Qt.AlignCenter)
        es_title = QLabel("Tidak ada inventaris ditemukan")
        es_title.setStyleSheet("font-size: 16px; font-weight: 500; color: #6B6A66;")
        es_title.setAlignment(Qt.AlignCenter)
        es_layout.addWidget(es_icon)
        es_layout.addWidget(es_title)
        layout.addWidget(self.empty_state)
        self.empty_state.setVisible(False)

        scroll.setWidget(content)
        outer.addWidget(scroll)
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

        self.result_count.setText(f"Menampilkan {len(filtered)} inventaris")
        self._populate_grid(filtered)

    def _populate_grid(self, data):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if len(data) == 0:
            self.empty_state.setVisible(True)
            self.customer_grid.setVisible(False)
            return

        self.empty_state.setVisible(False)
        self.customer_grid.setVisible(True)

        for idx, item in enumerate(data):
            card = InventoryCard(item)
            card.open_detail.connect(self.open_detail.emit)
            row, col = divmod(idx, 3) # 3 Kolom kartu
            self.grid_layout.addWidget(card, row, col)

    def _search(self, text):
        if not text.strip():
            self._load_data()
            return
        results = search_inventory(text)
        self._load_data(results)