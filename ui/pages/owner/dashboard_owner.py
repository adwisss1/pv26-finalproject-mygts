from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush

from controllers.inventory_controller import get_all_inventory
from controllers.rental_controller import get_rentals_for_owner
from controllers.auth_controller import get_current_user
from utils.worker import DataWorker
from utils.export import prepare_rental_export
from utils.export import export_csv, export_pdf
from ui.pages.owner.add_customer_page import AddCustomerDialog
from ui.components import create_status_badge

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
               "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

CATEGORY_COLORS = {
    "Kostum":     "#0F6E56",
    "Aksesoris":  "#BA7517",
    "Properti":   "#1D9E75",
    "Alat Musik": "#5B4B8A",
    "Make Up":    "#C75B7A",
    "Lainnya":    "#6B6A66",
}

STATUS_LABELS = {
    "pending":   ("Menunggu",  "#BA7517", "#FEF3E8"),
    "confirmed": ("Aktif",     "#0F6E56", "#E8F0EE"),
    "active":    ("Aktif",     "#0F6E56", "#E8F0EE"),
    "returned":  ("Selesai",   "#1D9E75", "#F0FDF8"),
    "rejected":  ("Ditolak",   "#6B6A66", "#EDECE8"),
    "overdue":   ("Terlambat", "#E24B4A", "#FEF2F2"),
}


# ─────────────────────────────────────────────────────────────────────────────
#  METRIC CARD
# ─────────────────────────────────────────────────────────────────────────────

class MetricCard(QFrame):
    def __init__(self, title, value, color, icon):
        super().__init__()
        self._color = color
        self.setObjectName("metricCard")
        self.setProperty("accent", color)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icon_pill = QLabel(icon)
        icon_pill.setFixedSize(36, 36)
        icon_pill.setAlignment(Qt.AlignCenter)
        icon_pill.setObjectName("metricIcon")
        icon_pill.setProperty("iconColor", color)

        title_label = QLabel(title)
        title_label.setObjectName("metricCardTitle")

        top_row.addWidget(icon_pill)
        top_row.addWidget(title_label, 1)
        layout.addLayout(top_row)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("metricCardValue")
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


# ─────────────────────────────────────────────────────────────────────────────
#  NOTIFICATION ITEM
# ─────────────────────────────────────────────────────────────────────────────

