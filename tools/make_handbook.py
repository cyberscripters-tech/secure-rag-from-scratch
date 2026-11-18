"""Generates data/acme/pdfs/handbook.pdf: the fictional Acme Robotics handbook used in the series.

Every fact here is invented. One section per page, so page numbers stay stable
(EP01 and EP02 refer to "handbook.pdf, page 12" for the refund policy).

    python tools/make_handbook.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "data" / "acme" / "pdfs" / "handbook.pdf"

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=20, spaceAfter=10, textColor=colors.HexColor("#0B3954"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13.5, spaceBefore=10, spaceAfter=4,
                    textColor=colors.HexColor("#087E8B"))
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=10.5, leading=15, spaceAfter=6)
B = ParagraphStyle("B", parent=P, leftIndent=14, bulletIndent=4, spaceAfter=3)
TITLE = ParagraphStyle("T", parent=H1, fontSize=34, leading=40, alignment=TA_CENTER, spaceAfter=18)
SUB = ParagraphStyle("S", parent=P, fontSize=14, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))


def bullets(items):
    return [Paragraph(i, B, bulletText="•") for i in items]


def table(rows, widths):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3954")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6F8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


S = []  # story

# ---- p1 cover
S += [Spacer(1, 60 * mm), Paragraph("ACME ROBOTICS", TITLE),
      Paragraph("Employee &amp; Customer Policy Handbook", SUB), Spacer(1, 8 * mm),
      Paragraph("Version 7.2  ·  Effective 2 March 2026", SUB), Spacer(1, 60 * mm),
      Paragraph("Internal use only. Owner: People Operations &amp; Finance. Questions: handbook@acme-robotics.example", SUB),
      PageBreak()]

# ---- p2 about
S += [Paragraph("1. Welcome to Acme Robotics", H1),
      Paragraph("Acme Robotics designs and builds collaborative robots for small and mid-sized factories. "
                "We were founded in 2014 in Pune, India, and today employ around 420 people across offices in "
                "Pune, Bengaluru, Munich and Austin.", P),
      Paragraph("1.1 What we sell", H2),
      *bullets(["<b>AX-200 Robotic Arm</b>: a six-axis collaborative arm with a 7 kg payload, used for pick-and-place, "
                "machine tending and quality inspection.",
                "<b>Rover-S</b>: an autonomous mobile platform that moves parts between workstations.",
                "<b>Acme Cloud Console</b>: our SaaS platform for programming, monitoring and updating robots remotely."]),
      Paragraph("1.2 Our values", H2),
      *bullets(["<b>Safety first.</b> No deadline is worth an injury, for our customers or for us.",
                "<b>Own the outcome.</b> If you see a problem, you own it until it reaches the right person.",
                "<b>Write it down.</b> Decisions, designs and incidents are documented so others can learn from them."]),
      Paragraph("This handbook explains how we work and the policies we apply to customers. It is reviewed every "
                "six months. If anything here conflicts with your employment contract, your contract wins.", P),
      PageBreak()]

# ---- p3 conduct
S += [Paragraph("2. People Policies", H1), Paragraph("2.1 Code of conduct", H2),
      Paragraph("We expect everyone to treat colleagues, customers and partners with respect. Harassment, "
                "discrimination and retaliation are not tolerated in any form, in the office, online or at company events.", P),
      Paragraph("Conflicts of interest must be disclosed to your manager and to legal@acme-robotics.example within "
                "14 days of becoming aware of them. This includes investments in suppliers or competitors and "
                "close relatives working at a customer you manage.", P),
      Paragraph("2.2 Gifts and hospitality", H2),
      Paragraph("You may accept gifts from business partners worth up to INR 5,000 (or EUR 55 / USD 60) per year "
                "from any single company. Anything above that must be declined politely or handed to People Operations. "
                "Cash and gift cards are never acceptable.", P),
      Paragraph("2.3 Speaking up", H2),
      Paragraph("Concerns about fraud, safety or misconduct can be raised with your manager, with People Operations, "
                "or anonymously through the Ethics Line at ethics.acme-robotics.example. Reports are reviewed by the "
                "Ethics Committee within 10 working days.", P),
      PageBreak()]

# ---- p4 hours / hybrid
S += [Paragraph("2.4 Working hours and hybrid work", H2),
      Paragraph("Standard working time is 40 hours per week. Core collaboration hours are 11:00 to 16:00 local time, "
                "when everyone should be reachable. Outside core hours you may arrange your day as you prefer.", P),
      Paragraph("Most roles are hybrid: employees work from the office at least <b>three days per week</b>. "
                "Manufacturing, lab and support-desk roles are fully on-site. Fully remote arrangements need approval "
                "from your department head and People Operations.", P),
      Paragraph("2.5 Working from abroad", H2),
      Paragraph("You may work from another country for up to 20 working days per calendar year, provided you notify "
                "People Operations at least two weeks in advance. Longer stays require a tax and immigration review.", P),
      Paragraph("2.6 Overtime", H2),
      Paragraph("Overtime for hourly employees must be approved in advance by a manager and is paid at 1.5 times the "
                "normal rate. Salaried employees may take time off in lieu for weekend work on customer installations.", P),
      PageBreak()]

# ---- p5 leave
S += [Paragraph("2.7 Leave policy", H2),
      table([["Leave type", "Allowance", "Notes"],
             ["Annual leave", "24 working days / year", "Up to 5 unused days carry over to 31 March"],
             ["Sick leave", "12 days / year", "Medical certificate needed after 3 consecutive days"],
             ["Parental leave", "26 weeks (birth parent), 8 weeks (other parent)", "Fully paid"],
             ["Bereavement", "5 days", "Immediate family"],
             ["Volunteering", "2 days / year", "For registered non-profits"]],
            [38 * mm, 62 * mm, 70 * mm]),
      Spacer(1, 6 * mm),
      Paragraph("Leave is requested in the PeopleHub portal. Requests of five days or more should be submitted at "
                "least three weeks in advance. Public holidays follow the calendar of your office location.", P),
      Paragraph("During the annual shutdown, from 24 December to 1 January, the offices are closed and three days of "
                "annual leave are deducted automatically. Support-desk staff on the holiday rota receive these days back.", P),
      PageBreak()]

# ---- p6 expenses
S += [Paragraph("2.8 Expenses and travel", H2),
      Paragraph("Business expenses are submitted in the Expensify app within 30 days, with a receipt for anything over "
                "INR 500. Expenses are reimbursed with the next monthly payroll.", P),
      table([["Category", "Limit (India)", "Limit (EU / US)"],
             ["Hotel, per night", "INR 9,000", "EUR 170 / USD 190"],
             ["Meals, per day", "INR 2,500", "EUR 60 / USD 70"],
             ["Client dinner, per person", "INR 4,000", "EUR 90 / USD 100"],
             ["Home-office setup (one-time)", "INR 25,000", "EUR 400 / USD 450"]],
            [62 * mm, 50 * mm, 58 * mm]),
      Spacer(1, 6 * mm),
      Paragraph("Flights under 6 hours are booked in economy class. Flights of 6 hours or more may be booked in premium "
                "economy. All travel is booked through the travel desk (travel@acme-robotics.example) so that we know "
                "where employees are in an emergency.", P),
      PageBreak()]

# ---- p7 IT security
S += [Paragraph("3. IT, Security and Facilities", H1), Paragraph("3.1 Accounts and passwords", H2),
      *bullets(["Passwords must be at least 14 characters and must not be reused across services.",
                "Multi-factor authentication (MFA) is mandatory for email, the Cloud Console admin area, GitHub and VPN.",
                "Use the company password manager (1Password). Never share passwords in chat or email."]),
      Paragraph("3.2 VPN and remote access", H2),
      Paragraph("Access to internal systems from outside the office requires the Acme VPN (GlobalProtect). "
                "Production systems of the Acme Cloud Console can only be reached through the bastion host, "
                "and access is granted per ticket for a maximum of 8 hours.", P),
      Paragraph("3.3 Laptops and devices", H2),
      Paragraph("Company laptops are encrypted and managed centrally. Do not disable endpoint protection. Personal phones "
                "may be used for email only after enrolling in the device management app.", P),
      Paragraph("3.4 Reporting security incidents", H2),
      Paragraph("Report a lost device, phishing email or suspected breach to security@acme-robotics.example or by calling "
                "the 24/7 security hotline on extension 4444 <b>within one hour</b> of noticing it. You will never be "
                "punished for reporting a mistake quickly.", P),
      PageBreak()]

# ---- p8 data classification
S += [Paragraph("3.5 Data classification", H2),
      table([["Class", "Examples", "Rules"],
             ["Public", "Website, brochures", "Can be shared freely"],
             ["Internal", "This handbook, org charts", "Employees and contractors only"],
             ["Confidential", "Customer contracts, pricing deals, roadmaps", "Need-to-know; encrypted at rest"],
             ["Restricted", "Salaries, health data, source code signing keys", "Named individuals only; audited access"]],
            [30 * mm, 70 * mm, 70 * mm]),
      Spacer(1, 6 * mm),
      Paragraph("Restricted data must never be pasted into external AI tools, chatbots or translation services. "
                "Approved internal AI assistants may process Internal and Confidential data only.", P),
      Paragraph("3.6 Use of AI assistants", H2),
      Paragraph("Employees may use the approved internal assistant for drafting, summarising and searching company "
                "documents. Answers must be checked against the cited source before being sent to customers.", P),
      PageBreak()]

# ---- p9 facilities
S += [Paragraph("3.7 Offices and facilities", H2),
      Paragraph("The Pune headquarters is open from 07:00 to 21:00 on weekdays. Access requires your badge at all times; "
                "visitors must be registered at reception and escorted.", P),
      *bullets(["<b>Ground floor:</b> reception, cafeteria and customer demo area.",
                "<b>First floor:</b> engineering and the robotics lab (safety shoes required).",
                "<b>Second floor:</b> sales, finance and People Operations.",
                "<b>Third floor:</b> the server room and network operations centre (restricted badge access)."]),
      Paragraph("3.8 Lab safety", H2),
      Paragraph("Robots in the lab must be operated inside marked safety zones with the emergency stop within reach. "
                "New lab users complete the four-hour Robot Safety course before receiving lab access.", P),
      PageBreak()]

# ---- p10 support SLAs
S += [Paragraph("4. Customer Policies", H1), Paragraph("4.0 Support and service levels", H2),
      Paragraph("Customers contact support through the Cloud Console, by email at support@acme-robotics.example, or by "
                "phone. Response targets depend on the customer's plan and the severity of the issue.", P),
      table([["Severity", "Standard", "Business", "Enterprise"],
             ["P1: production stopped", "8 business hours", "2 hours", "30 minutes, 24/7"],
             ["P2: degraded", "2 business days", "8 business hours", "4 hours"],
             ["P3: question", "5 business days", "2 business days", "1 business day"]],
            [48 * mm, 40 * mm, 40 * mm, 42 * mm]),
      Spacer(1, 6 * mm),
      Paragraph("Enterprise customers also get a named Technical Account Manager and a quarterly business review.", P),
      PageBreak()]

# ---- p11 plans & pricing
S += [Paragraph("4.1 Plans and billing", H2),
      Paragraph("Acme Cloud Console is sold on three plans: <b>Standard</b>, <b>Business</b> and <b>Enterprise</b>. "
                "Standard and Business are billed monthly or annually by credit card or invoice. Enterprise contracts "
                "are annual, invoiced in advance, with payment terms of net 45 days.", P),
      Paragraph("Price changes are announced at least 60 days in advance and apply from the next renewal. "
                "Discounts above 20% require approval from the VP of Sales; discounts above 35% also require "
                "approval from the CFO.", P),
      Paragraph("Invoices are issued by the billing team (billing@acme-robotics.example). Customers who are more than "
                "30 days late with payment receive a reminder; after 60 days, access to the Cloud Console may be "
                "restricted to read-only mode.", P),
      PageBreak()]

# ---- p12 REFUNDS
S += [Paragraph("4.2 Refunds for subscriptions", H2),
      Paragraph("<b>Enterprise customers</b> may request a full refund within <b>30 days of the invoice date</b>. "
                "Refund requests are handled by the billing team and must be submitted by the customer's account owner "
                "through their Technical Account Manager or to billing@acme-robotics.example.", P),
      Paragraph("After 30 days, refunds for Enterprise annual contracts are <b>prorated</b>: the customer receives a credit "
                "for the unused full months remaining in the contract term, minus a 10% early-termination fee. "
                "Prorated refunds are issued as credit notes within 15 business days.", P),
      Paragraph("<b>Business</b> plan customers may cancel at any time; monthly plans are not refunded for the current "
                "month, and annual Business plans are refunded pro rata within the first 90 days only.", P),
      Paragraph("<b>Standard</b> plan subscriptions are non-refundable, but customers can cancel at any time to stop the "
                "next renewal.", P),
      Paragraph("Refunds above USD 25,000 (or equivalent) need written approval from the CFO. Hardware purchases "
                "are not covered by this section; see 4.3 Warranty and returns.", P),
      PageBreak()]

# ---- p13 warranty
S += [Paragraph("4.3 Warranty and hardware returns", H2),
      Paragraph("The <b>AX-200 Robotic Arm</b> comes with a 24-month limited warranty covering defects in materials and "
                "workmanship. The <b>Rover-S</b> platform has a 12-month warranty; its battery pack is covered for 18 months "
                "or 1,500 charge cycles, whichever comes first.", P),
      Paragraph("Customers may return unused hardware in its original packaging within 14 days of delivery for a full "
                "refund minus shipping costs. Installed or used hardware cannot be returned, but may be repaired under warranty.", P),
      Paragraph("The warranty does not cover damage caused by operating the robot outside its rated payload, by "
                "unauthorised modifications, or by collisions in an area without a valid safety assessment.", P),
      Paragraph("Extended warranty (\"Acme Care\") adds up to 36 extra months and next-business-day on-site repair. "
                "It must be purchased within 90 days of delivery.", P),
      PageBreak()]

# ---- p14 privacy
S += [Paragraph("4.4 Customer data and privacy", H2),
      Paragraph("Robot telemetry from the Cloud Console is stored in the region the customer selects (India, EU or US) and "
                "is retained for 13 months. Customers can export or delete their data at any time from the Console.", P),
      Paragraph("Acme employees may access customer data only to provide support, and only after the customer opens a "
                "ticket. Every access is logged and reviewed monthly by the security team.", P),
      Paragraph("Personal data breaches affecting customers are reported to the customer within 48 hours of confirmation, "
                "and to regulators as required by law (for example within 72 hours under GDPR).", P),
      PageBreak()]

# ---- p15 contacts
S += [Paragraph("5. Who to contact", H1),
      table([["Topic", "Contact"],
             ["Leave, payroll, benefits", "people@acme-robotics.example"],
             ["Expenses and travel", "travel@acme-robotics.example"],
             ["Billing, invoices, refunds", "billing@acme-robotics.example"],
             ["Security incidents (24/7)", "security@acme-robotics.example · ext. 4444"],
             ["IT helpdesk", "it@acme-robotics.example · ext. 2000"],
             ["Legal and conflicts of interest", "legal@acme-robotics.example"],
             ["This handbook", "handbook@acme-robotics.example"]],
            [70 * mm, 100 * mm])]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(20 * mm, 12 * mm, "Acme Robotics · Employee & Customer Policy Handbook v7.2 · INTERNAL")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=22 * mm, bottomMargin=22 * mm, title="Acme Robotics Handbook",
                            author="Acme Robotics (fictional)")
    doc.build(S, onFirstPage=footer, onLaterPages=footer)
    print("wrote", OUT)
