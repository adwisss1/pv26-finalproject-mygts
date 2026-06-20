from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

from controllers.rental_controller import (
    get_rentals_for_owner, confirm_rental, reject_rental, calculate_fine
)
from controllers.auth_controller import get_current_user


# ─────────────────────────────────────────────────────────────────────────────
#  TAB BAR  — pill style modern
# ─────────────────────────────────────────────────────────────────────────────

class TabBar(QFrame):
    tab_changed = Signal(str)

    TABS = [
        ("pending",   "Menunggu",        "⏳"),
        ("confirmed", "Dikonfirmasi",     "✅"),
        ("rejected",  "Ditolak",          "✗"),
    ]

    def __init__(self):
        super().__init__()
        self._active = "pending"
        self._buttons: dict[str, QPushButton] = {}
        self._counts: dict[str, int] = {}
        self.setObjectName("tabBar")
        self.setFixedHeight(52)
        self.setStyleSheet("""
            #tabBar {
                background: #ECEAE6;
                border-radius: 14px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        for key, label, icon in self.TABS:
            btn = QPushButton(f"{icon}  {label}")
            btn.setObjectName(f"tab_{key}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            layout.addWidget(btn)
            self._buttons[key] = btn

        self._apply_styles()

    def _on_click(self, key: str):
        self._active = key
        self._apply_styles()
        self.tab_changed.emit(key)

    def set_count(self, key: str, count: int):
        self._counts[key] = count
        self._apply_styles()

    def _apply_styles(self):
        for key, btn in self._buttons.items():
            label_map = {"pending": "Menunggu", "confirmed": "Dikonfirmasi", "rejected": "Ditolak"}
            icon_map  = {"pending": "⏳", "confirmed": "✅", "rejected": "✗"}
            cnt = self._counts.get(key, 0)
            cnt_str = f"  ({cnt})" if key == "pending" and cnt > 0 else ""
            btn.setText(f"{icon_map[key]}  {label_map[key]}{cnt_str}")

            if key == self._active:
                color_map = {
                    "pending":   ("#0F6E56", "#ffffff"),
                    "confirmed": ("#1D9E75", "#ffffff"),
                    "rejected":  ("#E24B4A", "#ffffff"),
                }
                bg, fg = color_map[key]
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {bg};
                        border: none;
                        border-radius: 10px;
                        font-size: 13px;
                        font-weight: 600;
                        color: {fg};
                        padding: 0 18px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        border-radius: 10px;
                        font-size: 13px;
                        font-weight: 400;
                        color: #6B6A66;
                        padding: 0 18px;
                    }
                    QPushButton:hover {
                        background: #D8D6D2;
                        color: #1A1A1A;
                    }
                """)


# ─────────────────────────────────────────────────────────────────────────────
#  RENTAL CONFIRM CARD  — modern card design
# ─────────────────────────────────────────────────────────────────────────────