class NotificationItem(QFrame):
    clicked = Signal(str)
    clicked_item = Signal(object)

    def __init__(self, dot_color, text, link_text, link_key):
        super().__init__()
        self._key = link_key
        self.setObjectName("notificationItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 13, 16, 13)
        layout.setSpacing(14)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setObjectName("notifDot")
        dot.setProperty("dotColor", dot_color)
        layout.addWidget(dot, 0, Qt.AlignTop)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setObjectName("notifText")
        layout.addWidget(text_label, 1)

        link = QPushButton(link_text)
        link.setCursor(Qt.PointingHandCursor)
        link.setFixedHeight(30)
        link.setObjectName("notifLink")
        link.clicked.connect(lambda: self.clicked.emit(self._key))
        layout.addWidget(link)

    def mousePressEvent(self, event):
        try:
            self.clicked_item.emit(self)
        except Exception:
            pass
        return super().mousePressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
#  BAR CHART — Tren penyewaan per bulan (sudah ada, dipertahankan persis)
# ─────────────────────────────────────────────────────────────────────────────

class BarChart(QWidget):
    def __init__(self, data, bar_color="#0F6E56"):
        super().__init__()
        self._data      = data or []
        self._bar_color = bar_color
        self.setMinimumHeight(200)
        self.setObjectName("transparentContent")

    def set_data(self, data):
        self._data = data or []
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        ml, mr, mt, mb = 44, 20, 20, 44

        chart_w = w - ml - mr
        chart_h = h - mt - mb

        values  = [v for _, v in self._data]
        max_val = max(values) if max(values) > 0 else 1

        n     = len(self._data)
        bar_w = min(36, chart_w // n - 14)
        gap   = (chart_w - bar_w * n) / (n + 1)

        # Grid lines + Y labels
        y_ticks = 4
        for i in range(y_ticks + 1):
            y   = int(mt + chart_h - (chart_h / y_ticks) * i)
            val = int((max_val / y_ticks) * i)

            painter.setPen(QColor("#B0AEA9"))
            painter.setFont(QFont("", 9))
            painter.drawText(
                QRect(0, y - 8, ml - 10, 16),
                Qt.AlignRight | Qt.AlignVCenter, str(val)
            )
            painter.setPen(QPen(QColor("#ECEAE6"), 1, Qt.DashLine))
            painter.drawLine(ml, y, w - mr, y)

        painter.setPen(QPen(QColor("#D4D2CD"), 1))
        painter.drawLine(ml, mt, ml, mt + chart_h)
        painter.drawLine(ml, mt + chart_h, w - mr, mt + chart_h)

        for i, (label, val) in enumerate(self._data):
            bar_h = int((val / max_val) * chart_h) if max_val > 0 else 0
            x     = int(ml + gap + i * (bar_w + gap))
            y     = int(mt + chart_h - bar_h)

            if val > 0:
                grad = QLinearGradient(x, y, x, y + bar_h)
                grad.setColorAt(0, QColor(self._bar_color))
                grad.setColorAt(1, QColor(self._bar_color + "80"))
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(x, y, int(bar_w), bar_h, 4, 4)

                painter.setPen(QColor(self._bar_color))
                painter.setFont(QFont("", 9, QFont.Bold))
                painter.drawText(
                    QRect(x, y - 18, int(bar_w), 16),
                    Qt.AlignCenter, str(val)
                )
            else:
                painter.setBrush(QColor("#F0EFEB"))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(x, mt + chart_h - 4, int(bar_w), 4, 2, 2)

            painter.setPen(QColor("#8C8A86"))
            painter.setFont(QFont("", 9))
            painter.drawText(
                QRect(int(x - gap / 2), mt + chart_h + 10, int(bar_w + gap), 20),
                Qt.AlignCenter, label
            )

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
#  DONUT CHART — Distribusi inventaris per kategori (BARU)
# ─────────────────────────────────────────────────────────────────────────────

class DonutChart(QWidget):
    """Chart donut untuk distribusi kategori inventaris."""

    def __init__(self, data=None):
        super().__init__()
        # data = list of (label, value, color)
        self._data = data or []
        self.setMinimumSize(200, 200)
        self.setObjectName("transparentContent")

    def set_data(self, data):
        self._data = data or []
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Bagi area: donut di kiri, legend di kanan
        donut_size = min(w * 0.5, h - 20)
        cx = int(donut_size / 2) + 10
        cy = h // 2
        outer_r = int(donut_size / 2) - 6
        inner_r = int(outer_r * 0.55)

        total = sum(v for _, v, _ in self._data) or 1
        start_angle = 90 * 16   # mulai dari atas

        for label, val, color in self._data:
            span = int((val / total) * 360 * 16)
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawPie(cx - outer_r, cy - outer_r,
                            outer_r * 2, outer_r * 2,
                            start_angle, span)
            start_angle += span

        # Lubang tengah (efek donut)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)

        # Total di tengah
        painter.setPen(QColor("#1A1A1A"))
        painter.setFont(QFont("", 14, QFont.Bold))
        painter.drawText(
            QRect(cx - inner_r, cy - 12, inner_r * 2, 24),
            Qt.AlignCenter, str(total)
        )
        painter.setPen(QColor("#8C8A86"))
        painter.setFont(QFont("", 8))
        painter.drawText(
            QRect(cx - inner_r, cy + 8, inner_r * 2, 16),
            Qt.AlignCenter, "item"
        )

        # Legend di kanan
        legend_x = int(donut_size) + 20
        legend_y = cy - (len(self._data) * 22) // 2

        for label, val, color in self._data:
            pct = f"{val/total*100:.0f}%"
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(legend_x, legend_y, 10, 10, 3, 3)

            painter.setPen(QColor("#1A1A1A"))
            painter.setFont(QFont("", 9))
            painter.drawText(legend_x + 16, legend_y + 10,
                             f"{label} ({pct})")
            legend_y += 22

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD OWNER
# ─────────────────────────────────────────────────────────────────────────────

class DashboardOwner(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._worker      = None   # DataWorker aktif
        self._data_cached = None   # Cache data untuk menghindari refetch
        self._build_ui()

    def reset(self):
        """Reset dashboard state untuk owner baru (sebelum login owner lain)."""
        print("[DashboardOwner.reset] Resetting dashboard for new owner...")
        # Stop worker jika sedang berjalan dan disconnect signals
        if self._worker:
            try:
                # Disconnect semua signals dari worker lama
                self._worker.result.disconnect()
                self._worker.error.disconnect()
                self._worker.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                if self._worker.isRunning():
                    self._worker.quit()
                    self._worker.wait()
            except RuntimeError:
                pass
            self._worker = None
        
        # Clear UI elements
        self.header_title.setText("Halo, Pemilik!")
        self.card_total.set_value(0)
        self.card_active.set_value(0)
        self.card_pending.set_value(0)
        self.card_overdue.set_value(0)
        self.recent_table.setRowCount(0)
        print("[DashboardOwner.reset] Dashboard reset complete")

    def refresh(self):
        """Load data di background thread agar UI tidak freeze."""
        # Jangan fetch ulang jika ada worker yang masih jalan
        try:
            if self._worker and self._worker.isRunning():
                print("[DashboardOwner] Worker sudah jalan, skip refresh")
                return
        except RuntimeError:
            # Worker sudah didelete, set ke None
            self._worker = None
        
        print("[DashboardOwner] Starting data refresh...")
        self._set_loading(True)
        self._worker = DataWorker(self._fetch_all_data)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.error.connect(self._on_data_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self):
        """Cleanup worker thread setelah selesai."""
        self._set_loading(False)
        if self._worker:
            self._worker.quit()
            self._worker.wait()
            self._worker = None

    # ── Fetch (dijalankan di thread) ─────────────────────────────────────

    def _fetch_all_data(self):
        items   = get_all_inventory() or []
        rentals = get_rentals_for_owner() or []
        user    = get_current_user()
        return {"items": items, "rentals": rentals, "user": user}

    # ── Callback hasil thread ────────────────────────────────────────────

    def _on_data_loaded(self, data):
        items   = data["items"]
        rentals = data["rentals"]
        user    = data["user"]

        # keep rentals for export
        self._rentals = rentals

        if user:
            self.header_title.setText(f"Halo, {user.get('name', 'Pemilik')}!")

        # Metric cards
        self.card_total.set_value(len(items))

        now = datetime.now().strftime("%Y-%m-%d")
        active_count  = 0
        pending_count = 0
        overdue_count = 0

        for r in rentals:
            s   = r.get("status", "")
            end = r.get("end_date", "0000")
            if s == "pending":
                pending_count += 1
            elif s in ("confirmed", "active"):
                if end < now:
                    overdue_count += 1
                else:
                    active_count += 1
            elif s == "overdue":
                overdue_count += 1

        self.card_active.set_value(active_count)
        self.card_pending.set_value(pending_count)
        self.card_overdue.set_value(overdue_count)

        self._build_notifications(pending_count, active_count, overdue_count)
        self._build_chart(rentals)
        self._build_category_chart(items)
        self._build_recent_table(rentals)

    def _on_data_error(self, msg):
        print(f"[DashboardOwner] Error loading data: {msg}")
        self._set_loading(False)

    def _set_loading(self, loading: bool):
        self.loading_label.setVisible(loading)

    # ── Build UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("transparentScroll")

        content = QWidget()
        content.setObjectName("transparentContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(22)

        # ── Header ──────────────────────────────────────────────────────
        header = QHBoxLayout()

        left_header = QVBoxLayout()
        left_header.setSpacing(4)

        greeting = QLabel("Selamat datang kembali 👋")
        greeting.setObjectName("muted")
        self.header_title = QLabel("Dasbor Pemilik")
        self.header_title.setObjectName("pageTitle")
        left_header.addWidget(greeting)
        left_header.addWidget(self.header_title)

        header.addLayout(left_header)
        header.addStretch()

        today    = datetime.now()
        date_str = today.strftime("%d %B %Y")
        date_pill = QLabel(f"📅  {date_str}")
        date_pill.setObjectName("datePill")
        self.date_label = date_pill
        header.addWidget(date_pill)

        # Tombol Tambah Customer
        add_customer_btn = QPushButton("➕ Tambah Customer")
        add_customer_btn.setCursor(Qt.PointingHandCursor)
        add_customer_btn.setFixedHeight(36)
        add_customer_btn.setObjectName("primary")
        add_customer_btn.clicked.connect(self._open_add_customer_dialog)
        header.addWidget(add_customer_btn)

        # Label loading (tersembunyi saat idle)
        self.loading_label = QLabel("⏳ Memuat data...")
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setVisible(False)
        header.addWidget(self.loading_label)

        layout.addLayout(header)
        # build the rest of dashboard content
        self._build_metric_and_body(layout)

        # finalize scroll/content (must be done here where `scroll` and `content` are defined)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _open_add_customer_dialog(self):
        dlg = AddCustomerDialog(self)
        if dlg.exec() == QDialog.Accepted:
            # refresh data after new customer
            try:
                self.refresh()
            except Exception:
                pass

        return

    # ── Metric cards and body (moved out of dialog handler) ──────────
    def _build_metric_and_body(self, layout):
        self.card_total   = MetricCard("Total Inventaris",       "—", "#0F6E56", "📦")
        self.card_active  = MetricCard("Sedang Disewa",          "—", "#BA7517", "⏱")
        self.card_pending = MetricCard("Menunggu Konfirmasi",    "—", "#3B82F6", "🔔")
        self.card_overdue = MetricCard("Terlambat Dikembalikan", "—", "#E24B4A", "⚠️")

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        for card in (self.card_total, self.card_active, self.card_pending, self.card_overdue):
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        # ── Baris tengah: Notifikasi + Bar Chart ────────────────────────
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        # Notifikasi
        notif_card = self._make_card_frame()
        notif_layout = QVBoxLayout(notif_card)
        notif_layout.setContentsMargins(0, 0, 0, 16)
        notif_layout.setSpacing(0)
        notif_layout.addLayout(self._card_header("🚨  Perlu Tindakan Segera"))
        notif_layout.addWidget(self._separator())
        self.notif_container = QVBoxLayout()
        self.notif_container.setSpacing(0)
        notif_layout.addLayout(self.notif_container)
        notif_layout.addStretch()
        mid_row.addWidget(notif_card, 2)

        # Bar chart tren 6 bulan
        chart_card = self._make_card_frame()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(0, 0, 0, 16)
        chart_layout.setSpacing(0)
        chart_layout.addLayout(self._card_header("📈  Tren Penyewaan 6 Bulan Terakhir"))
        chart_layout.addWidget(self._separator())
        chart_inner = QWidget()
        chart_inner.setObjectName("transparentContent")
        ci_l = QVBoxLayout(chart_inner)
        ci_l.setContentsMargins(16, 12, 16, 8)
        self.bar_chart = BarChart([])
        ci_l.addWidget(self.bar_chart)
        chart_layout.addWidget(chart_inner, 1)
        mid_row.addWidget(chart_card, 3)

        layout.addLayout(mid_row)

        # ── Baris bawah: Donut kategori + Tabel penyewaan terbaru ───────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Donut chart kategori
        donut_card = self._make_card_frame()
        donut_layout = QVBoxLayout(donut_card)
        donut_layout.setContentsMargins(0, 0, 0, 16)
        donut_layout.setSpacing(0)
        donut_layout.addLayout(self._card_header("🗂  Distribusi Kategori Inventaris"))
        donut_layout.addWidget(self._separator())
        donut_inner = QWidget()
        donut_inner.setObjectName("transparentContent")
        di_l = QVBoxLayout(donut_inner)
        di_l.setContentsMargins(16, 16, 16, 8)
        self.donut_chart = DonutChart([])
        self.donut_chart.setMinimumHeight(200)
        di_l.addWidget(self.donut_chart)
        donut_layout.addWidget(donut_inner, 1)
        bottom_row.addWidget(donut_card, 2)

        # Tabel penyewaan terbaru
        recent_card = self._make_card_frame()
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(0)

        recent_header = self._card_header("🕐  Penyewaan Terbaru")
        view_all_btn = QPushButton("Lihat semua →")
        view_all_btn.setCursor(Qt.PointingHandCursor)
        view_all_btn.setObjectName("link")
        view_all_btn.clicked.connect(lambda: self.navigate_to.emit("history"))
        recent_header.addWidget(view_all_btn)
        
        # Export buttons for recent rentals
        btn_export_csv = QPushButton("CSV")
        btn_export_csv.setCursor(Qt.PointingHandCursor)
        btn_export_csv.setObjectName("outline")
        btn_export_csv.clicked.connect(self._export_recent_csv)
        recent_header.addWidget(btn_export_csv)

        btn_export_pdf = QPushButton("PDF")
        btn_export_pdf.setCursor(Qt.PointingHandCursor)
        btn_export_pdf.setObjectName("outline")
        btn_export_pdf.clicked.connect(self._export_recent_pdf)
        recent_header.addWidget(btn_export_pdf)

        recent_layout.addLayout(recent_header)
        recent_layout.addWidget(self._separator())

        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Penyewa", "Item", "Tgl Mulai", "Status"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setShowGrid(False)
        self.recent_table.setObjectName("rentalsTable")
        self.recent_table.setSortingEnabled(True)
        recent_layout.addWidget(self.recent_table, 1)
        bottom_row.addWidget(recent_card, 3)

        layout.addLayout(bottom_row)

    # ── Helper UI ─────────────────────────────────────────────────────────

    def _make_card_frame(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        return card

    def _card_header(self, title: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(20, 16, 20, 16)
        lbl = QLabel(title)
        lbl.setObjectName("cardHeader")
        row.addWidget(lbl)
        row.addStretch()
        return row

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("divider")
        return sep

    # ── Build sub-components ──────────────────────────────────────────────

    def _build_notifications(self, pending, active, overdue):
        while self.notif_container.count():
            item = self.notif_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items_added = 0

        def add_notif(color, text, key):
            nonlocal items_added
            if items_added > 0:
                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setObjectName("divider")
                self.notif_container.addWidget(sep)
            notif = NotificationItem(color, text, "Lihat →", key)
            notif.clicked.connect(self.navigate_to.emit)
            # allow clicking the whole item to select / highlight it
            notif.clicked_item.connect(self._on_owner_notif_clicked)
            self.notif_container.addWidget(notif)
            items_added += 1

        if pending > 0:
            add_notif("#E24B4A",
                      f"{pending} penyewaan menunggu konfirmasi Anda", "pending")
        if active > 0:
            add_notif("#BA7517",
                      f"{active} penyewaan sedang berjalan", "returns")
        if overdue > 0:
            add_notif("#E24B4A",
                      f"{overdue} barang terlambat dikembalikan", "returns")

        if items_added == 0:
            empty = QLabel("✅  Tidak ada tindakan yang diperlukan saat ini.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setObjectName("emptyText")
            self.notif_container.addWidget(empty)

    def _on_owner_notif_clicked(self, item_widget):
        # Clear selected on all items
        for i in range(self.notif_container.count()):
            it = self.notif_container.itemAt(i).widget()
            if not it: continue
            it.setProperty("selected", False)
            it.style().unpolish(it); it.style().polish(it); it.update()

        # Set selected on clicked
        item_widget.setProperty("selected", True)
        item_widget.style().unpolish(item_widget); item_widget.style().polish(item_widget); item_widget.update()

    def _build_chart(self, rentals):
        now    = datetime.now()
        months = []
        for i in range(5, -1, -1):
            m = now.month - i
            y = now.year
            if m <= 0:
                m += 12
                y -= 1
            months.append((y, m))

        data = []
        for y, m in months:
            label = MONTH_NAMES[m - 1]
            count = sum(
                1 for r in rentals
                if r.get("created_at", "").startswith(f"{y}-{m:02d}")
            )
            data.append((label, count))

        self.bar_chart.set_data(data)

    def _build_category_chart(self, items):
        """Hitung jumlah item per kategori untuk donut chart."""
        counts = {}
        for item in items:
            cat = item.get("category", "Lainnya")
            counts[cat] = counts.get(cat, 0) + 1

        data = [
            (cat, count, CATEGORY_COLORS.get(cat, "#6B6A66"))
            for cat, count in sorted(counts.items(), key=lambda x: -x[1])
        ]
        self.donut_chart.set_data(data)

    def _build_recent_table(self, rentals):
        """Isi tabel 8 penyewaan terbaru."""
        # Urutkan berdasarkan created_at terbaru
        sorted_r = sorted(
            rentals,
            key=lambda r: r.get("created_at", ""),
            reverse=True
        )[:8]

        self.recent_table.setRowCount(len(sorted_r))

        for row, r in enumerate(sorted_r):
            # Kolom Penyewa
            user_data = r.get("users") or {}
            penyewa   = user_data.get("name", r.get("user_id", "—"))
            self.recent_table.setItem(row, 0, QTableWidgetItem(penyewa))

            # Kolom Item
            inv_data = r.get("inventories") or {}
            item_name = inv_data.get("name", r.get("inventory_id", "—"))
            # Potong jika terlalu panjang
            if len(item_name) > 22:
                item_name = item_name[:22] + "…"
            self.recent_table.setItem(row, 1, QTableWidgetItem(item_name))

            # Kolom Tgl Mulai
            start = r.get("start_date", "—")
            self.recent_table.setItem(row, 2, QTableWidgetItem(start))

            # Kolom Status (badge warna)
            status_key = r.get("status", "")
            label = STATUS_LABELS.get(status_key, (status_key, "#6B6A66", "#EDECE8"))[0]
            # use centralized badge widget for consistent styling
            self.recent_table.setCellWidget(row, 3, create_status_badge(status_key, label))

            self.recent_table.setRowHeight(row, 40)

    def _export_recent_csv(self):
        rents = getattr(self, "_rentals", []) or []
        if not rents:
            QMessageBox.information(self, "Export", "Belum ada data untuk di-export.")
            return
        flat = prepare_rental_export(rents)
        path = export_csv(flat)
        QMessageBox.information(self, "Export CSV", f"Berhasil di-export ke:\n{path}")

    def _export_recent_pdf(self):
        rents = getattr(self, "_rentals", []) or []
        if not rents:
            QMessageBox.information(self, "Export", "Belum ada data untuk di-export.")
            return
        flat = prepare_rental_export(rents)
        path = export_pdf(flat, title="Penyewaan Terbaru - MyGTS")
        QMessageBox.information(self, "Export PDF", f"Berhasil di-export ke:\n{path}")