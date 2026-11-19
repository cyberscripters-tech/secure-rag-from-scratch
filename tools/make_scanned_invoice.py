"""Generates data/acme/pdfs/scanned_invoice.pdf: a fictional invoice that looks scanned.

The output PDF contains only an image (no text layer), slightly rotated, grey and grainy,
so normal text extraction returns nothing and we need OCR.

    python tools/make_scanned_invoice.py      (needs: pdftoppm from poppler-utils)
"""
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent.parent / "data" / "acme" / "pdfs" / "scanned_invoice.pdf"

ROWS = [("AX200-BASE", "AX-200 arm with controller and teach pendant", "3", "28,900.00", "86,700.00"),
        ("AX200-GRIP2", "Two-finger adaptive gripper kit", "3", "3,450.00", "10,350.00"),
        ("CARE-36", "Acme Care, 36 months", "3", "3,900.00", "11,700.00"),
        ("INSTALL", "On-site installation and safety assessment", "1", "6,400.00", "6,400.00")]


def draw_invoice(path):
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, h - 30 * mm, "ACME ROBOTICS")
    c.setFont("Helvetica", 9.5)
    c.drawString(20 * mm, h - 36 * mm, "Acme Robotics Pvt. Ltd. · Hinjewadi Phase 2 · Pune 411057 · India")
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(w - 20 * mm, h - 30 * mm, "INVOICE")
    c.setFont("Helvetica", 10.5)
    y = h - 52 * mm
    for k, v in [("Invoice no.", "INV-2026-0418"), ("Invoice date", "14 September 2026"),
                 ("Customer PO", "PO-77120"), ("Payment terms", "Net 45 days"), ("Due date", "29 October 2026")]:
        c.drawString(120 * mm, y, k)
        c.drawRightString(w - 20 * mm, y, v)
        y -= 6 * mm
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(20 * mm, h - 52 * mm, "Bill to")
    c.setFont("Helvetica", 10.5)
    for i, l in enumerate(["Brightline Packaging GmbH", "Attn: Accounts Payable", "Industriestrasse 12",
                           "70565 Stuttgart, Germany"]):
        c.drawString(20 * mm, h - 58 * mm - i * 6 * mm, l)
    y = h - 100 * mm
    c.setFillColor(colors.HexColor("#DDDDDD"))
    c.rect(20 * mm, y - 2 * mm, w - 40 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9.5)
    cols = [20, 50, 128, 145, 172]
    for x, t in zip(cols, ["Item", "Description", "Qty", "Unit EUR", "Amount EUR"]):
        c.drawString(x * mm, y, t)
    c.setFont("Helvetica", 9.5)
    for r in ROWS:
        y -= 9 * mm
        for x, t in zip(cols, r):
            c.drawString(x * mm, y, t)
    y -= 14 * mm
    for k, v, bold in [("Subtotal", "115,150.00", False), ("VAT reverse charge (EU B2B)", "0.00", False),
                       ("Total due (EUR)", "115,150.00", True)]:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11 if bold else 10)
        c.drawString(115 * mm, y, k)
        c.drawRightString(w - 20 * mm, y, v)
        y -= 7 * mm
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, 40 * mm, "Bank: Example Bank AG · IBAN DE00 0000 0000 0000 0000 00 (fictional)")
    c.drawString(20 * mm, 34 * mm, "Questions about this invoice: billing@acme-robotics.example")
    c.save()


def scanify(png, out_pdf):
    img = Image.open(png).convert("L")
    rnd = random.Random(42)
    img = img.rotate(1.2, resample=Image.BICUBIC, expand=True, fillcolor=245)
    px = img.load()
    for _ in range(img.width * img.height // 60):  # speckle noise
        x, y = rnd.randrange(img.width), rnd.randrange(img.height)
        px[x, y] = rnd.choice([30, 90, 200])
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img = img.point(lambda v: int(v * 0.92 + 8))  # greyish paper
    img.save(out_pdf, "PDF", resolution=150)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "inv.pdf"
        draw_invoice(src)
        subprocess.run(["pdftoppm", "-r", "150", "-png", "-singlefile", str(src), str(Path(d) / "inv")], check=True)
        scanify(Path(d) / "inv.png", OUT)
    print("wrote", OUT)
