import base64
import urllib.request
import uuid
import os

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
from api.supabase_client import get_client

CATEGORY_PILL_COLORS = {
    "Kostum":     ("#E8F0EE", "#0F6E56"),
    "Aksesoris":  ("#FEF3E8", "#BA7517"),
    "Properti":   ("#E8F7F2", "#1D9E75"),
    "Alat Musik": ("#EEE8F8", "#5B4B8A"),
    "Make Up":    ("#F8E8EF", "#C75B7A"),
    "Lainnya":    ("#EDECE8", "#6B6A66"),
}

STATUS_STYLES = {
    "Tersedia":     ("#E8F7F2", "#1D9E75"),
    "Semua Disewa": ("#FEF3E8", "#BA7517"),
    "Tidak Aktif":  ("#EDECE8", "#6B6A66"),
}

STORAGE_BUCKET = "inventory-images"   # ← ganti jika nama bucket berbeda


# ─────────────────────────────────────────────────────────────────────────────
#  UPLOAD foto ke Supabase Storage → return public URL
# ─────────────────────────────────────────────────────────────────────────────

def _upload_photo(local_path: str) -> str:
    """
    Upload file lokal ke Supabase Storage bucket STORAGE_BUCKET.
    Return public URL string, atau "" jika gagal.
    """
    try:
        ext      = os.path.splitext(local_path)[1].lower() or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png",  ".webp": "image/webp"}
        mime = mime_map.get(ext, "image/jpeg")

        with open(local_path, "rb") as f:
            file_bytes = f.read()

        client = get_client()
        client.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": mime}
        )
        public_url = client.storage.from_(STORAGE_BUCKET).get_public_url(filename)
        return public_url
    except Exception as e:
        print(f"[upload_photo] gagal: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
#  LOAD QPixmap dari URL / base64 / path lokal
# ─────────────────────────────────────────────────────────────────────────────

def _load_pixmap(source: str, size: int = 46) -> QPixmap | None:
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


def _make_thumbnail(item: dict, size: int = 46) -> QWidget:
    wrap = QWidget()
    lay  = QHBoxLayout(wrap)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setAlignment(Qt.AlignCenter)

    frame = QFrame()
    frame.setFixedSize(size, size)
    frame.setStyleSheet(
        "background: #F8F7F4; border: 1px solid #E0DDD8; border-radius: 8px; overflow: hidden;"
    )
    fl = QVBoxLayout(frame)
    fl.setContentsMargins(0, 0, 0, 0)
    fl.setAlignment(Qt.AlignCenter)

    source  = item.get("image_url") or ""
    pixmap  = _load_pixmap(source, size)

    if pixmap:
        lbl = QLabel()
        lbl.setFixedSize(size, size)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background: transparent;")
        lbl.setPixmap(pixmap)
        fl.addWidget(lbl)
    else:
        # Inisial nama sebagai placeholder
        initial = (item.get("name") or "?")[0].upper()
        ph = QLabel(initial)
        ph.setAlignment(Qt.AlignCenter)
        ph.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #A8A6A2; background: transparent;"
        )
        fl.addWidget(ph)

    lay.addWidget(frame)
    return wrap


def _calc_status(item):
    if item.get("condition", "Baik") == "Rusak Berat":
        return "Tidak Aktif"
    stock   = item.get("stock", 0)
    rentals = get_rentals_by_inventory(item.get("id", "")) or []
    active  = sum(1 for r in rentals if r.get("status") in ("pending", "confirmed", "active"))
    return "Semua Disewa" if (active >= stock or stock <= 0) else "Tersedia"


# ─────────────────────────────────────────────────────────────────────────────
#  STATUS BADGE
# ─────────────────────────────────────────────────────────────────────────────