class RentalConfirmCard(QFrame):
    confirmed = Signal(str)
    rejected  = Signal(str)

    _STATUS_CONFIG = {
        "pending":   ("#F59E0B", "#FFFBEB", "Menunggu"),
        "confirmed": ("#0F6E56", "#F0FDF8", "Dikonfirmasi"),
        "rejected":  ("#E24B4A", "#FEF2F2", "Ditolak"),
    }

    def __init__(self, rental_data: dict, mode: str):
        super().__init__()
        self._rental_id = rental_data.get("id", "")
        self._mode = mode
        self.setObjectName("confirmCard")

        accent, bg, _ = self._STATUS_CONFIG.get(mode, ("#ccc", "#fff", "-"))
        self.setStyleSheet(f"""
            #confirmCard {{
                background: #ffffff;
                border: 1px solid #ECEAE6;
                border-left: 4px solid {accent};
                border-radius: 14px;
            }}
            #confirmCard:hover {{
                border-color: {accent};
                border-left: 4px solid {accent};
            }}
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 18))
        self.setGraphicsEffect(shadow)

        self._build(rental_data, mode, accent, bg)

    def _build(self, r: dict, mode: str, accent: str, bg: str):
        from datetime import datetime

        inv   = r.get("inventories") or {}
        user  = r.get("users") or {}
        start = r.get("start_date", "")
        end   = r.get("end_date", "")
        price = inv.get("price_per_day", 0)
        notes = r.get("notes", "")

        days = 0
        if start and end:
            try:
                days = max(1, (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days)
            except ValueError:
                days = 0
        total = price * days

        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(20)

        # ── Avatar kolom ──────────────────────────────────────────────────
        avatar_col = QVBoxLayout()
        avatar_col.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        avatar_col.setSpacing(8)

        avatar = QFrame()
        avatar.setFixedSize(52, 52)
        avatar.setStyleSheet(f"""
            background: {accent}22;
            border-radius: 26px;
            border: 2px solid {accent}44;
        """)
        av_lay = QVBoxLayout(avatar)
        av_lay.setAlignment(Qt.AlignCenter)
        av_lay.setContentsMargins(0, 0, 0, 0)
        initial = (user.get("name") or "?")[0].upper()
        av_lbl = QLabel(initial)
        av_lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {accent}; background: transparent;")
        av_lbl.setAlignment(Qt.AlignCenter)
        av_lay.addWidget(av_lbl)

        name_lbl = QLabel(user.get("name", "-"))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1A1A1A; background: transparent;")
        name_lbl.setWordWrap(True)
        name_lbl.setMaximumWidth(106)

        role_badge = QLabel("Customer")
        role_badge.setAlignment(Qt.AlignCenter)
        role_badge.setStyleSheet("""
            font-size: 10px; font-weight: 600; color: #0F6E56;
            background: #E8F5F1; border-radius: 4px;
            padding: 2px 8px;
        """)

        avatar_col.addWidget(avatar, 0, Qt.AlignHCenter)
        avatar_col.addWidget(name_lbl)
        avatar_col.addWidget(role_badge, 0, Qt.AlignHCenter)

        av_widget = QWidget()
        av_widget.setLayout(avatar_col)
        av_widget.setFixedWidth(110)
        av_widget.setStyleSheet("background: transparent;")
        outer.addWidget(av_widget)

        # ── Divider ───────────────────────────────────────────────────────
        div = QFrame()
        div.setFixedWidth(1)
        div.setStyleSheet("background: #ECEAE6; border: none;")
        outer.addWidget(div)

        # ── Info kolom ────────────────────────────────────────────────────
        info_col = QVBoxLayout()
        info_col.setSpacing(6)
        info_col.setAlignment(Qt.AlignTop)

        item_name = QLabel(inv.get("name", "-"))
        item_name.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #111111; background: transparent;"
        )
        info_col.addWidget(item_name)

        # Kategori pill
        cat_row = QHBoxLayout()
        cat_row.setSpacing(8)
        cat_badge = QLabel(f"📁  {inv.get('category', '-')}")
        cat_badge.setStyleSheet("""
            font-size: 11px; font-weight: 500; color: #6B6A66;
            background: #F4F3F0; border-radius: 6px;
            padding: 3px 10px;
        """)
        cat_row.addWidget(cat_badge)
        cat_row.addStretch()
        info_col.addLayout(cat_row)

        # Tanggal
        date_lbl = QLabel(f"📅  {start}  →  {end}   ({days} hari)")
        date_lbl.setStyleSheet(
            "font-size: 13px; color: #6B6A66; background: transparent;"
        )
        info_col.addWidget(date_lbl)

        # Total harga
        total_lbl = QLabel(f"💰  Rp {total:,.0f}".replace(",", "."))
        total_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {accent}; background: transparent;"
        )
        info_col.addWidget(total_lbl)

        if notes:
            notes_lbl = QLabel(f"📝  {notes}")
            notes_lbl.setWordWrap(True)
            notes_lbl.setStyleSheet(
                "font-size: 12px; color: #A8A6A2; background: transparent; font-style: italic;"
            )
            info_col.addWidget(notes_lbl)

        info_widget = QWidget()
        info_widget.setLayout(info_col)
        info_widget.setStyleSheet("background: transparent;")
        outer.addWidget(info_widget, 1)

        # ── Aksi kolom ────────────────────────────────────────────────────
        action_col = QVBoxLayout()
        action_col.setAlignment(Qt.AlignCenter)
        action_col.setSpacing(10)

        if mode == "pending":
            confirm_btn = QPushButton("✓  Konfirmasi")
            confirm_btn.setCursor(Qt.PointingHandCursor)
            confirm_btn.setFixedSize(140, 40)
            confirm_btn.setStyleSheet("""
                QPushButton {
                    background: #0F6E56; border: none; border-radius: 10px;
                    font-size: 13px; font-weight: 600; color: #ffffff;
                }
                QPushButton:hover { background: #0A5A45; }
                QPushButton:pressed { background: #084D3C; }
            """)
            confirm_btn.clicked.connect(lambda: self.confirmed.emit(self._rental_id))

            reject_btn = QPushButton("✗  Tolak")
            reject_btn.setCursor(Qt.PointingHandCursor)
            reject_btn.setFixedSize(140, 40)
            reject_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1.5px solid #E24B4A;
                    border-radius: 10px;
                    font-size: 13px; font-weight: 500; color: #E24B4A;
                }
                QPushButton:hover { background: #FDE8E8; }
                QPushButton:pressed { background: #FDD0D0; }
            """)
            reject_btn.clicked.connect(lambda: self.rejected.emit(self._rental_id))

            action_col.addWidget(confirm_btn)
            action_col.addWidget(reject_btn)

        else:
            accent_c, bg_c, label_c = self._STATUS_CONFIG.get(mode, ("#ccc", "#eee", "-"))
            status_chip = QFrame()
            status_chip.setStyleSheet(f"""
                background: {bg_c};
                border: 1.5px solid {accent_c}44;
                border-radius: 10px;
            """)
            chip_lay = QHBoxLayout(status_chip)
            chip_lay.setContentsMargins(14, 10, 14, 10)
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background: {accent_c}; border-radius: 4px;")
            chip_lbl = QLabel(label_c)
            chip_lbl.setStyleSheet(
                f"font-size: 13px; font-weight: 600; color: {accent_c}; background: transparent;"
            )
            chip_lay.addWidget(dot)
            chip_lay.addSpacing(8)
            chip_lay.addWidget(chip_lbl)
            action_col.addWidget(status_chip)

        action_widget = QWidget()
        action_widget.setLayout(action_col)
        action_widget.setFixedWidth(160)
        action_widget.setStyleSheet("background: transparent;")
        outer.addWidget(action_widget)


# ─────────────────────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────

class EmptyState(QWidget):
    _CONFIG = {
        "pending":   ("⏳", "Tidak ada penyewaan menunggu",   "Semua permintaan sudah ditangani."),
        "confirmed": ("✅", "Belum ada yang dikonfirmasi",     "Penyewaan yang disetujui akan muncul di sini."),
        "rejected":  ("✗",  "Tidak ada yang ditolak",         "Penyewaan yang ditolak akan muncul di sini."),
    }

    def __init__(self, tab: str):
        super().__init__()
        icon, title, sub = self._CONFIG.get(tab, ("📭", "Kosong", ""))
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 48, 0, 48)

        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("font-size: 40px; background: transparent;")

        tl = QLabel(title)
        tl.setAlignment(Qt.AlignCenter)
        tl.setStyleSheet("font-size: 16px; font-weight: 600; color: #3A3A3A; background: transparent;")

        sl = QLabel(sub)
        sl.setAlignment(Qt.AlignCenter)
        sl.setStyleSheet("font-size: 13px; color: #A8A6A2; background: transparent;")

        layout.addWidget(ic)
        layout.addWidget(tl)
        layout.addWidget(sl)
        self.setStyleSheet("background: transparent;")


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIRM RENTAL PAGE
# ─────────────────────────────────────────────────────────────────────────────

class ConfirmRentalPage(QWidget):
    navigate_to  = Signal(str)
    badge_updated = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._current_tab = "pending"
        self._build_ui()

    def refresh(self):
        self._load_data()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(28, 28, 28, 28)
        self._content_layout.setSpacing(20)

        # ── Header (TANPA duplikasi — topbar sudah tampilkan judul) ──────
        header_row = QHBoxLayout()
        sub = QLabel("Kelola dan tindaklanjuti permintaan penyewaan dari customer.")
        sub.setStyleSheet("font-size: 13px; color: #8C8A86; background: transparent;")
        header_row.addWidget(sub)
        header_row.addStretch()

        # Summary count pill
        self._summary_pill = QLabel("Memuat...")
        self._summary_pill.setStyleSheet("""
            font-size: 12px; color: #0F6E56; font-weight: 600;
            background: #E8F5F1; border-radius: 20px;
            padding: 6px 14px;
        """)
        header_row.addWidget(self._summary_pill)
        self._content_layout.addLayout(header_row)

        # ── Tab bar ──────────────────────────────────────────────────────
        self._tab_bar = TabBar()
        self._tab_bar.tab_changed.connect(self._switch_tab)

        tab_wrap = QHBoxLayout()
        tab_wrap.addWidget(self._tab_bar)
        tab_wrap.addStretch()
        self._content_layout.addLayout(tab_wrap)

        # ── Cards area ───────────────────────────────────────────────────
        self._cards_container = QVBoxLayout()
        self._cards_container.setSpacing(12)
        self._content_layout.addLayout(self._cards_container)
        self._content_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _switch_tab(self, key: str):
        self._current_tab = key
        self._load_data()

    def _load_data(self):
        rentals = get_rentals_for_owner() or []

        pending_count   = sum(1 for r in rentals if r.get("status") == "pending")
        confirmed_count = sum(1 for r in rentals if r.get("status") == "confirmed")
        rejected_count  = sum(1 for r in rentals if r.get("status") == "rejected")

        self._tab_bar.set_count("pending",   pending_count)
        self._tab_bar.set_count("confirmed", confirmed_count)
        self._tab_bar.set_count("rejected",  rejected_count)

        self._summary_pill.setText(f"{pending_count} menunggu tindakan")
        self.badge_updated.emit("pending", str(pending_count))

        filtered = [r for r in rentals if r.get("status") == self._current_tab]
        self._render_cards(filtered)

    def _render_cards(self, data: list):
        # Hapus card lama
        while self._cards_container.count():
            item = self._cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            self._cards_container.addWidget(EmptyState(self._current_tab))
            return

        for r in data:
            card = RentalConfirmCard(r, self._current_tab)
            card.confirmed.connect(self._on_confirm)
            card.rejected.connect(self._on_reject)
            self._cards_container.addWidget(card)

    def _on_confirm(self, rental_id: str):
        ok = confirm_rental(rental_id)
        if ok:
            self._load_data()
        else:
            QMessageBox.warning(self, "Gagal", "Gagal mengkonfirmasi penyewaan.")

    def _on_reject(self, rental_id: str):
        reply = QMessageBox.question(
            self, "Konfirmasi Penolakan",
            "Apakah Anda yakin ingin menolak penyewaan ini?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok = reject_rental(rental_id)
            if ok:
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Gagal menolak penyewaan.")