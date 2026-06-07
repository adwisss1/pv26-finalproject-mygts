from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QMessageBox, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QColor

from controllers.rental_controller import get_rentals_for_owner, get_rentals_for_customer
from controllers.inventory_controller import CATEGORIES
from controllers.auth_controller import get_current_user, is_owner
from utils.export import export_csv, export_pdf


STATUS_BADGE_STYLES = {
    "returned": ("#E8F7F2", "#1D9E75", "Selesai"),
    "active": ("#E8F0EE", "#0F6E56", "Aktif"),
    "confirmed": ("#E8F0EE", "#0F6E56", "Aktif"),
    "pending": ("#FEF3E8", "#BA7517", "Menunggu"),
    "rejected": ("#EDECE8", "#6B6A66", "Dibatalkan"),
    "overdue": ("#FDE8E8", "#E24B4A", "Terlambat"),
}

CATEGORY_COLORS = {
    "Kostum": ("#E8F0EE", "#0F6E56"),
    "Aksesoris": ("#FEF3E8", "#BA7517"),
    "Properti": ("#E8F7F2", "#1D9E75"),
    "Alat Musik": ("#EEE8F8", "#5B4B8A"),
    "Make Up": ("#F8E8EF", "#C75B7A"),
    "Lainnya": ("#EDECE8", "#6B6A66"),
}


