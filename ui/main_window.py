from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStatusBar, QFrame,
    QMessageBox, QSizePolicy, QSpacerItem, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QFont, QPixmap, QPainter, QColor

from ui.pages.login_page import LoginPage
from ui.pages.customer.dashboard_customer import DashboardCustomer
from ui.pages.owner.dashboard_owner import DashboardOwner

from ui.pages.owner.inventory_page import InventoryPage as OwnerInventoryPage
from ui.pages.owner.add_customer_page import AddCustomerPage
from ui.pages.customer.inventory_page import InventoryPage as CustomerInventoryPage

from ui.pages.customer.rental_page import RentalPage
from ui.pages.customer.history_page import HistoryPage
from ui.pages.item_detail_page import ItemDetailPage
from ui.pages.owner.confirm_rental_page import ConfirmRentalPage
from ui.pages.owner.confirm_return_page import ConfirmReturnPage
from ui.pages.notification_page import NotificationPage

from controllers.auth_controller import get_current_user, logout as auth_logout, is_owner

# ── Info Anggota Kelompok ────────────────────────────────────────────────────
ANGGOTA = [
    ("Baiq Adelia Dwi Savitri", "F1D02310006"),
    ("Lalu Muhammad Farhan",    "F1D02310119"),
    ("Syamsul Rijal",           "F1D02310025"),
]

# Indeks halaman
PAGE_LOGIN              = 0
PAGE_DASHBOARD_CUSTOMER = 1
PAGE_DASHBOARD_OWNER    = 2
PAGE_INVENTORY_OWNER    = 3
PAGE_RENTAL             = 4
PAGE_HISTORY            = 5
PAGE_ITEM_DETAIL        = 6
PAGE_CONFIRM_RENTAL     = 7
PAGE_CONFIRM_RETURN     = 8
PAGE_NOTIFICATIONS      = 9
PAGE_INVENTORY_CUSTOMER = 10
PAGE_ADD_CUSTOMER       = 11

PAGE_NAMES = {
    PAGE_DASHBOARD_CUSTOMER: "Beranda",
    PAGE_DASHBOARD_OWNER:    "Dashboard",
    PAGE_INVENTORY_OWNER:    "Kelola Inventaris",
    PAGE_INVENTORY_CUSTOMER: "Lihat Inventaris",
    PAGE_RENTAL:             "Penyewaan Saya",
    PAGE_HISTORY:            "Laporan & Riwayat",
    PAGE_ITEM_DETAIL:        "Detail Item",
    PAGE_CONFIRM_RENTAL:     "Konfirmasi Penyewaan",
    PAGE_CONFIRM_RETURN:     "Konfirmasi Pengembalian",
    PAGE_NOTIFICATIONS:      "Notifikasi",
    PAGE_ADD_CUSTOMER:       "Tambah Customer",
}

# ─────────────────────────────────────────────────────────────────────────────
#  TEMA GELAP / TERANG
# ─────────────────────────────────────────────────────────────────────────────

LIGHT_THEME = """
/* === LIGHT MODE === */
QMainWindow, QWidget#mainContent { background: #F8F7F4; }
#sidebar { background-color: #F8F7F4; border-right: 0.5px solid #E0DDD8; }
#topbar  { background: #ffffff; border-bottom: 0.5px solid #E0DDD8; }
QStatusBar { background: #F8F7F4; color: #8C8A86; font-size: 11px; border-top: 0.5px solid #E0DDD8; }
QMenuBar { background: #F8F7F4; color: #1A1A1A; }
QMenuBar::item:selected { background: #0F6E56; color: white; border-radius: 4px; }
QMenu { background: #ffffff; border: 0.5px solid #E0DDD8; border-radius: 8px; }
QMenu::item { padding: 8px 24px; font-size: 13px; color: #1A1A1A; border-radius: 4px; }
QMenu::item:selected { background: #E8F0EE; color: #0F6E56; }
QScrollBar:vertical { background: transparent; width: 6px; }
QScrollBar::handle:vertical { background: #D4D2CD; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #A8A6A2; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #1A1A1A; color: #ffffff; border: none; border-radius: 6px; padding: 6px 10px; }
"""

