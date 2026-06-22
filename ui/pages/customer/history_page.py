from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QMessageBox, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor, QPixmap
import base64
import urllib.request

from controllers.rental_controller import get_rentals_for_owner, get_rentals_for_customer
from utils.worker import DataWorker
from controllers.inventory_controller import CATEGORIES
from controllers.auth_controller import get_current_user, is_owner
from utils.export import export_csv, export_pdf, prepare_rental_export
from ui.components import apply_danger, apply_success, apply_primary, apply_link, input_style, create_status_badge, apply_warning
# ─────────────────────────────────────────────────────────────────────────────
#  HELPER FUNCTION: Load image from URL/base64
# ─────────────────────────────────────────────────────────────────────────────

def _load_pixmap(source: str, size: int = 48) -> QPixmap | None:
    """Load QPixmap dari URL, base64, atau path lokal."""
    if not source:
        return None
    try:
        pixmap = QPixmap()
        if source.startswith("http://") or source.startswith("https://"):
            req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
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
        # Crop tengah
        if scaled.width() > size or scaled.height() > size:
            x = (scaled.width() - size) // 2
            y = (scaled.height() - size) // 2
            scaled = scaled.copy(x, y, size, size)
        return scaled
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────────────────────
#  STATUS BADGE & CATEGORY STYLES
# ─────────────────────────────────────────────────────────────────────────────

STATUS_BADGE_STYLES = {
    "returned": ("#F0FDF8", "#1D9E75", "✓ Selesai"),
    "active": ("#E8F0EE", "#0F6E56", "► Aktif"),
    "confirmed": ("#E8F0EE", "#0F6E56", "► Aktif"),
    "pending": ("#FEF3E8", "#BA7517", "⏳ Menunggu"),
    "rejected": ("#FEF2F2", "#E24B4A", "✗ Ditolak"),
    "overdue": ("#FEF2F2", "#E24B4A", "⚠ Terlambat"),
}

