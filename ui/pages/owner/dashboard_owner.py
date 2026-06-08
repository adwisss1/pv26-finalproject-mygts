from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush

from controllers.inventory_controller import get_all_inventory
from controllers.rental_controller import get_rentals_for_owner
from controllers.auth_controller import get_current_user


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
               "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


# ─────────────────────────────────────────────────────────────────────────────
#  METRIC CARD
# ─────────────────────────────────────────────────────────────────────────────

class MetricCard(QFrame):
    def __init__(self, title, value, color, icon):
        super().__init__()
        self._color = color
        self.setObjectName("metricCard")
        self.setMinimumHeight(100)
        self.setStyleSheet(f"""
            #metricCard {{
                background: #ffffff;
                border: 1px solid #ECEAE6;
                border-radius: 14px;
            }}
            #metricCard:hover {{
                border: 1px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        # Baris atas: ikon kecil + judul
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icon_pill = QLabel(icon)
        icon_pill.setFixedSize(36, 36)
        icon_pill.setAlignment(Qt.AlignCenter)
        icon_pill.setStyleSheet(f"""
            font-size: 17px;
            background: {color}18;
            border-radius: 10px;
            color: {color};
        """)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 12px; font-weight: 500; color: #8C8A86; background: transparent;"
        )

        top_row.addWidget(icon_pill)
        top_row.addWidget(title_label, 1)
        layout.addLayout(top_row)

        # Angka besar
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(
            f"font-size: 36px; font-weight: 700; color: {color};"
            "letter-spacing: -1px; background: transparent;"
        )
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


# ─────────────────────────────────────────────────────────────────────────────
#  NOTIFICATION ITEM
# ─────────────────────────────────────────────────────────────────────────────

class NotificationItem(QFrame):
    clicked = Signal(str)

    def __init__(self, dot_color, text, link_text, link_key):
        super().__init__()
        self._key = link_key
        self.setObjectName("notifItem")
        self.setStyleSheet("""
            #notifItem { background: transparent; border-radius: 8px; }
            #notifItem:hover { background: #F5F4F0; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 13, 16, 13)
        layout.setSpacing(14)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            f"background: {dot_color}; border-radius: 4px; margin-top: 1px;"
        )
        layout.addWidget(dot, 0, Qt.AlignTop)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(
            "font-size: 13px; color: #2A2A2A; background: transparent; line-height: 1.4;"
        )
        layout.addWidget(text_label, 1)

        link = QPushButton(link_text)
        link.setCursor(Qt.PointingHandCursor)
        link.setFixedHeight(30)
        link.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #0F6E5640;
                border-radius: 6px;
                font-size: 12px; font-weight: 500;
                color: #0F6E56;
                padding: 0 10px;
            }
            QPushButton:hover {
                background: #0F6E5610;
                border-color: #0F6E56;
            }
        """)
        link.clicked.connect(lambda: self.clicked.emit(self._key))
        layout.addWidget(link)


# ─────────────────────────────────────────────────────────────────────────────
#  BAR CHART
# ─────────────────────────────────────────────────────────────────────────────

class BarChart(QWidget):
    def __init__(self, data, bar_color="#0F6E56"):
        super().__init__()
        self._data = data or []
        self._bar_color = bar_color
        self.setMinimumHeight(200)
        self.setStyleSheet("background: transparent;")

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

        values = [v for _, v in self._data]
        max_val = max(values) if max(values) > 0 else 1

        n = len(self._data)
        bar_w = min(36, chart_w // n - 14)
        gap = (chart_w - bar_w * n) / (n + 1)

        # Grid lines + Y labels
        y_ticks = 4
        for i in range(y_ticks + 1):
            y = int(mt + chart_h - (chart_h / y_ticks) * i)
            val = int((max_val / y_ticks) * i)

            painter.setPen(QColor("#B0AEA9"))
            painter.setFont(QFont("", 9))
            painter.drawText(
                QRect(0, y - 8, ml - 10, 16),
                Qt.AlignRight | Qt.AlignVCenter, str(val)
            )
            painter.setPen(QPen(QColor("#ECEAE6"), 1, Qt.DashLine))
            painter.drawLine(ml, y, w - mr, y)

        # Y-axis baseline
        painter.setPen(QPen(QColor("#D4D2CD"), 1))
        painter.drawLine(ml, mt, ml, mt + chart_h)
        painter.drawLine(ml, mt + chart_h, w - mr, mt + chart_h)

        # Bars dengan gradient
        for i, (label, val) in enumerate(self._data):
            bar_h = int((val / max_val) * chart_h) if max_val > 0 else 0
            x = int(ml + gap + i * (bar_w + gap))
            y = int(mt + chart_h - bar_h)

            if val > 0:
                grad = QLinearGradient(x, y, x, y + bar_h)
                grad.setColorAt(0, QColor(self._bar_color))
                grad.setColorAt(1, QColor(self._bar_color + "80"))
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(x, y, int(bar_w), bar_h, 4, 4)

                # Value label di atas bar
                painter.setPen(QColor(self._bar_color))
                painter.setFont(QFont("", 9, QFont.Bold))
                painter.drawText(
                    QRect(x, y - 18, int(bar_w), 16),
                    Qt.AlignCenter, str(val)
                )
            else:
                # Bar kosong (outline tipis)
                painter.setBrush(QColor("#F0EFEB"))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(x, mt + chart_h - 4, int(bar_w), 4, 2, 2)

            # X label
            painter.setPen(QColor("#8C8A86"))
            painter.setFont(QFont("", 9))
            painter.drawText(
                QRect(int(x - gap / 2), mt + chart_h + 10, int(bar_w + gap), 20),
                Qt.AlignCenter, label
            )

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD OWNER
# ─────────────────────────────────────────────────────────────────────────────

class DashboardOwner(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def refresh(self):
        self._load_data()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(22)

        # ── Header (HANYA SATU, tanpa duplikasi) ──────────────────────────
        header = QHBoxLayout()
        header.setSpacing(0)

        left_header = QVBoxLayout()
        left_header.setSpacing(4)

        greeting = QLabel("Selamat datang kembali 👋")
        greeting.setStyleSheet(
            "font-size: 13px; color: #8C8A86; font-weight: 400; background: transparent;"
        )
        self.header_title = QLabel("Dasbor Pemilik")
        self.header_title.setStyleSheet(
            "font-size: 24px; font-weight: 700; color: #111111;"
            "letter-spacing: -0.5px; background: transparent;"
        )
        left_header.addWidget(greeting)
        left_header.addWidget(self.header_title)

        header.addLayout(left_header)
        header.addStretch()

        # Tanggal dengan pill style
        today = datetime.now()
        date_str = today.strftime("%d %B %Y")
        date_pill = QLabel(f"📅  {date_str}")
        date_pill.setStyleSheet("""
            font-size: 12px; color: #6B6A66;
            background: #ECEAE6;
            border-radius: 20px;
            padding: 6px 14px;
        """)
        self.date_label = date_pill
        header.addWidget(date_pill)

        layout.addLayout(header)

        # ── Metric cards ──────────────────────────────────────────────────
        self.card_total   = MetricCard("Total Inventaris",        "0", "#0F6E56", "📦")
        self.card_active  = MetricCard("Sedang Disewa",           "0", "#BA7517", "⏱")
        self.card_pending = MetricCard("Menunggu Konfirmasi",     "0", "#3B82F6", "🔔")
        self.card_overdue = MetricCard("Terlambat Dikembalikan",  "0", "#E24B4A", "⚠️")

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        for card in (self.card_total, self.card_active, self.card_pending, self.card_overdue):
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        # ── Mid row: Notifikasi + Chart ───────────────────────────────────
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        # Notifikasi
        notif_card = QFrame()
        notif_card.setObjectName("notifCard")
        notif_card.setStyleSheet("""
            #notifCard {
                background: #ffffff;
                border: 1px solid #ECEAE6;
                border-radius: 14px;
            }
        """)
        notif_layout = QVBoxLayout(notif_card)
        notif_layout.setContentsMargins(0, 0, 0, 16)
        notif_layout.setSpacing(0)

        notif_header_row = QHBoxLayout()
        notif_header_row.setContentsMargins(20, 16, 20, 16)
        notif_header_label = QLabel("🚨  Perlu Tindakan Segera")
        notif_header_label.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #1A1A1A; background: transparent;"
        )
        notif_header_row.addWidget(notif_header_label)
        notif_header_row.addStretch()
        notif_layout.addLayout(notif_header_row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #F0EFEB; border: none;")
        notif_layout.addWidget(sep)

        self.notif_container = QVBoxLayout()
        self.notif_container.setSpacing(0)
        self.notif_container.setContentsMargins(0, 0, 0, 0)
        notif_layout.addLayout(self.notif_container)
        notif_layout.addStretch()

        mid_row.addWidget(notif_card, 2)

        # Chart
        chart_card = QFrame()
        chart_card.setObjectName("chartCard")
        chart_card.setStyleSheet("""
            #chartCard {
                background: #ffffff;
                border: 1px solid #ECEAE6;
                border-radius: 14px;
            }
        """)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(0, 0, 0, 16)
        chart_layout.setSpacing(0)

        chart_header_row = QHBoxLayout()
        chart_header_row.setContentsMargins(20, 16, 20, 16)
        chart_header_label = QLabel("📈  Tren Penyewaan 6 Bulan Terakhir")
        chart_header_label.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #1A1A1A; background: transparent;"
        )
        chart_header_row.addWidget(chart_header_label)
        chart_header_row.addStretch()
        chart_layout.addLayout(chart_header_row)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background: #F0EFEB; border: none;")
        chart_layout.addWidget(sep2)

        chart_inner = QWidget()
        chart_inner.setStyleSheet("background: transparent;")
        ci_layout = QVBoxLayout(chart_inner)
        ci_layout.setContentsMargins(16, 12, 16, 8)
        self.bar_chart = BarChart([])
        ci_layout.addWidget(self.bar_chart)
        chart_layout.addWidget(chart_inner, 1)

        mid_row.addWidget(chart_card, 3)
        layout.addLayout(mid_row)

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Data loading ──────────────────────────────────────────────────────

    def _load_data(self):
        user = get_current_user()
        if user:
            name = user.get("name", "Pemilik")
            self.header_title.setText(f"Halo, {name}!")

        items = get_all_inventory() or []
        self.card_total.set_value(len(items))

        rentals = get_rentals_for_owner() or []

        active_count  = sum(1 for r in rentals if r.get("status") in ("confirmed", "active"))
        pending_count = sum(1 for r in rentals if r.get("status") == "pending")
        overdue_count = sum(1 for r in rentals if r.get("status") == "overdue")

        now = datetime.now().strftime("%Y-%m-%d")
        for r in rentals:
            s   = r.get("status", "")
            end = r.get("end_date", "0000")
            if s in ("confirmed", "active") and end < now:
                overdue_count += 1

        self.card_active.set_value(active_count)
        self.card_pending.set_value(pending_count)
        self.card_overdue.set_value(overdue_count)

        self._build_notifications(pending_count, active_count, overdue_count)
        self._build_chart(rentals)

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
                sep.setStyleSheet("background: #F0EFEB; border: none; margin: 0 20px;")
                self.notif_container.addWidget(sep)
            notif = NotificationItem(color, text, "Lihat →", key)
            notif.clicked.connect(self.navigate_to.emit)
            self.notif_container.addWidget(notif)
            items_added += 1

        if pending > 0:
            add_notif("#E24B4A", f"{pending} penyewaan menunggu konfirmasi", "pending_rentals")
        if active > 0:
            add_notif("#BA7517", f"{active} penyewaan harus dikembalikan hari ini", "active_rentals")
        if overdue > 0:
            add_notif("#E24B4A", f"{overdue} barang terlambat dikembalikan", "overdue_rentals")

        if items_added == 0:
            empty = QLabel("Tidak ada tindakan yang diperlukan saat ini.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                "font-size: 13px; color: #A8A6A2; padding: 32px 20px; background: transparent;"
            )
            self.notif_container.addWidget(empty)

    def _build_chart(self, rentals):
        now = datetime.now()
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