class RentalHistoryCard(QWidget):
    detail_clicked = Signal(str)

    def __init__(self, rental_data):
        super().__init__()
        self.rental_id = rental_data.get("id", "")
        self._data = rental_data
        self._build(rental_data)

    def _build(self, r):
        inv = r.get("inventories") or {}
        status = r.get("status", "")
        start = r.get("start_date", "")
        end = r.get("end_date", "")
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
                sd = datetime.strptime(start, "%Y-%m-%d")
                ed = datetime.strptime(end, "%Y-%m-%d")
                d = (ed - sd).days
                durasi = f"{d} hari" if d > 0 else "1 hari"
            except ValueError:
                durasi = "-"

        try:
            sd = datetime.strptime(start, "%Y-%m-%d").strftime("%d %B %Y") if start else "-"
        except ValueError:
            sd = start
        try:
            ed = datetime.strptime(end, "%Y-%m-%d").strftime("%d %B %Y") if end else "-"
        except ValueError:
            ed = end

        self.setObjectName("histCard")
        self.setStyleSheet("""
            #histCard { background: #ffffff; border: 0.5px solid #E0DDD8; border-radius: 12px; }
            #histCard:hover { border-color: #0F6E56; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        thumb = QFrame()
        thumb.setFixedSize(48, 48)
        thumb.setStyleSheet("background: #EDECE8; border-radius: 8px;")
        tl = QVBoxLayout(thumb)
        tl.setAlignment(Qt.AlignCenter)
        ti = QLabel("\u2610")
        ti.setStyleSheet("font-size: 18px; color: #A8A6A2; background: transparent;")
        tl.addWidget(ti)

        left_col = QVBoxLayout()
        left_col.setSpacing(4)
        nl = QLabel(name)
        nl.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A; background: transparent;")
        left_col.addWidget(nl)
        cb = QFrame()
        cb.setStyleSheet(f"background: {cat_bg}; border-radius: 4px;")
        cbl = QHBoxLayout(cb)
        cbl.setContentsMargins(6, 2, 6, 2)
        cblabel = QLabel(cat)
        cblabel.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {cat_fg}; background: transparent;")
        cbl.addWidget(cblabel)
        left_col.addWidget(cb)

        center = QVBoxLayout()
        center.setSpacing(4)
        for lbl, val in [("Tgl Sewa:", sd), ("Tenggat:", ed), ("Durasi:", durasi)]:
            row = QHBoxLayout()
            row.setSpacing(6)
            a = QLabel(lbl)
            a.setStyleSheet("font-size: 13px; color: #8C8A86; background: transparent;")
            b = QLabel(val)
            b.setStyleSheet("font-size: 13px; color: #1A1A1A; background: transparent;")
            row.addWidget(a); row.addWidget(b); row.addStretch()
            center.addLayout(row)

        right = QVBoxLayout()
        right.setSpacing(8)
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        badge = QFrame()
        badge.setStyleSheet(f"background: {bg}; border-radius: 8px; padding: 4px 12px;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(10, 4, 10, 4)
        dot = QLabel("\u25cf")
        dot.setStyleSheet(f"color: {fg}; font-size: 8px; background: transparent;")
        bl.addWidget(dot)
        txt = QLabel(label)
        txt.setStyleSheet(f"color: {fg}; font-size: 12px; font-weight: 600; background: transparent;")
        bl.addWidget(txt)
        right.addWidget(badge, 0, Qt.AlignRight)
        if fine and fine > 0:
            fl = QLabel(f"Denda: Rp {fine:,}")
            fl.setStyleSheet("font-size: 12px; color: #E24B4A; font-weight: 500; background: transparent;")
            right.addWidget(fl, 0, Qt.AlignRight)
        db = QPushButton("Lihat Detail")
        db.setCursor(Qt.PointingHandCursor)
        db.setStyleSheet("background: transparent; border: none; font-size: 12px; font-weight: 500; color: #0F6E56;")
        db.clicked.connect(lambda: self.detail_clicked.emit(self.rental_id))
        right.addWidget(db, 0, Qt.AlignRight)

        layout.addWidget(thumb)
        layout.addLayout(left_col, 1)
        layout.addLayout(center, 2)
        rw = QWidget()
        rw.setLayout(right)
        rw.setFixedWidth(160)
        layout.addWidget(rw)


def _status_badge_widget(status_key):
    bg, fg, label = STATUS_BADGE_STYLES.get(status_key, ("#EDECE8", "#6B6A66", status_key.title()))
    w = QFrame()
    w.setStyleSheet(f"background: {bg}; border-radius: 6px; padding: 4px 10px;")
    lo = QHBoxLayout(w)
    lo.setContentsMargins(8, 2, 8, 2)
    lo.setSpacing(6)
    dot = QLabel("\u25cf")
    dot.setStyleSheet(f"color: {fg}; font-size: 8px; background: transparent;")
    t = QLabel(label)
    t.setStyleSheet(f"color: {fg}; font-size: 12px; font-weight: 600; background: transparent;")
    lo.addWidget(dot); lo.addWidget(t)
    return w


class SummaryStat(QFrame):
    def __init__(self, label, value, color):
        super().__init__()
        self._color = color
        self.setStyleSheet("background: transparent;")
        lo = QVBoxLayout(self)
        lo.setSpacing(4)
        self.v = QLabel(str(value))
        self.v.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {color}; background: transparent;")
        l = QLabel(label)
        l.setStyleSheet("font-size: 12px; color: #8C8A86; background: transparent;")
        lo.addWidget(self.v)
        lo.addWidget(l)

    def set_value(self, value):
        self.v.setText(str(value))


class HistoryPage(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._all_data = []
        self._current_page = 0
        self._page_size = 10
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

        # Owner section
        self.owner_section = QWidget()
        self.owner_section.setStyleSheet("background: transparent;")
        ol = QVBoxLayout(self.owner_section)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.setSpacing(20)
        layout.addWidget(self.owner_section)

        # Customer section
        self.customer_section = QWidget()
        self.customer_section.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(self.customer_section)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(20)
        layout.addWidget(self.customer_section)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._build_owner_section(ol)
        self._build_customer_section(cl)

    def _build_owner_section(self, ol):
        # Header row
        header = QHBoxLayout()
        title = QLabel("Laporan & Riwayat Sewa")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        header.addWidget(title)
        header.addStretch()

        btn_export_pdf = QPushButton("  Export PDF")
        btn_export_pdf.setCursor(Qt.PointingHandCursor)
        btn_export_pdf.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 0.5px solid #D4D2CD;
                border-radius: 8px; padding: 10px 18px;
                font-size: 13px; font-weight: 500; color: #E24B4A;
            }
            QPushButton:hover { background: #FDE8E8; border-color: #E24B4A; }
        """)
        btn_export_pdf.clicked.connect(self._export_pdf)
        header.addWidget(btn_export_pdf)

        btn_export_csv = QPushButton("  Export CSV")
        btn_export_csv.setCursor(Qt.PointingHandCursor)
        btn_export_csv.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 0.5px solid #D4D2CD;
                border-radius: 8px; padding: 10px 18px;
                font-size: 13px; font-weight: 500; color: #1D9E75;
            }
            QPushButton:hover { background: #E8F7F2; border-color: #1D9E75; }
        """)
        btn_export_csv.clicked.connect(self._export_csv)
        header.addWidget(btn_export_csv)

        ol.addLayout(header)

        # Filter card
        fc = QFrame()
        fc.setStyleSheet("background: #ffffff; border: 0.5px solid #E0DDD8; border-radius: 12px; padding: 16px 20px;")
        fl = QHBoxLayout(fc)
        fl.setSpacing(12)

        fs = """
            QComboBox, QDateEdit {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 8px 12px; font-size: 13px; background: #ffffff;
                min-height: 20px;
            }
            QComboBox:focus, QDateEdit:focus { border-color: #0F6E56; }
        """

        fl.addWidget(QLabel("Dari:"))
        self.odf = QDateEdit()
        self.odf.setCalendarPopup(True)
        self.odf.setDate(QDate.currentDate().addMonths(-3))
        self.odf.setDisplayFormat("yyyy-MM-dd")
        self.odf.setStyleSheet(fs)
        fl.addWidget(self.odf)

        fl.addWidget(QLabel("sampai"))
        self.odt = QDateEdit()
        self.odt.setCalendarPopup(True)
        self.odt.setDate(QDate.currentDate())
        self.odt.setDisplayFormat("yyyy-MM-dd")
        self.odt.setStyleSheet(fs)
        fl.addWidget(self.odt)

        fl.addWidget(QLabel("Kategori:"))
        self.okf = QComboBox()
        self.okf.addItem("Semua Kategori")
        for c in CATEGORIES:
            self.okf.addItem(c)
        self.okf.setStyleSheet(fs)
        fl.addWidget(self.okf)

        fl.addWidget(QLabel("Status:"))
        self.osf = QComboBox()
        self.osf.addItems(["Semua Status", "Selesai", "Aktif", "Terlambat", "Dibatalkan"])
        self.osf.setStyleSheet(fs)
        fl.addWidget(self.osf)

        btn = QPushButton("Terapkan Filter")
        btn.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 8px 20px; font-size: 13px; font-weight: 600;
                color: #ffffff; min-height: 20px;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        btn.clicked.connect(self._load_data)
        fl.addWidget(btn)
        fl.addStretch()
        ol.addWidget(fc)

        # Summary strip
        self.summary_box = QFrame()
        self.summary_box.setStyleSheet("background: #F8F7F4; border-radius: 10px; padding: 16px 20px;")
        sl = QHBoxLayout(self.summary_box)
        sl.setSpacing(40)

        self.st_total = SummaryStat("Total Transaksi", "0", "#0F6E56")
        self.st_revenue = SummaryStat("Total Pendapatan", "Rp 0", "#1D9E75")
        self.st_durasi = SummaryStat("Rata-rata Durasi", "0 hari", "#0F6E56")

        sl.addWidget(self.st_total)
        sl.addWidget(self.st_revenue)
        sl.addWidget(self.st_durasi)
        sl.addStretch()
        ol.addWidget(self.summary_box)

        # Owner table
        tc = QFrame()
        tc.setStyleSheet("background: #ffffff; border: 0.5px solid #E0DDD8; border-radius: 12px;")
        tcl = QVBoxLayout(tc)
        tcl.setContentsMargins(0, 0, 0, 0)

        self.otable = QTableWidget()
        self.otable.setColumnCount(9)
        headers = ["No", "Nama Customer", "Nama Barang", "Kategori", "Tgl Ambil", "Tgl Kembali", "Durasi", "Denda", "Status"]
        self.otable.setHorizontalHeaderLabels(headers)
        self.otable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.otable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.otable.setColumnWidth(0, 50)
        self.otable.setSelectionBehavior(QTableWidget.SelectRows)
        self.otable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.otable.setAlternatingRowColors(False)
        self.otable.verticalHeader().setVisible(False)
        self.otable.setMouseTracking(True)
        self.otable.setStyleSheet("""
            QTableWidget {
                border: none; background: #ffffff; font-size: 13px;
                gridline-color: transparent; outline: none;
            }
            QTableWidget::item { padding: 10px 12px; border-bottom: 0.5px solid #EDECE8; }
            QTableWidget::item:selected { background: #E8F0EE; color: #1A1A1A; }
            QTableWidget::item:hover { background: #E8F0EE; }
            QHeaderView::section {
                background: #F8F7F4; border: none;
                font-size: 12px; font-weight: 500; color: #8C8A86;
                padding: 12px 12px; border-bottom: 0.5px solid #E0DDD8;
            }
        """)
        tcl.addWidget(self.otable)

        # Pagination
        pf = QFrame()
        pf.setStyleSheet("background: #ffffff; border-top: 0.5px solid #E0DDD8; border-radius: 0 0 12px 12px;")
        pl = QHBoxLayout(pf)
        pl.setContentsMargins(16, 10, 16, 10)

        self.ofooter = QLabel("Menampilkan 0 data")
        self.ofooter.setStyleSheet("font-size: 12px; color: #8C8A86;")
        pl.addWidget(self.ofooter)
        pl.addStretch()

        ns = """
            QPushButton {
                background: transparent; border: 0.5px solid #D4D2CD;
                border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #6B6A66;
            }
            QPushButton:hover { background: #EDECE8; }
            QPushButton:disabled { color: #D4D2CD; }
        """
        self.oprev = QPushButton("\u2039")
        self.oprev.setStyleSheet(ns)
        self.oprev.clicked.connect(self._prev_page)
        self.onxt = QPushButton("\u203a")
        self.onxt.setStyleSheet(ns)
        self.onxt.clicked.connect(self._next_page)
        pl.addWidget(self.oprev)
        pl.addWidget(self.onxt)
        tcl.addWidget(pf)
        ol.addWidget(tc)

        # Owner empty state
        self.oempty = QWidget()
        self.oempty.setStyleSheet("background: transparent;")
        el = QVBoxLayout(self.oempty)
        el.setAlignment(Qt.AlignCenter)
        el.setSpacing(8)
        ei = QLabel("\u2610")
        ei.setStyleSheet("font-size: 48px; color: #D4D2CD; background: transparent;")
        ei.setAlignment(Qt.AlignCenter)
        el.addWidget(ei)
        et = QLabel("Belum ada data transaksi")
        et.setStyleSheet("font-size: 16px; font-weight: 500; color: #6B6A66;")
        et.setAlignment(Qt.AlignCenter)
        el.addWidget(et)
        ol.addWidget(self.oempty)
        self.oempty.setVisible(False)

    def _build_customer_section(self, cl):
        title = QLabel("Riwayat Sewa")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        cl.addWidget(title)

        fc = QFrame()
        fc.setStyleSheet("background: #ffffff; border: 0.5px solid #E0DDD8; border-radius: 12px; padding: 16px 20px;")
        fl = QHBoxLayout(fc)
        fl.setSpacing(12)
        fs = """
            QComboBox, QDateEdit {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 8px 12px; font-size: 13px; background: #ffffff;
                min-height: 20px;
            }
            QComboBox:focus, QDateEdit:focus { border-color: #0F6E56; }
        """

        fl.addWidget(QLabel("Dari:"))
        self.cdf = QDateEdit()
        self.cdf.setCalendarPopup(True)
        self.cdf.setDate(QDate.currentDate().addMonths(-3))
        self.cdf.setDisplayFormat("yyyy-MM-dd")
        self.cdf.setStyleSheet(fs)
        fl.addWidget(self.cdf)
        fl.addWidget(QLabel("Sampai:"))
        self.cdt = QDateEdit()
        self.cdt.setCalendarPopup(True)
        self.cdt.setDate(QDate.currentDate())
        self.cdt.setDisplayFormat("yyyy-MM-dd")
        self.cdt.setStyleSheet(fs)
        fl.addWidget(self.cdt)
        fl.addWidget(QLabel("Status:"))
        self.csf = QComboBox()
        self.csf.addItems(["Semua", "Aktif", "Selesai", "Terlambat"])
        self.csf.setStyleSheet(fs)
        fl.addWidget(self.csf)

        btn = QPushButton("Terapkan")
        btn.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 8px 20px; font-size: 13px; font-weight: 600;
                color: #ffffff; min-height: 20px;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        btn.clicked.connect(self._load_data)
        fl.addWidget(btn)
        fl.addStretch()
        cl.addWidget(fc)

        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(12)
        cl.addLayout(self.list_container)

        self.cempty = QWidget()
        self.cempty.setStyleSheet("background: transparent;")
        el = QVBoxLayout(self.cempty)
        el.setAlignment(Qt.AlignCenter)
        el.setSpacing(8)
        ei = QLabel("\u2610")
        ei.setStyleSheet("font-size: 48px; color: #D4D2CD; background: transparent;")
        ei.setAlignment(Qt.AlignCenter)
        el.addWidget(ei)
        et = QLabel("Belum ada riwayat sewa")
        et.setStyleSheet("font-size: 16px; font-weight: 500; color: #6B6A66;")
        et.setAlignment(Qt.AlignCenter)
        el.addWidget(et)
        es = QLabel("Penyewaan yang sudah selesai akan muncul di sini")
        es.setStyleSheet("font-size: 13px; color: #A8A6A2;")
        es.setAlignment(Qt.AlignCenter)
        el.addWidget(es)
        cl.addWidget(self.cempty)
        self.cempty.setVisible(False)

        self.pg = QWidget()
        self.pg.setStyleSheet("background: transparent;")
        self.pgl = QHBoxLayout(self.pg)
        self.pgl.setContentsMargins(0, 0, 0, 0)
        self.pgl.setSpacing(6)
        self.pgl.addStretch()
        cl.addWidget(self.pg)
        self.pg.setVisible(False)

    def _load_data(self, data=None):
        user = get_current_user()
        if not user:
            return

        is_owner_view = is_owner()
        self.owner_section.setVisible(is_owner_view)
        self.customer_section.setVisible(not is_owner_view)

        rentals = (get_rentals_for_owner() if is_owner_view
                   else get_rentals_for_customer(user["id"])) or []

        if is_owner_view:
            self._load_owner(rentals)
        else:
            self._load_customer(rentals)

    def _load_owner(self, rentals):
        raw = list(rentals)

        # Apply filters
        cat_filter = self.okf.currentText()
        status_filter = self.osf.currentText()
        date_from = self.odf.date().toString("yyyy-MM-dd")
        date_to = self.odt.date().toString("yyyy-MM-dd")

        status_map = {
            "Semua Status": None,
            "Selesai": ["returned"],
            "Aktif": ["confirmed", "active"],
            "Terlambat": ["overdue"],
            "Dibatalkan": ["rejected"],
        }
        allowed = status_map.get(status_filter, None)

        now = datetime.now().strftime("%Y-%m-%d")
        filtered = []
        for r in raw:
            s = r.get("status", "")
            end = r.get("end_date", "0000")
            is_overdue = s in ("confirmed", "active") and end < now

            if allowed is not None:
                if is_overdue and "overdue" in allowed:
                    pass
                elif s not in allowed:
                    continue

            if cat_filter != "Semua Kategori":
                inv = r.get("inventories") or {}
                if inv.get("category", "") != cat_filter:
                    continue

            start_date = r.get("start_date", "")
            if not (date_from <= start_date <= date_to):
                continue

            filtered.append(r)

        self._all_data = filtered
        self._current_page = 0

        # Summary
        total_rentals = len(filtered)
        total_revenue = sum(r.get("fine_amount", 0) for r in filtered)
        for r in filtered:
            if r.get("status") == "returned":
                inv = r.get("inventories") or {}
                price = inv.get("price_per_day", 0)
                start = r.get("start_date", "")
                end = r.get("end_date", "")
                if start and end:
                    try:
                        sd = datetime.strptime(start, "%Y-%m-%d")
                        ed = datetime.strptime(end, "%Y-%m-%d")
                        days = max(1, (ed - sd).days)
                        total_revenue += price * days
                    except ValueError:
                        pass

        durations = []
        for r in filtered:
            start = r.get("start_date", "")
            end = r.get("end_date", "")
            if start and end:
                try:
                    sd = datetime.strptime(start, "%Y-%m-%d")
                    ed = datetime.strptime(end, "%Y-%m-%d")
                    durations.append(max(1, (ed - sd).days))
                except ValueError:
                    pass
        avg_dur = sum(durations) / len(durations) if durations else 0

        self.st_total.set_value(total_rentals)
        self.st_revenue.set_value(f"Rp {total_revenue:,}")
        self.st_durasi.set_value(f"{avg_dur:.1f} hari")

        # Render table
        self._render_owner_table(filtered)

    def _render_owner_table(self, data):
        total = len(data)
        pages = max(1, (total + self._page_size - 1) // self._page_size)
        if self._current_page >= pages:
            self._current_page = pages - 1

        start = self._current_page * self._page_size
        end = min(start + self._page_size, total)
        page_data = data[start:end]

        self.otable.setRowCount(len(page_data))
        now = datetime.now().strftime("%Y-%m-%d")

        for row, r in enumerate(page_data):
            inv = r.get("inventories") or {}
            usr = r.get("users") or {}
            s = r.get("status", "")
            start_d = r.get("start_date", "")
            end_d = r.get("end_date", "")
            fine = r.get("fine_amount", 0)

            is_overdue = s in ("confirmed", "active") and end_d and end_d < now
            status_key = "overdue" if is_overdue else s

            durasi = ""
            if start_d and end_d:
                try:
                    sd = datetime.strptime(start_d, "%Y-%m-%d")
                    ed = datetime.strptime(end_d, "%Y-%m-%d")
                    d = (ed - sd).days
                    durasi = f"{d} hari" if d > 0 else "1 hari"
                except ValueError:
                    durasi = "-"

            items = [
                str(start + row + 1),
                usr.get("name", "-"),
                inv.get("name", "-"),
                inv.get("category", "-"),
                start_d,
                end_d,
                durasi,
                f"Rp {fine:,}" if fine and fine > 0 else "-",
            ]

            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter)
                if col == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                    f = item.font()
                    f.setWeight(QFont.Weight.Medium)
                    item.setFont(f)
                self.otable.setItem(row, col, item)

            self.otable.setCellWidget(row, 8, _status_badge_widget(status_key))

        self.ofooter.setText(f"Menampilkan {start + 1}–{end} dari {total} data")
        self.oprev.setEnabled(self._current_page > 0)
        self.onxt.setEnabled(end < total)
        self.otable.setVisible(len(page_data) > 0)
        self.oempty.setVisible(len(page_data) == 0)
        self.summary_box.setVisible(len(page_data) > 0 or total > 0)

    def _load_customer(self, rentals):
        raw = list(rentals)
        sf = self.csf.currentText()
        df = self.cdf.date().toString("yyyy-MM-dd")
        dt = self.cdt.date().toString("yyyy-MM-dd")

        sm = {"Semua": None, "Aktif": ["confirmed", "active"], "Selesai": ["returned"], "Terlambat": ["overdue"]}
        allowed = sm.get(sf, None)

        now = datetime.now().strftime("%Y-%m-%d")
        filtered = []
        for r in raw:
            s = r.get("status", "")
            end = r.get("end_date", "0000")
            is_overdue = s in ("confirmed", "active") and end < now
            if allowed is not None:
                if is_overdue and "overdue" in allowed:
                    pass
                elif s not in allowed:
                    continue
            st = r.get("start_date", "")
            if not (df <= st <= dt):
                continue
            filtered.append(r)

        self._all_data = filtered
        self._current_page = 0
        self._render_customer()

    def _render_customer(self):
        while self.list_container.count():
            it = self.list_container.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        data = self._all_data
        total = len(data)
        if total == 0:
            self.cempty.setVisible(True)
            self.pg.setVisible(False)
            return
        self.cempty.setVisible(False)
        self.pg.setVisible(True)

        start = self._current_page * self._page_size
        end = min(start + self._page_size, total)
        for r in data[start:end]:
            c = RentalHistoryCard(r)
            c.detail_clicked.connect(self._on_detail)
            self.list_container.addWidget(c)
        self._render_customer_pagination(total)

    def _render_customer_pagination(self, total):
        while self.pgl.count():
            it = self.pgl.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self.pgl.addStretch()

        tp = (total + self._page_size - 1) // self._page_size
        cp = self._current_page
        bs = """
            QPushButton {{
                background: {bg}; border: 0.5px solid #D4D2CD;
                border-radius: 6px; padding: 6px 12px; font-size: 12px;
                font-weight: {fw}; color: {fg};
            }}
            QPushButton:hover {{ background: #EDECE8; }}
        """
        pb = QPushButton("\u2039")
        pb.setStyleSheet(bs.format(bg="#ffffff", fg="#6B6A66" if cp > 0 else "#D4D2CD", fw="400"))
        pb.setEnabled(cp > 0)
        pb.clicked.connect(lambda: self._go_customer_page(cp - 1))
        self.pgl.addWidget(pb)

        mv = 5
        pages = []
        if tp <= mv:
            pages = list(range(tp))
        elif cp <= mv // 2:
            pages = list(range(mv)) + ["...", tp - 1]
        elif cp >= tp - mv // 2 - 1:
            pages = [0, "..."] + list(range(tp - mv, tp))
        else:
            pages = [0, "..."] + list(range(cp - 1, cp + 2)) + ["...", tp - 1]

        for p in pages:
            if p == "...":
                d = QLabel("...")
                d.setStyleSheet("font-size: 12px; color: #A8A6A2; padding: 6px 4px; background: transparent;")
                self.pgl.addWidget(d)
            else:
                ia = p == cp
                b = QPushButton(str(p + 1))
                b.setStyleSheet(bs.format(bg="#0F6E56" if ia else "#ffffff", fg="#ffffff" if ia else "#1A1A1A", fw="600" if ia else "400"))
                b.clicked.connect(lambda checked, page=p: self._go_customer_page(page))
                self.pgl.addWidget(b)

        nb = QPushButton("\u203a")
        nb.setStyleSheet(bs.format(bg="#ffffff", fg="#6B6A66" if cp < tp - 1 else "#D4D2CD", fw="400"))
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
        total = len(self._all_data)
        if (self._current_page + 1) * self._page_size < total:
            self._current_page += 1
            self._render_owner_table(self._all_data)

    def _on_detail(self, rental_id):
        self.navigate_to.emit("history")

    def _export_csv(self):
        if not self._all_data:
            QMessageBox.information(self, "Export", "No data to export.")
            return
        flat = []
        for r in self._all_data:
            inv = r.get("inventories") or {}
            usr = r.get("users") or {}
            flat.append({
                "Customer": usr.get("name", "-"),
                "Item": inv.get("name", "-"),
                "Category": inv.get("category", "-"),
                "Start": r.get("start_date", ""),
                "End": r.get("end_date", ""),
                "Return": r.get("return_date", ""),
                "Status": r.get("status", ""),
                "Fine": str(r.get("fine_amount", 0)),
            })
        path = export_csv(flat)
        QMessageBox.information(self, "Export CSV", f"Exported to:\n{path}")

    def _export_pdf(self):
        if not self._all_data:
            QMessageBox.information(self, "Export", "No data to export.")
            return
        flat = []
        for r in self._all_data:
            inv = r.get("inventories") or {}
            usr = r.get("users") or {}
            flat.append({
                "Customer": usr.get("name", "-"),
                "Item": inv.get("name", "-"),
                "Category": inv.get("category", "-"),
                "Start": r.get("start_date", ""),
                "End": r.get("end_date", ""),
                "Return": r.get("return_date", ""),
                "Status": r.get("status", ""),
                "Fine": str(r.get("fine_amount", 0)),
            })
        path = export_pdf(flat, title="Laporan & Riwayat Sewa - MyGTS")
        QMessageBox.information(self, "Export PDF", f"Exported to:\n{path}")