DARK_THEME = """
/* === DARK MODE === */
QMainWindow, QWidget, QFrame, QScrollArea, QAbstractScrollArea { background: #1A1A1A; color: #E8E6E2; }
QWidget#mainContent { background: #1A1A1A; }
#sidebar { background-color: #222220; border-right: 0.5px solid #333330; }
#topbar  { background: #222220; border-bottom: 0.5px solid #333330; }
QStatusBar { background: #222220; color: #8C8A86; font-size: 11px; border-top: 0.5px solid #333330; }
QMenuBar { background: #222220; color: #E8E6E2; }
QMenuBar::item:selected { background: #0F6E56; color: white; border-radius: 4px; }
QMenu { background: #2A2A28; border: 0.5px solid #333330; border-radius: 8px; }
QMenu::item { padding: 8px 24px; font-size: 13px; color: #E8E6E2; border-radius: 4px; }
QMenu::item:selected { background: #1D4A3E; color: #1D9E75; }
QLabel { color: #E8E6E2; background: transparent; }
QPushButton { color: #E8E6E2; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {
    background: #2A2A28; color: #E8E6E2;
    border: 0.5px solid #444442; border-radius: 8px; padding: 8px 12px;
}
QLineEdit:focus, QTextEdit:focus { border-color: #0F6E56; }
QTableWidget { background: #222220; color: #E8E6E2; gridline-color: #333330; alternate-background-color: #272725; }
QTableWidget::item:selected { background: #1D4A3E; color: #E8E6E2; }
QHeaderView::section { background: #2A2A28; color: #8C8A86; border: none; padding: 8px; font-size: 11px; }
QScrollBar:vertical { background: transparent; width: 6px; }
QScrollBar::handle:vertical { background: #444442; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #666664; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #2A2A28; color: #E8E6E2; border: 0.5px solid #444442; border-radius: 6px; padding: 6px 10px; }
QMessageBox { background: #2A2A28; }
QDialog { background: #1A1A1A; }
"""


# ─────────────────────────────────────────────────────────────────────────────
#  NAV ITEM
# ─────────────────────────────────────────────────────────────────────────────

class _NavItem(QWidget):
    clicked = Signal(str)

    _STYLE_NORMAL = """
        QPushButton#navBtn {
            background: transparent;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 400;
            color: #6B6A66;
            text-align: left;
            padding-left: 14px;
        }
        QPushButton#navBtn:hover {
            background: #EDECE8;
            color: #1A1A1A;
        }
    """

    _STYLE_ACTIVE = """
        QPushButton#navBtn {
            background: #E8F0EE;
            border: none;
            border-left: 3px solid #0F6E56;
            border-radius: 0 8px 8px 0;
            font-size: 13px;
            font-weight: 600;
            color: #0F6E56;
            text-align: left;
            padding-left: 11px;
        }
        QPushButton#navBtn:hover {
            background: #DCE8E4;
            color: #0F6E56;
        }
    """

    _STYLE_NORMAL_DARK = """
        QPushButton#navBtn {
            background: transparent;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 400;
            color: #8C8A86;
            text-align: left;
            padding-left: 14px;
        }
        QPushButton#navBtn:hover {
            background: #2A2A28;
            color: #E8E6E2;
        }
    """

    _STYLE_ACTIVE_DARK = """
        QPushButton#navBtn {
            background: #1D3A30;
            border: none;
            border-left: 3px solid #1D9E75;
            border-radius: 0 8px 8px 0;
            font-size: 13px;
            font-weight: 600;
            color: #1D9E75;
            text-align: left;
            padding-left: 11px;
        }
        QPushButton#navBtn:hover {
            background: #1A3028;
            color: #1D9E75;
        }
    """

    def __init__(self, key: str, label: str, badge_text: str = None, parent=None):
        super().__init__(parent)
        self._key = key
        self._is_active = False
        self._dark_mode = False
        self.setFixedHeight(40)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self._btn = QPushButton(label)
        self._btn.setObjectName("navBtn")
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.setFixedHeight(40)
        self._btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._btn.clicked.connect(lambda: self.clicked.emit(self._key))
        row.addWidget(self._btn, 1)

        self._badge = None
        if badge_text:
            self._badge = QLabel(badge_text)
            self._badge.setFixedSize(20, 20)
            self._badge.setAlignment(Qt.AlignCenter)
            self._badge.setStyleSheet("""
                font-size: 10px; font-weight: 700;
                color: #ffffff;
                background: #E24B4A;
                border-radius: 10px;
            """)
            badge_wrap = QWidget()
            badge_wrap.setFixedSize(36, 40)
            badge_wrap.setStyleSheet("background: transparent;")
            bwl = QHBoxLayout(badge_wrap)
            bwl.setContentsMargins(0, 0, 12, 0)
            bwl.addWidget(self._badge)
            row.addWidget(badge_wrap)

        self.set_active(False)

    def set_active(self, active: bool):
        self._is_active = active
        self._refresh_style()

    def set_dark_mode(self, dark: bool):
        self._dark_mode = dark
        self._refresh_style()

    def _refresh_style(self):
        if self._dark_mode:
            style = self._STYLE_ACTIVE_DARK if self._is_active else self._STYLE_NORMAL_DARK
        else:
            style = self._STYLE_ACTIVE if self._is_active else self._STYLE_NORMAL
        self._btn.setStyleSheet(style)

    def update_badge(self, text: str):
        if self._badge:
            self._badge.setText(str(text))
            self._badge.setVisible(int(text) > 0)

    @property
    def key(self):
        return self._key


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

