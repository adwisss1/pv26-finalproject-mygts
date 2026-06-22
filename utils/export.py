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


def prepare_rental_export(rentals: list[dict]) -> list[dict]:
    """Normalize rental objects for export (CSV/PDF).
    Returns list of dicts with consistent keys.
    """
    rows = []
    for r in rentals or []:
        rows.append({
            "Customer": r.get("users", {}).get("name", "-"),
            "Item": r.get("inventories", {}).get("name", "-"),
            "Category": r.get("inventories", {}).get("category", "-"),
            "Start": r.get("start_date", ""),
            "End": r.get("end_date", ""),
            "Return": r.get("return_date", ""),
            "Status": r.get("status", ""),
            "Fine": str(r.get("fine_amount", 0)),
        })
    return rows


def print_rental_receipt(rental: dict, filename: str | None = None) -> str:
    """Generate rental receipt PDF untuk customer.
    Print nota detil sewa dengan format yang rapi dan profesional.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, 
        Spacer, HRFlowable, PageBreak
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    os.makedirs("exports", exist_ok=True)
    if not filename:
        rental_id = rental.get("id", "unknown")[:8]
        filename = f"exports/nota_sewa_{rental_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    
    styles = getSampleStyleSheet()
    brand_clr = colors.HexColor(APP_COLOR)
    dark_clr = colors.HexColor("#1A1A1A")
    grey_clr = colors.HexColor("#8C8A86")
    light_clr = colors.HexColor("#F5FAF8")
    
    elements = []
    
    # ── HEADER ─────────────────────────────────────────────────────────────
    style_app = ParagraphStyle(
        "AppName", parent=styles["Normal"],
        fontSize=16, fontName="Helvetica-Bold", textColor=brand_clr,
        spaceAfter=0, alignment=TA_CENTER,
    )
    style_receipt = ParagraphStyle(
        "Receipt", parent=styles["Normal"],
        fontSize=12, fontName="Helvetica-Bold", textColor=dark_clr,
        spaceAfter=4, alignment=TA_CENTER,
    )
    style_meta_center = ParagraphStyle(
        "MetaCenter", parent=styles["Normal"],
        fontSize=9, textColor=grey_clr, spaceAfter=0, alignment=TA_CENTER,
    )
    
    elements.append(Paragraph("MyGTS", style_app))
    elements.append(Paragraph("Nota Penyewaan", style_receipt))
    
    rental_id = rental.get("id", "-")
    elements.append(Paragraph(f"Nomor Transaksi: <b>{rental_id[:12]}</b>", style_meta_center))
    elements.append(Paragraph(
        f"Dicetak: {datetime.now().strftime('%d %B %Y, %H:%M WIB')}",
        style_meta_center
    ))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(
        width="100%", thickness=1.2, color=brand_clr, spaceAfter=8,
    ))
    
    # ── INFO CUSTOMER & BARANG ─────────────────────────────────────────────
    style_label = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold", textColor=dark_clr,
        spaceAfter=2,
    )
    style_value = ParagraphStyle(
        "Value", parent=styles["Normal"],
        fontSize=10, textColor=dark_clr, spaceAfter=6,
    )
    
    # Get data
    inv = rental.get("inventories", {})
    usr = rental.get("users", {})
    status = rental.get("status", "unknown")
    start_date = rental.get("start_date", "-")
    end_date = rental.get("end_date", "-")
    return_date = rental.get("return_date", "-")
    fine = rental.get("fine_amount", 0)
    notes = rental.get("notes", "-")
    
    # Format dates
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d %B %Y")
    except:
        pass
    try:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d %B %Y")
    except:
        pass
    try:
        if return_date and return_date != "-":
            return_date = datetime.strptime(return_date, "%Y-%m-%d").strftime("%d %B %Y")
    except:
        pass
    
    # 2-column layout untuk info penyewa dan barang
    info_data = [
        [
            Paragraph("<b>Informasi Penyewa</b>", style_label),
            Paragraph("<b>Informasi Barang</b>", style_label),
        ],
        [
            Paragraph(f"Nama: {usr.get('name', '-')}<br/>Email: {usr.get('email', '-')}", style_value),
            Paragraph(f"Nama: {inv.get('name', '-')}<br/>Kategori: {inv.get('category', '-')}", style_value),
        ]
    ]
    
    info_table = Table(info_data, colWidths=[8.5*cm, 8.5*cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), light_clr),
        ("TEXTCOLOR", (0, 0), (-1, 0), brand_clr),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D4D2CD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 12))
    
    # ── DETAIL PENYEWAAN ───────────────────────────────────────────────────
    elements.append(Paragraph("<b>Detail Penyewaan</b>", style_label))
    elements.append(Spacer(1, 4))
    
    detail_data = [
        ["Keterangan", "Tanggal"],
        ["Tanggal Sewa", start_date],
        ["Tanggal Kembali Rencana", end_date],
        ["Tanggal Pengembalian Aktual", return_date if status == "returned" else "–"],
        ["Status", status.title()],
    ]
    
    detail_table = Table(detail_data, colWidths=[7*cm, 10*cm])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_clr),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), dark_clr),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D4D2CD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_clr]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]))
    
    elements.append(detail_table)
    elements.append(Spacer(1, 12))
    
    # ── PERHITUNGAN DENDA (jika ada) ───────────────────────────────────────
    if status == "returned" or fine > 0:
        elements.append(Paragraph("<b>Perhitungan Denda</b>", style_label))
        elements.append(Spacer(1, 4))
        
        denda_data = [
            ["Deskripsi", "Jumlah"],
            [f"Denda Keterlambatan", f"Rp {fine:,}".replace(",", ".")],
        ]
        
        denda_table = Table(denda_data, colWidths=[10*cm, 7*cm])
        denda_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEF2F2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#E24B4A")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), dark_clr),
            ("FONTNAME", (1, 1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D4D2CD")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ]))
        
        elements.append(denda_table)
        elements.append(Spacer(1, 12))
    
    # ── CATATAN (jika ada) ─────────────────────────────────────────────────
    if notes and notes != "-":
        elements.append(Paragraph("<b>Catatan</b>", style_label))
        elements.append(Paragraph(notes, style_value))
        elements.append(Spacer(1, 8))
    
    # ── FOOTER ─────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=grey_clr, spaceAfter=6,
    ))
    
    style_footer = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=grey_clr, alignment=TA_CENTER, spaceAfter=0,
    )
    elements.append(Paragraph(
        f"Nota ini merupakan bukti penyewaan resmi dari {APP_NAME}. "
        f"Silakan simpan nota ini untuk referensi Anda.",
        style_footer
    ))
    
    doc.build(elements)
    return filename