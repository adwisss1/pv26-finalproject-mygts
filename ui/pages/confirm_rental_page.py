from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from controllers.rental_controller import (
    get_rentals_for_owner, confirm_rental, reject_rental, calculate_fine
)
from controllers.auth_controller import get_current_user


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


class RentalConfirmCard(QFrame):
    confirmed = Signal(str)
    rejected = Signal(str)

    def __init__(self, rental_data, mode):
        super().__init__()
        self._rental_id = rental_data.get("id", "")
        self._data = rental_data
        self._mode = mode  # "pending", "confirmed", "rejected"
        self.setObjectName("confirmCard")
        border_color = "#FFB347" if mode == "pending" else ("#0F6E56" if mode == "confirmed" else "#D4D2CD")
        self.setStyleSheet(f"""
            #confirmCard {{
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-left: 3px solid {border_color};
                border-radius: 12px;
            }}
        """)
        self._build(rental_data, mode)

    def _build(self, r, mode):
        inv_data = r.get("inventories") or {}
        user_data = r.get("users") or {}
        start = r.get("start_date", "")
        end = r.get("end_date", "")
        price = inv_data.get("price_per_day", 0)
        notes = r.get("notes", "")

        days = 0
        if start and end:
            from datetime import datetime
            try:
                sd = datetime.strptime(start, "%Y-%m-%d")
                ed = datetime.strptime(end, "%Y-%m-%d")
                days = max(1, (ed - sd).days)
            except ValueError:
                days = 0
        total = price * days

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        left_col = QVBoxLayout()
        left_col.setAlignment(Qt.AlignCenter)
        left_col.setSpacing(6)

        avatar = QFrame()
        avatar.setFixedSize(44, 44)
        avatar.setStyleSheet("background: #EDECE8; border-radius: 22px;")
        al = QVBoxLayout(avatar)
        al.setAlignment(Qt.AlignCenter)
        ai = QLabel(user_data.get("name", "?")[0].upper() if user_data.get("name") else "?")
        ai.setStyleSheet("font-size: 18px; font-weight: 600; color: #6B6A66; background: transparent;")
        al.addWidget(ai)
        left_col.addWidget(avatar, 0, Qt.AlignCenter)

        name_lbl = QLabel(user_data.get("name", "-"))
        name_lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #1A1A1A; background: transparent;")
        name_lbl.setAlignment(Qt.AlignCenter)
        left_col.addWidget(name_lbl)

        badge = QFrame()
        badge.setStyleSheet("background: #E8F0EE; border-radius: 4px;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(6, 2, 6, 2)
        bt = QLabel("Customer")
        bt.setStyleSheet("font-size: 10px; font-weight: 600; color: #0F6E56; background: transparent;")
        bl.addWidget(bt)
        left_col.addWidget(badge, 0, Qt.AlignCenter)

        left = QWidget()
        left.setLayout(left_col)
        left.setFixedWidth(80)

        center_col = QVBoxLayout()
        center_col.setSpacing(4)

        item_name = QLabel(inv_data.get("name", "-"))
        item_name.setStyleSheet("font-size: 15px; font-weight: 600; color: #1A1A1A; background: transparent;")
        center_col.addWidget(item_name)

        cat_lbl = QLabel(f"Kategori: {inv_data.get('category', '-')}")
        cat_lbl.setStyleSheet("font-size: 13px; color: #6B6A66; background: transparent;")
        center_col.addWidget(cat_lbl)

        dates_lbl = QLabel(f"Tgl Ambil: {start} | Kembali: {end}")
        dates_lbl.setStyleSheet("font-size: 13px; color: #6B6A66; background: transparent;")
        center_col.addWidget(dates_lbl)

        total_lbl = QLabel(f"Total: Rp {total:,}")
        total_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F6E56; background: transparent;")
        center_col.addWidget(total_lbl)

        if notes:
            notes_lbl = QLabel(f"Catatan: {notes}")
            notes_lbl.setStyleSheet("font-size: 12px; color: #A8A6A2; background: transparent;")
            notes_lbl.setWordWrap(True)
            center_col.addWidget(notes_lbl)

        thumbs_row = QHBoxLayout()
        thumbs_row.setSpacing(6)
        for _ in range(3):
            thumb = QFrame()
            thumb.setFixedSize(60, 60)
            thumb.setStyleSheet("background: #EDECE8; border: 0.5px solid #D4D2CD; border-radius: 6px;")
            tl = QVBoxLayout(thumb)
            tl.setAlignment(Qt.AlignCenter)
            ti = QLabel("\u2610")
            ti.setStyleSheet("font-size: 20px; color: #A8A6A2; background: transparent;")
            tl.addWidget(ti)
            thumbs_row.addWidget(thumb)
        center_col.addLayout(thumbs_row)

        center = QWidget()
        center.setLayout(center_col)

        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        right_col.setAlignment(Qt.AlignCenter)

        if mode == "pending":
            confirm_btn = QPushButton("\u2713 Konfirmasi")
            confirm_btn.setCursor(Qt.PointingHandCursor)
            confirm_btn.setFixedHeight(36)
            confirm_btn.setStyleSheet("""
                QPushButton {
                    background: #0F6E56; border: none; border-radius: 8px;
                    padding: 0 20px; font-size: 12px; font-weight: 600; color: #ffffff;
                }
                QPushButton:hover { background: #0A5A45; }
            """)
            confirm_btn.clicked.connect(lambda: self.confirmed.emit(self._rental_id))

            reject_btn = QPushButton("\u2717 Tolak")
            reject_btn.setCursor(Qt.PointingHandCursor)
            reject_btn.setFixedHeight(36)
            reject_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: 1px solid #E24B4A; border-radius: 8px;
                    padding: 0 20px; font-size: 12px; font-weight: 500; color: #E24B4A;
                }
                QPushButton:hover { background: #FDE8E8; }
            """)
            reject_btn.clicked.connect(lambda: self.rejected.emit(self._rental_id))

            right_col.addWidget(confirm_btn)
            right_col.addWidget(reject_btn)
        elif mode == "confirmed":
            confirmed_lbl = QLabel("Sudah Dikonfirmasi")
            confirmed_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1D9E75; background: transparent;")
            confirmed_lbl.setAlignment(Qt.AlignCenter)
            right_col.addWidget(confirmed_lbl)
        elif mode == "rejected":
            rejected_lbl = QLabel("Ditolak")
            rejected_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #E24B4A; background: transparent;")
            rejected_lbl.setAlignment(Qt.AlignCenter)
            right_col.addWidget(rejected_lbl)

        right = QWidget()
        right.setLayout(right_col)
        right.setFixedWidth(150)

        layout.addWidget(left)
        layout.addWidget(center, 1)
        layout.addWidget(right)


class ConfirmRentalPage(QWidget):
    navigate_to = Signal(str)
    badge_updated = Signal(str, str)  # key, count_text

    def __init__(self):
        super().__init__()
        self._current_tab = "pending"
        self._build_ui()

    def refresh(self):
        self._load_data()

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

        title = QLabel("Konfirmasi Penyewaan")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        layout.addWidget(title)

        self.tab_row = QHBoxLayout()
        self.tab_row.setSpacing(0)

        self.tab_buttons = {}
        for key, label in [("pending", "Menunggu Konfirmasi"), ("confirmed", "Sudah Dikonfirmasi"), ("rejected", "Ditolak")]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._switch_tab(k))
            self.tab_buttons[key] = btn
            self.tab_row.addWidget(btn)

        self.tab_row.addStretch()
        layout.addLayout(self.tab_row)

        self.cards_container = QVBoxLayout()
        self.cards_container.setSpacing(12)
        layout.addLayout(self.cards_container)

        self.empty_label = QLabel("")
        self.empty_label.setStyleSheet("font-size: 14px; color: #8C8A86; padding: 40px; background: transparent;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)

        scroll.setWidget(content)
        outer.addWidget(scroll)
        self._apply_tab_style()

    def _apply_tab_style(self):
        for key, btn in self.tab_buttons.items():
            is_active = key == self._current_tab
            btn.setStyleSheet(TAB_STYLES["active" if is_active else "inactive"])

    def _switch_tab(self, key):
        self._current_tab = key
        self._apply_tab_style()
        self._load_data()

    def _load_data(self):
        rentals = get_rentals_for_owner() or []
        self._all_rentals = rentals

        pending_count = sum(1 for r in rentals if r.get("status") == "pending")
        self.tab_buttons["pending"].setText(f"Menunggu Konfirmasi ({pending_count})")
        self.badge_updated.emit("pending", str(pending_count))

        status_map = {
            "pending": "pending",
            "confirmed": "confirmed",
            "rejected": "rejected",
        }
        target_status = status_map.get(self._current_tab, "pending")
        filtered = [r for r in rentals if r.get("status") == target_status]

        self._render_cards(filtered)

    def _render_cards(self, data):
        while self.cards_container.count():
            item = self.cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            self.empty_label.setVisible(True)
            msgs = {
                "pending": "Tidak ada penyewaan yang menunggu konfirmasi.",
                "confirmed": "Belum ada penyewaan yang dikonfirmasi.",
                "rejected": "Tidak ada penyewaan yang ditolak.",
            }
            self.empty_label.setText(msgs.get(self._current_tab, ""))
            return

        self.empty_label.setVisible(False)

        for r in data:
            card = RentalConfirmCard(r, self._current_tab)
            card.confirmed.connect(self._on_confirm)
            card.rejected.connect(self._on_reject)
            self.cards_container.addWidget(card)

    def _on_confirm(self, rental_id):
        ok = confirm_rental(rental_id)
        if ok:
            self._load_data()
        else:
            QMessageBox.warning(self, "Gagal", "Gagal mengkonfirmasi penyewaan.")

    def _on_reject(self, rental_id):
        reply = QMessageBox.question(
            self, "Konfirmasi", "Tolak penyewaan ini?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok = reject_rental(rental_id)
            if ok:
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal menolak penyewaan.")
