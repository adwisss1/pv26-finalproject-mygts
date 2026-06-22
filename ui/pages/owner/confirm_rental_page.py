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

            # mark active/inactive state for QSS
            if key == self._active:
                btn.setObjectName("tabActive")
                btn.setProperty("active", True)
                # Inline stylesheet untuk memastikan styling jelas
                btn.setStyleSheet("""
                    QPushButton#tabActive {
                        background: #0F6E56; color: #ffffff; border: 1px solid rgba(0,0,0,0.06);
                        border-radius: 12px; padding: 8px 18px; font-weight: 600; margin: 2px;
                    }
                    QPushButton#tabActive:hover { background: #0b5a47; }
                """)
            else:
                btn.setObjectName("tabInactive")
                btn.setProperty("active", False)
                # Inline stylesheet untuk inactive tab dengan warna gelap agar berbeda
                btn.setStyleSheet("""
                    QPushButton#tabInactive {
                        background: transparent; color: #1A1A1A; border: none; 
                        border-radius: 12px; padding: 8px 18px; margin: 2px; font-weight: 500;
                    }
                    QPushButton#tabInactive:hover { background: #E0DDD8; color: #000000; }
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
        # expose status for QSS rules (pending/confirmed/rejected)
        self.setProperty("status", mode)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 18))
        self.setGraphicsEffect(shadow)

        # resolve colors for status
        accent, bg, _label = self._STATUS_CONFIG.get(mode, ("#ccc", "#eee", "-"))
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
        avatar.setObjectName("avatar")
        # status property on parent will control avatar colors via QSS
        av_lay = QVBoxLayout(avatar)
        av_lay.setAlignment(Qt.AlignCenter)
        av_lay.setContentsMargins(0, 0, 0, 0)
        initial = (user.get("name") or "?")[0].upper()
        av_lbl = QLabel(initial)
        av_lbl.setObjectName("avatarLabel")
        av_lbl.setAlignment(Qt.AlignCenter)
        av_lay.addWidget(av_lbl)

        name_lbl = QLabel(user.get("name", "-"))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setObjectName("avatarName")
        name_lbl.setWordWrap(True)
        name_lbl.setMaximumWidth(106)

        role_badge = QLabel("Customer")
        role_badge.setAlignment(Qt.AlignCenter)
        role_badge.setObjectName("roleBadge")

        avatar_col.addWidget(avatar, 0, Qt.AlignHCenter)
        avatar_col.addWidget(name_lbl)
        avatar_col.addWidget(role_badge, 0, Qt.AlignHCenter)

        av_widget = QWidget()
        av_widget.setLayout(avatar_col)
        av_widget.setFixedWidth(110)
        av_widget.setObjectName("avatarContainer")
        outer.addWidget(av_widget)

        # ── Divider ───────────────────────────────────────────────────────
        div = QFrame()
        div.setFixedWidth(1)
        div.setObjectName("divider")
        outer.addWidget(div)

        # ── Info kolom ────────────────────────────────────────────────────
        info_col = QVBoxLayout()
        info_col.setSpacing(6)
        info_col.setAlignment(Qt.AlignTop)

        item_name = QLabel(inv.get("name", "-"))
        item_name.setObjectName("itemName")
        info_col.addWidget(item_name)

        # Kategori pill
        cat_row = QHBoxLayout()
        cat_row.setSpacing(8)
        cat_badge = QLabel(f"📁  {inv.get('category', '-')}")
        cat_badge.setObjectName("catBadge")
        cat_row.addWidget(cat_badge)
        cat_row.addStretch()
        info_col.addLayout(cat_row)

        # Tanggal
        date_lbl = QLabel(f"📅  {start}  →  {end}   ({days} hari)")
        date_lbl.setObjectName("dateLabel")
        info_col.addWidget(date_lbl)

        # Total harga
        total_lbl = QLabel(f"💰  Rp {total:,.0f}".replace(",", "."))
        total_lbl.setObjectName("totalLabel")
        total_lbl.setProperty("statusAccent", accent)
        info_col.addWidget(total_lbl)

        if notes:
            notes_lbl = QLabel(f"📝  {notes}")
            notes_lbl.setWordWrap(True)
            notes_lbl.setObjectName("notesLabel")
            info_col.addWidget(notes_lbl)

        info_widget = QWidget()
        info_widget.setLayout(info_col)
        info_widget.setObjectName("infoWidget")
        outer.addWidget(info_widget, 1)

        # ── Aksi kolom ────────────────────────────────────────────────────
        action_col = QVBoxLayout()
        action_col.setAlignment(Qt.AlignCenter)
        action_col.setSpacing(10)

        if mode == "pending":
            confirm_btn = QPushButton("✓  Konfirmasi")
            confirm_btn.setCursor(Qt.PointingHandCursor)
            confirm_btn.setMinimumWidth(140)
            confirm_btn.setFixedHeight(40)
            confirm_btn.setObjectName("btnConfirm")
            confirm_btn.setStyleSheet("""
                QPushButton {
                    background: #0F6E56;
                    color: #ffffff;
                    border: none;
                    border-radius: 10px;
                    padding: 8px 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #0A5A45;
                }
                QPushButton:pressed {
                    background: #08463a;
                }
            """)
            confirm_btn.clicked.connect(lambda: self.confirmed.emit(self._rental_id))

            reject_btn = QPushButton("✗  Tolak")
            reject_btn.setCursor(Qt.PointingHandCursor)
            reject_btn.setMinimumWidth(140)
            reject_btn.setFixedHeight(40)
            reject_btn.setObjectName("btnReject")
            reject_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1.5px solid #E24B4A;
                    color: #E24B4A;
                    border-radius: 10px;
                    padding: 8px 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #FDE8E8;
                }
                QPushButton:pressed {
                    background: #FDE8E8;
                    border-color: #C23C3A;
                }
            """)
            reject_btn.clicked.connect(lambda: self.rejected.emit(self._rental_id))

            action_col.addWidget(confirm_btn)
            action_col.addWidget(reject_btn)

        else:
            accent_c, bg_c, label_c = self._STATUS_CONFIG.get(mode, ("#ccc", "#eee", "-"))
            status_chip = QFrame()
            status_chip.setObjectName("statusChip")
            status_chip.setProperty("status", mode)
            chip_lay = QHBoxLayout(status_chip)
            chip_lay.setContentsMargins(14, 10, 14, 10)
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setObjectName("statusDot")
            dot.setProperty("status", mode)
            chip_lbl = QLabel(label_c)
            chip_lbl.setObjectName("statusLabel")
            chip_lbl.setProperty("status", mode)
            chip_lay.addWidget(dot)
            chip_lay.addSpacing(8)
            chip_lay.addWidget(chip_lbl)
            action_col.addWidget(status_chip)

        action_widget = QWidget()
        action_widget.setLayout(action_col)
        action_widget.setMinimumWidth(160)
        action_widget.setObjectName("actionWidget")
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
        ic.setObjectName("emptyIcon")

        tl = QLabel(title)
        tl.setAlignment(Qt.AlignCenter)
        tl.setObjectName("emptyTitle")

        sl = QLabel(sub)
        sl.setAlignment(Qt.AlignCenter)
        sl.setObjectName("emptySub")

        layout.addWidget(ic)
        layout.addWidget(tl)
        layout.addWidget(sl)
        self.setObjectName("transparentContent")


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
        self._load_data()

    def refresh(self):
        self._load_data()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("transparentScroll")

        content = QWidget()
        content.setObjectName("transparentContent")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(28, 28, 28, 28)
        self._content_layout.setSpacing(20)

        # ── Header (TANPA duplikasi — topbar sudah tampilkan judul) ──────
        header_row = QHBoxLayout()
        sub = QLabel("Kelola dan tindaklanjuti permintaan penyewaan dari customer.")
        sub.setObjectName("formSubtitle")
        header_row.addWidget(sub)
        header_row.addStretch()

        # Summary count pill
        self._summary_pill = QLabel("Memuat...")
        self._summary_pill.setObjectName("summaryPill")
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