class StatusBadge(QFrame):
    def __init__(self, status):
        super().__init__()
        bg, fg = STATUS_STYLES.get(status, ("#EDECE8", "#6B6A66"))
        self.setFixedHeight(26)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)
        dot  = QLabel("●")
        dot.setStyleSheet(f"color: {fg}; font-size: 10px; background: transparent;")
        text = QLabel(status)
        text.setStyleSheet(f"color: {fg}; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(dot)
        layout.addWidget(text)
        self.setStyleSheet(f"background: {bg}; border-radius: 6px;")


# ─────────────────────────────────────────────────────────────────────────────
#  PHOTO UPLOAD ZONE
# ─────────────────────────────────────────────────────────────────────────────

class PhotoUploadZone(QFrame):
    def __init__(self):
        super().__init__()
        self._path = ""
        self.setFixedHeight(130)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            PhotoUploadZone {
                border: 1.5px dashed #D4D2CD; border-radius: 10px; background: #FAF9F6;
            }
            PhotoUploadZone:hover { border-color: #0F6E56; background: #F4F3F0; }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        self._preview = QLabel()
        self._preview.setFixedSize(64, 64)
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet("background: transparent; border-radius: 8px;")
        self._preview.hide()

        self._icon = QLabel("🖼")
        self._icon.setStyleSheet("font-size: 30px; color: #A8A6A2; background: transparent;")

        self.label = QLabel("Klik untuk pilih foto inventaris")
        self.label.setStyleSheet("font-size: 12px; color: #8C8A86; background: transparent;")

        self._hint = QLabel("PNG, JPG, WEBP — maks 5MB")
        self._hint.setStyleSheet("font-size: 10px; color: #B0AEA9; background: transparent;")

        layout.addWidget(self._preview, 0, Qt.AlignCenter)
        layout.addWidget(self._icon,   0, Qt.AlignCenter)
        layout.addWidget(self.label,   0, Qt.AlignCenter)
        layout.addWidget(self._hint,   0, Qt.AlignCenter)

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._path = path
                scaled = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._preview.setPixmap(scaled)
                self._preview.show()
                self._icon.hide()
                filename = path.replace("\\", "/").split("/")[-1]
                self.label.setText(f"✓  {filename}")
                self.label.setStyleSheet("font-size: 12px; color: #0F6E56; background: transparent; font-weight: 600;")
                self.setStyleSheet(
                    "PhotoUploadZone { border: 1.5px solid #0F6E56; border-radius: 10px; background: #E8F5F1; }"
                )

    def get_path(self) -> str:
        return self._path


# ─────────────────────────────────────────────────────────────────────────────
#  INVENTORY DIALOG
# ─────────────────────────────────────────────────────────────────────────────

class InventoryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self._data = data
        is_edit    = data is not None
        self.setWindowTitle("Edit Inventaris" if is_edit else "Tambah Inventaris Baru")
        self.setFixedWidth(440)
        self.setStyleSheet("QDialog { background: #ffffff; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Edit Inventaris" if is_edit else "Tambah Inventaris Baru")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1A1A1A;")
        layout.addWidget(title)

        field_style = """
            QLineEdit, QTextEdit, QSpinBox {
                border: 1px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 13px; background: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border-color: #0F6E56; }
        """
        lbl_style = "font-size: 12px; font-weight: 600; color: #1A1A1A; padding-bottom: 2px;"

        def row(label, widget):
            l = QLabel(label); l.setStyleSheet(lbl_style)
            layout.addWidget(l); layout.addWidget(widget)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Contoh: Gendang Beleq")
        self.name_input.setStyleSheet(field_style)
        row("Nama Barang", self.name_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.setStyleSheet("""
            QComboBox { border: 1px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 13px; background: #ffffff; }
            QComboBox:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """)
        row("Kategori", self.category_combo)

        # Stok + Harga sejajar
        pair = QHBoxLayout()
        pair.setSpacing(12)

        sl = QVBoxLayout()
        sl.addWidget(QLabel("Jumlah Stok", styleSheet=lbl_style))
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 9999)
        self.stock_input.setStyleSheet(field_style)
        sl.addWidget(self.stock_input)

        pl = QVBoxLayout()
        pl.addWidget(QLabel("Harga Sewa / Hari", styleSheet=lbl_style))
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 999999999)
        self.price_input.setPrefix("Rp ")
        self.price_input.setStyleSheet(field_style)
        pl.addWidget(self.price_input)

        pair.addLayout(sl)
        pair.addLayout(pl)
        layout.addLayout(pair)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Deskripsi kondisi atau detail barang...")
        self.desc_input.setMaximumHeight(72)
        self.desc_input.setStyleSheet(field_style)
        row("Deskripsi", self.desc_input)

        lbl_foto = QLabel("Foto Inventaris")
        lbl_foto.setStyleSheet(lbl_style)
        layout.addWidget(lbl_foto)
        self.photo_zone = PhotoUploadZone()
        layout.addWidget(self.photo_zone)

        # Tombol
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Batal")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #D4D2CD; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600; color: #6B6A66; }
            QPushButton:hover { background: #EDECE8; }
        """)
        btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Simpan")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton { background: #0F6E56; border: none; border-radius: 8px;
                padding: 10px 24px; font-size: 13px; font-weight: 600; color: #ffffff; }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

        if data:
            self.name_input.setText(data.get("name", ""))
            self.category_combo.setCurrentText(data.get("category", ""))
            self.stock_input.setValue(data.get("stock", 0))
            self.price_input.setValue(data.get("price_per_day", 0))
            self.desc_input.setText(data.get("description", ""))

        self._image_url = ""

    def _on_save(self):
        """Upload foto dulu (jika ada), baru accept dialog."""
        path = self.photo_zone.get_path()
        if path:
            self.btn_save.setText("Mengupload...")
            self.btn_save.setEnabled(False)
            url = _upload_photo(path)
            self._image_url = url
            self.btn_save.setText("Simpan")
            self.btn_save.setEnabled(True)
        self.accept()

    def get_data(self) -> dict:
        return {
            "name":          self.name_input.text().strip(),
            "category":      self.category_combo.currentText(),
            "description":   self.desc_input.toPlainText().strip(),
            "stock":         self.stock_input.value(),
            "price_per_day": self.price_input.value(),
            "image_url":     self._image_url,   # ← URL hasil upload Supabase Storage
        }


# ─────────────────────────────────────────────────────────────────────────────
#  INVENTORY PAGE
# ─────────────────────────────────────────────────────────────────────────────

class InventoryPage(QWidget):
    open_detail = Signal(str)

    def __init__(self):
        super().__init__()
        self._page          = 0
        self._page_size     = 10
        self._items_data    = []
        self._filtered_data = []
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
        layout  = QVBoxLayout(content)
        layout.setContentsMargins(28, 16, 28, 28)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.addStretch()
        self.btn_add = QPushButton("+ Tambah Inventaris Baru")
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet("""
            QPushButton { background: #0F6E56; border: none; border-radius: 8px;
                font-size: 13px; font-weight: 700; color: #ffffff; padding: 12px 20px; }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_add.clicked.connect(self._add_dialog)
        hdr.addWidget(self.btn_add)
        layout.addLayout(hdr)

        # ── Filter ────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama barang...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit { border: 1px solid #D4D2CD; border-radius: 8px;
                padding: 10px 14px; font-size: 13px; background: #ffffff; }
            QLineEdit:focus { border-color: #0F6E56; }
        """)
        self.search_input.textChanged.connect(self._search)
        filter_row.addWidget(self.search_input)

        combo_style = """
            QComboBox { border: 1px solid #D4D2CD; border-radius: 8px;
                padding: 10px 14px; font-size: 13px; background: #ffffff; min-width: 160px; }
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

        # ── Table ─────────────────────────────────────────────────────────
        self.table_card = QFrame()
        self.table_card.setStyleSheet(
            "background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px;"
        )
        tc = QVBoxLayout(self.table_card)
        tc.setContentsMargins(0, 0, 0, 0)
        tc.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Foto", "Nama Barang", "Kategori", "Stok Total", "Stok Tersedia", "Status", "Aksi"]
        )
        hv = self.table.horizontalHeader()
        hv.setSectionResizeMode(0, QHeaderView.Fixed);  self.table.setColumnWidth(0, 80)
        hv.setSectionResizeMode(1, QHeaderView.Stretch)
        hv.setSectionResizeMode(2, QHeaderView.Fixed);  self.table.setColumnWidth(2, 140)
        hv.setSectionResizeMode(3, QHeaderView.Fixed);  self.table.setColumnWidth(3, 110)
        hv.setSectionResizeMode(4, QHeaderView.Fixed);  self.table.setColumnWidth(4, 110)
        hv.setSectionResizeMode(5, QHeaderView.Fixed);  self.table.setColumnWidth(5, 160)
        hv.setSectionResizeMode(6, QHeaderView.Fixed);  self.table.setColumnWidth(6, 100)

        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(64)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet("""
            QTableWidget { border: none; background: transparent; font-size: 13px;
                gridline-color: transparent; outline: none; }
            QTableWidget::item { padding: 0 16px; border-bottom: 1px solid #F0EFEB; }
            QHeaderView::section { background: #F8F7F4; border: none; font-size: 12px;
                font-weight: bold; color: #8C8A86; padding: 14px 16px;
                border-bottom: 1px solid #E0DDD8; }
        """)
        tc.addWidget(self.table)

        # ── Pagination footer ─────────────────────────────────────────────
        self.footer = QFrame()
        self.footer.setStyleSheet(
            "background: #ffffff; border-top: 1px solid #E0DDD8; border-radius: 0 0 12px 12px;"
        )
        fl = QHBoxLayout(self.footer)
        fl.setContentsMargins(20, 12, 20, 12)

        self.footer_label = QLabel("Menampilkan 0 inventaris")
        self.footer_label.setStyleSheet("font-size: 12px; color: #8C8A86;")
        fl.addWidget(self.footer_label)
        fl.addStretch()

        nav = """
            QPushButton { background: transparent; border: 1px solid #D4D2CD; border-radius: 6px;
                padding: 4px 12px; font-size: 14px; font-weight: bold; color: #6B6A66; }
            QPushButton:hover { background: #F0EFEB; }
            QPushButton:disabled { color: #D4D2CD; border-color: #E0DDD8; }
        """
        self.btn_prev = QPushButton("‹"); self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet(nav);  self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next = QPushButton("›"); self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(nav);  self.btn_next.clicked.connect(self._next_page)
        fl.addWidget(self.btn_prev); fl.addWidget(self.btn_next)
        tc.addWidget(self.footer)
        layout.addWidget(self.table_card)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ── Data ──────────────────────────────────────────────────────────────

    def _on_filter(self):
        self._load_data()

    def _load_data(self, data=None):
        if data is None:
            data = get_all_inventory() or []
        self._items_data = data

        cat_f    = self.category_filter.currentText()
        status_f = self.status_filter.currentText()

        filtered = list(data)
        if cat_f != "Semua Kategori":
            filtered = [i for i in filtered if i.get("category") == cat_f]
        if status_f != "Semua Status":
            filtered = [i for i in filtered if _calc_status(i) == status_f]

        self._page = 0
        self._populate_table(filtered)

    def _populate_table(self, data):
        self._filtered_data = data
        total  = len(data)
        pages  = max(1, (total + self._page_size - 1) // self._page_size)
        if self._page >= pages:
            self._page = pages - 1

        start     = self._page * self._page_size
        end       = min(start + self._page_size, total)
        page_data = data[start:end]

        self.table.setRowCount(len(page_data))

        for row, item in enumerate(page_data):
            name       = item.get("name", "")
            cat        = item.get("category", "")
            stock      = item.get("stock", 0)
            status     = _calc_status(item)
            global_row = start + row

            rentals    = get_rentals_by_inventory(item.get("id", "")) or []
            active_r   = sum(1 for r in rentals if r.get("status") in ("pending", "confirmed", "active"))
            available  = max(0, stock - active_r)

            # Col 0 — Foto
            self.table.setCellWidget(row, 0, _make_thumbnail(item, 46))

            # Col 1 — Nama
            ni = QTableWidgetItem(name)
            ni.setTextAlignment(Qt.AlignCenter)
            f  = ni.font(); f.setWeight(QFont.Weight.Bold); ni.setFont(f)
            self.table.setItem(row, 1, ni)

            # Col 2 — Kategori
            cat_bg, cat_fg = CATEGORY_PILL_COLORS.get(cat, ("#EDECE8", "#6B6A66"))
            cw = QWidget(); cl = QHBoxLayout(cw); cl.setContentsMargins(16, 0, 16, 0)
            cb = QFrame();  cb.setFixedHeight(24)
            cb.setStyleSheet(f"background: {cat_bg}; border-radius: 6px;")
            cbl = QHBoxLayout(cb); cbl.setContentsMargins(10, 2, 10, 2)
            cbl.addWidget(QLabel(cat, styleSheet=f"font-size:11px;font-weight:bold;color:{cat_fg};background:transparent;"))
            cl.addWidget(cb); cl.addStretch()
            self.table.setCellWidget(row, 2, cw)

            # Col 3 — Stok Total
            si = QTableWidgetItem(str(stock)); si.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, si)

            # Col 4 — Stok Tersedia
            ai = QTableWidgetItem(str(available)); ai.setTextAlignment(Qt.AlignCenter)
            af = ai.font(); af.setWeight(QFont.Weight.Bold); ai.setFont(af)
            ai.setForeground(QColor("#E24B4A") if available <= 0 else QColor("#1D9E75"))
            self.table.setItem(row, 4, ai)

            # Col 5 — Status
            sw = QWidget(); sl2 = QHBoxLayout(sw)
            sl2.setContentsMargins(12, 0, 12, 0); sl2.setAlignment(Qt.AlignCenter)
            sl2.addWidget(StatusBadge(status))
            self.table.setCellWidget(row, 5, sw)

            # Col 6 — Aksi
            aw = QWidget(); al = QHBoxLayout(aw)
            al.setContentsMargins(8, 0, 8, 0); al.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton("✎"); btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setFixedSize(32, 32)
            btn_edit.setStyleSheet("""
                QPushButton { background: transparent; border: none; font-size: 16px; color: #8C8A86; }
                QPushButton:hover { color: #0F6E56; background: #E8F0EE; border-radius: 8px; }
            """)
            btn_edit.clicked.connect(lambda _, r=global_row: self._edit_row(r))

            btn_del = QPushButton("✖"); btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setFixedSize(32, 32)
            btn_del.setStyleSheet("""
                QPushButton { background: transparent; border: none; font-size: 16px; color: #8C8A86; }
                QPushButton:hover { color: #E24B4A; background: #FEF2F2; border-radius: 8px; }
            """)
            btn_del.clicked.connect(lambda _, r=global_row: self._delete_row(r))

            al.addWidget(btn_edit); al.addWidget(btn_del)
            self.table.setCellWidget(row, 6, aw)

        self.footer_label.setText(
            f"Menampilkan {start + 1 if total > 0 else 0}–{end} dari {total} inventaris"
        )
        self.btn_prev.setEnabled(self._page > 0)
        self.btn_next.setEnabled(end < total)

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._populate_table(self._filtered_data)

    def _next_page(self):
        if (self._page + 1) * self._page_size < len(self._filtered_data):
            self._page += 1
            self._populate_table(self._filtered_data)

    def _search(self, text):
        self._load_data() if not text.strip() else self._load_data(search_inventory(text))

    def _get_item(self, row) -> dict | None:
        return self._filtered_data[row] if 0 <= row < len(self._filtered_data) else None

    def _edit_row(self, row):
        item = self._get_item(row)
        if not item: return
        dialog = InventoryDialog(self, {
            "name":          item.get("name", ""),
            "category":      item.get("category", ""),
            "stock":         item.get("stock", 0),
            "price_per_day": item.get("price_per_day", 0),
            "description":   item.get("description", ""),
        })
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            # Jika tidak upload foto baru, jangan timpa image_url lama
            if not data.get("image_url"):
                data.pop("image_url", None)
            if update_inventory(item["id"], data):
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal mengupdate inventaris.")

    def _delete_row(self, row):
        item = self._get_item(row)
        if not item: return
        reply = QMessageBox.question(
            self, "Konfirmasi", f"Hapus \"{item['name']}\"?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if delete_inventory(item["id"]):
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal menghapus inventaris.")

    def _add_dialog(self):
        dialog = InventoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if add_inventory(**data):
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal menambah inventaris.")