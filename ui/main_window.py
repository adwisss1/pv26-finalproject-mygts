from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStatusBar, QFrame,
    QMessageBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QFont, QPixmap, QPainter, QColor

from ui.pages.login_page import LoginPage
from ui.pages.customer.dashboard_customer import DashboardCustomer
from ui.pages.owner.dashboard_owner import DashboardOwner

from ui.pages.owner.inventory_page import InventoryPage as OwnerInventoryPage
from ui.pages.customer.inventory_page import InventoryPage as CustomerInventoryPage

from ui.pages.customer.rental_page import RentalPage
from ui.pages.customer.history_page import HistoryPage
from ui.pages.item_detail_page import ItemDetailPage
from ui.pages.owner.confirm_rental_page import ConfirmRentalPage
from ui.pages.owner.confirm_return_page import ConfirmReturnPage
from ui.pages.notification_page import NotificationPage

from controllers.auth_controller import get_current_user, logout as auth_logout, is_owner

# Definisikan indeks halaman agar tidak tabrakan
PAGE_LOGIN = 0
PAGE_DASHBOARD_CUSTOMER = 1
PAGE_DASHBOARD_OWNER = 2
PAGE_INVENTORY_OWNER = 3
PAGE_RENTAL = 4
PAGE_HISTORY = 5
PAGE_ITEM_DETAIL = 6
PAGE_CONFIRM_RENTAL = 7
PAGE_CONFIRM_RETURN = 8
PAGE_NOTIFICATIONS = 9
PAGE_INVENTORY_CUSTOMER = 10  # <-- Tambahan indeks khusus Customer

PAGE_NAMES = {
    PAGE_DASHBOARD_CUSTOMER: "Beranda",
    PAGE_DASHBOARD_OWNER: "Dashboard",
    PAGE_INVENTORY_OWNER: "Kelola Inventaris",
    PAGE_INVENTORY_CUSTOMER: "Lihat Inventaris",
    PAGE_RENTAL: "Penyewaan Saya",
    PAGE_HISTORY: "Laporan & Riwayat",
    PAGE_ITEM_DETAIL: "Detail Item",
    PAGE_CONFIRM_RENTAL: "Konfirmasi Penyewaan",
    PAGE_CONFIRM_RETURN: "Konfirmasi Pengembalian",
    PAGE_NOTIFICATIONS: "Notifikasi",
}

# ─────────────────────────────────────────────────────────────────────────────
#  NAV ITEM  — satu baris (ikon-huruf + badge opsional) yang rapi
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

    def __init__(self, key: str, label: str, badge_text: str = None, parent=None):
        super().__init__(parent)
        self._key = key
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
        self._btn.setStyleSheet(self._STYLE_ACTIVE if active else self._STYLE_NORMAL)

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
    ("dashboard",   "Dashboard",                  None),
    ("inventory",   "Kelola Inventaris",        None),
    ("pending",     "Konfirmasi Penyewaan",    "3"),
    ("returns",     "Konfirmasi Pengembalian",  None),
    ("history",     "Laporan & Riwayat",        None),
    ("notifications","Notifikasi",              None),
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
        self._cta_target: str | None = None

        self.setFixedWidth(220)
        self.setObjectName("sidebar")
        self.setStyleSheet("""
            #sidebar {
                background-color: #F8F7F4;
                border-right: 0.5px solid #E0DDD8;
            }
        """)
        self._build()

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
        title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #0F6E56; letter-spacing: -0.5px;"
        )
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
            #userSection {
                background: transparent;
                border-top: 0.5px solid #E0DDD8;
            }
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

        if self._current_role == "owner":
            nav_data = _OWNER_NAV
        else:
            nav_data = _CUSTOMER_NAV

        for key, label, badge in nav_data:
            item = _NavItem(key, label, badge)
            item.clicked.connect(self.navigate.emit)
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


# ─────────────────────────────────────────────────────────────────────────────
#  TOP BAR
# ─────────────────────────────────────────────────────────────────────────────

class TopBar(QFrame):
    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.setObjectName("topbar")
        self._build()

    def _build(self):
        self.setStyleSheet("""
            #topbar { background: #ffffff; border-bottom: 0.5px solid #E0DDD8; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)

        self.title_label = QLabel("Beranda")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 13px; color: #6B6A66; padding: 0 8px;")
        layout.addWidget(self.user_label)

        icon_style = """
            QPushButton {
                background: transparent; border: 0.5px solid #E0DDD8;
                border-radius: 8px; font-size: 13px; color: #6B6A66;
                padding: 8px 16px; font-weight: 400;
            }
            QPushButton:hover { background: #F8F7F4; border-color: #0F6E56; color: #0F6E56; }
        """
        self.logout_btn = QPushButton("Log out")
        self.logout_btn.setObjectName("topIconBtn")
        self.logout_btn.setStyleSheet(icon_style)
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_btn)

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

        self._pages_initialized = False
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
        self.topbar.setVisible(False)

        # Inisiasi QStackedWidget HANYA SEKALI
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #F8F7F4;")

        # Inisiasi semua halaman
        self.login_page = LoginPage()
        self.login_page.login_successful.connect(self._on_login_success)

        self.dashboard_customer = DashboardCustomer()
        self.dashboard_customer.navigate_to.connect(self._navigate_by_name)

        self.dashboard_owner = DashboardOwner()
        self.dashboard_owner.navigate_to.connect(self._navigate_by_name)

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

        # Masukkan ke stack SESUAI URUTAN INDEKS PAGE_*
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
        file_menu = menu.addMenu("File")
        file_menu.addAction(QAction("Keluar", self, triggered=self.close))
        help_menu = menu.addMenu("Bantuan")
        help_menu.addAction(QAction("Tentang MyGTS", self, triggered=self._show_about))

    def _build_status_bar(self):
        status = QStatusBar()
        status.setStyleSheet("font-size: 11px; color: #8C8A86; background: #F8F7F4; border-top: 0.5px solid #E0DDD8;")
        self.setStatusBar(status)

    def _show_login(self):
        self.sidebar.setVisible(False)
        self.topbar.setVisible(False)
        self.stack.setCurrentIndex(PAGE_LOGIN)

    def _show_authenticated(self, user):
        self.sidebar.setVisible(True)
        self.topbar.setVisible(True)

        role = user.get("role", "customer")
        self.topbar.set_user(f"{user['name']}")
        self.sidebar.set_user(user['name'], role)

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

    def _navigate_by_name(self, name):
        cu = get_current_user()
        role = cu.get("role", "customer") if cu else self.sidebar._current_role

        if role == "owner":
            mapping = {
                "dashboard":     PAGE_DASHBOARD_OWNER,
                "inventory":     PAGE_INVENTORY_OWNER,  # Owner pakai Inventory Owner
                "pending":       PAGE_CONFIRM_RENTAL,
                "returns":       PAGE_CONFIRM_RETURN,
                "add_item":      PAGE_INVENTORY_OWNER,
                "history":       PAGE_HISTORY,
                "notifications": PAGE_NOTIFICATIONS,
            }
        else:
            mapping = {
                "dashboard":     PAGE_DASHBOARD_CUSTOMER,
                "inventory":     PAGE_INVENTORY_CUSTOMER, # Customer pakai Inventory Customer
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

    def _show_about(self):
        QMessageBox.about(
            self, "Tentang MyGTS",
            "<b>MyGTS — My Gangsar Treasure System</b><br><br>"
            "Aplikasi manajemen inventaris sanggar berbasis desktop.<br>"
            "Dibangun dengan PySide6 + Supabase.<br><br>"
            "Anggota Kelompok:<br>"
        )