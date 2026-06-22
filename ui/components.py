from PySide6.QtCore import Qt


def _set_cursor_and_height(btn, height=None):
    try:
        btn.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass
    if height:
        try:
            btn.setFixedHeight(height)
        except Exception:
            pass


def apply_primary(btn, height=None):
    _set_cursor_and_height(btn, height)
    # mark widget for QSS styling instead of inline styles
    try:
        btn.setObjectName("primary")
    except Exception:
        pass


def apply_outline_primary(btn, height=None):
    _set_cursor_and_height(btn, height)
    try:
        btn.setObjectName("outline")
    except Exception:
        pass


def apply_success(btn, height=None):
    _set_cursor_and_height(btn, height)
    try:
        btn.setObjectName("success")
    except Exception:
        pass


def apply_danger(btn, height=None):
    _set_cursor_and_height(btn, height)
    try:
        btn.setObjectName("danger")
    except Exception:
        pass


def apply_warning(btn, height=None):
    _set_cursor_and_height(btn, height)
    try:
        btn.setObjectName("warning")
    except Exception:
        pass


def apply_nav(btn, height=None):
    _set_cursor_and_height(btn, height)
    try:
        btn.setObjectName("nav")
    except Exception:
        pass


def apply_link(btn, height=None):
    _set_cursor_and_height(btn, height)
    try:
        btn.setObjectName("link")
    except Exception:
        pass


def apply_disabled(btn, height=None):
    _set_cursor_and_height(btn, height)
    btn.setEnabled(False)
    try:
        btn.setObjectName("disabled")
    except Exception:
        pass


def input_style():
    # prefer QSS rules (no inline styles)
    return ""


def card_frame_style():
    return ""


def status_badge_style(bg, fg):
    # recommmend using QSS selectors; return empty to avoid inline styles
    return ""


from PySide6.QtWidgets import QWidget, QFrame, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt


def create_status_badge(status_key, label_text: str | None = None):
    """Factory that returns a ready-to-use status badge QWidget.
    Uses objectName/property so QSS can style it centrally.
    """
    w = QFrame()
    w.setObjectName("statusBadge")
    w.setProperty("status", status_key)
    lo = QHBoxLayout(w)
    lo.setContentsMargins(10, 4, 10, 4)
    lo.setSpacing(6)
    dot = QLabel("\u25cf")
    dot.setObjectName("badgeDot")
    text = QLabel(label_text or status_key.title())
    text.setObjectName("badgeText")
    lo.addWidget(dot)
    lo.addWidget(text)
    wrap = QWidget()
    wl = QHBoxLayout(wrap)
    wl.setContentsMargins(0, 0, 0, 0)
    wl.setAlignment(Qt.AlignCenter)
    wl.addWidget(w)
    return wrap


def create_pagination(container_layout, total_pages, current_page, on_page_cb):
    """Populate a layout with pagination buttons (prev, pages, next).
    `container_layout` is a QLayout instance already attached to a widget.
    """
    # clear existing
    while container_layout.count():
        it = container_layout.takeAt(0)
        if it.widget():
            it.widget().deleteLater()
    container_layout.addStretch()

    def _make_btn(text, obj_name, active=False, enabled=True, page=None):
        b = QPushButton(text)
        b.setObjectName(obj_name)
        b.setProperty("active", active)
        b.setEnabled(enabled)
        if page is not None:
            b.clicked.connect(lambda checked=False, p=page: on_page_cb(p))
        return b

    # prev
    container_layout.addWidget(_make_btn("\u2039", "pageNav", active=False, enabled=(current_page > 0), page=current_page - 1))
    for p in range(total_pages):
        ia = (p == current_page)
        container_layout.addWidget(_make_btn(str(p + 1), "pageBtn", active=ia, enabled=True, page=p))
    # next
    container_layout.addWidget(_make_btn("\u203a", "pageNav", active=False, enabled=(current_page < total_pages - 1), page=current_page + 1))
