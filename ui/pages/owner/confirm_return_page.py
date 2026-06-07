from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from controllers.rental_controller import (
    get_rentals_for_owner, process_return, calculate_fine
)
from controllers.auth_controller import get_current_user


class ReturnConfirmCard(QFrame):
    return_confirmed = Signal(str)

    def __init__(self, rental_data):
        super().__init__()
        self._rental_id = rental_data.get("id", "")
        self._data = rental_data
        self.setObjectName("returnCard")
        self.setStyleSheet("""
            #returnCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-left: 3px solid #0F6E56;
                border-radius: 12px;
            }
        """)
        self._build(rental_data)

    def _build(self, r):
        inv_data = r.get("inventories") or {}
        user_data = r.get("users") or {}
        start = r.get("start_date", "")
        end = r.get("end_date", "")
        price = inv_data.get("price_per_day", 0)

        days = 0
        if start and end:
            try:
                sd = datetime.strptime(start, "%Y-%m-%d")
                ed = datetime.strptime(end, "%Y-%m-%d")
                days = max(1, (ed - sd).days)
            except ValueError:
                days = 0
        total = price * days

        now = datetime.now().strftime("%Y-%m-%d")
        is_late = end and end < now
        late_days = 0
        if end:
            try:
                ed = datetime.strptime(end, "%Y-%m-%d")
                nd = datetime.strptime(now, "%Y-%m-%d")
                late_days = max(0, (nd - ed).days)
            except ValueError:
                pass
        fine = calculate_fine(end, now) if is_late else 0

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

        dates_lbl = QLabel(f"Tgl Ambil: {start} | Tenggat: {end}")
        dates_lbl.setStyleSheet("font-size: 13px; color: #6B6A66; background: transparent;")
        center_col.addWidget(dates_lbl)

        total_lbl = QLabel(f"Total Sewa: Rp {total:,}")
        total_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F6E56; background: transparent;")
        center_col.addWidget(total_lbl)

        fine_section = QFrame()
        if is_late:
            fine_section.setStyleSheet("background: #FDE8E8; border-radius: 6px; padding: 8px 12px;")
            fine_layout = QHBoxLayout(fine_section)
            fine_layout.setContentsMargins(12, 8, 12, 8)
            fn = QLabel(f"Terlambat {late_days} hari \u2014 Denda: Rp {fine:,}")
            fn.setStyleSheet("font-size: 13px; font-weight: 600; color: #E24B4A; background: transparent;")
            fine_layout.addWidget(fn)
        else:
            fine_section.setStyleSheet("background: #E8F7F2; border-radius: 6px; padding: 8px 12px;")
            fine_layout = QHBoxLayout(fine_section)
            fine_layout.setContentsMargins(12, 8, 12, 8)
            fn = QLabel("Dikembalikan tepat waktu")
            fn.setStyleSheet("font-size: 13px; font-weight: 600; color: #1D9E75; background: transparent;")
            fine_layout.addWidget(fn)
        center_col.addWidget(fine_section)

        thumbs_label = QLabel("Foto Pengembalian:")
        thumbs_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #6B6A66; background: transparent;")
        center_col.addWidget(thumbs_label)

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

        confirm_btn = QPushButton("Konfirmasi Pengembalian")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setFixedHeight(40)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 0 20px; font-size: 12px; font-weight: 600; color: #ffffff;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        confirm_btn.clicked.connect(lambda: self.return_confirmed.emit(self._rental_id))
        right_col.addWidget(confirm_btn)

        right = QWidget()
        right.setLayout(right_col)
        right.setFixedWidth(170)

        layout.addWidget(left)
        layout.addWidget(center, 1)
        layout.addWidget(right)


class ConfirmReturnPage(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
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

        title = QLabel("Konfirmasi Pengembalian")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        layout.addWidget(title)

        subtitle = QLabel("Review dan konfirmasi pengembalian barang oleh customer")
        subtitle.setStyleSheet("font-size: 14px; color: #8C8A86;")
        layout.addWidget(subtitle)

        self.cards_container = QVBoxLayout()
        self.cards_container.setSpacing(12)
        layout.addLayout(self.cards_container)

        self.empty_label = QLabel("Tidak ada barang yang perlu dikonfirmasi pengembaliannya.")
        self.empty_label.setStyleSheet("font-size: 14px; color: #8C8A86; padding: 40px; background: transparent;")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _load_data(self):
        rentals = get_rentals_for_owner() or []

        # Show confirmed/active rentals that need return confirmation
        active = [r for r in rentals if r.get("status") in ("confirmed", "active")]
        self._render_cards(active)

    def _render_cards(self, data):
        while self.cards_container.count():
            item = self.cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)

        for r in data:
            card = ReturnConfirmCard(r)
            card.return_confirmed.connect(self._on_return)
            self.cards_container.addWidget(card)

    def _on_return(self, rental_id):
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")

        # Find the rental to get end_date
        rentals = get_rentals_for_owner() or []
        rental = next((r for r in rentals if r.get("id") == rental_id), None)
        if not rental:
            return

        end_date = rental.get("end_date", today)
        result = process_return(rental_id, today, "", end_date)

        if result.get("success"):
            fine = result.get("fine", 0)
            msg = "Pengembalian berhasil dikonfirmasi."
            if fine > 0:
                msg += f"\nDenda: Rp {fine:,}"
            QMessageBox.information(self, "Berhasil", msg)
            self._load_data()
        else:
            QMessageBox.warning(self, "Gagal", "Gagal mengkonfirmasi pengembalian.")
