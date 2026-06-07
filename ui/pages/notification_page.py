from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal


NOTIF_ICONS = {
    "sewa": ("#0F6E56", "\u2610"),
    "konfirmasi": ("#1D9E75", "\u2713"),
    "pengembalian": ("#BA7517", "\u21b6"),
    "denda": ("#E24B4A", "\u26a0"),
}

TAB_STYLES = {
    "active": """
        QPushButton {
            background: transparent; border: none; border-bottom: 2px solid #0F6E56;
            font-size: 14px; font-weight: 600; color: #0F6E56; padding: 8px 16px;
        }
    """,
    "inactive": """
        QPushButton {
            background: transparent; border: none; border-bottom: 2px solid transparent;
            font-size: 14px; font-weight: 400; color: #8C8A86; padding: 8px 16px;
        }
        QPushButton:hover { color: #1A1A1A; }
    """,
}


class NotificationItem(QFrame):
    def __init__(self, notif_type, title, sub, timestamp, unread=True):
        super().__init__()
        bg, icon_char = NOTIF_ICONS.get(notif_type, ("#8C8A86", "\u2139"))

        self.setObjectName("notifRow")
        self.setStyleSheet(f"""
            #notifRow {{
                background: #ffffff;
                border-bottom: 0.5px solid #EDECE8;
                border-left: 3px solid {"#0F6E56" if unread else "transparent"};
                background-color: {"#F4F9F8" if unread else "#ffffff"};
            }}
            #notifRow:hover {{
                background-color: {"#EDF4F2" if unread else "#FAF9F6"};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet(f"background: {bg}; border-radius: 18px;")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        ic = QLabel(icon_char)
        ic.setStyleSheet("font-size: 16px; color: #ffffff; background: transparent;")
        il.addWidget(ic)

        if unread:
            dot = QLabel("\u25cf")
            dot.setStyleSheet("font-size: 10px; color: #3B82F6; background: transparent;")
            dot.setFixedWidth(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A; background: transparent;")
        title_row.addWidget(title_lbl)
        if unread:
            title_row.addWidget(dot)
        title_row.addStretch()
        text_col.addLayout(title_row)

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet("font-size: 13px; color: #8C8A86; background: transparent;")
        text_col.addWidget(sub_lbl)

        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignTop | Qt.AlignRight)
        ts = QLabel(timestamp)
        ts.setStyleSheet("font-size: 12px; color: #A8A6A2; background: transparent;")
        right_col.addWidget(ts)

        layout.addWidget(icon_frame)
        layout.addLayout(text_col, 1)
        rw = QWidget()
        rw.setLayout(right_col)
        rw.setFixedWidth(100)
        layout.addWidget(rw)


MOCK_NOTIFS = [
    {"type": "sewa", "title": "Permintaan penyewaan diterima oleh pemilik sanggar",
     "sub": "Kebaya Merah — 10 Jun 2025", "ts": "5 menit yang lalu", "unread": True},
    {"type": "konfirmasi", "title": "Penyewaan Kebaya Merah dikonfirmasi. Silakan ambil barang.",
     "sub": "Ambil sebelum 10 Jun 2025 pukul 16:00", "ts": "2 jam yang lalu", "unread": True},
    {"type": "pengembalian", "title": "Pengingat: Pengembalian Anda jatuh tempo besok",
     "sub": "Kebaya Merah — tenggat 15 Jun 2025", "ts": "5 jam yang lalu", "unread": True},
    {"type": "denda", "title": "Terlambat! Denda keterlambatan telah dihitung: Rp 25.000",
     "sub": "Kebaya Merah — terlambat 2 hari", "ts": "1 hari yang lalu", "unread": True},
    {"type": "sewa", "title": "Penyewaan baru oleh Ani menunggu konfirmasi",
     "sub": "Batik Tulis — 12 Jun 2025", "ts": "1 hari yang lalu", "unread": False},
    {"type": "konfirmasi", "title": "Pengembalian Kebaya Merah telah dikonfirmasi",
     "sub": "Dikembalikan tepat waktu — tidak ada denda", "ts": "3 hari yang lalu", "unread": False},
    {"type": "pengembalian", "title": "Barang berhasil dikembalikan ke sanggar",
     "sub": "Batik Tulis — kondisi baik", "ts": "5 hari yang lalu", "unread": False},
]


class NotificationPage(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_tab = "all"
        self._notifications = list(MOCK_NOTIFS)
        self._build_ui()

    def refresh(self):
        pass

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

        header = QHBoxLayout()
        title = QLabel("Notifikasi")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        header.addWidget(title)
        header.addStretch()

        self.mark_read_btn = QPushButton("Tandai semua sudah dibaca")
        self.mark_read_btn.setCursor(Qt.PointingHandCursor)
        self.mark_read_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 12px; font-weight: 500; color: #0F6E56;
                padding: 4px 0;
            }
            QPushButton:hover { color: #0A5A45; }
        """)
        self.mark_read_btn.clicked.connect(self._mark_all_read)
        header.addWidget(self.mark_read_btn)

        layout.addLayout(header)

        self.tab_row = QHBoxLayout()
        self.tab_row.setSpacing(0)

        self.tab_buttons = {}
        for key, label in [
            ("all", "Semua"),
            ("unread", "Belum Dibaca"),
            ("sewa", "Penyewaan"),
            ("pengembalian", "Pengembalian"),
        ]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._switch_tab(k))
            self.tab_buttons[key] = btn
            self.tab_row.addWidget(btn)

        self.tab_row.addStretch()
        layout.addLayout(self.tab_row)
        self._apply_tab_style()

        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(0)
        layout.addLayout(self.list_container)

        self.empty_label = QLabel("")
        self.empty_label.setStyleSheet("font-size: 14px; color: #8C8A86; padding: 40px; background: transparent;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._render_list()

    def _apply_tab_style(self):
        ucount = sum(1 for n in self._notifications if n.get("unread"))
        self.tab_buttons["unread"].setText(f"Belum Dibaca ({ucount})" if ucount > 0 else "Belum Dibaca")
        for key, btn in self.tab_buttons.items():
            is_active = key == self._current_tab
            btn.setStyleSheet(TAB_STYLES["active" if is_active else "inactive"])

    def _switch_tab(self, key):
        self._current_tab = key
        self._apply_tab_style()
        self._render_list()

    def _render_list(self):
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = list(self._notifications)
        if self._current_tab == "unread":
            filtered = [n for n in filtered if n.get("unread")]
        elif self._current_tab == "sewa":
            filtered = [n for n in filtered if n.get("type") in ("sewa", "konfirmasi")]
        elif self._current_tab == "pengembalian":
            filtered = [n for n in filtered if n.get("type") in ("pengembalian", "denda")]

        if not filtered:
            self.empty_label.setVisible(True)
            self.empty_label.setText("Tidak ada notifikasi.")
            return

        self.empty_label.setVisible(False)
        for n in filtered:
            item = NotificationItem(
                n["type"], n["title"], n["sub"], n["ts"],
                unread=n.get("unread", False)
            )
            self.list_container.addWidget(item)

    def _mark_all_read(self):
        for n in self._notifications:
            n["unread"] = False
        self._apply_tab_style()
        self._render_list()
