from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStatusBar, QFrame,
    QMessageBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QFont, QPixmap, QPainter, QColor

from ui.pages.login_page import LoginPage
from ui.pages.dashboard_customer import DashboardCustomer
from ui.pages.dashboard_owner import DashboardOwner
from ui.pages.inventory_page import InventoryPage
from ui.pages.rental_page import RentalPage
from ui.pages.history_page import HistoryPage
from ui.pages.item_detail_page import ItemDetailPage
from ui.pages.confirm_rental_page import ConfirmRentalPage
from ui.pages.confirm_return_page import ConfirmReturnPage
from ui.pages.notification_page import NotificationPage

from controllers.auth_controller import get_current_user, logout as auth_logout, is_owner

PAGE_LOGIN = 0
PAGE_DASHBOARD_CUSTOMER = 1
PAGE_DASHBOARD_OWNER = 2
PAGE_INVENTORY = 3
PAGE_RENTAL = 4
PAGE_HISTORY = 5
PAGE_ITEM_DETAIL = 6
PAGE_CONFIRM_RENTAL = 7
PAGE_CONFIRM_RETURN = 8
PAGE_NOTIFICATIONS = 9

PAGE_NAMES = {
    PAGE_DASHBOARD_CUSTOMER: "Beranda",
    PAGE_DASHBOARD_OWNER: "Dasbor Pemilik",
    PAGE_INVENTORY: "Kelola Inventaris",
    PAGE_RENTAL: "Penyewaan Saya",
    PAGE_HISTORY: "Laporan & Riwayat",
    PAGE_ITEM_DETAIL: "Detail Item",
    PAGE_CONFIRM_RENTAL: "Konfirmasi Penyewaan",
    PAGE_CONFIRM_RETURN: "Konfirmasi Pengembalian",
    PAGE_NOTIFICATIONS: "Notifikasi",
}


