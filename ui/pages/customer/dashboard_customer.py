from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from controllers.inventory_controller import get_all_inventory
from controllers.rental_controller import get_rentals_for_customer
from controllers.auth_controller import get_current_user


CATEGORY_COLORS = {
    "Kostum": "#0F6E56",
    "Aksesoris": "#BA7517",
    "Properti": "#1D9E75",
    "Alat Musik": "#5B4B8A",
    "Make Up": "#C75B7A",
    "Lainnya": "#6B6A66",
}

CATEGORY_ICONS = {
    "Kostum": "\u265b",
    "Audio": "\u266b",
    "Properti": "\u2605",
    "Alat Musik": "\u266a",
    "Musik": "\u266a",
    "Make Up": "\u2726",
    "Aksesoris": "\u25c8",
    "Lainnya": "\u25a1",
}


class StatCard(QFrame):
    def __init__(self, title, value, icon_char, icon_bg_color, icon_fg_color="#0F6E56"):
        super().__init__()
        self.setObjectName("statCard")
        self.setStyleSheet("""
            #statCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(f"background: {icon_bg_color}; border-radius: 8px;")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        icon_label = QLabel(icon_char)
        icon_label.setStyleSheet(f"font-size: 20px; color: {icon_fg_color}; background: transparent;")
        il.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 12px; font-weight: 500; color: #8C8A86; background: transparent;")
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("font-size: 26px; font-weight: 700; color: #1A1A1A; background: transparent;")
        text_col.addWidget(lbl_title)
        text_col.addWidget(self.value_label)

        layout.addWidget(icon_frame)
        layout.addLayout(text_col, 1)

    def set_value(self, value):
        self.value_label.setText(str(value))


class InventoryCard(QFrame):
    def __init__(self, item_data, on_rent_callback):
        super().__init__()
        self._item = item_data
        self._on_rent = on_rent_callback
        self.setObjectName("invCard")
        self.setStyleSheet("""
            #invCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
            #invCard:hover {
                border-color: #0F6E56;
            }
        """)
        self._build(item_data)

    def _build(self, item):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cat = item.get("category", "")
        icon = CATEGORY_ICONS.get(cat, "\u25a1")
        cat_color = CATEGORY_COLORS.get(cat, "#6B6A66")

        img_placeholder = QFrame()
        img_placeholder.setFixedHeight(130)
        img_placeholder.setStyleSheet("""
            background: #EDECE8;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        img_layout = QVBoxLayout(img_placeholder)
        img_layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 36px; color: #A8A6A2; background: transparent;")
        img_layout.addWidget(icon_lbl)

        cat_badge = QFrame()
        cat_badge.setStyleSheet(f"background: {cat_color}18; border-radius: 4px; padding: 2px 8px;")
        cb_layout = QHBoxLayout(cat_badge)
        cb_layout.setContentsMargins(6, 2, 6, 2)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_label = QLabel(cat)
        cb_label.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {cat_color}; background: transparent;")
        cb_layout.addWidget(cb_label)
        img_layout.addWidget(cat_badge, 0, Qt.AlignCenter)

        info = QWidget()
        info.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(16, 12, 16, 16)
        info_layout.setSpacing(8)

        name = QLabel(item.get("name", ""))
        name.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A;")
        name.setWordWrap(True)
        info_layout.addWidget(name)

        price = QLabel(f"Rp {item.get('price_per_day', 0):,}")
        price.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F6E56;")
        per_day = QLabel("/ hari")
        per_day.setStyleSheet("font-size: 12px; font-weight: 400; color: #8C8A86;")
        price_row = QHBoxLayout()
        price_row.setContentsMargins(0, 0, 0, 0)
        price_row.setSpacing(0)
        price_row.addWidget(price)
        price_row.addWidget(per_day)
        price_row.addStretch()
        info_layout.addLayout(price_row)

        rent_btn = QPushButton("Sewa Sekarang")
        rent_btn.setCursor(Qt.PointingHandCursor)
        rent_btn.setFixedHeight(34)
        rent_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 0.5px solid #0F6E56; border-radius: 8px;
                font-size: 12px; font-weight: 500; color: #0F6E56;
            }}
            QPushButton:hover {{ background: #F8F7F4; }}
        """)
        rent_btn.clicked.connect(lambda: self._on_rent())
        info_layout.addWidget(rent_btn)

        layout.addWidget(img_placeholder)
        layout.addWidget(info)


class StatusBadge(QFrame):
    def __init__(self, text, status_type="active"):
        super().__init__()
        self.setObjectName("badge")
        colors = {
            "active": ("#E8F7F2", "#1D9E75"),
            "overdue": ("#FDE8E8", "#E24B4A"),
            "pending": ("#FEF3E8", "#BA7517"),
        }
        bg_hex, fg_hex = colors.get(status_type, ("#EDECE8", "#6B6A66"))
        self.setStyleSheet(f"""
            #badge {{
                background: {bg_hex}; border-radius: 8px;
                padding: 4px 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        label = QLabel(text)
        label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {fg_hex}; background: transparent;")
        layout.addWidget(label)


class DashboardCustomer(QWidget):
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

        self.welcome_label = QLabel("Selamat datang, Budi")
        self.welcome_label.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        self.date_label = QLabel("")
        self.date_label.setStyleSheet("font-size: 13px; color: #8C8A86; margin-top: 2px;")
        layout.addWidget(self.welcome_label)
        layout.addWidget(self.date_label)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.card_tersedia = StatCard("Inventaris Tersedia", "0", "\u2630", "#E8F0EE", "#0F6E56")
        self.card_disewa = StatCard("Sedang Disewa", "0", "\u25b6", "#FEF3E8", "#BA7517")
        self.card_menunggu = StatCard("Menunggu Konfirmasi", "0", "\u23f3", "#E8EEF8", "#4A7DC7")
        for card in (self.card_tersedia, self.card_disewa, self.card_menunggu):
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        self._build_popular_section(bottom_row)
        self._build_active_rentals_section(bottom_row)

        layout.addLayout(bottom_row)

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_popular_section(self, parent_layout):
        section = QWidget()
        section.setStyleSheet("background: transparent;")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(14)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Inventaris Pilihan")
        title.setStyleSheet("font-size: 18px; font-weight: 500; color: #1A1A1A;")
        self.lihat_semua_btn = QPushButton("Lihat Semua")
        self.lihat_semua_btn.setCursor(Qt.PointingHandCursor)
        self.lihat_semua_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 13px; font-weight: 500; color: #0F6E56;
            }
            QPushButton:hover { color: #0A5A45; }
        """)
        self.lihat_semua_btn.clicked.connect(lambda: self.navigate_to.emit("inventory"))
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.lihat_semua_btn)
        section_layout.addLayout(header)

        self.inventory_grid = QWidget()
        self.inventory_grid.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.inventory_grid)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        section_layout.addWidget(self.inventory_grid)

        parent_layout.addWidget(section, 2)

    def _build_active_rentals_section(self, parent_layout):
        section = QFrame()
        section.setObjectName("rentalsSection")
        section.setStyleSheet("""
            #rentalsSection {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
        """)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Penyewaan Aktif")
        title.setStyleSheet("font-size: 18px; font-weight: 500; color: #1A1A1A;")
        h_layout.addWidget(title)
        section_layout.addWidget(header)

        self.rentals_table = QTableWidget()
        self.rentals_table.setColumnCount(5)
        self.rentals_table.setHorizontalHeaderLabels([
            "Nama Item", "Kategori", "Tgl Ambil", "Tenggat Kembali", "Status"
        ])
        self.rentals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rentals_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rentals_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rentals_table.verticalHeader().setVisible(False)
        self.rentals_table.setShowGrid(False)
        self.rentals_table.setStyleSheet("""
            QTableWidget {
                border: none; border-top: 0.5px solid #E0DDD8;
                background: #ffffff; font-size: 13px;
                gridline-color: transparent;
            }
            QTableWidget::item { padding: 12px 16px; border-bottom: 0.5px solid #EDECE8; }
            QTableWidget::item:selected { background: #E8F0EE; color: #1A1A1A; }
            QHeaderView::section {
                background: #F8F7F4; border: none;
                font-size: 11px; font-weight: 600; color: #8C8A86;
                padding: 10px 16px; border-bottom: 0.5px solid #E0DDD8;
                text-transform: uppercase;
            }
            QTableWidget::item:hover { background: #FAF9F6; }
        """)
        self.rentals_table.setFixedWidth(520)
        section_layout.addWidget(self.rentals_table)

        footer = QWidget()
        footer.setStyleSheet("background: transparent; border-top: 0.5px solid #E0DDD8;")
        f_layout = QVBoxLayout(footer)
        f_layout.setContentsMargins(0, 0, 0, 0)
        detail_btn = QPushButton("Lihat Detail Semua Penyewaan")
        detail_btn.setCursor(Qt.PointingHandCursor)
        detail_btn.setFixedHeight(44)
        detail_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 13px; font-weight: 400; color: #8C8A86;
            }
            QPushButton:hover { color: #0F6E56; }
        """)
        detail_btn.clicked.connect(lambda: self.navigate_to.emit("rental"))
        f_layout.addWidget(detail_btn, 0, Qt.AlignCenter)
        section_layout.addWidget(footer)

        parent_layout.addWidget(section, 1)

    def _get_status_type(self, end_date_str):
        if not end_date_str:
            return "active"
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date < datetime.now().date():
                return "overdue"
            return "active"
        except ValueError:
            return "active"

    def _load_data(self):
        user = get_current_user()
        if user:
            self.welcome_label.setText(f"Selamat datang, {user['name']}")

        now = datetime.now()
        try:
            locale_date = now.strftime("%A, %d %B %Y")
        except Exception:
            locale_date = now.strftime("%Y-%m-%d")
        self.date_label.setText(locale_date)

        items = get_all_inventory() or []
        total_stock = sum(item.get("stock", 0) for item in items)
        self.card_tersedia.set_value(f"{total_stock:,}")

        rentals = get_rentals_for_customer(user["id"]) if user else []
        active_count = sum(1 for r in rentals if r.get("status") in ("confirmed", "active"))
        pending_count = sum(1 for r in rentals if r.get("status") == "pending")
        self.card_disewa.set_value(active_count)
        self.card_menunggu.set_value(pending_count)

        self._populate_inventory_grid(items[:4])
        self._populate_rentals_table(rentals)

    def _populate_inventory_grid(self, items):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, item in enumerate(items):
            card = InventoryCard(item, lambda i=item: self._on_rent(i))
            row, col = divmod(idx, 2)
            self.grid_layout.addWidget(card, row, col)

    def _on_rent(self, item):
        self.navigate_to.emit("rental")

    def _populate_rentals_table(self, rentals):
        active = [r for r in rentals if r.get("status") in ("confirmed", "active", "pending")]

        self.rentals_table.setRowCount(len(active))
        for row, r in enumerate(active):
            inv_data = r.get("inventories") or {}
            name = inv_data.get("name", "-")
            category = inv_data.get("category", "-")
            start_date = r.get("start_date", "")
            end_date = r.get("end_date", "")
            status = r.get("status", "")

            self.rentals_table.setItem(row, 0, QTableWidgetItem(name))
            self.rentals_table.setItem(row, 1, QTableWidgetItem(category))
            self.rentals_table.setItem(row, 2, QTableWidgetItem(start_date))
            self.rentals_table.setItem(row, 3, QTableWidgetItem(end_date))

            if status == "pending":
                badge = StatusBadge("Menunggu", "pending")
            elif status == "confirmed":
                badge = StatusBadge("Aktif", "active")
            elif status == "active":
                is_overdue = False
                if end_date:
                    try:
                        is_overdue = datetime.strptime(end_date, "%Y-%m-%d").date() < datetime.now().date()
                    except ValueError:
                        pass
                if is_overdue:
                    badge = StatusBadge("Terlambat", "overdue")
                else:
                    badge = StatusBadge("Aktif", "active")
            else:
                badge = StatusBadge(status.title(), "active")

            self.rentals_table.setCellWidget(row, 4, badge)
            self.rentals_table.setRowHeight(row, 48)
