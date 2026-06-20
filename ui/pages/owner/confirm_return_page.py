from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from controllers.rental_controller import (
    get_rentals_for_owner, process_return, calculate_fine
)
from controllers.auth_controller import get_current_user


def _shadow(blur=20, dy=3, alpha=22):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setOffset(0, dy)
    s.setColor(QColor(0, 0, 0, alpha))
    return s


# ─────────────────────────────────────────────────────────────────────────────
#  STAT CARD  — summary strip di bagian atas
# ─────────────────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, icon: str, label: str, value: str, accent: str):
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(88)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            #statCard {{
                background: #ffffff;
                border: 1px solid #ECEAE6;
                border-top: 3px solid {accent};
                border-radius: 12px;
            }}
        """)
        self.setGraphicsEffect(_shadow())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)

        top = QHBoxLayout()
        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 18px; background: transparent; color: {accent};")
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 11px; font-weight: 500; color: #8C8A86; background: transparent;")
        top.addWidget(ic)
        top.addWidget(lbl, 1)
        lay.addLayout(top)

        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(
            f"font-size: 30px; font-weight: 700; color: {accent}; "
            "letter-spacing: -1px; background: transparent;"
        )
        lay.addWidget(self.val_lbl)

    def set_value(self, v):
        self.val_lbl.setText(str(v))


# ─────────────────────────────────────────────────────────────────────────────
#  FILTER PILL BAR
# ─────────────────────────────────────────────────────────────────────────────

class FilterBar(QFrame):
    filter_changed = Signal(str)

    _ITEMS = [
        ("all",  "🗂  Semua"),
        ("late", "⚠  Terlambat"),
    ]

    def __init__(self):
        super().__init__()
        self._active = "all"
        self.setObjectName("filterBar")
        self.setFixedHeight(46)
        self.setStyleSheet("#filterBar { background: #ECEAE6; border-radius: 12px; }")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(5, 5, 5, 5)
        lay.setSpacing(4)

        self._btns: dict[str, QPushButton] = {}
        for key, label in self._ITEMS:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda _, k=key: self._click(k))
            lay.addWidget(btn)
            self._btns[key] = btn
        lay.addStretch()
        self._style()

    def _click(self, key):
        self._active = key
        self._style()
        self.filter_changed.emit(key)

    def _style(self):
        for key, btn in self._btns.items():
            if key == self._active:
                c = "#E24B4A" if key == "late" else "#0F6E56"
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {c}; border: none; border-radius: 8px;
                        font-size: 13px; font-weight: 600; color: #fff;
                        padding: 0 20px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent; border: none; border-radius: 8px;
                        font-size: 13px; font-weight: 400; color: #6B6A66;
                        padding: 0 20px;
                    }
                    QPushButton:hover { background: #D8D6D2; color: #1A1A1A; }
                """)


# ─────────────────────────────────────────────────────────────────────────────
#  RETURN CONFIRM CARD
# ─────────────────────────────────────────────────────────────────────────────

