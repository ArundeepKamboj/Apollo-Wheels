"""Synthetic, selectable-text PDF fixtures for the local MVP demo."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import uuid
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from .catalog import SERVICES

SUBSCRIBED_CODES = {
    "FUEL", "ITR", "MAP", "RR", "TOLL", "VIOLATION", "COLLISION", "INSURANCE", "MVR_SAFETY"
}


def make_text_pdf(lines: list[str], body_size: float | None = None, body_leading: float | None = None) -> bytes:
    """Create a paginated agreement PDF with readable commercial schedules."""
    buffer = BytesIO()
    if not any(str(line).strip() for line in lines):
        blank = canvas.Canvas(buffer, pagesize=letter)
        blank.showPage()
        blank.save()
        return buffer.getvalue()
    lease_document = bool(lines and "MASTER LEASE AGREEMENT" in str(lines[0]).upper())
    margin = .9 * inch if lease_document else .62 * inch
    document = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=margin, rightMargin=margin,
                                 topMargin=.8 * inch if lease_document else .72 * inch,
                                 bottomMargin=.72 * inch if lease_document else .62 * inch,
                                 title=str(lines[0] if lines else "Demo document"))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18,
                              leading=22, textColor=colors.HexColor("#173b46"), alignment=TA_LEFT, spaceAfter=7))
    styles.add(ParagraphStyle(name="DocSub", parent=styles["Normal"], fontSize=8, leading=11,
                              textColor=colors.HexColor("#56676c"), spaceAfter=4))
    default_size, default_leading, body_spacing = (12, 16, 5) if lease_document else (8, 9.5, 2)
    body_size = body_size or default_size
    body_leading = body_leading or default_leading
    if body_size >= 10:
        body_spacing = 5
    styles.add(ParagraphStyle(name="BodyCopy", parent=styles["BodyText"], fontName="Helvetica", fontSize=body_size,
                              leading=body_leading, textColor=colors.HexColor("#27363a"), spaceAfter=body_spacing))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold",
                              fontSize=11, leading=14, textColor=colors.HexColor("#126b69"), spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name="SmallCell", parent=styles["BodyText"], fontSize=7.5, leading=9,
                              textColor=colors.HexColor("#27363a")))
    styles.add(ParagraphStyle(name="SmallHead", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7,
                              leading=8.5, textColor=colors.white))
    title = str(lines[0]).strip() if lines else "Apollo Wheels Demonstration Document"
    metadata = [line for line in lines if line.startswith(("CLIENT_ID:", "CLIENT_NAME:", "AGREEMENT_ID:",
                                                           "AGREEMENT_TYPE:", "VERSION:", "EFFECTIVE_DATE:",
                                                           "INVOICE_NUMBER:", "BILLING_STREAM:", "PERIOD_START:",
                                                           "PERIOD_END:"))]
    service_rows = [line for line in lines if line.startswith("SERVICE|")]
    component_rows = [line for line in lines if line.startswith("COMPONENT|")]
    lease_rows = [line for line in lines if line.startswith("LEASE|")]
    invoice_rows = [line for line in lines if line.startswith("LINE|")]
    flow = [Paragraph(_pdf_safe(title), styles["DocTitle"]),
            Paragraph("SAMPLE AGREEMENT - FOR PRODUCT DEMONSTRATION", styles["DocSub"])]
    if metadata:
        meta = [[Paragraph(f"<b>{line.split(':', 1)[0].replace('_', ' ').title()}</b>", styles["SmallCell"]),
                 Paragraph(_pdf_safe(line.split(":", 1)[1].strip()), styles["SmallCell"])] for line in metadata]
        table = Table(meta, colWidths=[1.38 * inch, 5.0 * inch], hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4f3")),
                                   ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#d7e0df")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                                   ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        flow.extend([table, Spacer(1, 10)])

    contract_rows = service_rows + component_rows + lease_rows + invoice_rows
    body_lines = [line for line in lines[1:] if line not in metadata and line not in contract_rows
                  and line != "END_OF_AGREEMENT"]
    for line in body_lines:
        if line == "PAGE_BREAK":
            flow.append(PageBreak())
        elif line.startswith(("Contract clause", "Lease terms", "All rates", "All values")):
            flow.append(Paragraph(_pdf_safe(line), styles["SectionTitle"] if line.startswith("Contract clause") else styles["BodyCopy"]))
        elif line.startswith(("SECTION:", "SCHEDULE:", "RECITALS", "Section ", "Schedule ", "Appendix ")):
            flow.append(Paragraph(_pdf_safe(line), styles["SectionTitle"]))
        else:
            flow.append(Paragraph(_pdf_safe(line), styles["BodyCopy"]))

    if service_rows:
        flow.append(Paragraph("Schedule 1 - Services and recurring charges", styles["SectionTitle"]))
        data = [["Service", "Contractual service and charge terms"]]
        for row in service_rows:
            _, code, name, enrolled, _stream, component, rate, unit, charge_type, *details = row.split("|")
            basis, frequency, day, vehicles, drivers = details or ["USD", "monthly", "1", "", ""]
            quantity = f"{vehicles} covered vehicles" if vehicles else f"{drivers} covered drivers" if drivers else "the Customer account"
            status = "Included" if enrolled.lower() == "true" else "Not selected"
            if basis == "PERCENTAGE":
                rate_sentence = f"{rate} percent of monthly spend"
            elif basis == "BASIS_POINTS":
                rate_sentence = f"{rate} basis points of transaction value"
            else:
                rate_sentence = f"USD {rate} per {unit.replace('_', ' ')}"
            terms = (f"Service code: {code}. Status: {status}. Charge: {component.replace('_', ' ')}. Rate: {rate_sentence}. "
                     f"Billing: {frequency} on day {day}. Quantity basis: {quantity}.")
            data.append([name, terms])
        flow.append(_styled_table(data, [1.35, 5.05], styles))
    if component_rows:
        flow.append(Paragraph("Schedule 2 - One-time charges", styles["SectionTitle"]))
        data = [["Service", "Charge", "Description", "Amount", "Quantity"]]
        for row in component_rows:
            _, code, component, label, _type, amount, unit, quantity = row.split("|")
            data.append([code, component.replace("_", " ").title(), label, f"USD {amount}", f"{quantity} {unit}"])
        flow.append(_styled_table(data, [0.8, 1.3, 2.0, 1.1, .95], styles))
    if lease_rows:
        flow.append(Paragraph("Vehicle and lease schedule", styles["SectionTitle"]))
        data = [["Asset", "Description", "Quantity", "Monthly rate", "Term", "Effective"]]
        for row in lease_rows:
            parts = row.split("|")
            _, code, name, quantity, unit, rate, term, effective, frequency, day, make, model, engine, currency = parts
            data.append([code, f"{make} {model} ({engine})", f"{quantity} {unit.replace('_', ' ')}",
                         f"{currency} {float(rate):,.2f}", f"{term} months", effective])
        flow.append(_styled_table(data, [0.7, 1.4, 1.2, 1.1, .9, .85], styles))
    if invoice_rows:
        flow.append(Paragraph("Invoice detail", styles["SectionTitle"]))
        data = [["Stream", "Code", "Description", "Charge", "Qty", "Rate", "Amount"]]
        for row in invoice_rows:
            _, stream, code, name, component, charge_type, quantity, rate, unit, amount = row.split("|")
            data.append([stream.title(), code, name, component.replace("_", " ").title(), quantity,
                         f"{float(rate):,.2f} / {unit.replace('_', ' ')}", f"{float(amount):,.2f}"])
        flow.append(_styled_table(data, [.55, .85, 1.2, .9, .4, 1.35, .85], styles))

    def page_chrome(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d7e0df"))
        canvas.line(doc.leftMargin, .48 * inch, letter[0] - doc.rightMargin, .48 * inch)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#657477"))
        canvas.drawString(doc.leftMargin, .32 * inch, "APOLLO WHEELS  |  SAMPLE AGREEMENT")
        canvas.drawRightString(letter[0] - doc.rightMargin, .32 * inch, f"Page {doc.page}")
        canvas.restoreState()

    document.build(flow, onFirstPage=page_chrome, onLaterPages=page_chrome)
    return buffer.getvalue()


def _styled_table(rows: list[list[str]], widths_in: list[float], styles) -> Table:
    cells = [[Paragraph(_pdf_safe(cell), styles["SmallHead"] if row_index == 0 else styles["SmallCell"])
              for cell in row] for row_index, row in enumerate(rows)]
    table = Table(cells, colWidths=[width * inch for width in widths_in], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173b46")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f5")]),
                               ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#d7e0df")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return table


def _pdf_safe(value: object) -> str:
    text = (str(value).replace("—", "-").replace("–", "-").replace("·", "-")
            .replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'"))
    return escape(text.encode("ascii", "replace").decode("ascii"))


def _template_agreement_lines(kind: str, client_name: str, prefix: str) -> list[str]:
    """Read contract clauses from the supplied drafting templates for demo PDFs."""
    root = Path(__file__).resolve().parents[2]
    if kind == "MSA":
        path = root / "master_service_agreement_Template_and_Field_Guide.md"
        start, end = "# 3. Master Services Agreement", "# 5. Recommended schedules"
    else:
        path = root / "master_lease_agreement_template_and_field_guide.md"
        start, end = "# PART A — MASTER LEASE AGREEMENT", "# PART C — FLEET-LEASING ANALYSIS AND CONTROLS"
    customer_entity = f"{client_name}, LLC"
    field_values = {
        "AGREEMENT DATE": "1 January 2026", "AGREEMENT_DATE": "1 January 2026",
        "EFFECTIVE_DATE": "1 January 2026", "CUSTOMER_LEGAL_NAME": customer_entity,
        "PROVIDER_LEGAL_NAME": "Apollo Wheels LLC",
        "LESSEE FULL LEGAL NAME": customer_entity, "LESSOR FULL LEGAL NAME": "Apollo Wheels LLC",
        "ENTITY_TYPE": "limited liability company", "ENTITY TYPE": "limited liability company",
        "JURISDICTION": "Delaware", "PLACE_OF_FORMATION": "Delaware",
        "ADDRESS": "100 Sample Way, Dover, Delaware 19901",
        "CUSTOMER_REGISTERED_ADDRESS": "100 Sample Way, Dover, Delaware 19901",
        "PROVIDER_REGISTERED_ADDRESS": "200 Example Avenue, Dover, Delaware 19901",
        "PROVIDER_BUSINESS_DESCRIPTION": "fleet management, mobility and related support services",
        "CUSTOMER_BUSINESS_PURPOSE": "fleet management and vehicle operations",
        "CURRENCY": "USD", "MASTER_SERVICES_AGREEMENT_TITLE": "Master Services Agreement",
        "SIGNATORY_NAME": "Authorised Signatory", "SIGNATORY_TITLE": "Authorised Representative",
        "NAME": "Authorised Signatory", "TITLE": "Authorised Representative", "SIGNATURE_DATE": "1 January 2026",
        "CONTRACT_ID": f"{prefix}-MSA-001", "VERSION_AND_DATE": "Version 1.0 - 1 January 2026",
        "INITIAL_FLEET_COUNT": "500 vehicles", "VEHICLE_CLASSES": "light commercial vehicles",
        "COUNTRIES_STATES_REGIONS": "the United States", "COUNTRY_AND_JURISDICTION": "United States / Delaware",
        "SERVICE_COMMENCEMENT_DATE": "1 January 2026", "INITIAL_TERM": "three years",
        "INITIAL_TERM_END_DATE": "31 December 2028", "BUSINESS_OWNER": "Fleet Operations Director",
        "LEGAL_REVIEWER": "Legal Department", "COMMERCIAL_APPROVER": "Commercial Director",
        "OPERATIONS_APPROVER": "Operations Director", "PAYMENT_TERM": "30 days after invoice date",
        "GOVERNING_LAW": "the laws of Delaware", "NOTICE_EMAIL": "contracts@example.com",
        "NOTICE_ADDRESS": "the registered office stated above", "SIGNATORY_TITLE": "Authorised Representative",
    }

    def fill_field(match: re.Match) -> str:
        key = (match.group(1) or match.group(2)).strip().upper()
        return field_values.get(key, "the terms set out in the applicable Schedule")

    source = path.read_text(encoding="utf-8")
    source = source[source.index(start):source.index(end)]
    lines: list[str] = []
    paragraph: list[str] = []
    skipping = False
    skipping_why = False
    for raw in source.splitlines():
        line = raw.strip()
        if not line:
            skipping_why = False
            if paragraph:
                lines.append(" ".join(paragraph))
                paragraph = []
            continue
        if skipping_why:
            continue
        if line.startswith(("Why ", "**Why ")):
            skipping_why = True
            continue
        if line in {"---", "------------------------------------------------------------------------"}:
            continue
        if line.startswith("### ") and ("Field guide" in line or "Why it is needed" in line):
            skipping = True
            continue
        if line == "### Template":
            continue
        if skipping:
            if line.startswith("### ") or line.startswith("## ") or line.startswith("# "):
                skipping = False
            else:
                continue
        if line.startswith("|") or line.startswith("**Legal-use warning.") or line.startswith(("Why ", "**Why ")):
            continue
        if line.startswith("> **") or line.startswith("> "):
            line = line.lstrip("> ")
        line = re.sub(r"\[([^\]]+)\]|\{\{([^}]+)}}", fill_field, line)
        line = re.sub(r"\*\*(.*?)\*\*|\*(.*?)\*", lambda m: m.group(1) or m.group(2), line)
        line = line.replace("`", "")
        line = line.rstrip("\\").rstrip()
        line = re.sub(r"^[-*+]\s+", "- ", line)
        line = line.replace("[CLIENT NAME]", client_name).replace("{{CLIENT_NAME}}", client_name)
        if line.startswith("#"):
            if paragraph:
                lines.append(" ".join(paragraph))
                paragraph = []
            heading = re.sub(r"^#+\s*", "", line)
            heading = re.sub(r"\s+---\s+drafting template\s*$", "", heading, flags=re.IGNORECASE)
            lines.append("SECTION: " + heading)
        elif line.startswith("- ") or re.match(r"^\d+[.)]\s", line) or line.startswith("Synthetic Schedule:"):
            if paragraph:
                lines.append(" ".join(paragraph))
                paragraph = []
            lines.append(line)
        else:
            paragraph.append(line)
    if paragraph:
        lines.append(" ".join(paragraph))
    return lines


def _service_price(index: int, code: str, client_id: str = "C-1001") -> tuple[float, str, str, int, int, str]:
    """Return the single source of truth for the synthetic MSA and invoice rates."""
    amount = round(3.5 + index * 1.25, 2)
    component = "monthly_per_vehicle" if index % 3 else "monthly_account_fee"
    unit = "vehicle_month" if component == "monthly_per_vehicle" else "account_month"
    fleet_size = 500 if client_id == "C-1001" else 300
    driver_total = 600 if client_id == "C-1001" else 360
    vehicles, drivers = (fleet_size, 0) if unit == "vehicle_month" else (0, 0)
    if code == "MVR_SAFETY":
        component, unit, vehicles, drivers = "monthly_per_driver", "driver_month", 0, driver_total
    basis = "USD"
    if code == "TELEMATICS":
        amount, basis, unit = 1.5, "PERCENTAGE", "monthly_spend_percentage"
        component, vehicles = "monthly_account_fee", 0
    elif code == "REMARKETING":
        amount, basis, unit = 25.0, "BASIS_POINTS", "transaction_value_basis_points"
        component, vehicles = "monthly_account_fee", 0
    return amount, component, unit, vehicles, drivers, basis


def write_clean_msa(path: Path, client_id: str, client_name: str, prefix: str) -> Path:
    """Create a complete, business-readable MSA without template guidance text."""
    service_sections: list[str] = []
    for index, service in enumerate(SERVICES):
        subscribed = service["code"] in SUBSCRIBED_CODES
        amount, component, unit, vehicles, drivers, pricing_basis = _service_price(index, service["code"], client_id)
        quantity = f"{vehicles} covered vehicles" if vehicles else f"{drivers} covered drivers" if drivers else "the Customer account"
        status = "Included" if subscribed else "Not selected"
        if pricing_basis == "PERCENTAGE":
            rate_sentence = f"{amount:.2f} percent of monthly spend"
        elif pricing_basis == "BASIS_POINTS":
            rate_sentence = f"{amount:.2f} basis points of transaction value"
        else:
            rate_sentence = f"USD {amount:.2f} per {unit.replace('_', ' ')}"
        service_sections.extend([
            f"SECTION: Schedule 1.{index + 1} - {service['name']}",
            f"{service['name']} is a fleet-management service for the Customer's operating fleet. Provider will maintain the operational workflow, service records and customer support appropriate to this service, subject to the scope and service-management terms in this Agreement.",
            f"Service code: {service['code']}. Status: {status}. Charge: {component.replace('_', ' ')}. Rate: {rate_sentence}. Billing: monthly on day 1. Quantity basis: {quantity}.",
            (f"Because this Service is included, Provider will perform the activities described above for the applicable quantity basis and will report material service activity in the monthly service report. Customer will provide timely information, approvals and access reasonably needed for delivery."
             if subscribed else
             f"This Service is not selected for the initial term. Provider has no obligation to perform it and Customer will not be charged for it unless the Parties add it through a written change order stating scope, rate and effective date."),
        ])
        if index in {0, 2, 4, 6, 8, 10, 11}:
            service_sections.append("PAGE_BREAK")
    clauses = [
        "MASTER SERVICES AGREEMENT",
        f"CLIENT_ID: {client_id}", f"CLIENT_NAME: {client_name}", f"AGREEMENT_ID: {prefix}-MSA-001",
        "AGREEMENT_TYPE: MSA", "VERSION: 1.0", "EFFECTIVE_DATE: 2026-01-01",
        f"This sample agreement records the terms on which Apollo Wheels LLC provides fleet management services to {client_name}, LLC.",
        "SECTION: 1. Parties and purpose",
        f"This Master Services Agreement is made on 1 January 2026 between {client_name}, LLC, a Delaware limited liability company with offices at 100 Sample Way, Dover, Delaware 19901 (Customer), and Apollo Wheels LLC, a Delaware limited liability company with offices at 200 Example Avenue, Dover, Delaware 19901 (Provider).",
        "Customer operates a fleet of light commercial vehicles throughout the United States. Provider will provide the services selected in Schedule 1, and Customer will pay the charges stated in that Schedule.",
        "SECTION: 2. Definitions and interpretation",
        "Covered Vehicle means a vehicle included in the Customer fleet and approved for a selected service. Driver means an individual authorised by Customer to operate a Covered Vehicle. Fees means the recurring and one-time charges stated in Schedule 1 and Schedule 2. Services means the selected fleet management services described in this Agreement and the Schedules.",
        "References to a Schedule are references to a schedule forming part of this Agreement. If there is a conflict, this Agreement governs except that a commercial term expressly stated in Schedule 1 or Schedule 2 governs for the relevant service or charge.",
        "SECTION: 3. Services and service scope",
        "Provider will deliver each selected Service with reasonable skill and care, using suitably qualified personnel, systems and suppliers. The selected Services, charge basis, rates, billing cadence and initial quantity basis are stated in Schedule 1.",
        "Provider will maintain a service desk for operational enquiries during normal United States business hours. Emergency safety and accident reporting will be available at all times through the designated incident channel.",
        "Services do not include vehicle acquisition funding, insurance underwriting, legal advice, tax advice, or work outside the selected Services unless the Parties agree a written change order stating scope, price and implementation date.",
        "SECTION: 4. Customer responsibilities",
        "Customer will provide complete and accurate fleet, driver, vehicle, mileage and operating information reasonably needed for the Services. Customer will keep its authorised contacts current and will ensure that its drivers comply with applicable law, vehicle policies and reasonable safety instructions.",
        "Customer remains responsible for decisions about vehicle use, driver employment, route selection, cargo, regulatory permits, taxes, fines and any activity not expressly delegated to Provider. Customer will promptly notify Provider of material changes to fleet size, territory or operating requirements.",
        "SECTION: 5. Fees, invoicing and payment",
        "Provider will invoice recurring Fees monthly in arrears and any one-time charge in the first applicable billing period. Each invoice will identify the relevant service, quantity, rate, charge basis and billing period. Payment is due within 30 days after invoice date in United States dollars.",
        "Customer must notify Provider of a good-faith invoice dispute within 15 days after invoice date, with enough detail to identify the disputed item. Customer will pay undisputed amounts when due. The Parties will work in good faith to resolve a disputed amount promptly.",
        "Provider may change a rate only through a written change order signed by both Parties. Taxes, duties and government charges are excluded from the Fees unless expressly included in a Schedule.",
        "SECTION: 6. Service management and records",
        "Provider will provide monthly service reports covering selected-service activity, material incidents, open actions and agreed performance measures. The Parties will hold a monthly operational review and a quarterly commercial review.",
        "Provider will keep records reasonably necessary to support invoices and service reporting for at least 24 months after creation. On reasonable notice, Customer may review records directly related to an invoice, subject to confidentiality and information-security safeguards.",
        "SECTION: 7. Data, confidentiality and security",
        "Each Party will protect the other Party's Confidential Information and use it only to perform or receive the Services. Confidential Information may be disclosed to personnel and suppliers who need it for that purpose and who are bound by equivalent confidentiality obligations.",
        "Provider will apply reasonable administrative, technical and physical safeguards to Fleet Data. Customer retains ownership of its Fleet Data. Provider may use aggregated and de-identified data to operate, secure and improve its services.",
        "SECTION: 8. Compliance, insurance and suppliers",
        "Each Party will comply with laws applicable to its performance under this Agreement. Provider may use qualified suppliers to perform part of the Services but remains responsible for their performance as if it were its own.",
        "Each Party will maintain insurance customary for its business and sufficient to meet its obligations under this Agreement. Customer will maintain insurance and registrations required for its Covered Vehicles and operations.",
        "SECTION: 9. Liability and indemnities",
        "Neither Party is liable to the other for indirect, special, incidental, punitive or consequential loss, or for loss of profit, revenue, goodwill or anticipated savings. This exclusion does not apply where such exclusion is prohibited by law.",
        "Each Party's aggregate liability arising from this Agreement in a contract year is limited to the Fees paid or payable for the affected Services in that contract year, except for fraud, wilful misconduct, death or personal injury caused by negligence, breach of confidentiality, or liabilities that cannot lawfully be limited.",
        "Each Party will indemnify the other against third-party claims to the extent caused by its breach of law, negligence or wilful misconduct in connection with this Agreement, subject to the liability provisions above.",
        "SECTION: 10. Term, termination and transition",
        "This Agreement begins on the Effective Date and continues for an initial term ending 31 December 2028. It renews for successive one-year periods unless either Party gives at least 90 days' written notice before the end of the then-current term.",
        "Either Party may terminate this Agreement for material breach if the breach is not cured within 30 days after written notice. Either Party may terminate immediately if the other Party becomes insolvent or ceases a material part of its business.",
        "On termination, Provider will provide reasonable transition assistance for up to 90 days at the applicable Schedule 1 rates, and will return or securely delete Customer Fleet Data as directed, subject to legal retention obligations.",
        "SECTION: 11. General terms",
        "Neither Party may assign this Agreement without the other Party's written consent, except to an Affiliate or successor in connection with a merger, sale or reorganisation. This Agreement and its Schedules are the entire agreement about their subject matter and may be amended only in writing signed by both Parties.",
        "A notice under this Agreement must be in writing and delivered to the registered office above, with a copy to contracts@example.com. Delaware law governs this Agreement, and the state and federal courts located in Delaware have exclusive jurisdiction.",
        "SECTION: 12. Signature blocks",
        "IN WITNESS WHEREOF, the Parties have caused this Agreement to be executed by their authorised representatives.",
        f"CUSTOMER: {client_name}, LLC", "By: ________________________________  Name: Authorised Signatory  Title: Authorised Representative  Date: 1 January 2026",
        "PROVIDER: Apollo Wheels LLC", "By: ________________________________  Name: Authorised Signatory  Title: Authorised Representative  Date: 1 January 2026",
        "Schedule 1 forms part of this Agreement. Each service section below states the service scope, selection status, billing basis, recurring charge and initial quantity basis.",
        *service_sections,
        "Schedule 2 - One-time charges", "The one-time onboarding and configuration charge is USD 250.00, payable in the first billing period.",
        "END_OF_AGREEMENT",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(make_text_pdf(clauses, body_size=12, body_leading=16))
    return path


def write_clean_msa_sample(path: Path) -> Path:
    """Create the reviewable Northstar example used as the agreement baseline."""
    return write_clean_msa(path, "C-1001", "Northstar Fleet Services", "NORTHSTAR")


def write_demo_agreements(folder: Path, client_id: str, client_name: str, prefix: str = "DEMO") -> list[dict[str, object]]:
    folder.mkdir(parents=True, exist_ok=True)
    service_lines: list[str] = []
    for index, service in enumerate(SERVICES):
        subscribed = service["code"] in SUBSCRIBED_CODES
        amount, component, unit, vehicles, drivers, pricing_basis = _service_price(index, service["code"], client_id)
        vehicle_count = str(vehicles) if vehicles else ""
        driver_count = str(drivers) if drivers else ""
        service_lines.append(
            f"SERVICE|{service['code']}|{service['name']}|{str(subscribed).lower()}|SERVICE|{component}|"
            f"{amount:.2f}|{unit}|recurring|{pricing_basis}|monthly|1|{vehicle_count}|{driver_count}"
        )
    service_lines.append("COMPONENT|FUEL|activation|One-time setup|one_time|250.00|account|1")
    lease_quantity = 500 if client_id == "C-1001" else 300
    lease_rate = 1200.00 if client_id == "C-1001" else 1050.00
    mla_lines = [
        "MASTER LEASE AGREEMENT",
        f"CLIENT_ID: {client_id}",
        f"CLIENT_NAME: {client_name}",
        f"AGREEMENT_ID: {prefix}-MLA-001",
        "AGREEMENT_TYPE: MLA",
        "VERSION: 1.0",
        "EFFECTIVE_DATE: 2026-01-01",
        f"This sample agreement records the vehicle lease terms between Apollo Wheels LLC and {client_name}, LLC.",
        *_template_agreement_lines("MLA", client_name, prefix),
        "The vehicle and lease schedule below forms part of this Agreement and states the assets, rental, term and billing arrangement.",
        f"LEASE|LEASE-01|Fleet vehicle lease|{lease_quantity}|vehicle_month|{lease_rate:.2f}|48|2026-01-01|monthly|1|Ford|Transit|Hybrid|USD",
        "END_OF_AGREEMENT",
    ]
    items = []
    msa_filename = f"{prefix.lower()}_msa_v1.pdf"
    msa_path = folder / msa_filename
    write_clean_msa(msa_path, client_id, client_name, prefix)
    items = [{"id": f"{prefix}-MSA-001", "type": "MSA", "filename": msa_filename, "path": msa_path, "lines": []}]
    for agreement_type, agreement_id, lines in (("MLA", f"{prefix}-MLA-001", mla_lines),):
        filename = f"{prefix.lower()}_{agreement_type.lower()}_v1.pdf"
        path = folder / filename
        path.write_bytes(make_text_pdf(lines))
        items.append({"id": agreement_id, "type": agreement_type, "filename": filename, "path": path, "lines": lines})
    return items


def write_demo_invoice(
    folder: Path,
    client_id: str,
    client_name: str,
    period_start: str,
    period_end: str,
    number: str,
    stream: str = "SERVICE",
) -> dict[str, object]:
    folder.mkdir(parents=True, exist_ok=True)
    lines = [
        "APOLLO WHEELS — SYNTHETIC BILLING STATEMENT",
        f"CLIENT_ID: {client_id}",
        f"CLIENT_NAME: {client_name}",
        f"INVOICE_NUMBER: {number}",
        f"BILLING_STREAM: {stream}",
        f"PERIOD_START: {period_start}",
        f"PERIOD_END: {period_end}",
        "All values are synthetic demo assumptions.",
    ]
    if stream == "LEASE":
        quantity = 500 if client_id == "C-1001" else 300
        rate = 1200.00 if client_id == "C-1001" else 1050.00
        lines.append(f"LINE|LEASE|LEASE-01|Vehicle lease|monthly_lease|recurring|{quantity}|{rate:.2f}|vehicle_month|{quantity * rate:.2f}")
    else:
        # Bill every service marked subscribed in the matching sample MSA.
        for service in SERVICES:
            if service["code"] not in SUBSCRIBED_CODES:
                continue
            index = SERVICES.index(service)
            rate, component, unit, vehicles, drivers, _basis = _service_price(index, service["code"], client_id)
            if period_start == "2026-02-01" and service["code"] == "RR":
                rate += 1.25
            quantity = drivers or vehicles or 1
            lines.append(
                f"LINE|SERVICE|{service['code']}|{service['name']}|{component}|recurring|{quantity}|{rate:.2f}|{unit}|{rate * quantity:.2f}"
            )
        if period_start == "2026-01-01":
            lines.append("LINE|SERVICE|FUEL|Fuel|activation|one_time|1|250.00|account|250.00")
    filename = f"{period_start}_{stream.lower()}_{number.lower()}.pdf"
    path = folder / filename
    path.write_bytes(make_text_pdf(lines))
    return {"invoice_number": number, "filename": filename, "path": path, "lines": lines, "stream": stream,
            "period_start": period_start, "period_end": period_end}


def write_mla_from_extracted(path: Path, client_id: str, client_name: str, extracted: dict[str, object], version: str) -> Path:
    """Generate an MLA PDF from extracted terms (used for regeneration after save)."""
    from .extraction import extract_agreement_terms

    lease = extracted.get("lease", {}) or {}
    if not lease:
        raise ValueError("No lease data in extracted terms")

    lease_quantity = lease.get("quantity", 300)
    lease_rate = lease.get("contract_amount", 1050.00)
    lines = [
        "MASTER LEASE AGREEMENT",
        f"CLIENT_ID: {client_id}",
        f"CLIENT_NAME: {client_name}",
        f"AGREEMENT_ID: MLA-REGEN-{uuid.uuid4().hex[:8].upper()}",
        "AGREEMENT_TYPE: MLA",
        f"VERSION: {version}",
        f"EFFECTIVE_DATE: {lease.get('effective_from', '2026-01-01')}",
        f"This sample agreement records the vehicle lease terms between Apollo Wheels LLC and {client_name}, LLC.",
        *_template_agreement_lines("MLA", client_name, "MLA"),
        "The vehicle and lease schedule below forms part of this Agreement and states the assets, rental, term and billing arrangement.",
        f"LEASE|LEASE-01|Fleet vehicle lease|{lease_quantity}|vehicle_month|{lease_rate:.2f}|48|{lease.get('effective_from', '2026-01-01')}|{lease.get('billing_frequency', 'monthly')}|1|{lease.get('vehicle_make', 'Ford')}|{lease.get('vehicle_model', 'Transit')}|{lease.get('engine_type', 'Hybrid')}|USD",
        "END_OF_AGREEMENT",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(make_text_pdf(lines))
    return path


def write_msa_from_extracted(path: Path, client_id: str, client_name: str, extracted: dict[str, object], version: str) -> Path:
    """Generate an MSA PDF from extracted terms (used for regeneration after save)."""
    services = extracted.get("services", [])
    components = extracted.get("components", [])

    if not services and not components:
        raise ValueError("No service or component data in extracted terms")

    service_lines: list[str] = []
    for svc in services:
        svc_code = svc.get("service_code", "UNKNOWN")
        svc_name = svc.get("service_name", "Unknown Service")
        subscribed = svc.get("subscribed", False)
        component = "monthly_per_vehicle" if svc_code.endswith("_VEHICLE") else "monthly_account_fee"
        rate = svc.get("contract_amount", 0)
        unit = svc.get("rate_unit", "vehicle_month")
        basis = svc.get("pricing_basis", "USD")
        frequency = svc.get("billing_frequency", "monthly")
        day = svc.get("billing_day", "1")
        vehicles = svc.get("vehicle_count", 0)
        drivers = svc.get("driver_count", 0)
        qty = f"{vehicles} covered vehicles" if vehicles else f"{drivers} covered drivers" if drivers else "the Customer account"
        status = "Included" if subscribed else "Not selected"

        if basis == "PERCENTAGE":
            rate_sentence = f"{rate:.2f} percent of monthly spend"
        elif basis == "BASIS_POINTS":
            rate_sentence = f"{rate:.2f} basis points of transaction value"
        else:
            rate_sentence = f"USD {rate:.2f} per {unit.replace('_', ' ')}"

        charge = component.replace("_", " ")
        service_lines.append(
            f"SERVICE|{svc_code}|{svc_name}|{str(subscribed).lower()}|SERVICE|{charge}|"
            f"{rate:.2f}|{unit}|recurring|{basis}|{frequency}|{day}|{vehicles}|{drivers}"
        )

    for comp in components:
        comp_code = comp.get("component_name", "activation")
        comp_label = comp.get("component_name", "Setup")
        charge_type = comp.get("charge_type", "one_time")
        amount = comp.get("contract_amount", 250.00)
        unit = comp.get("rate_unit", "account")
        qty = comp.get("quantity", 1)
        service_lines.append(f"COMPONENT|{comp_code}|{comp_label}|{charge_type}|{charge_type}|{amount:.2f}|{unit}|{qty}")

    if not service_lines:
        raise ValueError("No service or component data to generate MSA")

    prefix = "REGEN"
    msa_filename = f"{prefix}_{client_id}_{version}.pdf"
    msa_path = path.parent / msa_filename
    service_lines.append("COMPONENT|FUEL|activation|One-time setup|one_time|250.00|account|1")

    all_lines = [
        "MASTER SERVICES AGREEMENT",
        f"CLIENT_ID: {client_id}",
        f"CLIENT_NAME: {client_name}",
        f"AGREEMENT_ID: {prefix}-MSA-001",
        "AGREEMENT_TYPE: MSA",
        f"VERSION: {version}",
        "EFFECTIVE_DATE: 2026-01-01",
        f"This sample agreement records the terms on which Apollo Wheels LLC provides fleet management services to {client_name}, LLC.",
        *_template_agreement_lines("MSA", client_name, prefix),
        "Schedule 1 forms part of this Agreement. Each service section below states the service scope, selection status, billing basis, recurring charge and initial quantity basis.",
        "SECTION: Schedule 1 - Services and recurring charges",
        *service_lines,
        "END_OF_AGREEMENT",
    ]
    msa_path.write_bytes(make_text_pdf(all_lines))
    return msa_path
