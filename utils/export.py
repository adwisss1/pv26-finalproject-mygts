"""
Utils: Export
Export data ke PDF dan CSV — dipakai di history_page dan menu File.
"""
import csv
import os
from datetime import datetime

# ── Info aplikasi untuk header PDF ──────────────────────────────────────────
APP_NAME    = "MyGTS — My Gangsar Treasure System"
APP_TAGLINE = "Sistem Manajemen Inventaris Sanggar Budaya"
APP_COLOR   = "#0F6E56"


def export_csv(data: list[dict], filename: str | None = None) -> str:
    """Export data ke file CSV. Return path file."""
    if not data:
        raise ValueError("Tidak ada data untuk diekspor.")

    os.makedirs("exports", exist_ok=True)
    if not filename:
        filename = f"exports/laporan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    return filename


def export_pdf(data: list[dict], title: str = "Laporan MyGTS",
               filename: str | None = None) -> str:
    """Export data ke file PDF dengan header profesional. Return path file."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    os.makedirs("exports", exist_ok=True)
    if not filename:
        filename = f"exports/laporan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles    = getSampleStyleSheet()
    brand_clr = colors.HexColor(APP_COLOR)
    dark_clr  = colors.HexColor("#1A1A1A")
    grey_clr  = colors.HexColor("#8C8A86")
    alt_clr   = colors.HexColor("#F5FAF8")

    style_app = ParagraphStyle(
        "AppName", parent=styles["Normal"],
        fontSize=18, fontName="Helvetica-Bold",
        textColor=brand_clr, spaceAfter=2,
    )
    style_tag = ParagraphStyle(
        "TagLine", parent=styles["Normal"],
        fontSize=10, textColor=grey_clr, spaceAfter=0,
    )
    style_title = ParagraphStyle(
        "ReportTitle", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=dark_clr, spaceAfter=4, spaceBefore=14,
    )
    style_meta = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=9, textColor=grey_clr,
    )
    style_summary = ParagraphStyle(
        "Summary", parent=styles["Normal"],
        fontSize=10, textColor=dark_clr,
        leftIndent=0, spaceAfter=4,
    )

    elements = []

    # ── Header aplikasi ────────────────────────────────────────────────────
    elements.append(Paragraph(APP_NAME, style_app))
    elements.append(Paragraph(APP_TAGLINE, style_tag))
    elements.append(HRFlowable(
        width="100%", thickness=1.5,
        color=brand_clr, spaceAfter=10, spaceBefore=6,
    ))

    # ── Judul laporan + metadata ──────────────────────────────────────────
    elements.append(Paragraph(title, style_title))
    now_str = datetime.now().strftime("%d %B %Y, %H:%M WIB")
    elements.append(Paragraph(f"Dicetak pada: {now_str}", style_meta))
    elements.append(Paragraph(f"Jumlah data: {len(data)} baris", style_meta))
    elements.append(Spacer(1, 12))

    # ── Ringkasan singkat (jika ada kolom numerik) ────────────────────────
    if data:
        numeric_cols = [
            k for k in data[0].keys()
            if any(
                isinstance(row.get(k), (int, float)) and not isinstance(row.get(k), bool)
                for row in data
            )
        ]
        if numeric_cols:
            elements.append(Paragraph("<b>Ringkasan:</b>", style_summary))
            for col in numeric_cols[:3]:   # maks 3 kolom
                values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
                if values:
                    total = sum(values)
                    avg   = total / len(values)
                    label_map = {
                        "fine_amount": "Total Denda",
                        "price_per_day": "Harga/Hari",
                        "stock": "Total Stok",
                    }
                    label = label_map.get(col, col.replace("_", " ").title())
                    elements.append(Paragraph(
                        f"  • {label}: total <b>{total:,.0f}</b>, rata-rata <b>{avg:,.1f}</b>",
                        style_summary
                    ))
            elements.append(Spacer(1, 8))

    # ── Tabel data ─────────────────────────────────────────────────────────
    if data:
        headers = list(data[0].keys())

        # Terjemahan header agar lebih mudah dibaca
        header_labels = {
            "id": "ID", "name": "Nama", "category": "Kategori",
            "status": "Status", "start_date": "Tgl Mulai", "end_date": "Tgl Selesai",
            "return_date": "Tgl Kembali", "fine_amount": "Denda (Rp)",
            "price_per_day": "Harga/Hari", "stock": "Stok",
            "condition": "Kondisi", "notes": "Catatan",
            "user_id": "User ID", "inventory_id": "Item ID",
            "created_at": "Dibuat", "description": "Deskripsi",
        }
        display_headers = [header_labels.get(h, h.replace("_", " ").title()) for h in headers]

        # Potong nilai panjang agar tidak meluber
        def _fmt(val):
            if val is None:
                return "-"
            s = str(val)
            return s[:40] + "…" if len(s) > 40 else s

        table_data = [display_headers] + [
            [_fmt(row.get(h, "")) for h in headers] for row in data
        ]

        page_width = A4[0] - 4*cm
        col_count  = len(headers)
        col_widths = [page_width / col_count] * col_count

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            # Header row
            ("BACKGROUND",  (0, 0), (-1, 0),  brand_clr),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, 0),  9),
            ("ALIGN",       (0, 0), (-1, 0),  "CENTER"),
            ("BOTTOMPADDING",(0,0),(-1, 0),   8),
            ("TOPPADDING",  (0, 0), (-1, 0),  8),
            # Data rows
            ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 1), (-1, -1), 8),
            ("TEXTCOLOR",   (0, 1), (-1, -1), dark_clr),
            ("ALIGN",       (0, 1), (-1, -1), "LEFT"),
            ("TOPPADDING",  (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING",(0,1),(-1, -1),  6),
            # Alternating rows
            ("ROWBACKGROUNDS",(0,1),(-1,-1),  [colors.white, alt_clr]),
            # Grid
            ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#D4D2CD")),
            ("LINEABOVE",   (0, 0), (-1, 0),  1.5, brand_clr),
            ("LINEBELOW",   (0, 0), (-1, 0),  0.8, brand_clr),
        ]))
        elements.append(t)

    # ── Footer ─────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=grey_clr, spaceAfter=6,
    ))
    elements.append(Paragraph(
        f"Laporan ini dibuat otomatis oleh {APP_NAME}. "
        f"Dicetak: {now_str}.",
        style_meta
    ))

    doc.build(elements)
    return filename