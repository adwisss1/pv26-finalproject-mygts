from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from controllers.rental_controller import get_rentals_for_owner, get_rentals_for_customer
from controllers.auth_controller import get_current_user, is_owner

NOTIF_ICONS = {
    "sewa": ("#0F6E56", "\u2610"),           # Kotak pesanan
    "konfirmasi": ("#1D9E75", "\u2713"),     # Centang
    "pengembalian": ("#BA7517", "\u21b6"),   # Panah kembali
    "denda": ("#E24B4A", "\u26a0"),          # Warning
}

TAB_STYLES = {
    "active": """
        QPushButton {
            background: transparent; border: none; border-bottom: 3px solid #0F6E56;
            font-size: 14px; font-weight: bold; color: #0F6E56; padding: 10px 16px;
        }
    """,
    "inactive": """
        QPushButton {
            background: transparent; border: none; border-bottom: 3px solid transparent;
            font-size: 14px; font-weight: bold; color: #8C8A86; padding: 10px 16px;
        }
        QPushButton:hover { color: #1A1A1A; }
    """,
}

class NotificationItem(QFrame):
    def __init__(self, notif_type, title, sub, timestamp, unread=True):
        super().__init__()
        bg, icon_char = NOTIF_ICONS.get(notif_type, ("#8C8A86", "\u2139"))

        self.setStyleSheet(f"""
            NotificationItem {{
                background: {"#F8FDFB" if unread else "transparent"};
                border-bottom: 1px solid #E0DDD8;
                border-left: 4px solid {"#0F6E56" if unread else "transparent"};
            }}
            NotificationItem:hover {{ background: {"#E8F7F2" if unread else "#FAFAF9"}; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        icon_frame = QFrame()
        icon_frame.setFixedSize(40, 40)
        icon_frame.setStyleSheet(f"background: {bg}; border-radius: 20px;")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        il.setContentsMargins(0,0,0,0)
        ic = QLabel(icon_char)
        ic.setStyleSheet("font-size: 18px; color: #ffffff; background: transparent;")
        il.addWidget(ic)

        if unread:
            dot = QLabel("\u25cf")
            dot.setStyleSheet("font-size: 12px; color: #E24B4A; background: transparent;")
            dot.setFixedWidth(16)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1A1A1A; background: transparent;")
        title_row.addWidget(title_lbl)
        if unread: title_row.addWidget(dot)
        title_row.addStretch()
        text_col.addLayout(title_row)

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet("font-size: 13px; color: #6B6A66; background: transparent;")
        text_col.addWidget(sub_lbl)

        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignTop | Qt.AlignRight)
        ts = QLabel(timestamp)
        ts.setStyleSheet("font-size: 12px; font-weight: bold; color: #A8A6A2; background: transparent;")
        right_col.addWidget(ts)

        layout.addWidget(icon_frame)
        layout.addLayout(text_col, 1)
        
        rw = QWidget()
        rw.setLayout(right_col)
        rw.setFixedWidth(120)
        layout.addWidget(rw)


class NotificationPage(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_tab = "all"
        self._notifications = []
        self._read_ids = set() # Menyimpan ID notifikasi yang sudah dibaca selama sesi berjalan
        self._build_ui()

    def refresh(self):
        self._load_data()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget(styleSheet="background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 16, 28, 28)
        layout.setSpacing(16)

        # ── Header & Tabs ──
        header_row = QHBoxLayout()
        
        self.tab_row = QHBoxLayout()
        self.tab_row.setSpacing(8)
        self.tab_buttons = {}
        for key, label in [("all", "Semua"), ("unread", "Belum Dibaca"), ("sewa", "Penyewaan"), ("pengembalian", "Pengembalian")]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._switch_tab(k))
            self.tab_buttons[key] = btn
            self.tab_row.addWidget(btn)
        
        header_row.addLayout(self.tab_row)
        header_row.addStretch()

        self.mark_read_btn = QPushButton("\u2713 Tandai semua dibaca")
        self.mark_read_btn.setCursor(Qt.PointingHandCursor)
        self.mark_read_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #D4D2CD; border-radius: 8px; font-size: 13px; font-weight: bold; color: #6B6A66; padding: 8px 16px; }
            QPushButton:hover { background: #F0EFEB; color: #1A1A1A; }
        """)
        self.mark_read_btn.clicked.connect(self._mark_all_read)
        header_row.addWidget(self.mark_read_btn)
        
        layout.addLayout(header_row)

        # ── Notification List Container ──
        self.card_frame = QFrame()
        self.card_frame.setStyleSheet("""
            QFrame { background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px; }
        """)
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(0)
        card_layout.addLayout(self.list_container)

        # Empty State
        self.empty_label = QLabel()
        self.empty_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #8C8A86; padding: 60px; border: none;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.empty_label)

        layout.addWidget(self.card_frame)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _load_data(self):
        user = get_current_user()
        if not user: return

        is_own = is_owner()
        raw_rentals = get_rentals_for_owner() if is_own else get_rentals_for_customer(user["id"])
        raw_rentals = raw_rentals or []

        notifs = []
        now_str = datetime.now().strftime("%Y-%m-%d")

        for r in raw_rentals:
            status, start, end = r.get("status", ""), r.get("start_date", ""), r.get("end_date", "")
            inv, u = r.get("inventories") or {}, r.get("users") or {}
            item_name, user_name = inv.get("name", "Barang"), u.get("name", "Customer")
            fine = r.get("fine_amount", 0)

            is_overdue = status in ("confirmed", "active") and end and end < now_str
            n_type, title = "sewa", ""
            sub = f"{item_name} — {start} s/d {end}"

            if is_own:
                if status == "pending":
                    n_type, title = "sewa", f"Permintaan sewa baru dari {user_name}"
                elif is_overdue:
                    n_type, title = "denda", f"Terlambat! {user_name} belum mengembalikan barang"
                    if fine > 0: sub += f" | Denda: Rp {fine:,.0f}".replace(",", ".")
                elif status in ("active", "confirmed"):
                    n_type, title = "konfirmasi", f"Penyewaan {item_name} oleh {user_name} disetujui"
                elif status == "returned":
                    n_type, title = "pengembalian", f"{user_name} telah mengembalikan {item_name}"
            else:
                if status == "pending":
                    n_type, title = "sewa", f"Penyewaan {item_name} sedang menunggu konfirmasi"
                elif is_overdue:
                    n_type, title = "denda", f"Peringatan! Pengembalian {item_name} telah lewat waktu"
                    if fine > 0: sub += f" | Denda: Rp {fine:,.0f}".replace(",", ".")
                elif status == "confirmed":
                    n_type, title = "konfirmasi", f"Penyewaan {item_name} dikonfirmasi. Silakan ambil."
                elif status == "active":
                    n_type, title = "konfirmasi", f"Masa sewa {item_name} sedang berjalan."
                elif status == "returned":
                    n_type, title = "pengembalian", f"Pengembalian {item_name} berhasil dikonfirmasi"

            if title:
                # Logika unread: jika rental pending atau overdue, anggap belum dibaca
                # Jika ID rental ini sudah pernah di-mark read, ubah jadi False
                is_unread = status == "pending" or is_overdue
                notif_id = f"{r.get('id')}_{status}" 
                
                if notif_id in self._read_ids:
                    is_unread = False

                notifs.append({
                    "id": notif_id, "type": n_type, "title": title,
                    "sub": sub, "ts": start, "unread": is_unread,
                    "date": r.get("created_at", start) # Untuk sorting
                })

        # Urutkan berdasarkan tanggal terbaru
        notifs.sort(key=lambda x: x["date"], reverse=True)
        self._notifications = notifs
        
        self._apply_tab_style()
        self._render_list()

    def _apply_tab_style(self):
        ucount = sum(1 for n in self._notifications if n.get("unread"))
        self.tab_buttons["unread"].setText(f"Belum Dibaca ({ucount})" if ucount > 0 else "Belum Dibaca")
        for key, btn in self.tab_buttons.items():
            btn.setStyleSheet(TAB_STYLES["active" if key == self._current_tab else "inactive"])

    def _switch_tab(self, key):
        self._current_tab = key
        self._apply_tab_style()
        self._render_list()

    def _render_list(self):
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        filtered = self._notifications
        if self._current_tab == "unread":
            filtered = [n for n in filtered if n.get("unread")]
        elif self._current_tab == "sewa":
            filtered = [n for n in filtered if n.get("type") in ("sewa", "konfirmasi")]
        elif self._current_tab == "pengembalian":
            filtered = [n for n in filtered if n.get("type") in ("pengembalian", "denda")]

        if not filtered:
            self.empty_label.setVisible(True)
            self.empty_label.setText(f"\U0001f514\n\nTidak ada notifikasi di kategori '{self.tab_buttons[self._current_tab].text()}'.")
            self.card_frame.setStyleSheet("QFrame { background: transparent; border: 1.5px dashed #D4D2CD; border-radius: 12px; }")
            return

        self.empty_label.setVisible(False)
        self.card_frame.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px; }")
        
        for n in filtered:
            item = NotificationItem(n["type"], n["title"], n["sub"], n["ts"], unread=n.get("unread", False))
            self.list_container.addWidget(item)

    def _mark_all_read(self):
        for n in self._notifications:
            n["unread"] = False
            self._read_ids.add(n["id"]) # Simpan state ke set lokal
            
        self._apply_tab_style()
        self._render_list()