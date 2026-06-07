from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from controllers.inventory_controller import get_all_inventory
from controllers.rental_controller import get_rentals_for_owner
from controllers.auth_controller import get_current_user


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
               "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


class MetricCard(QFrame):
    def __init__(self, title, value, color, icon):
        super().__init__()
        self.setObjectName("metricCard")
        self.setStyleSheet(f"""
            #metricCard {{
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px; padding: 20px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(f"background: {color}15; border-radius: 10px;")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 20px; color: {color}; background: transparent;")
        il.addWidget(ic)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {color}; letter-spacing: -0.5px;")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #8C8A86; letter-spacing: 0.2px;")

        text_col.addWidget(self.value_label)
        text_col.addWidget(title_label)

        layout.addWidget(icon_frame)
        layout.addLayout(text_col, 1)

    def set_value(self, value):
        self.value_label.setText(str(value))


class NotificationItem(QFrame):
    clicked = Signal(str)

    def __init__(self, dot_color, text, link_text, link_key):
        super().__init__()
        self._key = link_key
        self.setObjectName("notifItem")
        self.setStyleSheet("""
            #notifItem {
                background: transparent; border-radius: 8px;
            }
            #notifItem:hover { background: #FAF9F6; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {dot_color}; border-radius: 4px;")
        layout.addWidget(dot)

        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 14px; color: #1A1A1A; background: transparent;")
        layout.addWidget(text_label, 1)

        link = QPushButton(link_text)
        link.setCursor(Qt.PointingHandCursor)
        link.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 13px; font-weight: 500; color: #0F6E56;
            }
            QPushButton:hover { color: #0A5A45; }
        """)
        link.clicked.connect(lambda: self.clicked.emit(self._key))
        layout.addWidget(link)


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
        margin_left = 40
        margin_right = 16
        margin_top = 16
        margin_bottom = 36

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        values = [v for _, v in self._data]
        max_val = max(values) if values else 1

        n = len(self._data)
        bar_w = min(40, chart_w // n - 12)
        gap = (chart_w - bar_w * n) / (n + 1)

        # Y-axis line
        pen = QPen(QColor("#D4D2CD"), 0.5)
        painter.setPen(pen)
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + chart_h)

        # Y-axis labels
        font = QFont("Inter", 9)
        painter.setFont(font)

        y_ticks = 4
        for i in range(y_ticks + 1):
            y = margin_top + chart_h - (chart_h / y_ticks) * i
            val = int((max_val / y_ticks) * i)
            painter.setPen(QColor("#A8A6A2"))
            painter.drawText(QRect(0, int(y) - 8, margin_left - 8, 16),
                             Qt.AlignRight | Qt.AlignVCenter, str(val))
            painter.setPen(QPen(QColor("#EDECE8"), 0.5))
            painter.drawLine(int(margin_left + 2), int(y), int(w - margin_right), int(y))

        # Bars
        for i, (label, val) in enumerate(self._data):
            bar_h = int((val / max_val) * chart_h) if max_val > 0 else 0
            x = int(margin_left + gap + i * (bar_w + gap))
            y = int(margin_top + chart_h - bar_h)

            if val > 0:
                painter.setBrush(QColor(self._bar_color))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(x, y, int(bar_w), bar_h, 3, 3)

            painter.setPen(QColor("#6B6A66"))
            painter.drawText(QRect(int(x - gap / 2), int(margin_top + chart_h + 8),
                                   int(bar_w + gap), 20),
                             Qt.AlignCenter, label)

        painter.end()


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
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QHBoxLayout()
        self.header_title = QLabel("Dasbor Pemilik")
        self.header_title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        header.addWidget(self.header_title)
        header.addStretch()

        today = datetime.now()
        date_str = today.strftime("%d %B %Y")
        self.date_label = QLabel(date_str)
        self.date_label.setStyleSheet("font-size: 13px; color: #8C8A86; padding-top: 4px;")
        header.addWidget(self.date_label)

        layout.addLayout(header)

        self.card_total = MetricCard("Total Inventaris", "0", "#0F6E56", "\u2610")
        self.card_active = MetricCard("Sedang Disewa", "0", "#BA7517", "\u23f1")
        self.card_pending = MetricCard("Menunggu Konfirmasi", "0", "#3B82F6", "\u23f0")
        self.card_overdue = MetricCard("Terlambat Dikembalikan", "0", "#E24B4A", "\u26a0")

        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(16)
        for card in (self.card_total, self.card_active, self.card_pending, self.card_overdue):
            stats_grid.addWidget(card)
        layout.addLayout(stats_grid)

        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        # --- Perlu Tindakan Separa ---
        notif_card = QFrame()
        notif_card.setObjectName("notifCard")
        notif_card.setStyleSheet("""
            #notifCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
        """)
        notif_layout = QVBoxLayout(notif_card)
        notif_layout.setContentsMargins(0, 0, 0, 0)
        notif_layout.setSpacing(0)

        notif_header = QLabel("  Perlu Tindakan Segera")
        notif_header.setStyleSheet("""
            font-size: 16px; font-weight: 500; color: #1A1A1A;
            padding: 16px 20px; background: transparent;
        """)
        notif_layout.addWidget(notif_header)

        sep = QFrame()
        sep.setFixedHeight(0.5)
        sep.setStyleSheet("background: #E0DDD8; border: none;")
        notif_layout.addWidget(sep)

        self.notif_container = QVBoxLayout()
        self.notif_container.setSpacing(0)
        notif_layout.addLayout(self.notif_container)

        notif_layout.addStretch()
        mid_row.addWidget(notif_card, 2)

        # --- Grafik Penyewaan Bulanan ---
        chart_card = QFrame()
        chart_card.setObjectName("chartCard")
        chart_card.setStyleSheet("""
            #chartCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
        """)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(0)

        chart_header = QLabel("  Tren Penyewaan 6 Bulan Terakhir")
        chart_header.setStyleSheet("""
            font-size: 16px; font-weight: 500; color: #1A1A1A;
            padding: 16px 20px; background: transparent;
        """)
        chart_layout.addWidget(chart_header)

        sep2 = QFrame()
        sep2.setFixedHeight(0.5)
        sep2.setStyleSheet("background: #E0DDD8; border: none;")
        chart_layout.addWidget(sep2)

        self.bar_chart = BarChart([])
        chart_layout.addWidget(self.bar_chart, 1)

        mid_row.addWidget(chart_card, 3)

        layout.addLayout(mid_row)

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_data(self):
        user = get_current_user()
        if user:
            self.header_title.setText(f"Dasbor Pemilik")

        items = get_all_inventory() or []
        self.card_total.set_value(len(items))

        rentals = get_rentals_for_owner() or []

        active_count = sum(1 for r in rentals if r.get("status") in ("confirmed", "active"))
        pending_count = sum(1 for r in rentals if r.get("status") == "pending")
        overdue_count = sum(1 for r in rentals if r.get("status") == "overdue")

        now = datetime.now().strftime("%Y-%m-%d")
        for r in rentals:
            s = r.get("status", "")
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

        notifs = []

        if pending > 0:
            sep = QFrame()
            sep.setFixedHeight(0.5)
            sep.setStyleSheet("background: #EDECE8; border: none;")
            self.notif_container.addWidget(sep)
            item = NotificationItem(
                "#E24B4A",
                f"{pending} penyewaan menunggu konfirmasi",
                "Lihat \u2192", "pending_rentals"
            )
            item.clicked.connect(self.navigate_to.emit)
            self.notif_container.addWidget(item)

        if active > 0:
            sep = QFrame()
            sep.setFixedHeight(0.5)
            sep.setStyleSheet("background: #EDECE8; border: none;")
            self.notif_container.addWidget(sep)
            item = NotificationItem(
                "#BA7517",
                f"{active} penyewaan harus dikembalikan hari ini",
                "Lihat \u2192", "active_rentals"
            )
            item.clicked.connect(self.navigate_to.emit)
            self.notif_container.addWidget(item)

        if overdue > 0:
            sep = QFrame()
            sep.setFixedHeight(0.5)
            sep.setStyleSheet("background: #EDECE8; border: none;")
            self.notif_container.addWidget(sep)
            item = NotificationItem(
                "#E24B4A",
                f"{overdue} barang terlambat dikembalikan",
                "Lihat \u2192", "overdue_rentals"
            )
            item.clicked.connect(self.navigate_to.emit)
            self.notif_container.addWidget(item)

        if not notifs:
            label = QLabel("  Tidak ada notifikasi.")
            label.setStyleSheet("font-size: 13px; color: #8C8A86; padding: 20px;")
            self.notif_container.addWidget(label)

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
            count = sum(1 for r in rentals if r.get("created_at", "").startswith(f"{y}-{m:02d}"))
            data.append((label, count))

        self.bar_chart.set_data(data)