class Sidebar(QFrame):
    navigate = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_active = None
        self._current_role = "customer"
        self.setFixedWidth(220)
        self.setObjectName("sidebar")
        self._nav_container = None
        self._cta_wrap = None
        self._build()

    def _build(self):
        self.setStyleSheet("""
            #sidebar {
                background-color: #F8F7F4;
                border-right: 0.5px solid #E0DDD8;
            }
        """)
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        brand = QWidget()
        brand.setStyleSheet("background: transparent; padding: 0;")
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(20, 24, 20, 24)
        bl.setSpacing(2)
        title = QLabel("MyGTS")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F6E56; letter-spacing: -0.5px;")
        sub = QLabel("Inventory Management")
        sub.setStyleSheet("font-size: 12px; color: #8C8A86; font-weight: 400;")
        bl.addWidget(title)
        bl.addWidget(sub)

        sep = QFrame()
        sep.setFixedHeight(0.5)
        sep.setStyleSheet("background: #E0DDD8; border: none;")
        bl.addSpacing(12)
        bl.addWidget(sep)

        self._main_layout.addWidget(brand)

        self._nav_container = QWidget()
        self._nav_container.setStyleSheet("background: transparent;")
        self._nav_layout = QVBoxLayout(self._nav_container)
        self._nav_layout.setContentsMargins(12, 12, 12, 12)
        self._nav_layout.setSpacing(2)
        self._main_layout.addWidget(self._nav_container)

        self._main_layout.addStretch()

        self._cta_wrap = QWidget()
        self._cta_wrap.setStyleSheet("padding: 0 16px 16px; background: transparent;")
        self._cta_layout = QVBoxLayout(self._cta_wrap)
        self._cta_layout.setContentsMargins(0, 0, 0, 0)
        self.cta_btn = QPushButton("+ Sewa Baru")
        self.cta_btn.setObjectName("ctaBtn")
        self.cta_btn.setCursor(Qt.PointingHandCursor)
        self.cta_btn.setFixedHeight(42)
        self.cta_btn.clicked.connect(lambda: self.navigate.emit(self._cta_target or "rental"))
        self._cta_layout.addWidget(self.cta_btn)
        self._main_layout.addWidget(self._cta_wrap)

        user_wrap = QWidget()
        user_wrap.setObjectName("userSection")
        user_wrap.setStyleSheet("""
            #userSection {
                background: transparent;
                border-top: 0.5px solid #E0DDD8;
                padding: 16px 20px;
            }
        """)
        ul = QHBoxLayout(user_wrap)
        ul.setContentsMargins(20, 16, 20, 16)
        ul.setSpacing(12)

        avatar = QFrame()
        avatar.setFixedSize(36, 36)
        avatar.setObjectName("userAvatar")
        avatar.setStyleSheet("""
            #userAvatar {
                background: #0F6E56; border-radius: 18px;
            }
        """)
        al = QVBoxLayout(avatar)
        al.setAlignment(Qt.AlignCenter)
        ai = QLabel("U")
        ai.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff; background: transparent;")
        al.addWidget(ai)

        user_text = QVBoxLayout()
        user_text.setSpacing(1)
        self.sidebar_user_name = QLabel("User")
        self.sidebar_user_name.setStyleSheet("font-size: 13px; font-weight: 500; color: #1A1A1A; background: transparent;")
        self.sidebar_user_role = QLabel("Customer")
        self.sidebar_user_role.setObjectName("roleBadge")

        user_text.addWidget(self.sidebar_user_name)
        user_text.addWidget(self.sidebar_user_role)

        ul.addWidget(avatar)
        ul.addLayout(user_text, 1)
        self._main_layout.addWidget(user_wrap)

        self._rebuild_nav()

    def _rebuild_nav(self):
        while self._nav_layout.count():
            item = self._nav_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._nav_buttons = {}
        self._nav_badges = {}
        self._cta_target = None

        if self._current_role == "owner":
            owner_items = [
                ("dashboard", "Dasbor"),
                ("inventory", "Kelola Inventaris"),
                ("pending", "Konfirmasi Penyewaan", "3"),
                ("returns", "Konfirmasi Pengembalian"),
                ("history", "Laporan & Riwayat"),
                ("notifications", "Notifikasi"),
            ]
            for entry in owner_items:
                key = entry[0]
                label = entry[1]
                badge_text = entry[2] if len(entry) > 2 else None

                btn = QPushButton(f"  {label}")
                btn.setObjectName("navBtn")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFixedHeight(40)
                btn.clicked.connect(lambda checked, k=key: self.navigate.emit(k))
                self._nav_layout.addWidget(btn)
                self._nav_buttons[key] = btn

                if badge_text:
                    badge = QLabel(badge_text)
                    badge.setFixedSize(20, 20)
                    badge.setAlignment(Qt.AlignCenter)
                    badge.setStyleSheet("""
                        font-size: 10px; font-weight: 700; color: #ffffff;
                        background: #E24B4A; border-radius: 10px;
                    """)
                    b_layout = QHBoxLayout()
                    b_layout.setContentsMargins(0, 0, 16, 0)
                    b_layout.addStretch()
                    b_layout.addWidget(badge)
                    btn.setLayout(b_layout)
                    self._nav_badges[key] = badge

            self.cta_btn.setText("+ Tambah Barang")
            self._cta_target = "add_item"

        else:
            customer_items = [
                ("dashboard", "Beranda"),
                ("inventory", "Lihat Inventaris"),
                ("rental", "Penyewaan Saya"),
                ("history", "Riwayat Sewa"),
                ("notifications", "Notifikasi"),
            ]
            for key, label in customer_items:
                btn = QPushButton(f"  {label}")
                btn.setObjectName("navBtn")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFixedHeight(40)
                btn.clicked.connect(lambda checked, k=key: self.navigate.emit(k))
                self._nav_layout.addWidget(btn)
                self._nav_buttons[key] = btn

            self.cta_btn.setText("+ Sewa Baru")
            self._cta_target = "rental"

        self.apply_nav_style()

    def apply_nav_style(self):
        btn_style = """
            QPushButton#navBtn {
                background: transparent; border: none; border-radius: 8px;
                font-size: 14px; font-weight: 400; color: #6B6A66;
                padding-left: 16px; text-align: left;
            }
            QPushButton#navBtn:hover {
                background: #EDECE8; color: #1A1A1A;
            }
        """
        active_style = """
            QPushButton#navBtn {
                background: #E8F0EE; border-left: 3px solid #0F6E56;
                border-radius: 0 8px 8px 0;
                font-size: 14px; font-weight: 500; color: #0F6E56;
                padding-left: 13px; text-align: left;
            }
            QPushButton#navBtn:hover {
                background: #DCE8E4; color: #0F6E56;
            }
        """
        cta_style = """
            QPushButton#ctaBtn {
                background: #0F6E56; border: none; border-radius: 8px;
                font-size: 13px; font-weight: 600; color: #ffffff;
            }
            QPushButton#ctaBtn:hover { background: #0A5A45; }
        """
        for key, btn in self._nav_buttons.items():
            is_active = key == self._current_active
            btn.setStyleSheet(active_style if is_active else btn_style)
        self.cta_btn.setStyleSheet(cta_style)

    def set_active(self, key):
        self._current_active = key
        self.apply_nav_style()

    def update_badge(self, key, text):
        if key in self._nav_badges:
            self._nav_badges[key].setText(str(text))
            self._nav_badges[key].setVisible(int(text) > 0)

    def set_role(self, role):
        self._current_role = role
        self._rebuild_nav()

    def set_user(self, name, role):
        self._current_role = role
        self.sidebar_user_name.setText(name)
        role_text = "Pemilik Sanggar" if role == "owner" else "Customer"
        self.sidebar_user_role.setText(role_text)
        if role == "owner":
            self.sidebar_user_role.setStyleSheet("""
                font-size: 10px; font-weight: 600; color: #ffffff;
                background: #BA7517; border-radius: 4px;
                padding: 2px 8px; max-height: 18px;
            """)
        else:
            self.sidebar_user_role.setStyleSheet("""
                font-size: 10px; font-weight: 600; color: #ffffff;
                background: #0F6E56; border-radius: 4px;
                padding: 2px 8px; max-height: 18px;
            """)
        self._rebuild_nav()


