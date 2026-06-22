from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from controllers.inventory_controller import get_all_inventory
from controllers.rental_controller import get_rentals_for_customer, get_rentals_by_inventory
from controllers.auth_controller import get_current_user
from utils.worker import DataWorker
from ui.components import apply_outline_primary, apply_link
from ui.pages.customer.inventory_page import _load_pixmap
from PySide6.QtGui import QPixmap


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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setObjectName("statIconFrame")
        icon_frame.setProperty("iconBg", icon_bg_color)
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        icon_label = QLabel(icon_char)
        icon_label.setObjectName("statIconLabel")
        icon_label.setProperty("iconFg", icon_fg_color)
        il.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("cardTitle")
        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("cardValue")
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
        self._build(item_data)

    def _build(self, item):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        cat = item.get("category", "")
        icon = CATEGORY_ICONS.get(cat, "\u25a1")
        cat_color = CATEGORY_COLORS.get(cat, "#6B6A66")

        img_lbl = QLabel()
        img_lbl.setFixedSize(240, 130)
        img_lbl.setObjectName("imgPlaceholder")
        img_lbl.setAlignment(Qt.AlignCenter)

        # Try load image using shared loader; fall back to icon
        img_url = item.get("image_url", "")
        pix = None
        try:
            pix = _load_pixmap(img_url, size=130) if img_url else None
        except Exception:
            pix = None

        if pix:
            img_lbl.setPixmap(pix)
        else:
            icon_lbl = QLabel(icon)
            icon_lbl.setObjectName("cardIcon")
            # place icon centered inside the img_lbl as fallback
            img_lbl.setText(icon)

        cat_badge = QFrame()
        cat_badge.setObjectName("catBadge")
        cat_badge.setProperty("cat", cat)
        cb_layout = QHBoxLayout(cat_badge)
        cb_layout.setContentsMargins(6, 2, 6, 2)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_label = QLabel(cat)
        cb_label.setObjectName("catBadgeLabel")
        cb_label.setProperty("catColor", cat_color)
        cb_layout.addWidget(cb_label)
        # show category badge below image area
        # add image label to top of card
        # (category badge will be added below)
        
        # place image label in layout
        # use a container so category badge can be positioned
        image_container = QVBoxLayout()
        image_container.setContentsMargins(0,0,0,0)
        image_container.setSpacing(6)
        image_container.addWidget(img_lbl)
        image_container.addWidget(cat_badge, 0, Qt.AlignCenter)
        layout.addLayout(image_container)
        info = QWidget()
        info.setObjectName("cardInfo")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(16, 12, 16, 16)
        info_layout.setSpacing(8)

        name = QLabel(item.get("name", ""))
        name.setObjectName("itemName")
        name.setWordWrap(True)
        info_layout.addWidget(name)

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

        rent_btn = QPushButton("Sewa Sekarang")
        apply_outline_primary(rent_btn, height=34)
        rent_btn.clicked.connect(lambda: self._on_rent())
        info_layout.addWidget(rent_btn)

        layout.addWidget(info)


class StatusBadge(QFrame):
    def __init__(self, text, status_type="active"):
        super().__init__()
        self.setObjectName("statusBadge")
        self.setProperty("status", status_type)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        label = QLabel(text)
        label.setObjectName("badgeText")
        label.setProperty("textColor", "")
        layout.addWidget(label)


