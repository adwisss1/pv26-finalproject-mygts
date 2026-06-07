from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QMessageBox, QGridLayout, QDialog
)
from PySide6.QtCore import Qt, Signal

from controllers.inventory_controller import get_inventory_by_id, update_inventory, CATEGORIES
from controllers.rental_controller import get_rentals_by_inventory
from controllers.auth_controller import is_owner


_CONDITION_COLORS = {
    "Baik": ("#E8F7F2", "#1D9E75", "#1D9E75", "Available"),
    "Rusak Ringan": ("#FEF3E8", "#BA7517", "#BA7517", "Maintenance"),
    "Rusak Berat": ("#FDE8E8", "#E24B4A", "#E24B4A", "Maintenance"),
}


class SpecRow(QWidget):
    def __init__(self, label, value, icon_char=""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        left = QVBoxLayout()
        left.setSpacing(2)
        lbl_label = QLabel(label)
        lbl_label.setStyleSheet("font-size: 12px; color: #8C8A86; background: transparent;")
        value_style = "font-size: 14px; font-weight: 500; color: #1A1A1A;"
        if icon_char:
            self.value_label = QLabel(f"{icon_char}  {value}")
        else:
            self.value_label = QLabel(value)
        self.value_label.setStyleSheet(value_style + "background: transparent;")

        left.addWidget(lbl_label)
        left.addWidget(self.value_label)
        layout.addLayout(left)

    def set_value(self, text):
        self.value_label.setText(text)


class HistoryItem(QFrame):
    def __init__(self, icon_char, title, subtitle, note=""):
        super().__init__()
        self.setStyleSheet("""
            background: transparent;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet("background: #F8F7F4; border-radius: 18px;")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel(icon_char)
        icon_lbl.setStyleSheet("font-size: 14px; color: #0F6E56; background: transparent;")
        il.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        t1 = QLabel(title)
        t1.setStyleSheet("font-size: 13px; font-weight: 500; color: #1A1A1A; background: transparent;")
        t2 = QLabel(subtitle)
        t2.setStyleSheet("font-size: 11px; color: #8C8A86; background: transparent;")
        text_col.addWidget(t1)
        text_col.addWidget(t2)

        layout.addWidget(icon_frame)
        layout.addLayout(text_col, 1)


class ItemDetailPage(QWidget):
    navigate_to = Signal(str)
    _current_item_id = None

    def __init__(self):
        super().__init__()
        self._build_ui()

    def load_item(self, item_id):
        self._current_item_id = item_id
        self.refresh()

    def refresh(self):
        if self._current_item_id:
            self._load_data(self._current_item_id)

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
        layout.setSpacing(24)

        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        breadcrumb = QHBoxLayout()
        breadcrumb.setSpacing(8)

        self.btn_back = QPushButton("\u2190  Back to Inventory")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 13px; color: #8C8A86; padding: 4px 0;
            }
            QPushButton:hover { color: #0F6E56; }
        """)
        self.btn_back.clicked.connect(lambda: self.navigate_to.emit("inventory"))

        self.bc_category = QLabel()
        self.bc_category.setStyleSheet("font-size: 13px; color: #8C8A86;")
        sep1 = QLabel("/")
        sep1.setStyleSheet("font-size: 13px; color: #8C8A86;")
        self.bc_name = QLabel()
        self.bc_name.setStyleSheet("font-size: 13px; font-weight: 500; color: #1A1A1A;")

        breadcrumb.addWidget(self.btn_back)
        breadcrumb.addWidget(sep1)
        breadcrumb.addWidget(self.bc_category)
        breadcrumb.addStretch()

        self.btn_maintenance = QPushButton("Set Maintenance")
        self.btn_maintenance.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 0.5px solid #0F6E56;
                border-radius: 8px; padding: 10px 20px;
                font-size: 13px; font-weight: 500; color: #0F6E56;
            }
            QPushButton:hover { background: #F8F7F4; }
        """)
        self.btn_maintenance.clicked.connect(self._toggle_maintenance)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background: #0F6E56; border: none; border-radius: 8px;
                padding: 10px 20px; font-size: 13px; font-weight: 600; color: #ffffff;
            }
            QPushButton:hover { background: #0A5A45; }
        """)
        self.btn_edit.clicked.connect(self._edit_item)

        header_row.addLayout(breadcrumb)
        header_row.addStretch()
        header_row.addWidget(self.btn_maintenance)
        header_row.addWidget(self.btn_edit)
        layout.addLayout(header_row)

        bento = QHBoxLayout()
        bento.setSpacing(24)

        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        self.image_card = QFrame()
        self.image_card.setObjectName("imageCard")
        self.image_card.setMinimumHeight(320)
        self.image_card.setStyleSheet("""
            #imageCard {
                background: #EDECE8; border: 0.5px solid #E0DDD8;
                border-radius: 12px;
            }
        """)
        img_layout = QVBoxLayout(self.image_card)
        img_layout.setAlignment(Qt.AlignCenter)
        self.img_placeholder = QLabel("\u2610")
        self.img_placeholder.setStyleSheet("font-size: 64px; color: #A8A6A2; background: transparent;")
        self.img_status_badge = QLabel()
        self.img_status_badge.setStyleSheet("""
            background: #E8F7F2; color: #1D9E75; font-size: 12px;
            font-weight: 500; padding: 6px 14px; border-radius: 8px;
        """)
        img_layout.addWidget(self.img_placeholder)

        status_row = QHBoxLayout()
        status_row.addStretch()
        status_row.addWidget(self.img_status_badge)
        img_layout.addLayout(status_row)

        left_col.addWidget(self.image_card)

        thumb_row = QHBoxLayout()
        thumb_row.setSpacing(8)
        for color in ["#EDECE8", "#F0EFEA", "#F3F2EE"]:
            thumb = QFrame()
            thumb.setFixedSize(72, 72)
            thumb.setStyleSheet(f"background: {color}; border: 0.5px solid #E0DDD8; border-radius: 8px;")
            tl = QVBoxLayout(thumb)
            tl.setAlignment(Qt.AlignCenter)
            ti = QLabel("\u2610")
            ti.setStyleSheet("font-size: 20px; color: #A8A6A2; background: transparent;")
            tl.addWidget(ti)
            thumb_row.addWidget(thumb)

        thumb_row.addStretch()
        left_col.addLayout(thumb_row)

        left_widget = QWidget()
        left_widget.setLayout(left_col)

        right_col = QVBoxLayout()
        right_col.setSpacing(20)

        self.info_card = QFrame()
        self.info_card.setObjectName("infoCard")
        self.info_card.setStyleSheet("""
            #infoCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px; padding: 24px;
            }
        """)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setSpacing(16)

        name_price = QHBoxLayout()
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        self.detail_name = QLabel()
        self.detail_name.setStyleSheet("font-size: 22px; font-weight: 600; color: #1A1A1A;")
        self.detail_sku = QLabel()
        self.detail_sku.setStyleSheet("font-size: 13px; color: #8C8A86;")
        name_col.addWidget(self.detail_name)
        name_col.addWidget(self.detail_sku)

        price_col = QVBoxLayout()
        price_col.setAlignment(Qt.AlignRight)
        self.detail_price = QLabel()
        self.detail_price.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F6E56;")
        self.detail_price_per = QLabel("per day")
        self.detail_price_per.setStyleSheet("font-size: 12px; color: #8C8A86;")
        price_col.addWidget(self.detail_price)
        price_col.addWidget(self.detail_price_per)

        name_price.addLayout(name_col)
        name_price.addStretch()
        name_price.addLayout(price_col)
        info_layout.addLayout(name_price)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #E0DDD8; max-height: 0.5px;")
        info_layout.addWidget(sep)

        desc_title = QLabel("Description")
        desc_title.setStyleSheet("font-size: 14px; font-weight: 500; color: #1A1A1A;")
        self.detail_desc = QLabel()
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setStyleSheet("font-size: 14px; color: #6B6A66;")
        info_layout.addWidget(desc_title)
        info_layout.addWidget(self.detail_desc)

        specs_grid = QGridLayout()
        specs_grid.setSpacing(16)

        self.spec_condition = SpecRow("Condition", "", "\u25cf")
        self.spec_category = SpecRow("Category", "")
        self.spec_stock = SpecRow("Stock", "")
        self.spec_created = SpecRow("Added Date", "")
        self.spec_rentals_count = SpecRow("Total Rentals", "")

        specs_grid.addWidget(self.spec_condition, 0, 0)
        specs_grid.addWidget(self.spec_category, 0, 1)
        specs_grid.addWidget(self.spec_stock, 1, 0)
        specs_grid.addWidget(self.spec_created, 1, 1)
        specs_grid.addWidget(self.spec_rentals_count, 2, 0, 1, 2)
        info_layout.addLayout(specs_grid)

        right_col.addWidget(self.info_card)

        self.history_card = QFrame()
        self.history_card.setObjectName("historyCard")
        self.history_card.setStyleSheet("""
            #historyCard {
                background: #ffffff; border: 0.5px solid #E0DDD8;
                border-radius: 12px; padding: 24px;
            }
        """)
        history_layout = QVBoxLayout(self.history_card)
        history_layout.setSpacing(12)

        hist_header = QHBoxLayout()
        hist_title = QLabel("Recent History")
        hist_title.setStyleSheet("font-size: 18px; font-weight: 500; color: #1A1A1A;")
        hist_header.addWidget(hist_title)
        hist_header.addStretch()
        history_layout.addLayout(hist_header)

        self.history_container = QVBoxLayout()
        self.history_container.setSpacing(0)
        history_layout.addLayout(self.history_container)
        history_layout.addStretch()

        right_col.addWidget(self.history_card)

        right_widget = QWidget()
        right_widget.setLayout(right_col)

        bento.addWidget(left_widget, 5)
        bento.addWidget(right_widget, 7)
        layout.addLayout(bento)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._toggle_owner_actions()

    def _toggle_owner_actions(self):
        visible = is_owner()
        self.btn_maintenance.setVisible(visible)
        self.btn_edit.setVisible(visible)

    def _load_data(self, item_id):
        item = get_inventory_by_id(item_id)
        if not item:
            self.detail_name.setText("Item not found")
            return

        name = item.get("name", "")
        cat = item.get("category", "")
        desc = item.get("description", "")
        stock = item.get("stock", 0)
        price = item.get("price_per_day", 0)
        condition = item.get("condition", "Baik")
        created = item.get("created_at", "")[:10]

        self.bc_category.setText(cat)
        self.bc_name.setText(name)

        self.detail_name.setText(name)
        sku_prefix = {"Kostum": "CST", "Aksesoris": "ACS", "Properti": "PRP",
                       "Alat Musik": "INS", "Make Up": "MKU", "Lainnya": "OTH"}
        prefix = sku_prefix.get(cat, "ITM")
        self.detail_sku.setText(f"SKU: {prefix}-{item_id[:4].upper()}-{item_id[4:8].upper()}")

        self.detail_price.setText(f"Rp {price:,}")
        self.detail_desc.setText(desc or "No description available.")

        cond_bg, cond_fg, cond_dot, cond_label = _CONDITION_COLORS.get(
            condition, ("#E8F7F2", "#1D9E75", "#1D9E75", "Available")
        )
        self.spec_condition.set_value(f"{condition} ({cond_label})")
        self.spec_category.set_value(cat)
        self.spec_stock.set_value(str(stock))
        self.spec_created.set_value(created)

        self.img_status_badge.setText(f"\u25cf  {cond_label}")
        self.img_status_badge.setStyleSheet(f"""
            background: {cond_bg}; color: {cond_fg}; font-size: 12px;
            font-weight: 500; padding: 6px 14px; border-radius: 8px;
        """)

        rentals = get_rentals_by_inventory(item_id) or []
        self.spec_rentals_count.set_value(f"{len(rentals)} transactions")

        while self.history_container.count():
            child = self.history_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        recent = sorted(rentals, key=lambda r: r.get("created_at", ""), reverse=True)[:5]
        if not recent:
            empty = QLabel("No rental history for this item.")
            empty.setStyleSheet("font-size: 13px; color: #8C8A86; padding: 8px 0; background: transparent;")
            self.history_container.addWidget(empty)
        else:
            for r in recent:
                user_data = r.get("users") or {}
                status = r.get("status", "")
                start = r.get("start_date", "")
                end = r.get("end_date", "")
                if status == "returned":
                    icon = "\u2713"
                    title = "Returned & Inspected"
                    subtitle = f"by {user_data.get('name', '-')} \u2022 {r.get('return_date', '-')}"
                elif status == "active":
                    icon = "\u2197"
                    title = "Currently Rented"
                    subtitle = f"{user_data.get('name', '-')} \u2022 {start} to {end}"
                elif status == "confirmed":
                    icon = "\u25a0"
                    title = "Upcoming Rental"
                    subtitle = f"{user_data.get('name', '-')} \u2022 {start} to {end}"
                else:
                    icon = "\u25cb"
                    title = "Rental Request"
                    subtitle = f"{user_data.get('name', '-')} \u2022 Status: {status}"
                self.history_container.addWidget(HistoryItem(icon, title, subtitle))

    def _toggle_maintenance(self):
        if not self._current_item_id:
            return
        item = get_inventory_by_id(self._current_item_id)
        if not item:
            return
        current_cond = item.get("condition", "Baik")
        new_cond = "Rusak Ringan" if current_cond == "Baik" else "Baik"
        ok = update_inventory(self._current_item_id, {"condition": new_cond})
        if ok:
            self.refresh()
        else:
            QMessageBox.warning(self, "Failed", "Failed to update condition.")

    def _edit_item(self):
        if not self._current_item_id:
            return
        from ui.pages.inventory_page import InventoryDialog
        item = get_inventory_by_id(self._current_item_id)
        if not item:
            return
        current = {
            "name": item.get("name", ""),
            "category": item.get("category", ""),
            "stock": item.get("stock", 0),
            "price_per_day": item.get("price_per_day", 0),
            "condition": item.get("condition", "Baik"),
            "description": item.get("description", ""),
        }
        dialog = InventoryDialog(self, current)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            ok = update_inventory(self._current_item_id, {
                "name": data["name"],
                "category": data["category"],
                "description": data["description"],
                "stock": data["stock"],
                "price_per_day": data["price_per_day"],
                "condition": data["condition"],
            })
            if ok:
                self.refresh()
            else:
                QMessageBox.warning(self, "Failed", "Failed to update item.")
