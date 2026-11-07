"""PDF text extraction and deterministic parsing for synthetic demo documents."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from .catalog import SERVICES


def extract_pdf_pages(path: Path) -> list[str]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ValueError("PDF could not be read; it may be corrupt or malformed.") from exc
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported in this MVP.")
    try:
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ValueError("Could not extract text from this PDF.") from exc
    if not any(page.strip() for page in pages):
        raise ValueError("This PDF has no selectable text. Scanned PDF OCR is planned for a later phase.")
    return pages


def extract_pdf_text(path: Path) -> str:
    return "\n".join(extract_pdf_pages(path)).strip()


def parse_key_values(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip().upper()] = value.strip()
    return result


def parse_service_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        parts = line.strip().split("|")
        if len(parts) not in {9, 14} or parts[0] != "SERVICE":
            continue
        _, code, name, subscribed, stream, component, rate, unit, charge_type = parts[:9]
        details = parts[9:]
        pricing_basis, frequency, billing_day, vehicles, drivers = details or ("USD", "monthly", "1", "", "")
        rows.append({
            "service_code": code.strip(),
            "service_name": name.strip(),
            "subscribed": subscribed.strip().lower() == "true",
            "billing_stream": stream.strip(),
            "component_name": component.strip(),
            "contract_amount": float(rate.strip()),
            "rate_unit": unit.strip(),
            "charge_type": charge_type.strip(),
            "pricing_basis": pricing_basis.strip(),
            "billing_frequency": frequency.strip(),
            "billing_day": billing_day.strip() or None,
            "vehicle_count": float(vehicles) if vehicles else None,
            "driver_count": float(drivers) if drivers else None,
            "field_confidence": {"service_code": 0.99, "subscribed": 0.99, "contract_amount": 0.99,
                                 "rate_unit": 0.99, "charge_type": 0.99, "pricing_basis": 0.99,
                                 "billing_frequency": 0.99, "billing_day": 0.99,
                                 "vehicle_count": 0.99, "driver_count": 0.99},
            "confidence_method": "Exact synthetic row match (heuristic, not calibrated)",
            "evidence_page": 1,
            "source_text": line.strip(),
        })
    if rows:
        return rows

    # Clean sample agreements express each commercial term as a sentence in
    # Schedule 1. Parse that visible agreement language when no legacy
    # pipe-delimited fixture rows are present.
    names = {service["code"]: service["name"] for service in SERVICES}
    pattern = re.compile(
        r"Service code:\s*(?P<code>[A-Z_]+)\.\s*Status:\s*(?P<status>Included|Not selected)\."
        r"\s*Charge:\s*(?P<component>[^.]+)\.\s*Rate:\s*(?P<rate_clause>.*?)\.\s*Billing:\s*"
        r"(?P<frequency>[^.]+?)\s*on day\s*(?P<day>[^.]+)\.\s*Quantity\s+basis:\s*(?P<quantity>[^.]+)\.",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        values = {key: " ".join(value.split()) for key, value in match.groupdict().items()}
        code = values["code"].upper()
        if code not in names:
            continue
        rate_clause = values["rate_clause"].lower()
        usd_rate = re.fullmatch(r"usd\s+(\d+(?:\.\d+)?)\s+per\s+(.+)", rate_clause)
        percentage_rate = re.fullmatch(r"(\d+(?:\.\d+)?)\s+percent\s+of\s+(.+)", rate_clause)
        basis_points_rate = re.fullmatch(r"(\d+(?:\.\d+)?)\s+basis points\s+of\s+(.+)", rate_clause)
        if usd_rate:
            amount, basis, unit = float(usd_rate.group(1)), "USD", usd_rate.group(2)
        elif percentage_rate:
            amount, basis, unit = float(percentage_rate.group(1)), "PERCENTAGE", percentage_rate.group(2)
        elif basis_points_rate:
            amount, basis, unit = float(basis_points_rate.group(1)), "BASIS_POINTS", basis_points_rate.group(2)
        else:
            continue
        quantity = values["quantity"].lower()
        vehicle_count = re.search(r"(\d+)\s+covered vehicles", quantity)
        driver_count = re.search(r"(\d+)\s+covered drivers", quantity)
        rows.append({
            "service_code": code,
            "service_name": names[code],
            "subscribed": values["status"].lower() == "included",
            "billing_stream": "SERVICE",
            "component_name": values["component"].lower().replace(" ", "_"),
            "contract_amount": amount,
            "rate_unit": unit.lower().replace(" ", "_"),
            "charge_type": "recurring",
            "pricing_basis": basis,
            "billing_frequency": values["frequency"].lower(),
            "billing_day": values["day"],
            "vehicle_count": float(vehicle_count.group(1)) if vehicle_count else None,
            "driver_count": float(driver_count.group(1)) if driver_count else None,
            "field_confidence": {"service_code": 0.99, "subscribed": 0.99, "contract_amount": 0.99,
                                 "rate_unit": 0.99, "charge_type": 0.99, "pricing_basis": 0.99,
                                 "billing_frequency": 0.99, "billing_day": 0.99,
                                 "vehicle_count": 0.99, "driver_count": 0.99},
            "confidence_method": "Exact commercial schedule sentence match (heuristic, not calibrated)",
            "evidence_page": 1,
            "source_text": match.group(0),
        })
    return rows


def parse_extra_components(text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        parts = line.strip().split("|")
        if len(parts) != 8 or parts[0] != "COMPONENT":
            continue
        _, code, component, label, charge_type, amount, unit, quantity = parts
        rows.append({
            "service_code": code,
            "component_name": component,
            "display_name": label,
            "charge_type": charge_type,
            "contract_amount": float(amount),
            "rate_unit": unit,
            "quantity": float(quantity),
            "billing_stream": "SERVICE",
            "subscribed": True,
            "pricing_basis": "USD",
            "billing_frequency": "one_time",
            "billing_day": None,
            "source_text": line,
            "field_confidence": {"component_name": 0.99, "contract_amount": 0.99, "charge_type": 0.99,
                                 "pricing_basis": 0.99, "billing_frequency": 0.99},
            "confidence_method": "Exact synthetic row match (heuristic, not calibrated)",
            "evidence_page": 1,
        })
    if rows:
        return rows
    visible = re.search(
        r"Schedule 2 - One-time charges\s+Service\s+Charge\s+Description\s+Amount\s+Quantity\s+"
        r"(?P<code>[A-Z_]+)\s+(?P<component>[A-Za-z ]+)\s+(?P<label>[A-Za-z -]+)\s+USD\s*"
        r"(?P<amount>\d+(?:\.\d+)?)\s+(?P<quantity>\d+)\s+(?P<unit>[A-Za-z_ ]+)", text, re.DOTALL)
    if visible:
        item = visible.groupdict()
        rows.append({
            "service_code": item["code"], "component_name": item["component"].strip().lower().replace(" ", "_"),
            "display_name": item["label"].strip(), "charge_type": "one_time", "contract_amount": float(item["amount"]),
            "rate_unit": item["unit"].strip().lower().replace(" ", "_"), "quantity": float(item["quantity"]),
            "billing_stream": "SERVICE", "subscribed": True, "pricing_basis": "USD", "billing_frequency": "one_time",
            "billing_day": None, "source_text": visible.group(0),
            "field_confidence": {"component_name": 0.99, "contract_amount": 0.99, "charge_type": 0.99,
                                 "pricing_basis": 0.99, "billing_frequency": 0.99},
            "confidence_method": "Exact visible schedule match (heuristic, not calibrated)", "evidence_page": 1,
        })
    return rows


def parse_billing_rows(text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        match = re.match(
            r"^LINE\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)$",
            line.strip(),
        )
        if not match:
            continue
        stream, code, name, component, charge_type, quantity, rate, unit, amount = match.groups()
        rows.append({
            "billing_stream": stream.strip(),
            "service_code": code.strip(),
            "service_name": name.strip(),
            "component_code": component.strip(),
            "component_name": component.strip().replace("_", " ").title(),
            "charge_type": charge_type.strip(),
            "quantity": float(quantity),
            "rate": float(rate),
            "rate_unit": unit.strip(),
            "amount": float(amount),
        })
    return rows


def parse_lease_row(text: str) -> dict[str, object] | None:
    for line in text.splitlines():
        parts = line.strip().split("|")
        if len(parts) not in {8, 14} or parts[0] != "LEASE":
            continue
        _, code, name, quantity, unit, amount, term_months, effective_from = parts[:8]
        details = parts[8:]
        frequency, billing_day, vehicle_make, vehicle_model, engine_type, pricing_basis = details or (
            "monthly", "1", "", "", "", "USD"
        )
        return {
            "service_code": code,
            "service_name": name,
            "subscribed": True,
            "billing_stream": "LEASE",
            "component_name": "monthly_lease",
            "contract_amount": float(amount),
            "rate_unit": unit,
            "quantity": float(quantity),
            "term_months": int(term_months),
            "effective_from": effective_from,
            "billing_frequency": frequency,
            "billing_day": billing_day,
            "vehicle_make": vehicle_make,
            "vehicle_model": vehicle_model,
            "engine_type": engine_type,
            "pricing_basis": pricing_basis,
            "source_text": line.strip(),
            "field_confidence": {"quantity": 0.99, "contract_amount": 0.99, "rate_unit": 0.99,
                                 "term_months": 0.99, "effective_from": 0.99, "billing_frequency": 0.99,
                                 "billing_day": 0.99, "vehicle_make": 0.99, "vehicle_model": 0.99,
                                 "engine_type": 0.99, "pricing_basis": 0.99},
            "confidence_method": "Exact synthetic row match (heuristic, not calibrated)",
            "evidence_page": 1,
        }
    visible = re.search(
        r"Vehicle and lease schedule\s+Asset\s+Description\s+Quantity\s+Monthly rate\s+Term\s+Effective\s+"
        r"(?P<code>LEASE-[A-Z0-9_-]+)\s+(?P<make>[A-Za-z]+)\s+(?P<model>[A-Za-z0-9 -]+)\s+\((?P<engine>[^)]+)\)\s+"
        r"(?P<quantity>\d+)\s+vehicle month\s+USD\s*(?P<amount>\d+(?:,\d{3})*(?:\.\d+)?)\s+"
        r"(?P<term>\d+)\s+months\s+(?P<effective>\d{4}-\d{2}-\d{2})", text, re.DOTALL)
    if not visible:
        return None
    item = visible.groupdict()
    return {
        "service_code": item["code"], "service_name": "Fleet vehicle lease", "subscribed": True,
        "billing_stream": "LEASE", "component_name": "monthly_lease", "contract_amount": float(item["amount"].replace(",", "")),
        "rate_unit": "vehicle_month", "quantity": float(item["quantity"]), "term_months": int(item["term"]),
        "effective_from": item["effective"], "billing_frequency": "monthly", "billing_day": "1",
        "vehicle_make": item["make"], "vehicle_model": item["model"].strip(), "engine_type": item["engine"],
        "pricing_basis": "USD", "source_text": visible.group(0),
        "field_confidence": {"quantity": 0.99, "contract_amount": 0.99, "rate_unit": 0.99,
                             "term_months": 0.99, "effective_from": 0.99, "billing_frequency": 0.99,
                             "billing_day": 0.99, "vehicle_make": 0.99, "vehicle_model": 0.99,
                             "engine_type": 0.99, "pricing_basis": 0.99},
        "confidence_method": "Exact visible lease schedule match (heuristic, not calibrated)", "evidence_page": 1,
    }
