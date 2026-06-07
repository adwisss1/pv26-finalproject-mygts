import os
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QFileDialog, QGridLayout,
    QLineEdit, QComboBox, QDateEdit, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QDate, QSize

from controllers.inventory_controller import get_all_inventory
from controllers.rental_controller import (
    create_rental, confirm_rental, set_pickup_photo, process_return,
    get_rentals_for_owner, get_rentals_for_customer, calculate_fine
)
from controllers.auth_controller import get_current_user, is_owner
from utils.photo_upload import upload_photo
from utils.validators import validate_rental_dates


_TAB_ALL = 0
_TAB_ACTIVE = 1
_TAB_OVERDUE = 2
_TAB_COMPLETED = 3


class StepIndicator(QWidget):
    def __init__(self, current_step=1):
        super().__init__()
        self._current_step = current_step
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        steps = [
            ("Detail\nPenyewaan", 1),
            ("Upload Foto\nPengambilan", 2),
            ("Konfirmasi", 3),
        ]

        for i, (label, num) in enumerate(steps):
            if i > 0:
                line = QFrame()
                line.setFixedHeight(2)
                is_completed = num <= self._current_step
                line.setStyleSheet(f"""
                    background: {'#0F6E56' if is_completed else '#E0DDD8'};
                    border: none; max-height: 2px; min-height: 2px;
                """)
                layout.addWidget(line)

            step_wrap = QWidget()
            step_wrap.setStyleSheet("background: transparent;")
            sw_layout = QVBoxLayout(step_wrap)
            sw_layout.setContentsMargins(0, 0, 0, 0)
            sw_layout.setAlignment(Qt.AlignCenter)
            sw_layout.setSpacing(6)

            if num < self._current_step:
                circle = QFrame()
                circle.setFixedSize(28, 28)
                circle.setStyleSheet("""
                    background: #0F6E56; border-radius: 14px;
                """)
                cl = QVBoxLayout(circle)
                cl.setAlignment(Qt.AlignCenter)
                ci = QLabel("\u2713")
                ci.setStyleSheet("font-size: 12px; font-weight: 700; color: #ffffff; background: transparent;")
                cl.addWidget(ci)
            elif num == self._current_step:
                circle = QFrame()
                circle.setFixedSize(28, 28)
                circle.setStyleSheet("""
                    background: #0F6E56; border-radius: 14px;
                """)
                cl = QVBoxLayout(circle)
                cl.setAlignment(Qt.AlignCenter)
                ci = QLabel(str(num))
                ci.setStyleSheet("font-size: 12px; font-weight: 700; color: #ffffff; background: transparent;")
                cl.addWidget(ci)
            else:
                circle = QFrame()
                circle.setFixedSize(28, 28)
                circle.setStyleSheet("""
                    background: transparent; border: 1.5px solid #D4D2CD; border-radius: 14px;
                """)
                cl = QVBoxLayout(circle)
                cl.setAlignment(Qt.AlignCenter)
                ci = QLabel(str(num))
                ci.setStyleSheet("font-size: 12px; font-weight: 600; color: #A8A6A2; background: transparent;")
                cl.addWidget(ci)

            sw_layout.addWidget(circle, 0, Qt.AlignCenter)

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignCenter)
            if num <= self._current_step:
                lbl.setStyleSheet("font-size: 11px; font-weight: 500; color: #0F6E56; background: transparent;")
            else:
                lbl.setStyleSheet("font-size: 11px; font-weight: 400; color: #A8A6A2; background: transparent;")
            sw_layout.addWidget(lbl)

            layout.addWidget(step_wrap)


