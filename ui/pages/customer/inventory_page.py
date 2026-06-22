import base64
import urllib.request

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QColor

from controllers.inventory_controller import CATEGORIES, get_all_inventory, search_inventory
from controllers.rental_controller import get_rentals_by_inventory
from ui.components import apply_success, apply_disabled, apply_nav

# ─────────────────────────────────────────────────────────────────────────────
#  LOAD QPixmap dari URL / base64 / path lokal
# ─────────────────────────────────────────────────────────────────────────────

def _load_pixmap(source: str, size: int = 160) -> QPixmap | None:
    if not source:
        return None
    try:
        pixmap = QPixmap()
        if source.startswith("http://") or source.startswith("https://"):
            req  = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=5).read()
            pixmap.loadFromData(data)
        elif source.startswith("data:image"):
            b64 = source.split(",", 1)[1]
            pixmap.loadFromData(base64.b64decode(b64))
        else:
            try:
                pixmap.loadFromData(base64.b64decode(source))
            except Exception:
                pixmap = QPixmap(source)

        if pixmap.isNull():
            return None
        scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        # crop tengah
        if scaled.width() > size or scaled.height() > size:
            x = (scaled.width()  - size) // 2
            y = (scaled.height() - size) // 2
            scaled = scaled.copy(x, y, size, size)
        return scaled
    except Exception:
        return None

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

