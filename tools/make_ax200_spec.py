"""Generates data/acme/pdfs/ax200_spec.pdf: a fictional 2-page product spec sheet full of tables.

    python tools/make_ax200_spec.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "data" / "acme" / "pdfs" / "ax200_spec.pdf"
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=20, textColor=colors.HexColor("#0B3954"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13.5, spaceBefore=12, spaceAfter=6,
                    textColor=colors.HexColor("#087E8B"))
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=10.5, leading=15, spaceAfter=6)


def table(rows, widths):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3954")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6F8")]),
    ]))
    return t


S = [
    Paragraph("AX-200 Collaborative Robotic Arm: Technical Data Sheet", H1),
    Paragraph("The AX-200 is a six-axis collaborative arm for pick-and-place, machine tending and inspection. "
              "It is certified for collaborative operation without fencing after a risk assessment.", P),
    Paragraph("1. Technical specifications", H2),
    table([["Parameter", "Value"],
           ["Payload", "7 kg"],
           ["Reach", "850 mm"],
           ["Pose repeatability", "± 0.03 mm"],
           ["Degrees of freedom", "6 rotating joints"],
           ["Robot weight", "24.5 kg"],
           ["Max. tool (TCP) speed", "2.0 m/s"],
           ["Ingress protection", "IP54"],
           ["Power consumption", "150 W typical, 350 W max"],
           ["Operating temperature", "0 to 45 °C"],
           ["Noise level", "< 65 dB(A)"]], [70 * mm, 90 * mm]),
    Paragraph("2. Joint ranges and speeds", H2),
    table([["Joint", "Working range", "Max. speed"],
           ["J1 base", "± 360°", "180 °/s"],
           ["J2 shoulder", "± 360°", "180 °/s"],
           ["J3 elbow", "± 160°", "180 °/s"],
           ["J4 wrist 1", "± 360°", "225 °/s"],
           ["J5 wrist 2", "± 360°", "225 °/s"],
           ["J6 wrist 3", "infinite", "300 °/s"]], [50 * mm, 55 * mm, 55 * mm]),
    PageBreak(),
    Paragraph("3. Options and list prices (2026)", H2),
    table([["Code", "Option", "List price (EUR)"],
           ["AX200-BASE", "AX-200 arm with controller and teach pendant", "28,900"],
           ["AX200-GRIP2", "Two-finger adaptive gripper kit", "3,450"],
           ["AX200-VAC", "Vacuum gripper kit", "2,180"],
           ["AX200-VIS", "Wrist camera + vision software licence", "4,700"],
           ["AX200-RAIL", "1.5 m linear rail (7th axis)", "9,800"],
           ["CARE-36", "Acme Care: +36 months warranty, next-day on-site", "3,900"]],
          [32 * mm, 95 * mm, 33 * mm]),
    Paragraph("Prices exclude VAT and installation. Volume discounts follow the discount approval rules in the "
              "Employee &amp; Customer Policy Handbook, section 4.1.", P),
    Paragraph("4. Safety functions", H2),
    Paragraph("The AX-200 provides 17 configurable safety functions, including joint position and speed limits, "
              "force limiting (default 150 N), tool orientation limits and safe home position. Safety settings are "
              "password-protected and every change is written to the controller's audit log.", P),
    Paragraph("A protective stop is triggered within 250 ms when a collision force above the configured limit "
              "is detected. The emergency stop on the teach pendant is a category 1 stop.", P),
]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(20 * mm, 287 * mm, "ACME ROBOTICS · AX-200 Data Sheet · Rev. C")
    canvas.drawString(20 * mm, 12 * mm, "Acme Robotics (fictional) · Specifications subject to change")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page} of 2")
    canvas.restoreState()


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm,
                      bottomMargin=20 * mm, title="AX-200 Data Sheet").build(S, onFirstPage=footer, onLaterPages=footer)
    print("wrote", OUT)