class DashboardCustomer(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._worker = None
        self._build_ui()

    def reset(self):
        """Reset dashboard state untuk user baru (sebelum login user lain)."""
        print("[DashboardCustomer.reset] Resetting dashboard for new user...")
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
        self.welcome_label.setText("Selamat datang")
        self.welcome_label.repaint()
        self.date_label.setText("")
        self.date_label.repaint()
        self.card_tersedia.set_value(0)
        self.card_disewa.set_value(0)
        self.card_menunggu.set_value(0)
        
        # Clear inventory grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear rentals table
        self.rentals_table.setRowCount(0)
        print("[DashboardCustomer.reset] Dashboard reset complete")

    def refresh(self):
        """Load data di background thread agar UI tidak freeze."""
        # Jangan fetch ulang jika ada worker yang masih jalan
        try:
            if self._worker and self._worker.isRunning():
                print("[DashboardCustomer] Worker sudah jalan, skip refresh")
                return
        except RuntimeError:
            # Worker sudah didelete, set ke None
            self._worker = None
        
        self._set_loading(True)
        self._worker = DataWorker(self._fetch_data)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.error.connect(lambda e: self._on_worker_error(e))
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_error(self, error_msg):
        """Handle worker error."""
        print(f"[DashboardCustomer] Error: {error_msg}")
        self._set_loading(False)

    def _on_worker_finished(self):
        """Cleanup worker thread setelah selesai."""
        self._set_loading(False)
        if self._worker:
            self._worker.quit()
            self._worker.wait()
            self._worker = None

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("pageContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self.welcome_label = QLabel("Selamat datang, Budi")
        self.welcome_label.setObjectName("pageTitle")
        self.date_label = QLabel("")
        self.date_label.setObjectName("muted")
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
        section.setObjectName("section")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(14)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Inventaris Pilihan")
        title.setObjectName("sectionTitle")
        self.lihat_semua_btn = QPushButton("Lihat Semua")
        apply_link(self.lihat_semua_btn)
        self.lihat_semua_btn.clicked.connect(lambda: self.navigate_to.emit("inventory"))
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.lihat_semua_btn)
        section_layout.addLayout(header)

        self.inventory_grid = QWidget()
        self.inventory_grid.setObjectName("inventoryGrid")
        self.grid_layout = QGridLayout(self.inventory_grid)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        section_layout.addWidget(self.inventory_grid)

        parent_layout.addWidget(section, 2)

    def _build_active_rentals_section(self, parent_layout):
        section = QFrame()
        section.setObjectName("rentalsSection")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("sectionHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Penyewaan Aktif")
        title.setObjectName("sectionTitle")
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
        self.rentals_table.setObjectName("rentalsTable")
        self.rentals_table.setFixedWidth(520)
        # enable sorting for active rentals table
        self.rentals_table.setSortingEnabled(True)
        section_layout.addWidget(self.rentals_table)

        footer = QWidget()
        footer.setObjectName("cardFooter")
        f_layout = QVBoxLayout(footer)
        f_layout.setContentsMargins(0, 0, 0, 0)
        detail_btn = QPushButton("Lihat Detail Semua Penyewaan")
        apply_link(detail_btn, height=44)
        detail_btn.clicked.connect(lambda: self.navigate_to.emit("history"))
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

    def _fetch_data(self):
        """Dijalankan di background thread."""
        user    = get_current_user()
        print(f"[DashboardCustomer._fetch_data] Current user: {user}")
        items   = get_all_inventory() or []
        rentals = get_rentals_for_customer(user["id"]) if user else []
        print(f"[DashboardCustomer._fetch_data] Fetched {len(items)} items, {len(rentals)} rentals")
        return {"user": user, "items": items, "rentals": rentals}

    def _on_data_loaded(self, data):
        user    = data["user"]
        items   = data["items"]
        rentals = data["rentals"]
        self._set_loading(False)
        
        # Update stats cards
        if user:
            welcome_text = f"Selamat datang, {user['name']}"
            print(f"[DashboardCustomer._on_data_loaded] Setting welcome text: {welcome_text}")
            self.welcome_label.setText(welcome_text)
            self.welcome_label.repaint()
        else:
            print("[DashboardCustomer._on_data_loaded] WARNING: user is None!")

        now = datetime.now()
        try:
            locale_date = now.strftime("%A, %d %B %Y")
        except Exception:
            locale_date = now.strftime("%Y-%m-%d")
        self.date_label.setText(locale_date)

        # Hitung barang yang tersedia (tidak sedang disewa semua)
        available_count = sum(1 for item in items if item.get("stock", 0) > 0)
        self.card_tersedia.set_value(available_count)

        active_count = sum(1 for r in rentals if r.get("status") in ("confirmed", "active"))
        pending_count = sum(1 for r in rentals if r.get("status") == "pending")
        self.card_disewa.set_value(active_count)
        self.card_menunggu.set_value(pending_count)

        self._populate_inventory_grid(items[:4])
        self._populate_rentals_table(rentals)

    def _set_loading(self, loading: bool):
        if hasattr(self, 'welcome_label'):
            pass   # bisa tambah spinner di sini jika mau

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