CATEGORY_COLORS = {
    "Kostum": ("#E8F0EE", "#0F6E56"),
    "Aksesoris": ("#FEF3E8", "#BA7517"),
    "Properti": ("#E8F7F2", "#1D9E75"),
    "Alat Musik": ("#EEE8F8", "#5B4B8A"),
    "Make Up": ("#F8E8EF", "#C75B7A"),
    "Lainnya": ("#EDECE8", "#6B6A66"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  HELPER WIDGETS
# ─────────────────────────────────────────────────────────────────────────────



class SummaryStat(QFrame):
    def __init__(self, label, value, color):
        super().__init__()
        self.setObjectName("summaryStat")
        lo = QVBoxLayout(self)
        lo.setContentsMargins(20, 20, 20, 20)
        lo.setSpacing(6)
        
        self.v = QLabel(str(value))
        self.v.setObjectName("summaryValue")
        self.v.setProperty("valueColor", color)
        
        l = QLabel(label)
        l.setObjectName("summaryLabel")
        
        lo.addWidget(self.v)
        lo.addWidget(l)
        lo.addStretch()

    def set_value(self, value):
        self.v.setText(str(value))

class RentalHistoryCard(QFrame):
    detail_clicked = Signal(str)
    return_clicked = Signal(str)  # Rental ID untuk return process
    print_clicked = Signal(dict)   # Rental data untuk print nota

    def __init__(self, rental_data):
        super().__init__()
        self.rental_id = rental_data.get("id", "")
        self.rental_data = rental_data
        self._build(rental_data)

    def _build(self, r):
        inv = r.get("inventories") or {}
        status = r.get("status", "")
        start, end = r.get("start_date", ""), r.get("end_date", "")
        fine = r.get("fine_amount", 0)
        cat = inv.get("category", "")
        name = inv.get("name", "-")

        is_overdue = status in ("active", "confirmed") and end and end < datetime.now().strftime("%Y-%m-%d")
        status_key = "overdue" if is_overdue else status
        bg, fg, label = STATUS_BADGE_STYLES.get(status_key, ("#EDECE8", "#6B6A66", status.title()))
        cat_bg, cat_fg = CATEGORY_COLORS.get(cat, ("#EDECE8", "#6B6A66"))

        durasi = ""
        if start and end:
            try:
                d = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
                durasi = f"{d} hari" if d > 0 else "1 hari"
            except: durasi = "-"

        try: sd = datetime.strptime(start, "%Y-%m-%d").strftime("%d %b %Y") if start else "-"
        except: sd = start
        
        try: ed = datetime.strptime(end, "%Y-%m-%d").strftime("%d %b %Y") if end else "-"
        except: ed = end

        self.setObjectName("rentalHistoryCard")
        self.setProperty("status", status)

        # Tambah notifikasi jika status accepted/rejected
        notification_widget = None
        if status == "confirmed":  # Owner accepted
            notif = QFrame()
            notif.setObjectName("notifAccepted")
            notif.setProperty("notifType", "accepted")
            nl = QHBoxLayout(notif)
            nl.setContentsMargins(8, 4, 8, 4)
            nl.setSpacing(6)
            w1 = QLabel("✓")
            w1.setObjectName("notifSymbol")
            w1.setProperty("symColor", "#1D9E75")
            w2 = QLabel("Penyewaan diterima pemilik!")
            w2.setObjectName("notifText")
            w2.setProperty("textColor", "#1D9E75")
            nl.addWidget(w1)
            nl.addWidget(w2)
            nl.addStretch()
            notification_widget = notif
        elif status == "rejected":  # Owner rejected
            notif = QFrame()
            notif.setObjectName("notifRejected")
            notif.setProperty("notifType", "rejected")
            nl = QHBoxLayout(notif)
            nl.setContentsMargins(8, 4, 8, 4)
            nl.setSpacing(6)
            w1 = QLabel("✗")
            w1.setObjectName("notifSymbol")
            w1.setProperty("symColor", "#E24B4A")
            w2 = QLabel("Penyewaan ditolak pemilik")
            w2.setObjectName("notifText")
            w2.setProperty("textColor", "#E24B4A")
            nl.addWidget(w1)
            nl.addWidget(w2)
            nl.addStretch()
            notification_widget = notif

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        # Notifikasi di atas (jika ada)
        if notification_widget:
            layout.addWidget(notification_widget)

        # ═══════════════════════════════════════════════════════════════════════════
        # MAIN CONTENT ROW: [Image] [Name/Cat] [Dates] [DetailBtn] [Status]
        # ═══════════════════════════════════════════════════════════════════════════
        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(12)

        # ── 1. THUMBNAIL DENGAN IMAGE (FIXED WIDTH) ──
        thumb = QFrame()
        thumb.setFixedSize(72, 72)
        thumb.setObjectName("thumb")
        tl = QVBoxLayout(thumb)
        tl.setAlignment(Qt.AlignCenter)
        tl.setContentsMargins(0, 0, 0, 0)
        
        img_url = inv.get("image_url", "")
        img_lbl = QLabel()
        img_lbl.setFixedSize(72, 72)
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setObjectName("thumbImage")
        
        if img_url:
            pix = _load_pixmap(img_url, 72)
            if pix:
                img_lbl.setPixmap(pix)
            else:
                img_lbl.setText("\U0001f4f7")
        else:
            img_lbl.setText("\U0001f4f7")
        
        tl.addWidget(img_lbl)
        main_row.addWidget(thumb, 0, Qt.AlignTop)

        # ── 2. NAMA & KATEGORI (FIXED WIDTH) ──
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        left_col.setContentsMargins(0, 0, 0, 0)
        
        lbl_name = QLabel(name)
        lbl_name.setObjectName("rentalName")
        left_col.addWidget(lbl_name)
        
        cb = QFrame()
        cb.setObjectName("catBadge")
        cbl = QHBoxLayout(cb)
        cbl.setContentsMargins(8, 2, 8, 2)
        cbl.setSpacing(0)
        lbl_cat = QLabel(cat)
        lbl_cat.setObjectName("catLabel")
        cbl.addWidget(lbl_cat)
        left_col.addWidget(cb)
        left_col.addStretch()
        
        left_widget = QWidget()
        left_widget.setLayout(left_col)
        left_widget.setFixedWidth(120)
        main_row.addWidget(left_widget, 0, Qt.AlignTop)

        # ── 3. RENTAL INFO / DATES (EXPANDABLE) ──
        center = QVBoxLayout()
        center.setSpacing(2)
        center.setContentsMargins(0, 0, 0, 0)
        
        for lbl, val in [("Tgl Sewa:", sd), ("Tenggat:", ed), ("Durasi:", durasi)]:
            # Gabungkan label dan value jadi satu untuk tidak ada jarak
            combined_text = f'<span style="color: #8C8A86; font-weight: 500;">{lbl}</span><span style="color: #1A1A1A; font-weight: 600; margin-left: 0px;">\u00a0{val}</span>'
            row_lbl = QLabel(combined_text)
            row_lbl.setObjectName("rentalInfoRow")
            center.addWidget(row_lbl)
        
        center_widget = QWidget()
        center_widget.setLayout(center)
        main_row.addWidget(center_widget, 1, Qt.AlignTop)

        # ── 4. DETAIL BUTTON (FIXED WIDTH FULL BUTTON) ──
        inv_id = inv.get("id", "")
        db = QPushButton("Lihat Detail")
        apply_success(db, height=36)
        db.setFixedWidth(120)
        db.clicked.connect(lambda: self.detail_clicked.emit(inv_id))
        main_row.addWidget(db, 0, Qt.AlignTop)

        # ── 4B. CETAK NOTA BUTTON (FIXED WIDTH, same size as detail button) ──
        if status in ("confirmed", "active", "returned", "overdue"):
            btn_print = QPushButton("Cetak Nota")
            apply_warning(btn_print)
            btn_print.setFixedHeight(36)
            btn_print.setFixedWidth(120)
            btn_print.clicked.connect(lambda: self.print_clicked.emit(self.rental_data))
            main_row.addWidget(btn_print, 0, Qt.AlignTop)

        # ── 5. STATUS & CETAK (RIGHT SIDE) ──
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        right_col.setContentsMargins(0, 0, 0, 0)
        
        # Status badge
        badge = QFrame()
        badge.setObjectName("statusBadgeWrap")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(10, 4, 10, 4)
        d1 = QLabel("\u25cf")
        d1.setObjectName("badgeDot")
        d2 = QLabel(label)
        d2.setObjectName("badgeText")
        bl.addWidget(d1)
        bl.addWidget(d2)
        right_col.addWidget(badge, 0, Qt.AlignRight | Qt.AlignTop)
        
        # Denda info jika ada
        if fine > 0:
            denda_lbl = QLabel(f"Denda: Rp {fine:,}".replace(",", "."))
            denda_lbl.setObjectName("rowLabel")
            denda_lbl.setStyleSheet("font-size: 10px; color: #E24B4A; font-weight: bold;")
            right_col.addWidget(denda_lbl, 0, Qt.AlignRight)
        
        
        right_widget = QWidget()
        right_widget.setLayout(right_col)
        right_widget.setFixedWidth(140)
        main_row.addWidget(right_widget, 0, Qt.AlignTop)

        layout.addLayout(main_row)

        # ═══════════════════════════════════════════════════════════════════════════
        # ACTION ROW: Return button jika applicable
        # ═══════════════════════════════════════════════════════════════════════════
        if status in ("active", "confirmed", "pending", "overdue"):
            action_row = QHBoxLayout()
            action_row.setContentsMargins(0, 0, 0, 0)
            action_row.setSpacing(0)
            action_row.addStretch()
            
            btn_return = QPushButton("↩ Kembalikan Barang")
            apply_primary(btn_return)
            btn_return.setFixedHeight(36)
            btn_return.setFixedWidth(150)
            btn_return.clicked.connect(lambda: self.return_clicked.emit(self.rental_id))
            action_row.addWidget(btn_return, 0, Qt.AlignRight)
            
            layout.addLayout(action_row)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

class HistoryPage(QWidget):
    navigate_to = Signal(str)
    open_item_detail = Signal(str)  # Emit inventory_id untuk membuka detail item

    def __init__(self):
        super().__init__()
        self._all_data = []
        self._current_page = 0
        self._page_size = 10
        self._worker = None
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

        # Container Owner
        self.owner_section = QWidget()
        self.owner_section.setObjectName("transparentContent")
        ol = QVBoxLayout(self.owner_section)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.setSpacing(24)
        layout.addWidget(self.owner_section)

        # Container Customer
        self.customer_section = QWidget()
        self.customer_section.setObjectName("transparentContent")
        cl = QVBoxLayout(self.customer_section)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(24)
        layout.addWidget(self.customer_section)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._build_owner_section(ol)
        self._build_customer_section(cl)

    def _build_owner_section(self, ol):
        # Header Aksi (Judul dihapus agar tidak double)
        header = QHBoxLayout()
        header.addStretch()

        btn_export_pdf = QPushButton(" \U0001f4c4 Export PDF")
        apply_danger(btn_export_pdf)
        btn_export_pdf.clicked.connect(self._export_pdf)
        header.addWidget(btn_export_pdf)

        btn_export_csv = QPushButton(" \U0001f4ca Export CSV")
        apply_success(btn_export_csv)
        btn_export_csv.clicked.connect(self._export_csv)
        header.addWidget(btn_export_csv)

        ol.addLayout(header)

        # Filter Box — 2 baris agar tidak terpotong
        fc = QFrame()
        fc.setObjectName("filterCard")
        fc_main = QVBoxLayout(fc)
        fc_main.setContentsMargins(20, 16, 20, 16)
        fc_main.setSpacing(10)

        fs = input_style()
        lbl_style = "font-size: 13px; font-weight: 500; color: #6B6A66;"

        # Baris 1: Rentang Tanggal
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(QLabel("Dari:", styleSheet=lbl_style))
        self.odf = QDateEdit(calendarPopup=True)
        self.odf.setDate(QDate.currentDate().addYears(-2))
        self.odf.setDisplayFormat("yyyy-MM-dd")
        self.odf.setObjectName("input")
        row1.addWidget(self.odf)
        row1.addWidget(QLabel("s/d", styleSheet=lbl_style))
        self.odt = QDateEdit(calendarPopup=True)
        self.odt.setDate(QDate.currentDate())
        self.odt.setDisplayFormat("yyyy-MM-dd")
        self.odt.setObjectName("input")
        row1.addWidget(self.odt)
        row1.addStretch()
        fc_main.addLayout(row1)

        # Baris 2: Filter Kategori + Status + Tombol
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(QLabel("Kategori:", styleSheet=lbl_style))
        self.okf = QComboBox()
        self.okf.addItems(["Semua Kategori"] + CATEGORIES)
        self.okf.setObjectName("combo")
        row2.addWidget(self.okf)
        row2.addWidget(QLabel("Status:", styleSheet=lbl_style))
        self.osf = QComboBox()
        self.osf.addItems(["Semua Status", "Selesai", "Aktif", "Terlambat", "Dibatalkan"])
        self.osf.setObjectName("combo")
        row2.addWidget(self.osf)
        row2.addStretch()
        btn = QPushButton("Terapkan Filter")
        apply_primary(btn, height=38)
        btn.clicked.connect(self._load_data)
        row2.addWidget(btn)
        fc_main.addLayout(row2)
        ol.addWidget(fc)

        # Summary Cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)
        
        self.st_total = SummaryStat("Total Transaksi", "0", "#1A1A1A")
        self.st_revenue = SummaryStat("Total Pendapatan", "Rp 0", "#0F6E56")
        self.st_durasi = SummaryStat("Rata-rata Durasi", "0 hari", "#BA7517")
        
        summary_layout.addWidget(self.st_total)
        summary_layout.addWidget(self.st_revenue)
        summary_layout.addWidget(self.st_durasi)
        ol.addLayout(summary_layout)

        # Table Section
        from ui.components import card_frame_style
        tc = QFrame(styleSheet=card_frame_style())
        tcl = QVBoxLayout(tc)
        tcl.setContentsMargins(0, 0, 0, 0)
        tcl.setSpacing(0)

        self.otable = QTableWidget(columnCount=9)
        self.otable.setHorizontalHeaderLabels(["No", "Nama Customer", "Nama Barang", "Kategori", "Tgl Ambil", "Tgl Kembali", "Durasi", "Denda", "Status"])
        
        hv = self.otable.horizontalHeader()
        hv.setSectionResizeMode(QHeaderView.Stretch)
        hv.setSectionResizeMode(0, QHeaderView.Fixed); self.otable.setColumnWidth(0, 60)
        hv.setSectionResizeMode(8, QHeaderView.Fixed); self.otable.setColumnWidth(8, 120)
        
        self.otable.setSelectionMode(QTableWidget.NoSelection)
        self.otable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.otable.verticalHeader().setVisible(False)
        self.otable.verticalHeader().setDefaultSectionSize(56)
        self.otable.setFocusPolicy(Qt.NoFocus)
        self.otable.setObjectName("ownerTable")
        # enable sorting
        self.otable.setSortingEnabled(True)
        tcl.addWidget(self.otable)

        # Pagination Footer
        pf = QFrame()
        pf.setObjectName("paginationFooter")
        pl = QHBoxLayout(pf)
        pl.setContentsMargins(20, 12, 20, 12)

        self.ofooter = QLabel("Menampilkan 0 data")
        self.ofooter.setObjectName("mutedSmall")
        pl.addWidget(self.ofooter)
        pl.addStretch()

        self.oprev = QPushButton("\u2039", cursor=Qt.PointingHandCursor)
        self.oprev.setObjectName("nav")
        self.oprev.clicked.connect(self._prev_page)
        self.onxt = QPushButton("\u203a", cursor=Qt.PointingHandCursor)
        self.onxt.setObjectName("nav")
        self.onxt.clicked.connect(self._next_page)
        
        pl.addWidget(self.oprev)
        pl.addWidget(self.onxt)
        tcl.addWidget(pf)
        ol.addWidget(tc)

        # Empty State
        self.oempty = QFrame()
        self.oempty.setObjectName("emptyCard")
        self.oempty.setMinimumHeight(200)
        el = QVBoxLayout(self.oempty)
        el.setAlignment(Qt.AlignCenter)
        ico = QLabel("\u2610")
        ico.setObjectName("emptyIcon")
        ico.setAlignment(Qt.AlignCenter)
        el.addWidget(ico)
        t1 = QLabel("Belum ada data transaksi")
        t1.setObjectName("emptyText")
        t1.setAlignment(Qt.AlignCenter)
        el.addWidget(t1)
        ol.addWidget(self.oempty)
        self.oempty.setVisible(False)

    def _build_customer_section(self, cl):
        # Filter Box — Modern single line
        fc = QFrame()
        fc.setObjectName("filterCard")
        fc_main = QHBoxLayout(fc)
        fc_main.setContentsMargins(16, 12, 16, 12)
        fc_main.setSpacing(8)
        fc_main.setAlignment(Qt.AlignVCenter)

        lbl_style = "font-size: 12px; font-weight: 600; color: #6B6A66; border: none;"

        # "Dari" label + date
        fc_main.addWidget(QLabel("Dari:", styleSheet=lbl_style))
        self.cdf = QDateEdit(calendarPopup=True)
        self.cdf.setDate(QDate.currentDate().addYears(-2))
        self.cdf.setDisplayFormat("yyyy-MM-dd")
        self.cdf.setObjectName("input")
        self.cdf.setMinimumHeight(32)
        self.cdf.setMaximumWidth(140)
        fc_main.addWidget(self.cdf)

        # "s/d" label + date
        fc_main.addWidget(QLabel("s/d", styleSheet=lbl_style))
        self.cdt = QDateEdit(calendarPopup=True)
        self.cdt.setDate(QDate.currentDate())
        self.cdt.setDisplayFormat("yyyy-MM-dd")
        self.cdt.setObjectName("input")
        self.cdt.setMinimumHeight(32)
        self.cdt.setMaximumWidth(140)
        fc_main.addWidget(self.cdt)

        # "Status" label + combo
        fc_main.addWidget(QLabel("Status:", styleSheet=lbl_style))
        self.csf = QComboBox()
        self.csf.addItems(["Semua", "Aktif", "Selesai", "Terlambat", "Menunggu"])
        self.csf.setObjectName("combo")
        self.csf.setMinimumHeight(32)
        self.csf.setMinimumWidth(140)
        fc_main.addWidget(self.csf)
        
        fc_main.addStretch()
        
        # Apply button
        btn = QPushButton("Terapkan")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(32)
        btn.setObjectName("primary")
        btn.clicked.connect(self._load_data)
        fc_main.addWidget(btn)
        
        cl.addWidget(fc)

        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(12)
        cl.addLayout(self.list_container)

        self.cempty = QFrame(styleSheet="background: #FAFAF9; border: 1.5px dashed #D4D2CD; border-radius: 12px;")
        self.cempty.setMinimumHeight(240)
        el = QVBoxLayout(self.cempty)
        el.setAlignment(Qt.AlignCenter)
        el.addWidget(QLabel("\U0001f4e6", styleSheet="font-size: 40px; color: #D4D2CD; background: transparent;", alignment=Qt.AlignCenter))
        el.addWidget(QLabel("Belum ada riwayat sewa", styleSheet="font-size: 16px; font-weight: bold; color: #1A1A1A; background: transparent;", alignment=Qt.AlignCenter))
        el.addWidget(QLabel("Penyewaan yang sudah selesai akan muncul di sini.", styleSheet="font-size: 13px; color: #8C8A86; background: transparent;", alignment=Qt.AlignCenter))
        cl.addWidget(self.cempty)
        self.cempty.setVisible(False)

        self.pg = QWidget(styleSheet="background: transparent;")
        self.pgl = QHBoxLayout(self.pg)
        self.pgl.setContentsMargins(0, 0, 0, 0)
        self.pgl.setSpacing(8)
        self.pgl.addStretch()
        cl.addWidget(self.pg)
        self.pg.setVisible(False)

    def _load_data(self, data=None):
        user = get_current_user()
        if not user:
            return

        self._is_owner_view = is_owner()
        self.owner_section.setVisible(self._is_owner_view)
        self.customer_section.setVisible(not self._is_owner_view)

        # Tampilkan indikator loading
        self._set_loading(True)

        uid = user["id"]
        fetch_fn = get_rentals_for_owner if self._is_owner_view else lambda: get_rentals_for_customer(uid)

        self._worker = DataWorker(fetch_fn)
        self._worker.result.connect(self._on_rentals_loaded)
        self._worker.error.connect(lambda e: self._set_loading(False))
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self):
        """Cleanup worker after finished."""
        self._set_loading(False)
        if self._worker:
            self._worker.quit()
            self._worker.wait()
            self._worker = None

    def _on_rentals_loaded(self, rentals):
        rentals = rentals or []
        if self._is_owner_view:
            self._load_owner(rentals)
        else:
            self._load_customer(rentals)

    def _set_loading(self, loading: bool):
        # Tampilkan/sembunyikan tabel sementara loading
        if hasattr(self, "otable"):
            if loading:
                self.otable.setEnabled(False)
            else:
                self.otable.setEnabled(True)

    def _load_owner(self, rentals):
        raw = list(rentals)
        cat_filter = self.okf.currentText()
        status_filter = self.osf.currentText()
        date_from = self.odf.date().toString("yyyy-MM-dd")
        date_to = self.odt.date().toString("yyyy-MM-dd")

        status_map = {
            "Semua Status": None, "Selesai": ["returned"], "Aktif": ["confirmed", "active"],
            "Terlambat": ["overdue"], "Dibatalkan": ["rejected"]
        }
        allowed = status_map.get(status_filter, None)
        now = datetime.now().strftime("%Y-%m-%d")
        
        filtered = []
        for r in raw:
            s, end = r.get("status", ""), r.get("end_date", "0000")
            is_overdue = s in ("confirmed", "active") and end < now

            if allowed is not None:
                if is_overdue and "overdue" in allowed: pass
                elif s not in allowed: continue

            if cat_filter != "Semua Kategori":
                inv = r.get("inventories") or {}
                if inv.get("category", "") != cat_filter: continue

            start_date = r.get("start_date", "")
            if not (date_from <= start_date <= date_to): continue
            filtered.append(r)

        self._all_data = filtered
        self._current_page = 0

        # Stats Calc
        total_revenue = sum(r.get("fine_amount", 0) for r in filtered)
        durations = []
        for r in filtered:
            if r.get("status") == "returned":
                inv = r.get("inventories") or {}
                start, end = r.get("start_date", ""), r.get("end_date", "")
                if start and end:
                    try:
                        d = max(1, (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days)
                        total_revenue += inv.get("price_per_day", 0) * d
                    except: pass
            
            start, end = r.get("start_date", ""), r.get("end_date", "")
            if start and end:
                try: durations.append(max(1, (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days))
                except: pass
                
        avg_dur = sum(durations) / len(durations) if durations else 0

        self.st_total.set_value(len(filtered))
        self.st_revenue.set_value(f"Rp {total_revenue:,.0f}".replace(",", "."))
        self.st_durasi.set_value(f"{avg_dur:.1f} hari")

        self._render_owner_table(filtered)

    def _render_owner_table(self, data):
        total = len(data)
        pages = max(1, (total + self._page_size - 1) // self._page_size)
        if self._current_page >= pages: self._current_page = max(0, pages - 1)

        start = self._current_page * self._page_size
        end = min(start + self._page_size, total)
        page_data = data[start:end]

        self.otable.setRowCount(len(page_data))
        now = datetime.now().strftime("%Y-%m-%d")

        for row, r in enumerate(page_data):
            inv, usr = r.get("inventories") or {}, r.get("users") or {}
            s, start_d, end_d = r.get("status", ""), r.get("start_date", ""), r.get("end_date", "")
            fine = r.get("fine_amount", 0)

            is_overdue = s in ("confirmed", "active") and end_d and end_d < now
            status_key = "overdue" if is_overdue else s

            durasi = ""
            if start_d and end_d:
                try:
                    d = (datetime.strptime(end_d, "%Y-%m-%d") - datetime.strptime(start_d, "%Y-%m-%d")).days
                    durasi = f"{d} hari" if d > 0 else "1 hari"
                except: durasi = "-"

            items = [
                str(start + row + 1), usr.get("name", "-"), inv.get("name", "-"),
                inv.get("category", "-"), start_d, end_d, durasi,
                f"Rp {fine:,.0f}".replace(",", ".") if fine > 0 else "-",
            ]

            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter if col in (0, 6) else Qt.AlignVCenter)
                if col == 0:
                    f = item.font(); f.setWeight(QFont.Weight.Bold); item.setFont(f)
                self.otable.setItem(row, col, item)

            # use centralized status badge factory
            badge_label = STATUS_BADGE_STYLES.get(status_key, (None, None, status_key.title()))[2]
            self.otable.setCellWidget(row, 8, create_status_badge(status_key, badge_label))

        self.ofooter.setText(f"Menampilkan {start + 1 if total > 0 else 0}–{end} dari {total} data")
        self.oprev.setEnabled(self._current_page > 0)
        self.onxt.setEnabled(end < total)
        self.otable.setVisible(len(page_data) > 0)
        self.oempty.setVisible(len(page_data) == 0)

    def _load_customer(self, rentals):
        raw = list(rentals)
        sf, df, dt = self.csf.currentText(), self.cdf.date().toString("yyyy-MM-dd"), self.cdt.date().toString("yyyy-MM-dd")
        sm = {
            "Semua": None, 
            "Aktif": ["confirmed", "active"], 
            "Selesai": ["returned"], 
            "Terlambat": ["overdue"],
            "Menunggu": ["pending"]
        }
        allowed, now = sm.get(sf, None), datetime.now().strftime("%Y-%m-%d")
        
        filtered = []
        for r in raw:
            s, end = r.get("status", ""), r.get("end_date", "0000")
            if allowed is not None:
                is_overdue = s in ("confirmed", "active") and end < now
                if is_overdue and "overdue" in allowed: pass
                elif s not in allowed: continue
            st = r.get("start_date", "")
            if df <= st <= dt: filtered.append(r)

        self._all_data = filtered
        self._current_page = 0
        self._render_customer()

    def _render_customer(self):
        while self.list_container.count():
            it = self.list_container.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        total = len(self._all_data)
        if total == 0:
            self.cempty.setVisible(True); self.pg.setVisible(False)
            return
            
        self.cempty.setVisible(False); self.pg.setVisible(True)

        start = self._current_page * self._page_size
        for r in self._all_data[start:min(start + self._page_size, total)]:
            c = RentalHistoryCard(r)
            c.detail_clicked.connect(self._on_detail)
            c.return_clicked.connect(self._on_return_requested)
            c.print_clicked.connect(self._on_print_nota)
            self.list_container.addWidget(c)
            
        self._render_customer_pagination(total)

    def _render_customer_pagination(self, total):
        while self.pgl.count():
            it = self.pgl.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self.pgl.addStretch()

        tp = max(1, (total + self._page_size - 1) // self._page_size)
        cp = self._current_page
        # Previous button
        pb = QPushButton("\u2039", cursor=Qt.PointingHandCursor)
        pb.setObjectName("pageNav")
        pb.setEnabled(cp > 0)
        pb.clicked.connect(lambda: self._go_customer_page(cp - 1))
        self.pgl.addWidget(pb)

        # Page number buttons
        for p in range(tp):
            ia = p == cp
            b = QPushButton(str(p + 1), cursor=Qt.PointingHandCursor)
            b.setObjectName("pageBtn")
            b.setProperty("active", ia)
            b.clicked.connect(lambda checked, page=p: self._go_customer_page(page))
            self.pgl.addWidget(b)

        # Next button
        nb = QPushButton("\u203a", cursor=Qt.PointingHandCursor)
        nb.setObjectName("pageNav")
        nb.setEnabled(cp < tp - 1)
        nb.clicked.connect(lambda: self._go_customer_page(cp + 1))
        self.pgl.addWidget(nb)

    def _go_customer_page(self, page):
        self._current_page = page
        self._render_customer()

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_owner_table(self._all_data)

    def _next_page(self):
        if (self._current_page + 1) * self._page_size < len(self._all_data):
            self._current_page += 1
            self._render_owner_table(self._all_data)

    def _on_detail(self, inventory_id):
        self.open_item_detail.emit(inventory_id)

    def _on_return_requested(self, rental_id):
        """Handle return request - show confirmation dialog"""
        from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton
        from controllers.rental_controller import process_return
        from datetime import datetime
        
        # Find rental data
        rental = None
        for r in self._all_data:
            if r.get("id") == rental_id:
                rental = r
                break
        
        if not rental:
            QMessageBox.warning(self, "Error", "Rental tidak ditemukan")
            return
        
        # Konfirmasi pengembalian
        confirm_msg = f"Apakah Anda yakin ingin mengembalikan '{rental.get('inventories', {}).get('name', 'item')}' hari ini?"
        reply = QMessageBox.question(self, "Konfirmasi Pengembalian", confirm_msg, 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            return_date = datetime.now().strftime("%Y-%m-%d")
            end_date = rental.get("end_date", return_date)
            
            # Process return (untuk MVP, tidak ada photo upload - gunakan placeholder)
            result = process_return(rental_id, return_date, "", end_date)
            
            if result.get("success"):
                fine = result.get("fine", 0)
                if fine > 0:
                    msg = f"Pengembalian berhasil!\nDenda keterlambatan: Rp {fine:,}".replace(",", ".")
                else:
                    msg = "Pengembalian berhasil!"
                QMessageBox.information(self, "Sukses", msg)
                self._load_data()
            else:
                QMessageBox.warning(self, "Error", f"Gagal mengembalikan: {result.get('error', 'Unknown error')}")

    def _on_print_nota(self, rental_data):
        """Handle print rental receipt request"""
        import os
        import platform
        from utils.export import print_rental_receipt
        
        try:
            path = print_rental_receipt(rental_data)
            
            # Buat dialog dengan informasi lengkap
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Nota Berhasil Dicetak")
            msg_box.setIcon(QMessageBox.Information)
            
            # Dapatkan absolute path untuk folder exports
            abs_path = os.path.abspath(path)
            export_dir = os.path.dirname(abs_path)
            filename = os.path.basename(path)
            
            msg_text = f"Nota sewa berhasil dicetak!\n\n"
            msg_text += f"Nama File: {filename}\n"
            msg_text += f"Lokasi: {export_dir}\n\n"
            msg_text += f"Silakan buka folder 'exports' di folder aplikasi untuk mengakses file nota."
            
            msg_box.setText(msg_text)
            
            # Tambahkan tombol "Buka Folder"
            btn_open = msg_box.addButton("Buka Folder", QMessageBox.ActionRole)
            msg_box.addButton("OK", QMessageBox.AcceptRole)
            
            if msg_box.exec() == 0:  # Jika tombol "Buka Folder" diklik
                try:
                    if platform.system() == "Windows":
                        os.startfile(export_dir)
                    elif platform.system() == "Darwin":  # macOS
                        os.system(f"open '{export_dir}'")
                    else:  # Linux
                        os.system(f"xdg-open '{export_dir}'")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Gagal membuka folder:\n{str(e)}")
                    
        except Exception as e:
            QMessageBox.warning(
                self, "Error", 
                f"Gagal mencetak nota:\n{str(e)}"
            )

    def _export_csv(self):
        if not self._all_data:
            QMessageBox.information(self, "Export", "Belum ada data untuk di-export.")
            return
        flat = prepare_rental_export(self._all_data)
        path = export_csv(flat)
        QMessageBox.information(self, "Export CSV", f"Berhasil di-export ke:\n{path}")

    def _export_pdf(self):
        if not self._all_data:
            QMessageBox.information(self, "Export", "Belum ada data untuk di-export.")
            return
        flat = prepare_rental_export(self._all_data)
        path = export_pdf(flat, title="Laporan & Riwayat Sewa - MyGTS")
        QMessageBox.information(self, "Export PDF", f"Berhasil di-export ke:\n{path}")