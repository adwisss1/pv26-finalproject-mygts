from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QColor

from controllers.inventory_controller import CATEGORIES, get_all_inventory, search_inventory
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

# ─────────────────────────────────────────────────────────────────────────────
#  ITEM CARD WIDGET (Tampilan Katalog E-Commerce)
# ─────────────────────────────────────────────────────────────────────────────
class ItemCard(QFrame):
    detail_clicked = Signal(str)

    def __init__(self, item, available_stock):
        super().__init__()
        self.item_id = item.get("id", "")
        
        # Ukuran fixed untuk setiap kartu agar grid rapi
        self.setFixedSize(240, 340)
        self.setStyleSheet("""
            ItemCard {
                background: #ffffff;
                border: 1px solid #E0DDD8;
                border-radius: 12px;
            }
            ItemCard:hover {
                border-color: #0F6E56;
                background: #FAFAF9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # --- 1. Area Gambar ---
        img_path = item.get("image", "")
        img_lbl = QLabel()
        img_lbl.setFixedSize(210, 160)
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet("background: #F8F7F4; border-radius: 8px; border: none;")
        
        if img_path:
            pix = QPixmap(img_path)
            if not pix.isNull():
                img_lbl.setPixmap(pix.scaled(210, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_lbl.setText("\U0001f4f7")
                img_lbl.setStyleSheet("font-size: 32px; color: #D4D2CD; background: #F8F7F4; border-radius: 8px; border: none;")
        else:
            img_lbl.setText("\U0001f4f7")
            img_lbl.setStyleSheet("font-size: 32px; color: #D4D2CD; background: #F8F7F4; border-radius: 8px; border: none;")
        layout.addWidget(img_lbl)

        # --- 2. Kategori & Stok ---
        cat = item.get("category", "")
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        
        cat_bg, cat_fg = CATEGORY_PILL_COLORS.get(cat, ("#EDECE8", "#6B6A66"))
        cb = QLabel(cat)
        cb.setStyleSheet(f"background: {cat_bg}; color: {cat_fg}; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 6px; border: none;")
        meta_row.addWidget(cb)
        meta_row.addStretch()
        
        stock_lbl = QLabel(f"Stok: {available_stock}")
        stock_color = "#E24B4A" if available_stock <= 0 else "#8C8A86"
        stock_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {stock_color}; border: none;")
        meta_row.addWidget(stock_lbl)
        
        layout.addLayout(meta_row)

        # --- 3. Nama Barang ---
        name = item.get("name", "")
        n_lbl = QLabel(name)
        n_lbl.setWordWrap(True)
        n_lbl.setFixedHeight(36) # Sediakan ruang untuk 2 baris teks
        n_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        n_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #1A1A1A; border: none;")
        layout.addWidget(n_lbl)

        # --- 4. Harga ---
        price = item.get("price_per_day", 0)
        p_lbl = QLabel(f"Rp {price:,.0f} / hari".replace(',', '.'))
        p_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #0F6E56; border: none;")
        layout.addWidget(p_lbl)

        layout.addStretch()

        # --- 5. Tombol Aksi ---
        btn = QPushButton("Lihat Detail")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(36)
        
        if available_stock > 0 and _calc_status(item) != "Tidak Aktif":
            btn.setStyleSheet("""
                QPushButton { background: #E8F7F2; border: 1px solid #1D9E75; border-radius: 8px; font-size: 13px; font-weight: bold; color: #0F6E56; }
                QPushButton:hover { background: #0F6E56; color: #ffffff; }
            """)
            btn.clicked.connect(lambda: self.detail_clicked.emit(self.item_id))
        else:
            btn.setText("Sedang Kosong")
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton { background: #F8F7F4; border: 1px solid #E0DDD8; border-radius: 8px; font-size: 13px; font-weight: bold; color: #A8A6A2; }
            """)
        layout.addWidget(btn)

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
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 16, 28, 28)
        layout.setSpacing(24)

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

        # ── Grid Katalog Section ──
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        layout.addWidget(self.grid_container)
        layout.addStretch() # Mendorong grid ke atas

        # ── Pagination Footer ──
        self.footer = QFrame()
        self.footer.setStyleSheet("background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px;")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(20, 12, 20, 12)

        self.footer_label = QLabel("Menampilkan 0 inventaris")
        self.footer_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #8C8A86; border: none;")
        f_layout.addWidget(self.footer_label)
        f_layout.addStretch()

        nav_style = """
            QPushButton { background: transparent; border: 1px solid #D4D2CD; border-radius: 8px; padding: 4px 16px; font-size: 16px; font-weight: bold; color: #6B6A66; }
            QPushButton:hover { background: #F0EFEB; color: #1A1A1A; }
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