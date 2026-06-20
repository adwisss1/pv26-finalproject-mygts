from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QMessageBox, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor

from controllers.rental_controller import get_rentals_for_owner, get_rentals_for_customer
from utils.worker import DataWorker
from controllers.inventory_controller import CATEGORIES
from controllers.auth_controller import get_current_user, is_owner
from utils.export import export_csv, export_pdf


STATUS_BADGE_STYLES = {
    "returned": ("#F0FDF8", "#1D9E75", "Selesai"),
    "active": ("#E8F0EE", "#0F6E56", "Aktif"),
    "confirmed": ("#E8F0EE", "#0F6E56", "Aktif"),
    "pending": ("#FEF3E8", "#BA7517", "Menunggu"),
    "rejected": ("#FAF9F6", "#6B6A66", "Dibatalkan"),
    "overdue": ("#FEF2F2", "#E24B4A", "Terlambat"),
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

def _status_badge_widget(status_key):
    bg, fg, label = STATUS_BADGE_STYLES.get(status_key, ("#FAF9F6", "#6B6A66", status_key.title()))
    w = QFrame()
    w.setStyleSheet(f"background: {bg}; border-radius: 6px;")
    lo = QHBoxLayout(w)
    lo.setContentsMargins(10, 4, 10, 4)
    lo.setSpacing(6)
    
    dot = QLabel("\u25cf")
    dot.setStyleSheet(f"color: {fg}; font-size: 8px; background: transparent;")
    t = QLabel(label)
    t.setStyleSheet(f"color: {fg}; font-size: 11px; font-weight: bold; background: transparent;")
    
    lo.addWidget(dot)
    lo.addWidget(t)
    
    wrap = QWidget()
    wl = QHBoxLayout(wrap)
    wl.setContentsMargins(0,0,0,0)
    wl.setAlignment(Qt.AlignCenter)
    wl.addWidget(w)
    return wrap

class SummaryStat(QFrame):
    def __init__(self, label, value, color):
        super().__init__()
        self.setStyleSheet("""
            SummaryStat {
                background: #ffffff;
                border: 1px solid #E0DDD8;
                border-radius: 12px;
            }
        """)
        lo = QVBoxLayout(self)
        lo.setContentsMargins(20, 20, 20, 20)
        lo.setSpacing(6)
        
        self.v = QLabel(str(value))
        self.v.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {color}; border: none;")
        
        l = QLabel(label)
        l.setStyleSheet("font-size: 13px; color: #8C8A86; font-weight: 600; border: none;")
        
        lo.addWidget(self.v)
        lo.addWidget(l)
        lo.addStretch()

    def set_value(self, value):
        self.v.setText(str(value))

class RentalHistoryCard(QFrame):
    detail_clicked = Signal(str)

    def __init__(self, rental_data):
        super().__init__()
        self.rental_id = rental_data.get("id", "")
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

        self.setStyleSheet("""
            RentalHistoryCard { background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px; }
            RentalHistoryCard:hover { border-color: #0F6E56; background: #FAFAF9;}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        thumb = QFrame()
        thumb.setFixedSize(48, 48)
        thumb.setStyleSheet("background: #F8F7F4; border-radius: 8px; border: 1px solid #E0DDD8;")
        tl = QVBoxLayout(thumb)
        tl.setAlignment(Qt.AlignCenter)
        tl.addWidget(QLabel("\U0001f4f7", styleSheet="font-size: 18px; color: #A8A6A2; background: transparent;"))

        left_col = QVBoxLayout()
        left_col.addWidget(QLabel(name, styleSheet="font-size: 14px; font-weight: bold; color: #1A1A1A; border:none;"))
        cb = QFrame(styleSheet=f"background: {cat_bg}; border-radius: 4px;")
        cbl = QHBoxLayout(cb)
        cbl.setContentsMargins(8, 2, 8, 2)
        cbl.addWidget(QLabel(cat, styleSheet=f"font-size: 10px; font-weight: bold; color: {cat_fg}; border:none;"))
        left_col.addWidget(cb)
        left_col.addStretch()

        center = QVBoxLayout()
        for lbl, val in [("Tgl Sewa:", sd), ("Tenggat:", ed), ("Durasi:", durasi)]:
            row = QHBoxLayout()
            row.addWidget(QLabel(lbl, styleSheet="font-size: 12px; color: #8C8A86; border:none;"))
            row.addWidget(QLabel(val, styleSheet="font-size: 12px; font-weight: 500; color: #1A1A1A; border:none;"))
            row.addStretch()
            center.addLayout(row)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        badge = QFrame(styleSheet=f"background: {bg}; border-radius: 6px;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(10, 4, 10, 4)
        bl.addWidget(QLabel("\u25cf", styleSheet=f"color: {fg}; font-size: 8px; border:none;"))
        bl.addWidget(QLabel(label, styleSheet=f"color: {fg}; font-size: 11px; font-weight: bold; border:none;"))
        right.addWidget(badge, 0, Qt.AlignRight)
        
        if fine > 0:
            right.addWidget(QLabel(f"Denda: Rp {fine:,}", styleSheet="font-size: 11px; color: #E24B4A; font-weight: bold; border:none;"), 0, Qt.AlignRight)
            
        db = QPushButton("Lihat Detail")
        db.setCursor(Qt.PointingHandCursor)
        db.setStyleSheet("background: transparent; border: none; font-size: 12px; font-weight: bold; color: #0F6E56;")
        db.clicked.connect(lambda: self.detail_clicked.emit(self.rental_id))
        right.addWidget(db, 0, Qt.AlignRight)

        layout.addWidget(thumb)
        layout.addLayout(left_col, 1)
        layout.addLayout(center, 2)
        
        rw = QWidget(fixedWidth=160)
        rw.setLayout(right)
        layout.addWidget(rw)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

class HistoryPage(QWidget):
    navigate_to = Signal(str)

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
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget(styleSheet="background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 16, 28, 28)
        layout.setSpacing(24)

        # Container Owner
        self.owner_section = QWidget(styleSheet="background: transparent;")
        ol = QVBoxLayout(self.owner_section)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.setSpacing(24)
        layout.addWidget(self.owner_section)

        # Container Customer
        self.customer_section = QWidget(styleSheet="background: transparent;")
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
        btn_export_pdf.setCursor(Qt.PointingHandCursor)
        btn_export_pdf.setStyleSheet("""
            QPushButton { background: #ffffff; border: 1px solid #D4D2CD; border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: bold; color: #E24B4A; }
            QPushButton:hover { background: #FDE8E8; border-color: #E24B4A; }
        """)
        btn_export_pdf.clicked.connect(self._export_pdf)
        header.addWidget(btn_export_pdf)

        btn_export_csv = QPushButton(" \U0001f4ca Export CSV")
        btn_export_csv.setCursor(Qt.PointingHandCursor)
        btn_export_csv.setStyleSheet("""
            QPushButton { background: #ffffff; border: 1px solid #D4D2CD; border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: bold; color: #1D9E75; }
            QPushButton:hover { background: #E8F7F2; border-color: #1D9E75; }
        """)
        btn_export_csv.clicked.connect(self._export_csv)
        header.addWidget(btn_export_csv)

        ol.addLayout(header)

        # Filter Box — 2 baris agar tidak terpotong
        fc = QFrame()
        fc.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px; }")
        fc_main = QVBoxLayout(fc)
        fc_main.setContentsMargins(20, 16, 20, 16)
        fc_main.setSpacing(10)

        fs = """
            QComboBox, QDateEdit { border: 1px solid #D4D2CD; border-radius: 8px; padding: 8px 12px; font-size: 13px; background: #ffffff; min-width: 130px; }
            QComboBox:focus, QDateEdit:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """
        lbl_style = "font-size: 13px; font-weight: 500; color: #6B6A66;"

        # Baris 1: Rentang Tanggal
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(QLabel("Dari:", styleSheet=lbl_style))
        self.odf = QDateEdit(calendarPopup=True)
        self.odf.setDate(QDate.currentDate().addYears(-2))
        self.odf.setDisplayFormat("yyyy-MM-dd")
        self.odf.setStyleSheet(fs)
        row1.addWidget(self.odf)
        row1.addWidget(QLabel("s/d", styleSheet=lbl_style))
        self.odt = QDateEdit(calendarPopup=True)
        self.odt.setDate(QDate.currentDate())
        self.odt.setDisplayFormat("yyyy-MM-dd")
        self.odt.setStyleSheet(fs)
        row1.addWidget(self.odt)
        row1.addStretch()
        fc_main.addLayout(row1)

        # Baris 2: Filter Kategori + Status + Tombol
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(QLabel("Kategori:", styleSheet=lbl_style))
        self.okf = QComboBox()
        self.okf.addItems(["Semua Kategori"] + CATEGORIES)
        self.okf.setStyleSheet(fs)
        row2.addWidget(self.okf)
        row2.addWidget(QLabel("Status:", styleSheet=lbl_style))
        self.osf = QComboBox()
        self.osf.addItems(["Semua Status", "Selesai", "Aktif", "Terlambat", "Dibatalkan"])
        self.osf.setStyleSheet(fs)
        row2.addWidget(self.osf)
        row2.addStretch()
        btn = QPushButton("Terapkan Filter")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(38)
        btn.setStyleSheet("QPushButton { background: #0F6E56; border: none; border-radius: 8px; padding: 0 24px; font-size: 13px; font-weight: bold; color: #ffffff; } QPushButton:hover { background: #0A5A45; }")
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
        tc = QFrame(styleSheet="background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px;")
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
        self.otable.setStyleSheet("""
            QTableWidget { border: none; background: transparent; font-size: 13px; gridline-color: transparent; outline: none; }
            QTableWidget::item { padding: 0px 16px; border-bottom: 1px solid #F0EFEB; }
            QHeaderView::section { background: #F8F7F4; border: none; font-size: 12px; font-weight: bold; color: #8C8A86; padding: 14px 16px; border-bottom: 1px solid #E0DDD8; }
        """)
        tcl.addWidget(self.otable)

        # Pagination Footer
        pf = QFrame(styleSheet="background: #ffffff; border-top: 1px solid #E0DDD8; border-radius: 0 0 12px 12px;")
        pl = QHBoxLayout(pf)
        pl.setContentsMargins(20, 12, 20, 12)

        self.ofooter = QLabel("Menampilkan 0 data", styleSheet="font-size: 12px; color: #8C8A86;")
        pl.addWidget(self.ofooter)
        pl.addStretch()

        ns = "QPushButton { background: transparent; border: 1px solid #D4D2CD; border-radius: 6px; padding: 4px 12px; font-size: 14px; font-weight: bold; color: #6B6A66; } QPushButton:hover { background: #F0EFEB; } QPushButton:disabled { color: #D4D2CD; border-color: #E0DDD8; }"
        self.oprev = QPushButton("\u2039", cursor=Qt.PointingHandCursor, styleSheet=ns)
        self.oprev.clicked.connect(self._prev_page)
        self.onxt = QPushButton("\u203a", cursor=Qt.PointingHandCursor, styleSheet=ns)
        self.onxt.clicked.connect(self._next_page)
        
        pl.addWidget(self.oprev)
        pl.addWidget(self.onxt)
        tcl.addWidget(pf)
        ol.addWidget(tc)

        # Empty State
        self.oempty = QFrame(styleSheet="background: #FAFAF9; border: 1.5px dashed #D4D2CD; border-radius: 12px;")
        self.oempty.setMinimumHeight(200)
        el = QVBoxLayout(self.oempty)
        el.setAlignment(Qt.AlignCenter)
        el.addWidget(QLabel("\u2610", styleSheet="font-size: 40px; color: #D4D2CD; background: transparent;", alignment=Qt.AlignCenter))
        el.addWidget(QLabel("Belum ada data transaksi", styleSheet="font-size: 15px; font-weight: bold; color: #6B6A66; background: transparent;", alignment=Qt.AlignCenter))
        ol.addWidget(self.oempty)
        self.oempty.setVisible(False)

    def _build_customer_section(self, cl):
        # Filter Box — 2 baris agar tidak terpotong
        fc = QFrame()
        fc.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px; }")
        fc_main = QVBoxLayout(fc)
        fc_main.setContentsMargins(20, 16, 20, 16)
        fc_main.setSpacing(10)

        fs = """
            QComboBox, QDateEdit { border: 1px solid #D4D2CD; border-radius: 8px; padding: 8px 12px; font-size: 13px; background: #ffffff; min-width: 130px; }
            QComboBox:focus, QDateEdit:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """
        lbl_style = "font-size: 13px; font-weight: 500; color: #6B6A66;"

        # Baris 1: Rentang Tanggal
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(QLabel("Dari:", styleSheet=lbl_style))
        self.cdf = QDateEdit(calendarPopup=True)
        self.cdf.setDate(QDate.currentDate().addYears(-2))
        self.cdf.setDisplayFormat("yyyy-MM-dd")
        self.cdf.setStyleSheet(fs)
        row1.addWidget(self.cdf)
        row1.addWidget(QLabel("s/d", styleSheet=lbl_style))
        self.cdt = QDateEdit(calendarPopup=True)
        self.cdt.setDate(QDate.currentDate())
        self.cdt.setDisplayFormat("yyyy-MM-dd")
        self.cdt.setStyleSheet(fs)
        row1.addWidget(self.cdt)
        row1.addStretch()
        fc_main.addLayout(row1)

        # Baris 2: Status + Tombol Terapkan
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(QLabel("Status:", styleSheet=lbl_style))
        self.csf = QComboBox()
        self.csf.addItems(["Semua", "Aktif", "Selesai", "Terlambat"])
        self.csf.setStyleSheet(fs)
        row2.addWidget(self.csf)
        row2.addStretch()
        btn = QPushButton("Terapkan")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(38)
        btn.setStyleSheet("QPushButton { background: #0F6E56; border: none; border-radius: 8px; padding: 0 24px; font-size: 13px; font-weight: bold; color: #ffffff; } QPushButton:hover { background: #0A5A45; }")
        btn.clicked.connect(self._load_data)
        row2.addWidget(btn)
        fc_main.addLayout(row2)
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
        self._worker.finished.connect(lambda: self._set_loading(False))
        self._worker.start()

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

            self.otable.setCellWidget(row, 8, _status_badge_widget(status_key))

        self.ofooter.setText(f"Menampilkan {start + 1 if total > 0 else 0}–{end} dari {total} data")
        self.oprev.setEnabled(self._current_page > 0)
        self.onxt.setEnabled(end < total)
        self.otable.setVisible(len(page_data) > 0)
        self.oempty.setVisible(len(page_data) == 0)

    def _load_customer(self, rentals):
        raw = list(rentals)
        sf, df, dt = self.csf.currentText(), self.cdf.date().toString("yyyy-MM-dd"), self.cdt.date().toString("yyyy-MM-dd")
        sm = {"Semua": None, "Aktif": ["confirmed", "active"], "Selesai": ["returned"], "Terlambat": ["overdue"]}
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
            self.list_container.addWidget(c)
            
        self._render_customer_pagination(total)

    def _render_customer_pagination(self, total):
        while self.pgl.count():
            it = self.pgl.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self.pgl.addStretch()

        tp = max(1, (total + self._page_size - 1) // self._page_size)
        cp = self._current_page
        bs = "QPushButton {{ background: {bg}; border: 1px solid #D4D2CD; border-radius: 6px; padding: 4px 10px; font-size: 13px; font-weight: {fw}; color: {fg}; }} QPushButton:hover {{ background: #F0EFEB; }}"
        
        pb = QPushButton("\u2039", cursor=Qt.PointingHandCursor)
        pb.setStyleSheet(bs.format(bg="#ffffff", fg="#6B6A66" if cp > 0 else "#D4D2CD", fw="bold"))
        pb.setEnabled(cp > 0)
        pb.clicked.connect(lambda: self._go_customer_page(cp - 1))
        self.pgl.addWidget(pb)

        for p in range(tp):
            ia = p == cp
            b = QPushButton(str(p + 1), cursor=Qt.PointingHandCursor)
            b.setStyleSheet(bs.format(bg="#0F6E56" if ia else "#ffffff", fg="#ffffff" if ia else "#1A1A1A", fw="bold" if ia else "normal"))
            b.clicked.connect(lambda checked, page=p: self._go_customer_page(page))
            self.pgl.addWidget(b)

        nb = QPushButton("\u203a", cursor=Qt.PointingHandCursor)
        nb.setStyleSheet(bs.format(bg="#ffffff", fg="#6B6A66" if cp < tp - 1 else "#D4D2CD", fw="bold"))
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

    def _on_detail(self, rental_id):
        self.navigate_to.emit("history")

    def _export_csv(self):
        if not self._all_data:
            QMessageBox.information(self, "Export", "Belum ada data untuk di-export.")
            return
        flat = [{"Customer": r.get("users", {}).get("name", "-"), "Item": r.get("inventories", {}).get("name", "-"), "Category": r.get("inventories", {}).get("category", "-"), "Start": r.get("start_date", ""), "End": r.get("end_date", ""), "Return": r.get("return_date", ""), "Status": r.get("status", ""), "Fine": str(r.get("fine_amount", 0))} for r in self._all_data]
        path = export_csv(flat)
        QMessageBox.information(self, "Export CSV", f"Berhasil di-export ke:\n{path}")

    def _export_pdf(self):
        if not self._all_data:
            QMessageBox.information(self, "Export", "Belum ada data untuk di-export.")
            return
        flat = [{"Customer": r.get("users", {}).get("name", "-"), "Item": r.get("inventories", {}).get("name", "-"), "Category": r.get("inventories", {}).get("category", "-"), "Start": r.get("start_date", ""), "End": r.get("end_date", ""), "Return": r.get("return_date", ""), "Status": r.get("status", ""), "Fine": str(r.get("fine_amount", 0))} for r in self._all_data]
        path = export_pdf(flat, title="Laporan & Riwayat Sewa - MyGTS")
        QMessageBox.information(self, "Export PDF", f"Berhasil di-export ke:\n{path}")