# ─────────────────────────────────────────────────────────────────────────────
#  ITEM CARD WIDGET (Tampilan Katalog E-Commerce)
# ─────────────────────────────────────────────────────────────────────────────
class ItemCard(QFrame):
    detail_clicked = Signal(str)

    def __init__(self, item, available_stock):
        super().__init__()
        self.item_id = item.get("id", "")
        
        # Ukuran fixed untuk setiap kartu agar grid rapi
        self.setFixedSize(260, 380)
        self.setObjectName("invCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cat = item.get("category", "")
        img_url = item.get("image_url", "")
        
        # ── 1. IMAGE AREA ──
        img_lbl = QLabel()
        img_lbl.setFixedSize(260, 140)
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setObjectName("imgPlaceholder")
        
        if img_url:
            pix = _load_pixmap(img_url, 140)
            if pix:
                img_lbl.setPixmap(pix)
            else:
                img_lbl.setText("\U0001f4f7")
        else:
            img_lbl.setText("\U0001f4f7")
        
        # ── 2. CATEGORY BADGE (below image) ──
        cat_bg, cat_fg = CATEGORY_PILL_COLORS.get(cat, ("#EDECE8", "#6B6A66"))
        cat_badge = QFrame()
        cat_badge.setObjectName("catBadge")
        cat_badge.setProperty("cat", cat)
        cb_layout = QHBoxLayout(cat_badge)
        cb_layout.setContentsMargins(6, 2, 6, 2)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_label = QLabel(cat)
        cb_label.setObjectName("catLabel")
        cb_layout.addWidget(cb_label)
        
        # Image container with category badge
        image_container = QVBoxLayout()
        image_container.setContentsMargins(0, 0, 0, 0)
        image_container.setSpacing(6)
        image_container.addWidget(img_lbl)
        image_container.addWidget(cat_badge, 0, Qt.AlignCenter)
        layout.addLayout(image_container)
        
        # ── 3. INFO CONTAINER ──
        info = QWidget()
        info.setObjectName("cardInfo")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(16, 12, 16, 16)
        info_layout.setSpacing(8)
        
        # Nama barang
        name = QLabel(item.get("name", ""))
        name.setObjectName("itemName")
        name.setWordWrap(True)
        info_layout.addWidget(name)
        
        # Harga per hari
        price = QLabel(f"Rp {item.get('price_per_day', 0):,}")
        price.setObjectName("itemPrice")
        per_day = QLabel("/ hari")
        per_day.setObjectName("itemPerDay")
        price_row = QHBoxLayout()
        price_row.setContentsMargins(0, 0, 0, 0)
        price_row.setSpacing(0)
        price_row.addWidget(price)
        price_row.addWidget(per_day)
        price_row.addStretch()
        info_layout.addLayout(price_row)
        
        # Stok info
        stock_lbl = QLabel(f"Stok: {available_stock}")
        stock_color = "#E24B4A" if available_stock <= 0 else "#8C8A86"
        stock_lbl.setObjectName("stockLabel")
        stock_lbl.setProperty("stockColor", stock_color)
        stock_lbl.setStyleSheet(f"font-size: 12px; color: {stock_color};")
        info_layout.addWidget(stock_lbl)
        
        info_layout.addStretch()
        
        # ── 4. ACTION BUTTON ──
        btn = QPushButton("Lihat Detail")
        if available_stock > 0 and _calc_status(item) != "Tidak Aktif":
            apply_success(btn, height=34)
            btn.clicked.connect(lambda: self.detail_clicked.emit(self.item_id))
        else:
            btn.setText("Sedang Kosong")
            apply_disabled(btn, height=34)
        info_layout.addWidget(btn)
        
        layout.addWidget(info)

# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOMER INVENTORY PAGE (KATALOG WIDGET)
# ─────────────────────────────────────────────────────────────────────────────
class InventoryPage(QWidget):
    open_detail = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._page = 0
        self._page_size = 12 # Ubah jadi 12 agar pas grid 4 kolom x 3 baris
        self._items_data = []
        self._build_ui()

    def refresh(self):
        self._load_data()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("transparentScroll")

        content = QWidget()
        content.setObjectName("transparentContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 16, 28, 28)
        layout.setSpacing(24)

        # ── Filter Section ──
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        filter_row.setAlignment(Qt.AlignVCenter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama barang...")
        self.search_input.setFixedWidth(300)
        self.search_input.setObjectName("search")
        self.search_input.textChanged.connect(self._search)
        filter_row.addWidget(self.search_input)

        combo_style = """
            QComboBox { border: 1px solid #D4D2CD; border-radius: 8px; padding: 10px 14px; font-size: 13px; background: #ffffff; min-width: 160px; }
            QComboBox:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Semua Kategori"] + CATEGORIES)
        self.category_filter.setObjectName("combo")
        self.category_filter.setMinimumHeight(36)
        self.category_filter.currentTextChanged.connect(self._on_filter)
        filter_row.addWidget(self.category_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Semua Status", "Tersedia", "Semua Disewa", "Tidak Aktif"])
        self.status_filter.setObjectName("combo")
        self.status_filter.setMinimumHeight(36)
        self.status_filter.currentTextChanged.connect(self._on_filter)
        filter_row.addWidget(self.status_filter)
        
        self.btn_reset = QPushButton("↻ Reset")
        self.btn_reset.setObjectName("outline")
        self.btn_reset.setMinimumHeight(36)
        self.btn_reset.clicked.connect(self._reset_filters)
        filter_row.addWidget(self.btn_reset)
        
        filter_row.addStretch()
        
        layout.addLayout(filter_row)

        # ── Grid Katalog Section ──
        self.grid_container = QWidget()
        self.grid_container.setObjectName("transparentContent")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        layout.addWidget(self.grid_container)
        layout.addStretch() # Mendorong grid ke atas

        # ── Pagination Footer ──
        self.footer = QFrame()
        self.footer.setObjectName("paginationFooter")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(20, 12, 20, 12)

        self.footer_label = QLabel("Menampilkan 0 inventaris")
        self.footer_label.setObjectName("mutedSmall")
        f_layout.addWidget(self.footer_label)
        f_layout.addStretch()

        self.btn_prev = QPushButton("\u2039")
        apply_nav(self.btn_prev)
        self.btn_prev.clicked.connect(self._prev_page)
        
        self.btn_next = QPushButton("\u203a")
        apply_nav(self.btn_next)
        self.btn_next.clicked.connect(self._next_page)
        
        f_layout.addWidget(self.btn_prev)
        f_layout.addWidget(self.btn_next)
        
        layout.addWidget(self.footer)

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

        self._populate_grid(filtered)
        self._page = 0

    def _populate_grid(self, data):
        self._filtered_data = data
        total = len(data)
        pages = max(1, (total + self._page_size - 1) // self._page_size)
        if self._page >= pages:
            self._page = pages - 1

        start = self._page * self._page_size
        end = min(start + self._page_size, total)
        page_data = data[start:end]

        # Bersihkan grid sebelumnya
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        # Render kartu baru (Max 4 kolom per baris)
        columns = 4 
        for index, item in enumerate(page_data):
            item_id = item.get("id", "")
            stock = item.get("stock", 0)

            rentals = get_rentals_by_inventory(item_id) or []
            active_rentals = sum(1 for r in rentals if r.get("status") in ("pending", "confirmed", "active"))
            available = max(0, stock - active_rentals)

            card = ItemCard(item, available)
            card.detail_clicked.connect(self.open_detail.emit)
            
            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)

        self.footer_label.setText(f"Menampilkan {start + 1 if total > 0 else 0}–{end} dari {total} inventaris")
        self.btn_prev.setEnabled(self._page > 0)
        self.btn_next.setEnabled(end < total)

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._populate_grid(self._filtered_data)

    def _next_page(self):
        total = len(self._filtered_data)
        if (self._page + 1) * self._page_size < total:
            self._page += 1
            self._populate_grid(self._filtered_data)

    def _search(self, text):
        if not text.strip():
            self._load_data()
            return
        results = search_inventory(text)
        self._load_data(results)

    def _reset_filters(self):
        """Reset all filters to default state."""
        self.search_input.clear()
        self.category_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self._page = 0
        self._load_data()