from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QMessageBox, QGridLayout, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from controllers.inventory_controller import get_inventory_by_id, update_inventory, CATEGORIES
from ui.pages.customer.inventory_page import _load_pixmap
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
        lbl_label.setObjectName("formLabel")
        value_style = "font-size: 14px; font-weight: 500; color: #1A1A1A;"
        if icon_char:
            self.value_label = QLabel(f"{icon_char}  {value}")
        else:
            self.value_label = QLabel(value)
        self.value_label.setObjectName("itemValue")

        left.addWidget(lbl_label)
        left.addWidget(self.value_label)
        layout.addLayout(left)

    def set_value(self, text):
        self.value_label.setText(text)


class HistoryItem(QFrame):
    def __init__(self, icon_char, title, subtitle, note=""):
        super().__init__()
        self.setObjectName("historyItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setObjectName("iconFrameSmall")
        il = QVBoxLayout(icon_frame)
        il.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel(icon_char)
        icon_lbl.setObjectName("iconSmall")
        il.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        t1 = QLabel(title)
        t1.setObjectName("historyTitle")
        t2 = QLabel(subtitle)
        t2.setObjectName("historySubtitle")
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
        scroll.setObjectName("transparentScroll")

        content = QWidget()
        content.setObjectName("transparentContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        breadcrumb = QHBoxLayout()
        breadcrumb.setSpacing(8)

        self.btn_back = QPushButton("\u2190  Back to History")
        self.btn_back.setObjectName("link")
        self.btn_back.clicked.connect(lambda: self.navigate_to.emit("history"))

        self.bc_category = QLabel()
        self.bc_category.setObjectName("muted")
        sep1 = QLabel("/")
        sep1.setObjectName("muted")
        self.bc_name = QLabel()
        self.bc_name.setObjectName("itemTitle")

        breadcrumb.addWidget(self.btn_back)
        breadcrumb.addWidget(sep1)
        breadcrumb.addWidget(self.bc_category)
        breadcrumb.addStretch()

        self.btn_maintenance = QPushButton("Set Maintenance")
        self.btn_maintenance.setObjectName("outline")
        self.btn_maintenance.clicked.connect(self._toggle_maintenance)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setObjectName("primary")
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
        img_layout = QVBoxLayout(self.image_card)
        img_layout.setAlignment(Qt.AlignCenter)
        self.img_placeholder = QLabel("\u2610")
        self.img_placeholder.setObjectName("imgPlaceholder")
        self.img_status_badge = QLabel()
        self.img_status_badge.setObjectName("imgStatusBadge")
        img_layout.addWidget(self.img_placeholder)

        status_row = QHBoxLayout()
        status_row.addStretch()
        status_row.addWidget(self.img_status_badge)
        img_layout.addLayout(status_row)

        left_col.addWidget(self.image_card)

        # Thumbnail container (hidden if only 1 image)
        self.thumb_container = QWidget()
        thumb_row = QHBoxLayout(self.thumb_container)
        thumb_row.setSpacing(8)
        for color in ["#EDECE8", "#F0EFEA", "#F3F2EE"]:
            thumb = QFrame()
            thumb.setFixedSize(72, 72)
            thumb.setObjectName("thumb")
            tl = QVBoxLayout(thumb)
            tl.setAlignment(Qt.AlignCenter)
            ti = QLabel("☐")
            ti.setObjectName("thumbIcon")
            tl.addWidget(ti)
            thumb_row.addWidget(thumb)

        thumb_row.addStretch()
        left_col.addWidget(self.thumb_container)
        left_col.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left_col)

        right_col = QVBoxLayout()
        right_col.setSpacing(20)

        self.info_card = QFrame()
        self.info_card.setObjectName("infoCard")
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setSpacing(16)

        name_price = QHBoxLayout()
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        self.detail_name = QLabel()
        self.detail_name.setObjectName("detailName")
        self.detail_sku = QLabel()
        self.detail_sku.setObjectName("muted")
        name_col.addWidget(self.detail_name)
        name_col.addWidget(self.detail_sku)

        price_col = QVBoxLayout()
        price_col.setAlignment(Qt.AlignRight)
        self.detail_price = QLabel()
        self.detail_price.setObjectName("detailPrice")
        self.detail_price_per = QLabel("per day")
        self.detail_price_per.setObjectName("muted")
        price_col.addWidget(self.detail_price)
        price_col.addWidget(self.detail_price_per)

        name_price.addLayout(name_col)
        name_price.addStretch()
        name_price.addLayout(price_col)
        info_layout.addLayout(name_price)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("divider")
        info_layout.addWidget(sep)

        desc_title = QLabel("Description")
        desc_title.setObjectName("sectionTitle")
        self.detail_desc = QLabel()
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setObjectName("muted")
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
        history_layout = QVBoxLayout(self.history_card)
        history_layout.setSpacing(12)

        hist_header = QHBoxLayout()
        hist_title = QLabel("Recent History")
        hist_title.setObjectName("historyTitle")
        hist_header.addWidget(hist_title)
        hist_header.addStretch()
        history_layout.addLayout(hist_header)

        self.history_container = QVBoxLayout()
        self.history_container.setSpacing(0)
        history_layout.addLayout(self.history_container)
        history_layout.addStretch()

        right_col.addWidget(self.history_card)
        right_col.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_col)

        bento.addWidget(left_widget, 5)
        bento.addWidget(right_widget, 7)
        layout.addLayout(bento)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._toggle_owner_actions()

    def _toggle_owner_actions(self):
        visible = is_owner()
        self.btn_maintenance.setVisible(visible)
        self.btn_edit.setVisible(visible)
        self.history_card.setVisible(visible)  # Hanya tampil ke owner

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
        img_url = item.get("image_url", "")

        # Load main image
        try:
            pix = _load_pixmap(img_url, size=320) if img_url else None
            if pix:
                self.img_placeholder.setPixmap(pix)
            else:
                self.img_placeholder.setText("☐")
                self.img_placeholder.setObjectName("imgPlaceholder")
        except Exception:
            self.img_placeholder.setText("☐")
            self.img_placeholder.setObjectName("imgPlaceholder")

        # Hide thumbnail row if only 1 image (no gallery needed)
        self.thumb_container.setVisible(False)

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
        self.img_status_badge.setProperty("condition", condition)

        rentals = get_rentals_by_inventory(item_id) or []
        self.spec_rentals_count.set_value(f"{len(rentals)} transactions")

        while self.history_container.count():
            child = self.history_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        recent = sorted(rentals, key=lambda r: r.get("created_at", ""), reverse=True)[:5]
        if not recent:
            empty = QLabel("No rental history for this item.")
            empty.setObjectName("rowLabel")
            self.history_container.addWidget(empty)
        else:
            # Aggregasi: tampilkan berapa kali setiap customer menyewa item ini
            customer_rentals = {}
            for r in rentals:
                user_data = r.get("users") or {}
                user_id = user_data.get("id", "unknown")
                user_name = user_data.get("name", "Unknown")
                if user_id not in customer_rentals:
                    customer_rentals[user_id] = {"name": user_name, "count": 0}
                customer_rentals[user_id]["count"] += 1
            
            # Top customers berdasarkan count rental
            top_customers = sorted(customer_rentals.items(), 
                                 key=lambda x: x[1]["count"], 
                                 reverse=True)[:5]
            
            for user_id, data in top_customers:
                count = data["count"]
                name = data["name"]
                icon = "👤"  # Simbol customer
                title = name
                subtitle = f"{count} rental{'s' if count > 1 else ''}"
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
            QMessageBox.warning(self, "Gagal", "Gagal mengubah kondisi item.")

    def _edit_item(self):
        if not self._current_item_id:
            return
        from ui.pages.owner.inventory_page import InventoryDialog
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
                QMessageBox.warning(self, "Gagal", "Gagal mengupdate item.")