class PhotoUploadZone(QFrame):
    files_selected = Signal(list)

    def __init__(self, max_photos=5, banner_text=""):
        super().__init__()
        self._max = max_photos
        self._photos = []
        self._build(banner_text)

    def _build(self, banner_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if banner_text:
            banner = QFrame()
            banner.setStyleSheet("background: #E8F0FE; border-radius: 8px; padding: 12px 16px;")
            bl = QHBoxLayout(banner)
            bl.setContentsMargins(12, 10, 12, 10)
            bl.setSpacing(8)
            info_icon = QLabel("\u24d8")
            info_icon.setStyleSheet("font-size: 14px; color: #4A7DC7; background: transparent;")
            bl.addWidget(info_icon)
            banner_label = QLabel(banner_text)
            banner_label.setStyleSheet("font-size: 12px; color: #4A7DC7; background: transparent;")
            banner_label.setWordWrap(True)
            bl.addWidget(banner_label, 1)
            layout.addWidget(banner)

        drop_area = QFrame()
        drop_area.setObjectName("dropZone")
        drop_area.setFixedHeight(180)
        drop_area.setStyleSheet("""
            #dropZone {
                background: #FAF9F6; border: 1.5px dashed #D4D2CD;
                border-radius: 12px;
            }
            #dropZone:hover {
                border-color: #0F6E56; background: #F8F7F4;
            }
        """)
        drop_area.setCursor(Qt.PointingHandCursor)
        dl = QVBoxLayout(drop_area)
        dl.setAlignment(Qt.AlignCenter)
        dl.setSpacing(8)

        upload_icon = QLabel("\u2601")
        upload_icon.setStyleSheet("font-size: 32px; color: #A8A6A2; background: transparent;")
        dl.addWidget(upload_icon, 0, Qt.AlignCenter)

        upload_text = QLabel("Klik atau seret foto ke sini")
        upload_text.setStyleSheet("font-size: 14px; font-weight: 500; color: #6B6A66; background: transparent;")
        dl.addWidget(upload_text, 0, Qt.AlignCenter)

        upload_sub = QLabel(f"Format: JPG, PNG. Maks 5MB per foto")
        upload_sub.setStyleSheet("font-size: 12px; color: #A8A6A2; background: transparent;")
        dl.addWidget(upload_sub, 0, Qt.AlignCenter)

        def on_click(event):
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)"
            )
            if paths:
                remaining = self._max - len(self._photos)
                selected = paths[:remaining]
                self._photos.extend(selected)
                self.files_selected.emit(self._photos)

        drop_area.mousePressEvent = on_click

        layout.addWidget(drop_area)

        self.thumb_row = QHBoxLayout()
        self.thumb_row.setContentsMargins(0, 0, 0, 0)
        self.thumb_row.setSpacing(8)
        self.thumb_row.addStretch()
        layout.addLayout(self.thumb_row)

        self._render_thumbs()

    def set_photos(self, paths):
        self._photos = list(paths)
        self._render_thumbs()

    def get_photos(self):
        return list(self._photos)

    def _render_thumbs(self):
        while self.thumb_row.count():
            item = self.thumb_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for path in self._photos:
            thumb = self._make_thumb(path)
            self.thumb_row.addWidget(thumb)

        if len(self._photos) < self._max:
            add_btn = QFrame()
            add_btn.setFixedSize(80, 80)
            add_btn.setStyleSheet("""
                background: #FAF9F6; border: 1px dashed #D4D2CD;
                border-radius: 8px;
            """)
            add_btn.setCursor(Qt.PointingHandCursor)
            al = QVBoxLayout(add_btn)
            al.setAlignment(Qt.AlignCenter)
            plus = QLabel("+")
            plus.setStyleSheet("font-size: 24px; font-weight: 300; color: #A8A6A2; background: transparent;")
            al.addWidget(plus)

            def on_add(event):
                paths, _ = QFileDialog.getOpenFileNames(
                    self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)"
                )
                if paths:
                    remaining = self._max - len(self._photos)
                    selected = paths[:remaining]
                    self._photos.extend(selected)
                    self.files_selected.emit(self._photos)
                    self._render_thumbs()

            add_btn.mousePressEvent = on_add
            self.thumb_row.addWidget(add_btn)

        self.thumb_row.addStretch()

    def _make_thumb(self, path):
        thumb = QFrame()
        thumb.setFixedSize(80, 80)
        thumb.setStyleSheet("""
            background: #EDECE8; border: 0.5px solid #E0DDD8;
            border-radius: 8px;
        """)
        tl = QVBoxLayout(thumb)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)

        filename = os.path.basename(path)
        icon = QLabel("\u2610")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 20px; color: #A8A6A2; background: transparent;")
        tl.addWidget(icon, 1)

        close_btn = QPushButton("\u2716")
        close_btn.setFixedSize(18, 18)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #E24B4A; border: none; border-radius: 9px;
                font-size: 9px; font-weight: 700; color: #ffffff;
            }
            QPushButton:hover { background: #C73A3A; }
        """)

        def remove_photo():
            if path in self._photos:
                self._photos.remove(path)
                self.files_selected.emit(self._photos)
                self._render_thumbs()

        close_btn.clicked.connect(remove_photo)

        close_wrap = QWidget()
        close_wrap.setStyleSheet("background: transparent;")
        cw_layout = QHBoxLayout(close_wrap)
        cw_layout.setContentsMargins(0, 0, 0, 0)
        cw_layout.addStretch()
        cw_layout.addWidget(close_btn)
        tl.addWidget(close_wrap)

        return thumb


class RentalCard(QFrame):
    confirm_requested = Signal(str)
    pickup_requested = Signal(str)
    return_requested = Signal(str)

    def __init__(self, rental_data, is_owner_view=False):
        super().__init__()
        self.rental_id = rental_data.get("id", "")
        self._data = rental_data
        self._is_owner = is_owner_view
        self._build(rental_data)

    def _build(self, r):
        inv_data = r.get("inventories") or {}
        user_data = r.get("users") or {}
        status = r.get("status", "")
        start = r.get("start_date", "")
        end = r.get("end_date", "")
        return_date = r.get("return_date", "")
        fine = r.get("fine_amount", 0)
        has_pickup = bool(r.get("pickup_photo_url"))
        has_return_photo = bool(r.get("return_photo_url"))
        price_per_day = inv_data.get("price_per_day", 0)
        days = 0
        try:
            sd = datetime.strptime(start, "%Y-%m-%d")
            ed = datetime.strptime(end, "%Y-%m-%d")
            days = (ed - sd).days or 1
        except ValueError:
            days = 1
        total_price = days * price_per_day

        is_overdue = status in ("active", "confirmed") and end < datetime.now().strftime("%Y-%m-%d")
        is_completed = status == "returned"

        border = "#E24B4A" if is_overdue else "#E0DDD8"
        card_style = f"""
            background: #ffffff; border: 0.5px solid {border};
            border-radius: 12px; padding: 20px;
        """
        if is_completed:
            card_style = """
                background: #F8F7F4; border: 0.5px solid #E0DDD8;
                border-radius: 12px; padding: 20px;
            """

        self.setStyleSheet(card_style)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        status_colors = {
            "pending": ("#FEF3E8", "#BA7517", "Pending"),
            "confirmed": ("#E8F7F2", "#1D9E75", "Confirmed"),
            "active": ("#E8F7F2", "#1D9E75", "Active"),
            "returned": ("#EDECE8", "#6B6A66", "Completed"),
            "rejected": ("#FDE8E8", "#E24B4A", "Rejected"),
        }
        if is_overdue:
            status_display = ("#FDE8E8", "#E24B4A", "Overdue")
        else:
            status_display = status_colors.get(status, ("#EDECE8", "#6B6A66", status.title()))

        bg, fg, label = status_display
        badge = QFrame()
        badge.setStyleSheet(f"background: {bg}; border-radius: 6px; padding: 4px;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(8, 3, 8, 3)
        bl.setSpacing(4)
        dot = QLabel("\u25cf")
        dot.setStyleSheet(f"color: {fg}; font-size: 8px; background: transparent;")
        txt = QLabel(label)
        txt.setStyleSheet(f"color: {fg}; font-size: 12px; font-weight: 500; background: transparent;")
        bl.addWidget(dot)
        bl.addWidget(txt)

        price_label = QLabel(f"Rp {total_price:,}")
        price_label.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1A1A1A;"
            if not is_completed else "font-size: 18px; font-weight: 700; color: #8C8A86;"
        )

        top_row.addWidget(badge)
        top_row.addStretch()
        top_row.addWidget(price_label)
        layout.addLayout(top_row)

        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        avatar = QFrame()
        avatar.setFixedSize(40, 40)
        if self._is_owner:
            name_initials = (user_data.get("name", "?")[:2].upper()
                             if user_data.get("name") else "?")
        else:
            name_initials = inv_data.get("name", "?")[:2].upper()
        avatar.setStyleSheet(f"""
            background: #E8F0EE; border-radius: 20px;
        """)
        al = QVBoxLayout(avatar)
        al.setAlignment(Qt.AlignCenter)
        ai = QLabel(name_initials)
        ai.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F6E56; background: transparent;")
        al.addWidget(ai)

        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        if self._is_owner:
            name_label = QLabel(user_data.get("name", "-"))
            id_label = QLabel(f"ID: {r.get('id', '')[:8].upper()}")
        else:
            name_label = QLabel(inv_data.get("name", "-"))
            id_label = QLabel(f"ID: {r.get('id', '')[:8].upper()}")
        name_label.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #1A1A1A;"
            if not is_completed else "font-size: 15px; font-weight: 600; color: #8C8A86;"
        )
        id_label.setStyleSheet("font-size: 11px; color: #A8A6A2;")
        name_col.addWidget(name_label)
        name_col.addWidget(id_label)

        info_row.addWidget(avatar)
        info_row.addLayout(name_col)
        info_row.addStretch()
        layout.addLayout(info_row)

        if is_completed and fine > 0:
            fine_label = QLabel(f"Late fee: Rp {fine:,}")
            fine_label.setStyleSheet("font-size: 12px; color: #E24B4A; font-weight: 500;")
            layout.addWidget(fine_label)

        date_row = QHBoxLayout()
        date_row.setSpacing(6)
        cal_icon = QLabel("\u23f0")
        cal_icon.setStyleSheet("font-size: 14px; color: #8C8A86; background: transparent;")
        if is_completed and return_date:
            date_text = f"Returned {return_date}"
        elif is_overdue:
            date_text = f"Due: {end} (overdue)"
        else:
            date_text = f"{start} - {end}"
        date_label = QLabel(date_text)
        date_label.setStyleSheet(
            f"font-size: 12px; color: {'#E24B4A' if is_overdue else '#8C8A86'};"
            f"{' font-weight: 500;' if is_overdue else ''}"
        )
        date_row.addWidget(cal_icon)
        date_row.addWidget(date_label)
        date_row.addStretch()
        layout.addLayout(date_row)

        if self._is_owner:
            action_row = QHBoxLayout()
            action_row.setSpacing(8)
            action_row.setContentsMargins(0, 4, 0, 0)

            btn_style = """
                QPushButton {
                    border: none; border-radius: 6px;
                    padding: 6px 14px; font-size: 12px; font-weight: 500;
                }
            """

            if status == "pending":
                btn = QPushButton("Confirm")
                btn.setStyleSheet(btn_style + "background: #0F6E56; color: white;")
                btn.clicked.connect(lambda: self.confirm_requested.emit(self.rental_id))
                action_row.addWidget(btn)
            elif status == "confirmed":
                if not has_pickup:
                    btn = QPushButton("Upload Photo")
                    btn.setStyleSheet(btn_style + "background: #0F6E56; color: white;")
                    btn.clicked.connect(lambda: self.pickup_requested.emit(self.rental_id))
                    action_row.addWidget(btn)
                if not has_return_photo:
                    btn2 = QPushButton("Process Return")
                    btn2.setStyleSheet(btn_style + "background: #E24B4A; color: white;")
                    btn2.clicked.connect(lambda: self.return_requested.emit(self.rental_id))
                    action_row.addWidget(btn2)
            elif status == "active":
                if not has_return_photo:
                    btn = QPushButton("Process Return")
                    btn.setStyleSheet(btn_style + "background: #E24B4A; color: white;")
                    btn.clicked.connect(lambda: self.return_requested.emit(self.rental_id))
                    action_row.addWidget(btn)

            if action_row.count() > 0:
                action_row.addStretch()
                layout.addLayout(action_row)


class RentalPage(QWidget):
    navigate_to = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_tab = _TAB_ALL
        self._rental_step = 1
        self._pending_rental_data = None
        self._build_ui()

    def refresh(self):
        self._load_data()
        self._toggle_visibility()

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

        title = QLabel("Penyewaan Saya")
        title.setStyleSheet("font-size: 22px; font-weight: 500; color: #1A1A1A; letter-spacing: -0.3px;")
        layout.addWidget(title)

        self.step_widget = QWidget()
        self.step_widget.setStyleSheet("background: transparent;")
        step_layout = QVBoxLayout(self.step_widget)
        step_layout.setContentsMargins(0, 0, 0, 0)
        self.step_indicator = StepIndicator(current_step=1)
        step_layout.addWidget(self.step_indicator)
        layout.addWidget(self.step_widget)

        self.form_panel = QFrame()
        self.form_panel.setObjectName("rentalFormPanel")
        self.form_panel.setStyleSheet("""
            #rentalFormPanel {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px; padding: 24px;
            }
        """)
        form_layout = QVBoxLayout(self.form_panel)
        form_layout.setSpacing(16)

        form_title = QLabel("Detail Penyewaan")
        form_title.setStyleSheet("font-size: 18px; font-weight: 500; color: #1A1A1A;")
        form_layout.addWidget(form_title)

        form_grid = QGridLayout()
        form_grid.setSpacing(12)

        input_style = """
            QComboBox, QDateEdit, QTextEdit {
                border: 0.5px solid #D4D2CD; border-radius: 8px;
                padding: 10px 12px; font-size: 14px; background: #ffffff;
            }
            QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border-color: #0F6E56;
            }
        """
        lbl_style = "font-size: 14px; font-weight: 500; color: #1A1A1A; background: transparent;"

        form_grid.addWidget(QLabel("Barang:"), 0, 0)
        self.rental_item_combo = QComboBox()
        self.rental_item_combo.setMinimumWidth(200)
        self.rental_item_combo.setStyleSheet(input_style)
        form_grid.addWidget(self.rental_item_combo, 0, 1)

        form_grid.addWidget(QLabel("Tanggal Ambil:"), 1, 0)
        self.rental_start = QDateEdit()
        self.rental_start.setCalendarPopup(True)
        self.rental_start.setDate(QDate.currentDate())
        self.rental_start.setMinimumDate(QDate.currentDate())
        self.rental_start.setStyleSheet(input_style)
        form_grid.addWidget(self.rental_start, 1, 1)

        form_grid.addWidget(QLabel("Tanggal Kembali:"), 2, 0)
        self.rental_end = QDateEdit()
        self.rental_end.setCalendarPopup(True)
        self.rental_end.setDate(QDate.currentDate().addDays(1))
        self.rental_end.setMinimumDate(QDate.currentDate().addDays(1))
        self.rental_end.setStyleSheet(input_style)
        form_grid.addWidget(self.rental_end, 2, 1)

        form_grid.addWidget(QLabel("Catatan:"), 3, 0)
        self.rental_notes = QTextEdit()
        self.rental_notes.setPlaceholderText("Catatan tambahan (opsional)...")
        self.rental_notes.setMaximumHeight(60)
        self.rental_notes.setStyleSheet(input_style)
        form_grid.addWidget(self.rental_notes, 3, 1)

        form_layout.addLayout(form_grid)

        form_btn_row = QHBoxLayout()
        form_btn_row.addStretch()
        self.btn_next_step = QPushButton("Lanjut ke Upload Foto \u2192")
        self.btn_next_step.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 12px 24px; font-size: 14px; font-weight: 600;
                color: #ffffff;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_next_step.clicked.connect(self._go_to_step2)
        form_btn_row.addWidget(self.btn_next_step)
        form_layout.addLayout(form_btn_row)

        layout.addWidget(self.form_panel)

        self.photo_panel = QFrame()
        self.photo_panel.setObjectName("photoPanel")
        self.photo_panel.setStyleSheet("""
            #photoPanel {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px; padding: 24px;
            }
        """)
        photo_layout = QVBoxLayout(self.photo_panel)
        photo_layout.setSpacing(16)

        photo_title = QLabel("Upload Foto Pengambilan")
        photo_title.setStyleSheet("font-size: 18px; font-weight: 500; color: #1A1A1A;")
        photo_layout.addWidget(photo_title)

        self.pickup_upload = PhotoUploadZone(
            max_photos=5,
            banner_text="Foto wajib diunggah sebagai bukti kondisi barang saat diambil. Minimal 1 foto, maksimal 5 foto."
        )
        photo_layout.addWidget(self.pickup_upload)

        photo_btn_row = QHBoxLayout()
        photo_btn_row.setSpacing(12)
        self.btn_back_step = QPushButton("\u2190 Kembali")
        self.btn_back_step.setStyleSheet("""
            QPushButton {
                background: transparent; border: 0.5px solid #D4D2CD;
                border-radius: 8px; padding: 12px 24px;
                font-size: 14px; font-weight: 500; color: #6B6A66;
            }
            QPushButton:hover { background: #EDECE8; }
        """)
        self.btn_back_step.clicked.connect(self._go_to_step1)

        self.btn_confirm_step = QPushButton("Lanjut ke Konfirmasi \u2192")
        self.btn_confirm_step.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 12px 24px; font-size: 14px; font-weight: 600;
                color: #ffffff;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_confirm_step.clicked.connect(self._go_to_step3)

        photo_btn_row.addWidget(self.btn_back_step)
        photo_btn_row.addStretch()
        photo_btn_row.addWidget(self.btn_confirm_step)
        photo_layout.addLayout(photo_btn_row)

        layout.addWidget(self.photo_panel)

        self.confirm_panel = QFrame()
        self.confirm_panel.setObjectName("confirmPanel")
        self.confirm_panel.setStyleSheet("""
            #confirmPanel {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px; padding: 24px;
            }
        """)
        conf_layout = QVBoxLayout(self.confirm_panel)
        conf_layout.setSpacing(16)

        conf_title = QLabel("Konfirmasi Penyewaan")
        conf_title.setStyleSheet("font-size: 18px; font-weight: 500; color: #1A1A1A;")
        conf_layout.addWidget(conf_title)

        conf_detail = QLabel("Detail penyewaan akan ditampilkan di sini sebelum submit.")
        conf_detail.setStyleSheet("font-size: 14px; color: #6B6A66;")
        conf_layout.addWidget(conf_detail)

        self.confirm_detail_widget = QWidget()
        self.confirm_detail_widget.setStyleSheet("background: transparent;")
        cd_layout = QVBoxLayout(self.confirm_detail_widget)
        cd_layout.setSpacing(8)
        self.confirm_labels = {}
        for key in ["Barang", "Tanggal Ambil", "Tanggal Kembali", "Total Harga", "Catatan"]:
            row = QHBoxLayout()
            k = QLabel(f"{key}:")
            k.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A; background: transparent;")
            v = QLabel("-")
            v.setStyleSheet("font-size: 14px; color: #6B6A66; background: transparent;")
            row.addWidget(k)
            row.addWidget(v, 1)
            cd_layout.addLayout(row)
            self.confirm_labels[key] = v
        conf_layout.addWidget(self.confirm_detail_widget)

        conf_btn_row = QHBoxLayout()
        conf_btn_row.setSpacing(12)
        self.btn_back_photo = QPushButton("\u2190 Kembali")
        self.btn_back_photo.setStyleSheet("""
            QPushButton {
                background: transparent; border: 0.5px solid #D4D2CD;
                border-radius: 8px; padding: 12px 24px;
                font-size: 14px; font-weight: 500; color: #6B6A66;
            }
            QPushButton:hover { background: #EDECE8; }
        """)
        self.btn_back_photo.clicked.connect(self._go_to_step2)

        self.btn_submit = QPushButton("Ajukan Penyewaan")
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 12px 24px; font-size: 14px; font-weight: 600;
                color: #ffffff;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_submit.clicked.connect(self._create_rental)

        conf_btn_row.addWidget(self.btn_back_photo)
        conf_btn_row.addStretch()
        conf_btn_row.addWidget(self.btn_submit)
        conf_layout.addLayout(conf_btn_row)

        layout.addWidget(self.confirm_panel)

        # --- Owner tabs + KPI + cards ---
        self.owner_header = QWidget()
        self.owner_header.setStyleSheet("background: transparent;")
        owner_header_layout = QVBoxLayout(self.owner_header)
        owner_header_layout.setContentsMargins(0, 0, 0, 0)
        owner_header_layout.setSpacing(16)

        tabs = QHBoxLayout()
        tabs.setSpacing(24)
        self._tab_buttons = {}
        for i, (name, key) in enumerate([
            ("Semua", "all"),
            ("Aktif", "active"),
            ("Terlambat", "overdue"),
            ("Selesai", "completed"),
        ]):
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._tab_style(i == 0))
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            tabs.addWidget(btn)
            self._tab_buttons[i] = btn

        tabs.addStretch()
        owner_header_layout.addLayout(tabs)

        layout.addWidget(self.owner_header)

        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self.kpi_active = self._make_kpi("Active Rentals", "0", "\u25b6", "#E8F7F2")
        self.kpi_overdue = self._make_kpi("Overdue Items", "0", "\u26a0", "#FDE8E8")
        self.kpi_revenue = self._make_kpi("Pending Revenue", "Rp 0", "\u25a8", "#EDECE8")

        kpi_layout.addWidget(self.kpi_active)
        kpi_layout.addWidget(self.kpi_overdue)
        kpi_layout.addWidget(self.kpi_revenue)
        layout.addLayout(kpi_layout)

        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(16)
        layout.addLayout(self.cards_grid)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _show_step(self, step):
        self._rental_step = step
        self.step_indicator._current_step = step
        self.step_indicator._build()

        is_customer = not is_owner()
        self.step_widget.setVisible(is_customer and step > 0)
        self.form_panel.setVisible(is_customer and step == 1)
        self.photo_panel.setVisible(is_customer and step == 2)
        self.confirm_panel.setVisible(is_customer and step == 3)

    def _go_to_step1(self):
        self._show_step(1)

    def _go_to_step2(self):
        inv_id = self.rental_item_combo.currentData()
        if not inv_id:
            QMessageBox.warning(self, "Lengkapi Data", "Pilih barang yang akan disewa.")
            return
        start = self.rental_start.date().toString("yyyy-MM-dd")
        end = self.rental_end.date().toString("yyyy-MM-dd")
        valid, msg = validate_rental_dates(start, end)
        if not valid:
            QMessageBox.warning(self, "Tanggal Tidak Valid", msg)
            return

        self._pending_rental_data = {
            "inventory_id": inv_id,
            "start": start,
            "end": end,
            "notes": self.rental_notes.toPlainText().strip(),
            "item_name": self.rental_item_combo.currentText(),
        }
        self._show_step(2)

    def _go_to_step3(self):
        photos = self.pickup_upload.get_photos()
        if len(photos) == 0:
            QMessageBox.warning(self, "Foto Diperlukan", "Minimal 1 foto pengambilan harus diunggah.")
            return

        data = self._pending_rental_data
        if data:
            self.confirm_labels["Barang"].setText(data.get("item_name", "-"))
            self.confirm_labels["Tanggal Ambil"].setText(data.get("start", "-"))
            self.confirm_labels["Tanggal Kembali"].setText(data.get("end", "-"))
            self.confirm_labels["Catatan"].setText(data.get("notes", "-") or "-")

            days = 0
            try:
                sd = datetime.strptime(data["start"], "%Y-%m-%d")
                ed = datetime.strptime(data["end"], "%Y-%m-%d")
                days = (ed - sd).days or 1
            except ValueError:
                days = 1
            price = 0
            items = get_all_inventory() or []
            for item in items:
                if item.get("id") == data["inventory_id"]:
                    price = item.get("price_per_day", 0)
                    break
            total = days * price
            self.confirm_labels["Total Harga"].setText(f"Rp {total:,}")

        self._show_step(3)

    def _create_rental(self):
        user = get_current_user()
        if not user or not self._pending_rental_data:
            return

        data = self._pending_rental_data
        result = create_rental(user["id"], data["inventory_id"], data["start"], data["end"], data["notes"])
        if result:
            rental_id = result.get("id", "")
            photos = self.pickup_upload.get_photos()
            if photos and rental_id:
                try:
                    dest = f"pickup_{rental_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    url = upload_photo(photos[0], dest)
                    set_pickup_photo(rental_id, url)
                except Exception:
                    pass

            QMessageBox.information(self, "Berhasil", "Penyewaan berhasil diajukan. Menunggu konfirmasi pemilik.")
            self.rental_notes.clear()
            self.pickup_upload.set_photos([])
            self._pending_rental_data = None
            self._show_step(1)
            self._load_data()
        else:
            QMessageBox.warning(self, "Gagal", "Penyewaan gagal diajukan.")

    def _tab_style(self, active):
        if active:
            return """
                QPushButton {
                    background: transparent; border: none;
                    border-bottom: 2px solid #0F6E56;
                    font-size: 14px; font-weight: 500; color: #0F6E56;
                    padding: 4px 0;
                }
            """
        return """
            QPushButton {
                background: transparent; border: none;
                border-bottom: 2px solid transparent;
                font-size: 14px; font-weight: 400; color: #8C8A86;
                padding: 4px 0;
            }
            QPushButton:hover { color: #0F6E56; }
        """

    def _switch_tab(self, idx):
        self._current_tab = idx
        for i, btn in self._tab_buttons.items():
            btn.setStyleSheet(self._tab_style(i == idx))
        self._load_data()

    def _make_kpi(self, title, value, icon_char, bg_color):
        card = QFrame()
        card.setStyleSheet(f"""
            background: #ffffff; border: 0.5px solid #E0DDD8;
            border-radius: 12px; padding: 20px;
        """)
        layout = QHBoxLayout(card)
        layout.setSpacing(16)

        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(f"background: {bg_color}; border-radius: 22px;")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel(icon_char)
        icon_lbl.setStyleSheet("font-size: 18px; color: #0F6E56; background: transparent;")
        il.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 12px; color: #8C8A86; background: transparent;")
        self._kpi_values[title] = QLabel(value)
        self._kpi_values[title].setStyleSheet("font-size: 22px; font-weight: 700; color: #1A1A1A; background: transparent;")
        text_col.addWidget(lbl_title)
        text_col.addWidget(self._kpi_values[title])

        layout.addWidget(icon_frame)
        layout.addLayout(text_col, 1)
        return card

    _kpi_values = {}

    def _toggle_visibility(self):
        user = get_current_user()
        if not user:
            return
        is_owner_view = is_owner()

        self.owner_header.setVisible(is_owner_view)
        self.step_widget.setVisible(not is_owner_view)
        self.form_panel.setVisible(not is_owner_view and self._rental_step == 1)
        self.photo_panel.setVisible(not is_owner_view and self._rental_step == 2)
        self.confirm_panel.setVisible(not is_owner_view and self._rental_step == 3)

        if not is_owner_view:
            self.rental_item_combo.clear()
            items = get_all_inventory() or []
            for item in items:
                if item.get("stock", 0) > 0:
                    self.rental_item_combo.addItem(
                        f"{item['name']} (Rp {item['price_per_day']:,}/day)",
                        item["id"]
                    )

    def _load_data(self):
        user = get_current_user()
        if not user:
            return

        is_owner_view = is_owner()
        rentals = (get_rentals_for_owner() if is_owner_view
                   else get_rentals_for_customer(user["id"])) or []

        now = datetime.now().strftime("%Y-%m-%d")
        if self._current_tab == _TAB_ACTIVE:
            rentals = [r for r in rentals if r.get("status") in ("confirmed", "active")]
        elif self._current_tab == _TAB_OVERDUE:
            rentals = [r for r in rentals
                       if r.get("status") in ("confirmed", "active")
                       and r.get("end_date", "0000") < now]
        elif self._current_tab == _TAB_COMPLETED:
            rentals = [r for r in rentals if r.get("status") == "returned"]

        all_rentals = (get_rentals_for_owner() if is_owner_view
                       else get_rentals_for_customer(user["id"])) or []
        active_kpi = sum(1 for r in all_rentals if r.get("status") in ("confirmed", "active"))
        overdue_kpi = sum(1 for r in all_rentals
                          if r.get("status") in ("confirmed", "active")
                          and r.get("end_date", "0000") < now)
        total_revenue = sum(
            r.get("fine_amount", 0) + (
                (datetime.strptime(r.get("end_date", "now"), "%Y-%m-%d") -
                 datetime.strptime(r.get("start_date", "now"), "%Y-%m-%d")).days or 1
            ) * (r.get("inventories", {}).get("price_per_day", 0) or 0)
            for r in all_rentals if r.get("status") in ("confirmed", "active", "returned")
        )

        if "Active Rentals" in self._kpi_values:
            self._kpi_values["Active Rentals"].setText(str(active_kpi))
        if "Overdue Items" in self._kpi_values:
            self._kpi_values["Overdue Items"].setText(str(overdue_kpi))
        if "Pending Revenue" in self._kpi_values:
            self._kpi_values["Pending Revenue"].setText(f"Rp {total_revenue:,}")

        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rentals:
            empty = QLabel("No rentals found.")
            empty.setStyleSheet("font-size: 14px; color: #8C8A86; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            self.cards_grid.addWidget(empty, 0, 0, 1, 1)
        else:
            cols = 3
            for i, r in enumerate(rentals):
                card = RentalCard(r, is_owner_view=is_owner_view)
                card.confirm_requested.connect(self._confirm_rental)
                card.pickup_requested.connect(self._upload_pickup)
                card.return_requested.connect(self._process_return)
                self.cards_grid.addWidget(card, i // cols, i % cols)

    def _confirm_rental(self, rental_id):
        ok = confirm_rental(rental_id)
        if ok:
            self._load_data()
        else:
            QMessageBox.warning(self, "Gagal", "Konfirmasi gagal.")

    def _upload_pickup(self, rental_id):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        try:
            dest = f"pickup_{rental_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            url = upload_photo(path, dest)
            ok = set_pickup_photo(rental_id, url)
            if ok:
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Foto gagal disimpan.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Upload gagal:\n{str(e)}")

    def _process_return(self, rental_id):
        all_rentals = get_rentals_for_owner() if is_owner() else []
        end_date = "2025-01-01"
        for r in all_rentals:
            if r.get("id") == rental_id:
                end_date = r.get("end_date", "2025-01-01")
                break

        path, _ = QFileDialog.getOpenFileName(self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return

        return_date = datetime.now().strftime("%Y-%m-%d")
        try:
            dest = f"return_{rental_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            url = upload_photo(path, dest)
            result = process_return(rental_id, return_date, url, end_date)
            if result["success"]:
                fine = result["fine"]
                msg = "Return processed."
                if fine > 0:
                    msg += f"\nLate fee: Rp {fine:,}"
                QMessageBox.information(self, "Success", msg)
                self._load_data()
            else:
                QMessageBox.warning(self, "Gagal", "Return gagal diproses.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Upload gagal:\n{str(e)}")