class ReturnConfirmCard(QFrame):
    return_confirmed = Signal(str)

    def __init__(self, rental_data: dict):
        super().__init__()
        self._rental_id = rental_data.get("id", "")
        self.setObjectName("returnCard")

        end     = rental_data.get("end_date", "")
        now_str = datetime.now().strftime("%Y-%m-%d")
        is_late = bool(end and end < now_str)
        accent  = "#E24B4A" if is_late else "#0F6E56"

        self.setStyleSheet(f"""
            #returnCard {{
                background: #ffffff;
                border: 1px solid #ECEAE6;
                border-left: 4px solid {accent};
                border-radius: 14px;
            }}
        """)
        self.setGraphicsEffect(_shadow())
        self._build(rental_data, is_late, accent)

    def _build(self, r: dict, is_late: bool, accent: str):
        inv     = r.get("inventories") or {}
        user    = r.get("users") or {}
        start   = r.get("start_date", "")
        end     = r.get("end_date", "")
        price   = inv.get("price_per_day", 0)
        now_str = datetime.now().strftime("%Y-%m-%d")

        days = 0
        if start and end:
            try:
                days = max(1, (datetime.strptime(end, "%Y-%m-%d") -
                               datetime.strptime(start, "%Y-%m-%d")).days)
            except ValueError:
                pass
        total = price * days

        late_days = fine = 0
        if is_late and end:
            try:
                late_days = max(0, (datetime.strptime(now_str, "%Y-%m-%d") -
                                    datetime.strptime(end, "%Y-%m-%d")).days)
            except ValueError:
                pass
            fine = calculate_fine(end, now_str)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 20)
        outer.setSpacing(20)

        # ── Avatar ────────────────────────────────────────────────────────
        av_col = QVBoxLayout()
        av_col.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        av_col.setSpacing(7)

        circle = QFrame()
        circle.setFixedSize(54, 54)
        circle.setStyleSheet(f"""
            background: {accent}1A;
            border-radius: 27px;
            border: 2px solid {accent}50;
        """)
        cl = QVBoxLayout(circle)
        cl.setAlignment(Qt.AlignCenter)
        cl.setContentsMargins(0, 0, 0, 0)
        init_lbl = QLabel((user.get("name") or "?")[0].upper())
        init_lbl.setAlignment(Qt.AlignCenter)
        init_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: 700; color: {accent}; background: transparent;"
        )
        cl.addWidget(init_lbl)

        name_lbl = QLabel(user.get("name", "-"))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #1A1A1A; background: transparent;"
        )
        name_lbl.setWordWrap(True)
        name_lbl.setMinimumWidth(110)
        name_lbl.setMaximumWidth(120)

        role_pill = QLabel("Customer")
        role_pill.setAlignment(Qt.AlignCenter)
        role_pill.setStyleSheet("""
            font-size: 10px; font-weight: 600; color: #0F6E56;
            background: #E8F5F1; border-radius: 4px; padding: 2px 8px;
        """)

        av_col.addWidget(circle, 0, Qt.AlignHCenter)
        av_col.addWidget(name_lbl)
        av_col.addWidget(role_pill, 0, Qt.AlignHCenter)

        av_w = QWidget()
        av_w.setLayout(av_col)
        av_w.setFixedWidth(130)
        av_w.setStyleSheet("background: transparent;")
        outer.addWidget(av_w)

        # ── Divider ───────────────────────────────────────────────────────
        div = QFrame()
        div.setFixedWidth(1)
        div.setStyleSheet("background: #ECEAE6; border: none;")
        outer.addWidget(div)

        # ── Info ──────────────────────────────────────────────────────────
        info = QVBoxLayout()
        info.setSpacing(8)
        info.setAlignment(Qt.AlignTop)

        # Nama barang + kategori
        name_row = QHBoxLayout()
        item_lbl = QLabel(inv.get("name", "-"))
        item_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #111; background: transparent;"
        )
        cat_pill = QLabel(f"📁 {inv.get('category', '-')}")
        cat_pill.setStyleSheet("""
            font-size: 11px; font-weight: 500; color: #6B6A66;
            background: #F4F3F0; border-radius: 6px; padding: 3px 10px;
        """)
        name_row.addWidget(item_lbl)
        name_row.addSpacing(12)
        name_row.addWidget(cat_pill)
        name_row.addStretch()
        info.addLayout(name_row)

        # Tanggal dan harga dalam satu baris
        meta_row = QHBoxLayout()
        meta_row.setSpacing(20)
        date_lbl = QLabel(f"📅  {start}  →  {end}  ({days} hari)")
        date_lbl.setStyleSheet("font-size: 13px; color: #6B6A66; background: transparent;")
        price_lbl = QLabel(f"💰  Rp {total:,.0f}".replace(",", "."))
        price_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #0F6E56; background: transparent;"
        )
        meta_row.addWidget(date_lbl)
        meta_row.addWidget(price_lbl)
        meta_row.addStretch()
        info.addLayout(meta_row)

        # Status chip
        chip = QFrame()
        if is_late:
            chip.setStyleSheet("""
                background: #FEF2F2; border: 1px solid #E24B4A33; border-radius: 8px;
            """)
            cl2 = QHBoxLayout(chip)
            cl2.setContentsMargins(14, 8, 14, 8)
            cl2.setSpacing(10)
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet("background: #E24B4A; border-radius: 4px;")
            txt = QLabel(f"⚠  Terlambat {late_days} hari  —  Denda: Rp {fine:,.0f}".replace(",", "."))
            txt.setStyleSheet(
                "font-size: 13px; font-weight: 600; color: #E24B4A; background: transparent;"
            )
            cl2.addWidget(dot)
            cl2.addWidget(txt)
        else:
            chip.setStyleSheet("""
                background: #F0FDF8; border: 1px solid #0F6E5633; border-radius: 8px;
            """)
            cl2 = QHBoxLayout(chip)
            cl2.setContentsMargins(14, 8, 14, 8)
            cl2.setSpacing(10)
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet("background: #1D9E75; border-radius: 4px;")
            txt = QLabel("✓  Pengembalian tepat waktu")
            txt.setStyleSheet(
                "font-size: 13px; font-weight: 600; color: #1D9E75; background: transparent;"
            )
            cl2.addWidget(dot)
            cl2.addWidget(txt)
        info.addWidget(chip)

        info_w = QWidget()
        info_w.setLayout(info)
        info_w.setStyleSheet("background: transparent;")
        outer.addWidget(info_w, 1)

        # ── Tombol ────────────────────────────────────────────────────────
        btn_col = QVBoxLayout()
        btn_col.setAlignment(Qt.AlignCenter)
        btn_col.setSpacing(8)

        confirm_btn = QPushButton("↩  Konfirmasi Kembali")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setFixedSize(176, 44)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 10px;
                font-size: 13px; font-weight: 600; color: #ffffff;
            }
            QPushButton:hover  { background: #0A5A45; }
            QPushButton:pressed { background: #074D3A; }
        """)
        confirm_btn.clicked.connect(lambda: self.return_confirmed.emit(self._rental_id))
        btn_col.addWidget(confirm_btn)

        if is_late and fine > 0:
            fine_note = QLabel(f"+ denda Rp {fine:,.0f}".replace(",", "."))
            fine_note.setAlignment(Qt.AlignCenter)
            fine_note.setStyleSheet(
                "font-size: 11px; color: #E24B4A; background: transparent; font-weight: 500;"
            )
            btn_col.addWidget(fine_note)

        btn_w = QWidget()
        btn_w.setLayout(btn_col)
        btn_w.setFixedWidth(186)
        btn_w.setStyleSheet("background: transparent;")
        outer.addWidget(btn_w)


# ─────────────────────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────

class EmptyState(QFrame):
    def __init__(self, is_late_filter: bool = False):
        super().__init__()
        self.setObjectName("emptyCard")
        self.setStyleSheet("""
            #emptyCard {
                background: #ffffff;
                border: 1px dashed #D4D2CD;
                border-radius: 16px;
            }
        """)
        self.setMinimumHeight(260)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(12)
        lay.setContentsMargins(40, 40, 40, 40)

        if is_late_filter:
            icon_lbl  = QLabel("✅")
            title_txt = "Tidak ada keterlambatan"
            sub_txt   = "Semua penyewa mengembalikan barang tepat waktu."
        else:
            icon_lbl  = QLabel("📦")
            title_txt = "Tidak ada pengembalian aktif"
            sub_txt   = "Barang yang sedang disewa dan menunggu\npengembalian akan muncul di sini."

        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")

        title = QLabel(title_txt)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 17px; font-weight: 700; color: #2A2A2A; background: transparent;"
        )

        sub = QLabel(sub_txt)
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("font-size: 13px; color: #A8A6A2; background: transparent; line-height: 1.5;")

        lay.addWidget(icon_lbl)
        lay.addWidget(title)
        lay.addWidget(sub)
        self.setStyleSheet("""
            #emptyCard {
                background: #fafaf8;
                border: 1.5px dashed #D4D2CD;
                border-radius: 16px;
            }
        """)


# ─────────────────────────────────────────────────────────────────────────────
#  CONFIRM RETURN PAGE
# ─────────────────────────────────────────────────────────────────────────────

class ConfirmReturnPage(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._all_rentals: list = []
        self._filter = "all"
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
        self._main = QVBoxLayout(content)
        self._main.setContentsMargins(28, 24, 28, 28)
        self._main.setSpacing(20)

        # ── Sub-header ────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        sub = QLabel("Review dan konfirmasi pengembalian barang oleh customer.")
        sub.setStyleSheet("font-size: 13px; color: #8C8A86; background: transparent;")
        hdr.addWidget(sub)
        hdr.addStretch()
        self._main.addLayout(hdr)

        # ── Filter bar ────────────────────────────────────────────────────
        self._filter_bar = FilterBar()
        self._filter_bar.filter_changed.connect(self._set_filter)
        wrap = QHBoxLayout()
        wrap.addWidget(self._filter_bar)
        wrap.addStretch()
        self._main.addLayout(wrap)

        # ── Cards container ───────────────────────────────────────────────
        self._cards = QVBoxLayout()
        self._cards.setSpacing(12)
        self._main.addLayout(self._cards)
        self._main.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ── Logic ─────────────────────────────────────────────────────────────

    def _set_filter(self, key: str):
        self._filter = key
        self._render(self._all_rentals)

    def _load_data(self):
        rentals = self._all_rentals = [
            r for r in (get_rentals_for_owner() or [])
            if r.get("status") in ("confirmed", "active")
        ]
        self._render(rentals)

    def _render(self, data: list):
        while self._cards.count():
            item = self._cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        now_str = datetime.now().strftime("%Y-%m-%d")
        if self._filter == "late":
            data = [r for r in data if r.get("end_date", "9999") < now_str]

        if not data:
            self._cards.addWidget(EmptyState(is_late_filter=(self._filter == "late")))
            return

        for r in data:
            card = ReturnConfirmCard(r)
            card.return_confirmed.connect(self._on_return)
            self._cards.addWidget(card)

    def _on_return(self, rental_id: str):
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")

        rental = next(
            (r for r in (get_rentals_for_owner() or []) if r.get("id") == rental_id), None
        )
        if not rental:
            return

        result = process_return(rental_id, today, "", rental.get("end_date", today))
        if result.get("success"):
            fine = result.get("fine", 0)
            msg  = "Pengembalian berhasil dikonfirmasi."
            if fine > 0:
                msg += f"\nDenda: Rp {fine:,.0f}".replace(",", ".")
            QMessageBox.information(self, "Berhasil", msg)
            self._load_data()
        else:
            QMessageBox.warning(self, "Gagal", "Gagal mengkonfirmasi pengembalian.")