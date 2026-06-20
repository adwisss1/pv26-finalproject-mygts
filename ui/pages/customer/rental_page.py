import os
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QFileDialog, QGridLayout,
    QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpacerItem, QSizePolicy
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


# ─────────────────────────────────────────────────────────────────────────────
#  WIDGETS HELPER
# ─────────────────────────────────────────────────────────────────────────────

class StepIndicator(QFrame):
    def __init__(self, current_step=1):
        super().__init__()
        self._current_step = current_step
        self.setFixedWidth(500)  # Batasi lebar agar tidak melar
        self.setStyleSheet("background: transparent;")
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
            sw_layout = QVBoxLayout(step_wrap)
            sw_layout.setContentsMargins(0, 0, 0, 0)
            sw_layout.setAlignment(Qt.AlignCenter)
            sw_layout.setSpacing(8)

            circle = QFrame()
            circle.setFixedSize(32, 32)
            cl = QVBoxLayout(circle)
            cl.setAlignment(Qt.AlignCenter)
            cl.setContentsMargins(0,0,0,0)
            
            ci = QLabel("\u2713" if num < self._current_step else str(num))
            
            if num < self._current_step:
                circle.setStyleSheet("background: #0F6E56; border-radius: 16px;")
                ci.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff; background: transparent;")
            elif num == self._current_step:
                circle.setStyleSheet("background: #0F6E56; border-radius: 16px;")
                ci.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff; background: transparent;")
            else:
                circle.setStyleSheet("background: #ffffff; border: 2px solid #D4D2CD; border-radius: 16px;")
                ci.setStyleSheet("font-size: 14px; font-weight: bold; color: #A8A6A2; background: transparent;")
            
            cl.addWidget(ci)
            sw_layout.addWidget(circle, 0, Qt.AlignCenter)

            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignCenter)
            if num <= self._current_step:
                lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #0F6E56; background: transparent;")
            else:
                lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #A8A6A2; background: transparent;")
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
            info_icon.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A7DC7; background: transparent;")
            bl.addWidget(info_icon)
            banner_label = QLabel(banner_text)
            banner_label.setStyleSheet("font-size: 13px; color: #4A7DC7; background: transparent;")
            banner_label.setWordWrap(True)
            bl.addWidget(banner_label, 1)
            layout.addWidget(banner)

        drop_area = QFrame()
        drop_area.setFixedHeight(180)
        drop_area.setStyleSheet("""
            QFrame { background: #FAF9F6; border: 2px dashed #D4D2CD; border-radius: 12px; }
            QFrame:hover { border-color: #0F6E56; background: #F4F9F8; }
        """)
        drop_area.setCursor(Qt.PointingHandCursor)
        dl = QVBoxLayout(drop_area)
        dl.setAlignment(Qt.AlignCenter)
        dl.setSpacing(8)

        upload_icon = QLabel("\u2601")
        upload_icon.setStyleSheet("font-size: 40px; color: #A8A6A2; background: transparent; border: none;")
        dl.addWidget(upload_icon, 0, Qt.AlignCenter)

        upload_text = QLabel("Klik atau seret foto ke sini")
        upload_text.setStyleSheet("font-size: 15px; font-weight: bold; color: #1A1A1A; background: transparent; border: none;")
        dl.addWidget(upload_text, 0, Qt.AlignCenter)

        upload_sub = QLabel("Format: JPG, PNG. Maks 5MB per foto")
        upload_sub.setStyleSheet("font-size: 12px; color: #A8A6A2; background: transparent; border: none;")
        dl.addWidget(upload_sub, 0, Qt.AlignCenter)

        def on_click(event):
            paths, _ = QFileDialog.getOpenFileNames(self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)")
            if paths:
                remaining = self._max - len(self._photos)
                self._photos.extend(paths[:remaining])
                self.files_selected.emit(self._photos)
                self._render_thumbs()

        drop_area.mousePressEvent = on_click
        layout.addWidget(drop_area)

        self.thumb_row = QHBoxLayout()
        self.thumb_row.setContentsMargins(0, 0, 0, 0)
        self.thumb_row.setSpacing(12)
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
            if item.widget(): item.widget().deleteLater()

        for path in self._photos:
            self.thumb_row.addWidget(self._make_thumb(path))

        if len(self._photos) < self._max:
            add_btn = QPushButton("+")
            add_btn.setFixedSize(80, 80)
            add_btn.setCursor(Qt.PointingHandCursor)
            add_btn.setStyleSheet("QPushButton { background: #FAF9F6; border: 1.5px dashed #D4D2CD; border-radius: 8px; font-size: 28px; color: #A8A6A2; } QPushButton:hover { border-color: #0F6E56; color: #0F6E56; }")
            
            def on_add(event):
                paths, _ = QFileDialog.getOpenFileNames(self, "Pilih Foto", "", "Images (*.png *.jpg *.jpeg)")
                if paths:
                    self._photos.extend(paths[:self._max - len(self._photos)])
                    self.files_selected.emit(self._photos)
                    self._render_thumbs()
                    
            add_btn.clicked.connect(on_add)
            self.thumb_row.addWidget(add_btn)

        self.thumb_row.addStretch()

    def _make_thumb(self, path):
        thumb = QFrame()
        thumb.setFixedSize(80, 80)
        thumb.setStyleSheet("background: #EDECE8; border: 1px solid #E0DDD8; border-radius: 8px;")
        tl = QVBoxLayout(thumb)
        tl.setContentsMargins(0, 0, 0, 0)
        
        icon = QLabel("\u2610")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 24px; color: #A8A6A2; background: transparent; border:none;")
        tl.addWidget(icon, 1)

        close_btn = QPushButton("\u2716")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton { background: #E24B4A; border: none; border-radius: 10px; font-size: 10px; font-weight: bold; color: #ffffff; } QPushButton:hover { background: #C73A3A; }")
        
        def remove_photo():
            if path in self._photos:
                self._photos.remove(path)
                self.files_selected.emit(self._photos)
                self._render_thumbs()

        close_btn.clicked.connect(remove_photo)
        
        cw = QWidget(styleSheet="background:transparent;")
        cw_l = QHBoxLayout(cw)
        cw_l.setContentsMargins(0,4,4,0)
        cw_l.addStretch()
        cw_l.addWidget(close_btn)
        
        thumb.setLayout(QVBoxLayout())
        thumb.layout().setContentsMargins(0,0,0,0)
        thumb.layout().addWidget(cw)
        thumb.layout().addWidget(icon)
        thumb.layout().addStretch()
        
        return thumb

# --- (RentalCard diabaikan karena hanya untuk Owner, tapi dibiarkan agar kodenya tidak error) ---
class RentalCard(QFrame):
    # Dummy class agar fungsi Owner tetap jalan
    confirm_requested = Signal(str)
    pickup_requested = Signal(str)
    return_requested = Signal(str)
    def __init__(self, rental_data, is_owner_view=False):
        super().__init__()
        self.rental_id = rental_data.get("id", "")

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN RENTAL PAGE (CUSTOMER WIZARD)
# ─────────────────────────────────────────────────────────────────────────────

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
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget(styleSheet="background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 40)
        layout.setSpacing(28)

        title = QLabel("Penyewaan Saya")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1A1A1A; letter-spacing: -0.5px;")
        layout.addWidget(title)

        # ── CUSTOMER WIZARD CONTAINER ──
        # Menggunakan Alignment Center agar form tidak melar ke seluruh layar
        self.customer_container = QWidget(styleSheet="background: transparent;")
        cust_layout = QVBoxLayout(self.customer_container)
        cust_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        cust_layout.setContentsMargins(0, 0, 0, 0)
        cust_layout.setSpacing(24)

        self.step_indicator = StepIndicator(current_step=1)
        cust_layout.addWidget(self.step_indicator, 0, Qt.AlignHCenter)

        # Panel Lebar Tetap (600px)
        panel_style = """
            QFrame { background: #ffffff; border: 1px solid #E0DDD8; border-radius: 16px; padding: 32px; }
        """

        # STEP 1: FORM
        self.form_panel = QFrame()
        self.form_panel.setFixedWidth(700)
        self.form_panel.setStyleSheet(panel_style)
        form_layout = QVBoxLayout(self.form_panel)
        form_layout.setSpacing(18)
        form_layout.setContentsMargins(32, 28, 32, 28)

        form_title = QLabel("Detail Penyewaan")
        form_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1A1A1A; border: none;")
        form_layout.addWidget(form_title)

        input_style = """
            QComboBox, QDateEdit, QTextEdit {
                border: 1px solid #D4D2CD; border-radius: 8px; padding: 12px 14px; font-size: 13px; background: #ffffff;
            }
            QComboBox:focus, QDateEdit:focus, QTextEdit:focus { border-color: #0F6E56; }
            QComboBox::drop-down { border: none; width: 30px; }
        """
        lbl_style = "font-size: 13px; font-weight: 600; color: #6B6A66; border: none;"

        def add_field(label_text, widget):
            lay = QVBoxLayout()
            lay.setSpacing(6)
            lbl = QLabel(label_text, styleSheet=lbl_style)
            lay.addWidget(lbl)
            lay.addWidget(widget)
            form_layout.addLayout(lay)

        self.rental_item_combo = QComboBox()
        self.rental_item_combo.setStyleSheet(input_style)
        add_field("Pilih Barang yang Disewa", self.rental_item_combo)

        date_row = QHBoxLayout()
        date_row.setSpacing(16)
        
        start_lay = QVBoxLayout(); start_lay.setSpacing(6)
        start_lay.addWidget(QLabel("Tanggal Ambil", styleSheet=lbl_style))
        self.rental_start = QDateEdit(calendarPopup=True)
        self.rental_start.setDate(QDate.currentDate())
        self.rental_start.setMinimumDate(QDate.currentDate())
        self.rental_start.setDisplayFormat("yyyy-MM-dd")
        self.rental_start.setStyleSheet(input_style)
        start_lay.addWidget(self.rental_start)
        
        end_lay = QVBoxLayout(); end_lay.setSpacing(6)
        end_lay.addWidget(QLabel("Tanggal Kembali", styleSheet=lbl_style))
        self.rental_end = QDateEdit(calendarPopup=True)
        self.rental_end.setDate(QDate.currentDate().addDays(1))
        self.rental_end.setMinimumDate(QDate.currentDate().addDays(1))
        self.rental_end.setDisplayFormat("yyyy-MM-dd")
        self.rental_end.setStyleSheet(input_style)
        end_lay.addWidget(self.rental_end)
        
        date_row.addLayout(start_lay)
        date_row.addLayout(end_lay)
        form_layout.addLayout(date_row)

        self.rental_notes = QTextEdit()
        self.rental_notes.setPlaceholderText("Misal: Diambil jam 10 pagi, atau ada request khusus...")
        self.rental_notes.setMaximumHeight(80)
        self.rental_notes.setStyleSheet(input_style)
        add_field("Catatan Tambahan (Opsional)", self.rental_notes)

        form_layout.addSpacing(8)
        self.btn_next_step = QPushButton("Lanjut Upload Foto \u2192")
        self.btn_next_step.setCursor(Qt.PointingHandCursor)
        self.btn_next_step.setFixedHeight(44)
        self.btn_next_step.setStyleSheet("QPushButton { background: #0F6E56; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; color: #ffffff; } QPushButton:hover { background: #0A5A45; }")
        self.btn_next_step.clicked.connect(self._go_to_step2)
        form_layout.addWidget(self.btn_next_step)

        # STEP 2: PHOTO UPLOAD
        self.photo_panel = QFrame()
        self.photo_panel.setFixedWidth(700)
        self.photo_panel.setStyleSheet(panel_style)
        photo_layout = QVBoxLayout(self.photo_panel)
        photo_layout.setSpacing(18)
        photo_layout.setContentsMargins(32, 28, 32, 28)

        photo_layout.addWidget(QLabel("Upload Foto Pengambilan", styleSheet="font-size: 20px; font-weight: bold; color: #1A1A1A; border: none;"))
        self.pickup_upload = PhotoUploadZone(max_photos=5, banner_text="Foto wajib diunggah sebagai bukti kondisi barang saat diambil.")
        photo_layout.addWidget(self.pickup_upload)

        photo_btn_row = QHBoxLayout()
        photo_btn_row.setSpacing(12)
        
        self.btn_back_step = QPushButton("\u2190 Kembali")
        self.btn_back_step.setCursor(Qt.PointingHandCursor)
        self.btn_back_step.setFixedHeight(44)
        self.btn_back_step.setStyleSheet("QPushButton { background: #ffffff; border: 1px solid #D4D2CD; border-radius: 8px; font-size: 14px; font-weight: 600; color: #6B6A66; } QPushButton:hover { background: #F0EFEB; }")
        self.btn_back_step.clicked.connect(self._go_to_step1)
        
        self.btn_confirm_step = QPushButton("Lanjut Konfirmasi \u2192")
        self.btn_confirm_step.setCursor(Qt.PointingHandCursor)
        self.btn_confirm_step.setFixedHeight(44)
        self.btn_confirm_step.setStyleSheet("QPushButton { background: #0F6E56; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; color: #ffffff; } QPushButton:hover { background: #0A5A45; }")
        self.btn_confirm_step.clicked.connect(self._go_to_step3)
        
        photo_btn_row.addWidget(self.btn_back_step)
        photo_btn_row.addStretch()
        photo_btn_row.addWidget(self.btn_confirm_step)
        photo_layout.addLayout(photo_btn_row)

        # STEP 3: CONFIRMATION
        self.confirm_panel = QFrame()
        self.confirm_panel.setFixedWidth(700)
        self.confirm_panel.setStyleSheet(panel_style)
        conf_layout = QVBoxLayout(self.confirm_panel)
        conf_layout.setSpacing(18)
        conf_layout.setContentsMargins(32, 28, 32, 28)

        conf_layout.addWidget(QLabel("Konfirmasi Penyewaan", styleSheet="font-size: 20px; font-weight: bold; color: #1A1A1A; border: none;", alignment=Qt.AlignCenter))
        conf_layout.addWidget(QLabel("Mohon periksa kembali detail pesanan Anda sebelum diajukan.", styleSheet="font-size: 13px; color: #8C8A86; border: none;", alignment=Qt.AlignCenter))

        self.confirm_detail_widget = QFrame(styleSheet="background: #FAFAF9; border: 1.5px dashed #D4D2CD; border-radius: 12px; padding: 20px;")
        cd_layout = QVBoxLayout(self.confirm_detail_widget)
        cd_layout.setSpacing(12)
        
        self.confirm_labels = {}
        for key in ["Barang", "Tanggal Ambil", "Tanggal Kembali", "Catatan"]:
            row = QHBoxLayout()
            k = QLabel(f"{key}")
            k.setStyleSheet("font-size: 13px; font-weight: 600; color: #8C8A86; border: none;")
            v = QLabel("-")
            v.setStyleSheet("font-size: 13px; font-weight: 600; color: #1A1A1A; border: none;")
            v.setAlignment(Qt.AlignRight)
            row.addWidget(k); row.addWidget(v, 1)
            cd_layout.addLayout(row)
            self.confirm_labels[key] = v
            
        cd_layout.addWidget(QFrame(styleSheet="background: #D4D2CD; max-height: 1px; margin: 8px 0; border: none;"))
        
        total_row = QHBoxLayout()
        total_lbl = QLabel("Total Biaya")
        total_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #1A1A1A; border: none;")
        self.confirm_labels["Total Harga"] = QLabel("Rp 0")
        self.confirm_labels["Total Harga"].setStyleSheet("font-size: 18px; font-weight: 700; color: #0F6E56; border: none;")
        self.confirm_labels["Total Harga"].setAlignment(Qt.AlignRight)
        total_row.addWidget(total_lbl); total_row.addWidget(self.confirm_labels["Total Harga"])
        cd_layout.addLayout(total_row)
        
        conf_layout.addWidget(self.confirm_detail_widget)

        conf_btn_row = QHBoxLayout()
        conf_btn_row.setSpacing(12)
        
        self.btn_back_photo = QPushButton("\u2190 Edit Foto")
        self.btn_back_photo.setCursor(Qt.PointingHandCursor)
        self.btn_back_photo.setFixedHeight(44)
        self.btn_back_photo.setStyleSheet("QPushButton { background: #ffffff; border: 1px solid #D4D2CD; border-radius: 8px; font-size: 14px; font-weight: 600; color: #6B6A66; } QPushButton:hover { background: #F0EFEB; }")
        self.btn_back_photo.clicked.connect(self._go_to_step2)

        self.btn_submit = QPushButton("\u2713 Ajukan Penyewaan")
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.setFixedHeight(44)
        self.btn_submit.setStyleSheet("QPushButton { background: #0F6E56; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; color: #ffffff; } QPushButton:hover { background: #0A5A45; }")
        self.btn_submit.clicked.connect(self._create_rental)

        conf_btn_row.addWidget(self.btn_back_photo)
        conf_btn_row.addStretch()
        conf_btn_row.addWidget(self.btn_submit)
        conf_layout.addLayout(conf_btn_row)

        cust_layout.addWidget(self.form_panel)
        cust_layout.addWidget(self.photo_panel)
        cust_layout.addWidget(self.confirm_panel)
        layout.addWidget(self.customer_container)

        # ── OWNER CONTAINER (Sembunyikan dari Customer!) ──
        self.owner_container = QWidget(styleSheet="background: transparent;")
        owner_layout = QVBoxLayout(self.owner_container)
        owner_layout.setContentsMargins(0, 0, 0, 0)
        owner_layout.setSpacing(20)
        
        # Tabs
        self.owner_header = QWidget(styleSheet="background: transparent;")
        owner_header_layout = QVBoxLayout(self.owner_header)
        owner_header_layout.setContentsMargins(0, 0, 0, 0)
        tabs = QHBoxLayout()
        self._tab_buttons = {}
        for i, (name, key) in enumerate([("Semua", "all"), ("Aktif", "active"), ("Terlambat", "overdue"), ("Selesai", "completed")]):
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._tab_style(i == 0))
            btn.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            tabs.addWidget(btn)
            self._tab_buttons[i] = btn
        tabs.addStretch()
        owner_header_layout.addLayout(tabs)
        owner_layout.addWidget(self.owner_header)

        # KPIs
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)
        self.kpi_active = self._make_kpi("Active Rentals", "0", "\u25b6", "#E8F7F2")
        self.kpi_overdue = self._make_kpi("Overdue Items", "0", "\u26a0", "#FDE8E8")
        self.kpi_revenue = self._make_kpi("Pending Revenue", "Rp 0", "\u25a8", "#EDECE8")
        kpi_layout.addWidget(self.kpi_active)
        kpi_layout.addWidget(self.kpi_overdue)
        kpi_layout.addWidget(self.kpi_revenue)
        owner_layout.addLayout(kpi_layout)

        # Grid Cards
        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(16)
        owner_layout.addLayout(self.cards_grid)
        
        layout.addWidget(self.owner_container)
        # ──────────────────────────────────────────────────

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _show_step(self, step):
        self._rental_step = step
        self.step_indicator._current_step = step
        self.step_indicator._build()
        self.step_indicator.update()  # Force repaint
        self.step_indicator.repaint()

        is_customer = not is_owner()
        self.customer_container.setVisible(is_customer)
        self.form_panel.setVisible(is_customer and step == 1)
        self.photo_panel.setVisible(is_customer and step == 2)
        self.confirm_panel.setVisible(is_customer and step == 3)

    def _go_to_step1(self): self._show_step(1)

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
            "inventory_id": inv_id, "start": start, "end": end,
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
            self.confirm_labels["Barang"].setText(data.get("item_name", "-").split(" (Rp")[0])
            self.confirm_labels["Tanggal Ambil"].setText(data.get("start", "-"))
            self.confirm_labels["Tanggal Kembali"].setText(data.get("end", "-"))
            self.confirm_labels["Catatan"].setText(data.get("notes", "-") or "-")

            days = 1
            try:
                sd = datetime.strptime(data["start"], "%Y-%m-%d")
                ed = datetime.strptime(data["end"], "%Y-%m-%d")
                days = max(1, (ed - sd).days)
            except: pass
            
            price = 0
            items = get_all_inventory() or []
            for item in items:
                if item.get("id") == data["inventory_id"]:
                    price = item.get("price_per_day", 0)
                    break
            
            total = days * price
            self.confirm_labels["Total Harga"].setText(f"Rp {total:,.0f}".replace(",", "."))

        self._show_step(3)

    def _create_rental(self):
        user = get_current_user()
        if not user or not self._pending_rental_data: return

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
                except: pass

            QMessageBox.information(self, "Sukses!", "Penyewaan berhasil diajukan.\nMohon tunggu konfirmasi dari pemilik sanggar.")
            self.rental_notes.clear()
            self.pickup_upload.set_photos([])
            self._pending_rental_data = None
            self._show_step(1)
            self.navigate_to.emit("history") # Langsung arahkan ke history
        else:
            QMessageBox.warning(self, "Gagal", "Penyewaan gagal diajukan.")

    def _tab_style(self, active):
        return """
            QPushButton { background: transparent; border: none; border-bottom: 3px solid #0F6E56; font-size: 14px; font-weight: bold; color: #0F6E56; padding: 10px 0; }
        """ if active else """
            QPushButton { background: transparent; border: none; border-bottom: 3px solid transparent; font-size: 14px; font-weight: bold; color: #8C8A86; padding: 10px 0; }
            QPushButton:hover { color: #0F6E56; }
        """

    def _switch_tab(self, idx):
        self._current_tab = idx
        for i, btn in self._tab_buttons.items():
            btn.setStyleSheet(self._tab_style(i == idx))
        self._load_data()

    def _make_kpi(self, title, value, icon_char, bg_color):
        card = QFrame(styleSheet="background: #ffffff; border: 1px solid #E0DDD8; border-radius: 12px; padding: 20px;")
        layout = QHBoxLayout(card)
        layout.setSpacing(16)

        icon_frame = QFrame(fixedSize=QSize(48, 48), styleSheet=f"background: {bg_color}; border-radius: 24px;")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        il.addWidget(QLabel(icon_char, styleSheet="font-size: 20px; color: #0F6E56; background: transparent; border:none;"))

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addWidget(QLabel(title, styleSheet="font-size: 13px; font-weight:bold; color: #8C8A86; background: transparent; border:none;"))
        self._kpi_values[title] = QLabel(value, styleSheet="font-size: 24px; font-weight: bold; color: #1A1A1A; background: transparent; border:none;")
        text_col.addWidget(self._kpi_values[title])

        layout.addWidget(icon_frame)
        layout.addLayout(text_col, 1)
        return card

    _kpi_values = {}

    def _toggle_visibility(self):
        user = get_current_user()
        if not user: return
        
        is_owner_view = is_owner()
        # Perbaikan Bug: Hide total container Owner
        self.owner_container.setVisible(is_owner_view)
        
        if not is_owner_view:
            self._show_step(1)
            self.rental_item_combo.clear()
            items = get_all_inventory() or []
            for item in items:
                if item.get("stock", 0) > 0:
                    price_str = f"Rp {item['price_per_day']:,.0f}".replace(",", ".")
                    self.rental_item_combo.addItem(f"{item['name']} ({price_str}/hari)", item["id"])

    def _load_data(self):
        user = get_current_user()
        if not user: return

        if is_owner():
            # Owner logic dummy biarkan jalan agar tidak error
            pass


    def _create_rental(self):
        user = get_current_user()
        if not user or not self._pending_rental_data: 
            return

        data = self._pending_rental_data
        result = create_rental(user["id"], data["inventory_id"], data["start"], data["end"], data["notes"])
        
        if result:
            rental_id = result.get("id", "")
            photos = self.pickup_upload.get_photos()
            
            # Proses upload foto jika ada
            if photos and rental_id:
                try:
                    dest = f"pickup_{rental_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    url = upload_photo(photos[0], dest)
                    set_pickup_photo(rental_id, url)
                except: 
                    pass

            QMessageBox.information(self, "Sukses!", "Penyewaan berhasil diajukan.\nMohon tunggu konfirmasi dari pemilik sanggar.")
            
            # 1. Reset form kembali ke kondisi awal (Langkah 1)
            self.rental_notes.clear()
            self.pickup_upload.set_photos([])
            self._pending_rental_data = None
            self._show_step(1)
            
            # 2. Pindah paksa ke halaman "Riwayat Sewa" untuk melihat status
            self.navigate_to.emit("history") 
            
        else:
            QMessageBox.warning(self, "Gagal", "Penyewaan gagal diajukan. Periksa koneksi atau coba lagi.")