class TopBar(QFrame):
    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.setObjectName("topbar")
        self._build()

    def _build(self):
        self.setStyleSheet("""
            #topbar {
                background: #ffffff;
                border-bottom: 0.5px solid #E0DDD8;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)

        self.title_label = QLabel("Beranda")
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;"
        )
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

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #F8F7F4;")

        self.login_page = LoginPage()
        self.login_page.login_successful.connect(self._on_login_success)

        self.dashboard_customer = DashboardCustomer()
        self.dashboard_customer.navigate_to.connect(self._navigate_by_name)

        self.dashboard_owner = DashboardOwner()
        self.dashboard_owner.navigate_to.connect(self._navigate_by_name)

        self.inventory_page = InventoryPage()
        self.inventory_page.open_detail.connect(self._open_item_detail)
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

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.dashboard_customer)
        self.stack.addWidget(self.dashboard_owner)
        self.stack.addWidget(self.inventory_page)
        self.stack.addWidget(self.rental_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.item_detail_page)
        self.stack.addWidget(self.confirm_rental_page)
        self.stack.addWidget(self.confirm_return_page)
        self.stack.addWidget(self.notification_page)

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
                "dashboard": PAGE_DASHBOARD_OWNER,
                "inventory": PAGE_INVENTORY,
                "pending": PAGE_CONFIRM_RENTAL,
                "returns": PAGE_CONFIRM_RETURN,
                "add_item": PAGE_INVENTORY,
                "history": PAGE_HISTORY,
                "notifications": PAGE_NOTIFICATIONS,
            }
        else:
            mapping = {
                "dashboard": PAGE_DASHBOARD_CUSTOMER,
                "inventory": PAGE_INVENTORY,
                "rental": PAGE_RENTAL,
                "history": PAGE_HISTORY,
                "notifications": PAGE_NOTIFICATIONS,
            }

        idx = mapping.get(name)
        if idx is None:
            return

        page_name = PAGE_NAMES.get(idx, "")
        self.topbar.set_title(page_name)
        self.stack.setCurrentIndex(idx)
        self.sidebar.set_active(name)

        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    def _open_item_detail(self, item_id):
        self.item_detail_page.load_item(item_id)
        self.topbar.set_title("Item Detail")
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