_OWNER_NAV = [
    ("dashboard",    "Dashboard",               None),
    ("inventory",    "Kelola Inventaris",        None),
    ("add_customer", "Tambah Customer",          None),
    ("pending",      "Konfirmasi Penyewaan",     "3"),
    ("returns",      "Konfirmasi Pengembalian",  None),
    ("history",      "Laporan & Riwayat",        None),
    ("notifications","Notifikasi",               None),
]

_CUSTOMER_NAV = [
    ("dashboard",    "Beranda",          None),
    ("inventory",    "Lihat Inventaris", None),
    ("rental",       "Penyewaan Saya",   None),
    ("history",      "Riwayat Sewa",     None),
    ("notifications","Notifikasi",       None),
]


class Sidebar(QFrame):
    navigate = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_active: str | None = None
        self._current_role = "customer"
        self._nav_items: dict[str, _NavItem] = {}
        self._dark_mode = False

        self.setFixedWidth(220)
        self.setObjectName("sidebar")
        self._build()
        self._apply_theme()

    def _build(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self._main_layout.addWidget(self._make_brand())

        self._nav_container = QWidget()
        self._nav_container.setStyleSheet("background: transparent;")
        self._nav_layout = QVBoxLayout(self._nav_container)
        self._nav_layout.setContentsMargins(10, 10, 10, 10)
        self._nav_layout.setSpacing(2)
        self._main_layout.addWidget(self._nav_container)
        self._main_layout.addStretch(1)
        self._main_layout.addWidget(self._make_user_footer())
        self._rebuild_nav()

    def _make_brand(self) -> QWidget:
        brand = QWidget()
        brand.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(20, 24, 20, 20)
        bl.setSpacing(2)

        title = QLabel("MyGTS")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F6E56; letter-spacing: -0.5px;")
        sub = QLabel("Inventory Management")
        sub.setStyleSheet("font-size: 11px; color: #8C8A86; font-weight: 400;")

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #E0DDD8; border: none; margin-top: 12px;")

        bl.addWidget(title)
        bl.addWidget(sub)
        bl.addSpacing(12)
        bl.addWidget(sep)
        return brand

    def _make_user_footer(self) -> QWidget:
        user_wrap = QWidget()
        user_wrap.setObjectName("userSection")
        user_wrap.setStyleSheet("""
            #userSection { background: transparent; border-top: 0.5px solid #E0DDD8; }
        """)
        ul = QHBoxLayout(user_wrap)
        ul.setContentsMargins(16, 14, 16, 14)
        ul.setSpacing(10)

        avatar = QFrame()
        avatar.setFixedSize(34, 34)
        avatar.setObjectName("userAvatar")
        avatar.setStyleSheet("#userAvatar { background: #0F6E56; border-radius: 17px; }")
        al = QVBoxLayout(avatar)
        al.setAlignment(Qt.AlignCenter)
        al.setContentsMargins(0, 0, 0, 0)
        ai = QLabel("U")
        ai.setAlignment(Qt.AlignCenter)
        ai.setStyleSheet("font-size: 13px; font-weight: 600; color: #ffffff; background: transparent;")
        al.addWidget(ai)

        user_text = QVBoxLayout()
        user_text.setSpacing(3)
        self.sidebar_user_name = QLabel("User")
        self.sidebar_user_name.setStyleSheet("font-size: 13px; font-weight: 500; color: #1A1A1A; background: transparent;")
        self.sidebar_user_role = QLabel("Customer")
        self.sidebar_user_role.setObjectName("roleBadge")
        self._apply_role_badge_style("customer")

        user_text.addWidget(self.sidebar_user_name)
        user_text.addWidget(self.sidebar_user_role)

        ul.addWidget(avatar)
        ul.addLayout(user_text, 1)
        return user_wrap

    def _rebuild_nav(self):
        while self._nav_layout.count():
            item = self._nav_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._nav_items.clear()

        nav_data = _OWNER_NAV if self._current_role == "owner" else _CUSTOMER_NAV

        for key, label, badge in nav_data:
            item = _NavItem(key, label, badge)
            item.clicked.connect(self.navigate.emit)
            item.set_dark_mode(self._dark_mode)
            self._nav_layout.addWidget(item)
            self._nav_items[key] = item

        self._apply_active()

    def set_active(self, key: str):
        self._current_active = key
        self._apply_active()

    def update_badge(self, key: str, text):
        if key in self._nav_items:
            self._nav_items[key].update_badge(str(text))

    def set_role(self, role: str):
        self._current_role = role
        self._rebuild_nav()

    def set_user(self, name: str, role: str):
        self._current_role = role
        self.sidebar_user_name.setText(name)
        self.sidebar_user_role.setText("Pemilik Sanggar" if role == "owner" else "Customer")
        self._apply_role_badge_style(role)
        self._rebuild_nav()

    def _apply_active(self):
        for key, item in self._nav_items.items():
            item.set_active(key == self._current_active)

    def _apply_role_badge_style(self, role: str):
        color = "#BA7517" if role == "owner" else "#0F6E56"
        self.sidebar_user_role.setStyleSheet(f"""
            font-size: 10px; font-weight: 600; color: #ffffff;
            background: {color}; border-radius: 4px;
            padding: 2px 8px;
        """)

    def set_dark_mode(self, dark: bool):
        self._dark_mode = dark
        self._apply_theme()
        for item in self._nav_items.values():
            item.set_dark_mode(dark)

    def _apply_theme(self):
        if self._dark_mode:
            self.setStyleSheet("""
                #sidebar { background-color: #222220; border-right: 0.5px solid #333330; }
            """)
        else:
            self.setStyleSheet("""
                #sidebar { background-color: #F8F7F4; border-right: 0.5px solid #E0DDD8; }
            """)


# ─────────────────────────────────────────────────────────────────────────────
#  TOP BAR
# ─────────────────────────────────────────────────────────────────────────────

class TopBar(QFrame):
    logout_requested  = Signal()
    theme_toggled     = Signal(bool)   # True = dark mode

    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.setObjectName("topbar")
        self._dark_mode = False
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)

        self.title_label = QLabel("Beranda")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 13px; color: #6B6A66; padding: 0 8px;")
        layout.addWidget(self.user_label)

        # Tombol dark/light mode
        self.theme_btn = QPushButton("🌙 Dark")
        self.theme_btn.setFixedHeight(36)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        self.logout_btn = QPushButton("Log out")
        self.logout_btn.setObjectName("topIconBtn")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_btn)

        self._apply_theme()

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()
        self.theme_toggled.emit(self._dark_mode)

    def _apply_theme(self):
        if self._dark_mode:
            self.setStyleSheet("#topbar { background: #222220; border-bottom: 0.5px solid #333330; }")
            self.title_label.setStyleSheet("font-size: 22px; font-weight: 500; color: #E8E6E2; letter-spacing: -0.3px;")
            self.user_label.setStyleSheet("font-size: 13px; color: #8C8A86; padding: 0 8px;")
            btn_style = """
                QPushButton { background: #2A2A28; border: 0.5px solid #444442;
                    border-radius: 8px; font-size: 13px; color: #E8E6E2;
                    padding: 8px 16px; font-weight: 400; }
                QPushButton:hover { background: #333330; border-color: #1D9E75; color: #1D9E75; }
            """
            self.theme_btn.setText("☀️ Light")
            self.theme_btn.setStyleSheet(btn_style)
            self.logout_btn.setStyleSheet(btn_style)
        else:
            self.setStyleSheet("#topbar { background: #ffffff; border-bottom: 0.5px solid #E0DDD8; }")
            self.title_label.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
            self.user_label.setStyleSheet("font-size: 13px; color: #6B6A66; padding: 0 8px;")
            btn_style = """
                QPushButton { background: transparent; border: 0.5px solid #E0DDD8;
                    border-radius: 8px; font-size: 13px; color: #6B6A66;
                    padding: 8px 16px; font-weight: 400; }
                QPushButton:hover { background: #F8F7F4; border-color: #0F6E56; color: #0F6E56; }
            """
            self.theme_btn.setText("🌙 Dark")
            self.theme_btn.setStyleSheet(btn_style)
            self.logout_btn.setStyleSheet(btn_style)

    def set_title(self, text):
        self.title_label.setText(text)

    def set_user(self, name):
        self.user_label.setText(name)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyGTS — My Gangsar Treasure System")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self._dark_mode = False

        self._build_central()
        self._build_menu_bar()
        self._build_status_bar()
        self._show_login()

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self._navigate_by_name)
        self.sidebar.setVisible(False)

        right = QWidget()
        right.setObjectName("mainContent")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.topbar = TopBar()
        self.topbar.logout_requested.connect(self._on_logout)
        self.topbar.theme_toggled.connect(self._on_theme_toggle)
        self.topbar.setVisible(False)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #F8F7F4;")

        # Semua halaman
        self.login_page = LoginPage()
        self.login_page.login_successful.connect(self._on_login_success)

        self.dashboard_customer = DashboardCustomer()
        self.dashboard_customer.navigate_to.connect(self._navigate_by_name)

        self.dashboard_owner = DashboardOwner()
        self.dashboard_owner.navigate_to.connect(self._navigate_by_name)

        self.add_customer_page = AddCustomerPage()
        self.add_customer_page.back_clicked.connect(self._go_to_owner_dashboard)
        self.add_customer_page.customer_added.connect(self._on_customer_added)

        self.owner_inventory_page = OwnerInventoryPage()
        if hasattr(self.owner_inventory_page, 'open_detail'):
            self.owner_inventory_page.open_detail.connect(self._open_item_detail)

        self.customer_inventory_page = CustomerInventoryPage()
        self.customer_inventory_page.open_detail.connect(self._open_item_detail)

        self.rental_page = RentalPage()
        self.rental_page.navigate_to.connect(self._navigate_by_name)

        self.history_page = HistoryPage()
        self.history_page.navigate_to.connect(self._navigate_by_name)

        self.item_detail_page = ItemDetailPage()
        self.item_detail_page.navigate_to.connect(self._navigate_by_name)

        self.confirm_rental_page = ConfirmRentalPage()
        self.confirm_rental_page.navigate_to.connect(self._navigate_by_name)
        self.confirm_rental_page.badge_updated.connect(self.sidebar.update_badge)

        self.confirm_return_page = ConfirmReturnPage()
        self.confirm_return_page.navigate_to.connect(self._navigate_by_name)

        self.notification_page = NotificationPage()
        self.notification_page.navigate_to.connect(self._navigate_by_name)

        # Urutan harus sesuai konstanta PAGE_*
        self.stack.addWidget(self.login_page)                # 0
        self.stack.addWidget(self.dashboard_customer)        # 1
        self.stack.addWidget(self.dashboard_owner)           # 2
        self.stack.addWidget(self.owner_inventory_page)      # 3
        self.stack.addWidget(self.rental_page)               # 4
        self.stack.addWidget(self.history_page)              # 5
        self.stack.addWidget(self.item_detail_page)          # 6
        self.stack.addWidget(self.confirm_rental_page)       # 7
        self.stack.addWidget(self.confirm_return_page)       # 8
        self.stack.addWidget(self.notification_page)         # 9
        self.stack.addWidget(self.customer_inventory_page)   # 10
        self.stack.addWidget(self.add_customer_page)         # 11

        right_layout.addWidget(self.topbar)
        right_layout.addWidget(self.stack, 1)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(right, 1)

    def _build_menu_bar(self):
        menu = self.menuBar()
        menu.setStyleSheet("""
            QMenuBar { background: #F8F7F4; padding: 2px 8px; font-size: 13px; }
            QMenuBar::item:selected { background: #0F6E56; color: white; border-radius: 4px; }
        """)

        # Menu File
        file_menu = menu.addMenu("File")
        action_export = QAction("Export Laporan CSV", self)
        action_export.setShortcut("Ctrl+E")
        action_export.triggered.connect(self._quick_export)
        file_menu.addAction(action_export)
        file_menu.addSeparator()
        action_exit = QAction("Keluar", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # Menu Tampilan
        view_menu = menu.addMenu("Tampilan")
        self.action_dark = QAction("Mode Gelap", self)
        self.action_dark.setCheckable(True)
        self.action_dark.triggered.connect(self._toggle_theme_from_menu)
        view_menu.addAction(self.action_dark)

        # Menu Bantuan
        help_menu = menu.addMenu("Bantuan")
        help_menu.addAction(QAction("Tentang MyGTS", self, triggered=self._show_about))
        help_menu.addAction(QAction("Cara Penggunaan", self, triggered=self._show_help))

    def _build_status_bar(self):
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("""
            font-size: 11px; color: #8C8A86;
            background: #F8F7F4;
            border-top: 0.5px solid #E0DDD8;
        """)
        self.setStatusBar(self._status_bar)
        self._update_status_bar("Belum masuk")

    def _update_status_bar(self, extra_info: str = ""):
        # Tampilkan nama & NIM semua anggota (tidak bisa diedit)
        anggota_str = "  |  ".join(
            f"{nama} ({nim})" for nama, nim in ANGGOTA
        )
        if extra_info:
            self._status_bar.showMessage(f"MyGTS  ·  {extra_info}  ·  {anggota_str}")
        else:
            self._status_bar.showMessage(f"MyGTS  ·  {anggota_str}")

    # ── Tema gelap / terang ─────────────────────────────────────────────────

    def _on_theme_toggle(self, dark: bool):
        self._dark_mode = dark
        self._apply_app_theme()
        self.action_dark.setChecked(dark)
        self.sidebar.set_dark_mode(dark)

    def _toggle_theme_from_menu(self, checked: bool):
        self._dark_mode = checked
        self._apply_app_theme()
        self.topbar._dark_mode = checked
        self.topbar._apply_theme()
        self.sidebar.set_dark_mode(checked)

    def _apply_app_theme(self):
        app = QApplication.instance()
        if self._dark_mode:
            app.setStyleSheet(DARK_THEME)
            self.stack.setStyleSheet("background: #1A1A1A;")
        else:
            app.setStyleSheet(LIGHT_THEME)
            self.stack.setStyleSheet("background: #F8F7F4;")
            # Reload QSS file jika ada
            import os
            style_path = os.path.join(os.path.dirname(__file__), "..", "assets", "qss", "style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r") as f:
                    extra = f.read()
                app.setStyleSheet(app.styleSheet() + extra)

    # ── Navigasi ─────────────────────────────────────────────────────────────

    def _show_login(self):
        self.sidebar.setVisible(False)
        self.topbar.setVisible(False)
        self.stack.setCurrentIndex(PAGE_LOGIN)
        self._update_status_bar("Silakan masuk")

    def _show_authenticated(self, user):
        self.sidebar.setVisible(True)
        self.topbar.setVisible(True)

        role = user.get("role", "customer")
        self.topbar.set_user(user['name'])
        self.sidebar.set_user(user['name'], role)
        self._update_status_bar(f"Masuk sebagai {user['name']} ({role})")

        if role == "owner":
            self.stack.setCurrentIndex(PAGE_DASHBOARD_OWNER)
            self.dashboard_owner.refresh()
            self.topbar.set_title("Dasbor Pemilik")
        else:
            self.stack.setCurrentIndex(PAGE_DASHBOARD_CUSTOMER)
            self.dashboard_customer.refresh()
            self.topbar.set_title("Beranda")

        self.sidebar.set_active("dashboard")

    def _on_login_success(self, user):
        self._show_authenticated(user)

    def _on_logout(self):
        auth_logout()
        self._show_login()

    def _go_to_owner_dashboard(self):
        """Kembali ke dashboard owner."""
        self._navigate_by_name("dashboard")

    def _on_customer_added(self):
        """Handle setelah customer berhasil ditambahkan."""
        # Bisa menambahkan notifikasi atau logic lain di sini
        pass

    def _navigate_by_name(self, name):
        cu = get_current_user()
        role = cu.get("role", "customer") if cu else self.sidebar._current_role

        if role == "owner":
            mapping = {
                "dashboard":     PAGE_DASHBOARD_OWNER,
                "inventory":     PAGE_INVENTORY_OWNER,
                "add_customer":  PAGE_ADD_CUSTOMER,
                "pending":       PAGE_CONFIRM_RENTAL,
                "returns":       PAGE_CONFIRM_RETURN,
                "add_item":      PAGE_INVENTORY_OWNER,
                "history":       PAGE_HISTORY,
                "notifications": PAGE_NOTIFICATIONS,
            }
        else:
            mapping = {
                "dashboard":     PAGE_DASHBOARD_CUSTOMER,
                "inventory":     PAGE_INVENTORY_CUSTOMER,
                "rental":        PAGE_RENTAL,
                "history":       PAGE_HISTORY,
                "notifications": PAGE_NOTIFICATIONS,
            }

        idx = mapping.get(name)
        if idx is None:
            return

        self.topbar.set_title(PAGE_NAMES.get(idx, ""))
        self.stack.setCurrentIndex(idx)
        self.sidebar.set_active(name)

        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    def _open_item_detail(self, item_id):
        self.item_detail_page.load_item(item_id)
        self.topbar.set_title("Detail Item")
        self.stack.setCurrentIndex(PAGE_ITEM_DETAIL)
        self.sidebar.set_active("inventory")

    # ── Export cepat dari menu ───────────────────────────────────────────────

    def _quick_export(self):
        cu = get_current_user()
        if not cu:
            QMessageBox.warning(self, "Belum Masuk", "Silakan masuk terlebih dahulu.")
            return
        try:
            from controllers.rental_controller import get_rentals_for_owner, get_rentals_for_customer
            from utils.export import export_csv
            if cu.get("role") == "owner":
                data = get_rentals_for_owner() or []
            else:
                data = get_rentals_for_customer(cu.get("id", "")) or []
            if not data:
                QMessageBox.information(self, "Export", "Tidak ada data untuk diekspor.")
                return
            filename = export_csv(data)
            QMessageBox.information(self, "Export Berhasil", f"Data disimpan ke:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Gagal", str(e))

    # ── Dialog ──────────────────────────────────────────────────────────────

    def _show_about(self):
        anggota_html = "".join(
            f"<li>{nama} &nbsp;—&nbsp; <b>{nim}</b></li>"
            for nama, nim in ANGGOTA
        )
        QMessageBox.about(
            self, "Tentang MyGTS",
            f"""<b>MyGTS — My Gangsar Treasure System</b><br><br>
Aplikasi manajemen inventaris sanggar budaya berbasis desktop.<br>
Dibangun dengan <b>PySide6</b> + <b>Supabase</b>.<br><br>
<b>Anggota Kelompok:</b>
<ul>{anggota_html}</ul>
<br>Mata Kuliah: Pemrograman Visual<br>
Universitas Mataram &nbsp;·&nbsp; 2025/2026"""
        )

    def _show_help(self):
        QMessageBox.information(
            self, "Cara Penggunaan",
            "<b>Login:</b><br>"
            "• Customer: customer@mygts.com / customer123<br>"
            "• Owner: owner@mygts.com / owner123<br><br>"
            "<b>Fitur Utama:</b><br>"
            "• Customer: Lihat inventaris, buat penyewaan, cek riwayat<br>"
            "• Owner: Kelola inventaris, konfirmasi sewa & kembali, lihat laporan<br><br>"
            "<b>Dark Mode:</b> Klik tombol 🌙 Dark di pojok kanan atas<br>"
            "<b>Export:</b> Menu File → Export Laporan CSV"
        )