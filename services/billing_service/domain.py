"""Billing PDF ingestion, normalized line storage, reconciliation, history, and forecasting."""

from __future__ import annotations

import re
import json
import uuid
import os
from datetime import date
from pathlib import Path
from urllib.error import URLError
from services.service_client import open_service_url

from fastapi import UploadFile

from apollo_wheels_mvp.documents import extract_pdf_text, parse_billing_rows, parse_key_values
from apollo_wheels_mvp.storage import DOCUMENT_DIR, connect

# Absolute tolerance used when comparing two numeric values that are meant to
# be equal. It is small enough to ignore floating-point rounding from cents
# arithmetic but large enough to flag a genuine rate/quantity mismatch. It is
# a demo default, not a confirmed Wheels policy.
RATE_TOLERANCE = 0.005


def _classify_issues(issues: list[str]) -> tuple[str | None, str | None]:
    """Map raw comparison findings onto a (severity, category) pair.

    Categories are intentionally coarse: they describe the *kind* of problem,
    not a confirmed business rule. Severity is a demo ordering hint and is not
    a financial-materiality measure.
    """
    if not issues:
        return None, None
    joined = " ".join(issues)
    if "Missing billing" in joined or "not present in the uploaded contract" in joined:
        return "high", "missed_revenue"
    if "Missing pricing setup" in joined:
        return "high", "missing_pricing"
    if "Billed quantity differs" in joined or "Configured quantity differs" in joined:
        return "high", "quantity_mismatch"
    if "Billed rate differs" in joined or "Configured rate differs" in joined:
        return "medium", "rate_mismatch"
    if "pricing basis" in joined or "rate unit" in joined:
        return "medium", "basis_mismatch"
    return "low", "other"


async def ingest_billing_pdf(client_id: str, upload: UploadFile, uploaded_by: str) -> dict[str, object]:
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise ValueError("Upload a PDF file.")
    content = await upload.read()
    if not content.startswith(b"%PDF"):
        raise ValueError("The uploaded file is not a valid PDF.")
    if len(content) > 20 * 1024 * 1024:
        raise ValueError("PDF uploads must be 20 MB or smaller in this MVP.")
    with connect() as db:
        if not db.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone():
            raise ValueError("Client not found.")
    doc_id = str(uuid.uuid4())
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(upload.filename).name)
    path = DOCUMENT_DIR / f"{doc_id}_{safe_name}"
    path.write_bytes(content)
    try:
        text = extract_pdf_text(path)
        metadata = parse_key_values(text)
        lines = parse_billing_rows(text)
        invoice_number = metadata.get("INVOICE_NUMBER", Path(upload.filename).stem)
        start, end = metadata.get("PERIOD_START"), metadata.get("PERIOD_END")
        stream = metadata.get("BILLING_STREAM", "COMBINED")
        if not lines or not start or not end:
            raise ValueError("Could not find billing period and line items in this PDF.")
        with connect() as db:
            db.execute(
                """INSERT INTO billing_documents
                (id,client_id,invoice_number,billing_stream,period_start,period_end,filename,file_path,status,uploaded_by)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (doc_id, client_id, invoice_number, stream, start, end, upload.filename, str(path), "ingested", uploaded_by),
            )
            for line in lines:
                agreement_type = "MLA" if line["billing_stream"] == "LEASE" else "MSA"
                agreement = db.execute(
                    "SELECT id FROM agreements WHERE client_id=? AND agreement_type=? ORDER BY created_at DESC LIMIT 1",
                    (client_id, agreement_type),
                ).fetchone()
                db.execute(
                    """INSERT INTO billing_lines
                    (id,billing_document_id,agreement_id,agreement_type,billing_stream,service_code,service_name,
                     component_code,component_name,charge_type,quantity,rate,rate_unit,amount,currency)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (str(uuid.uuid4()), doc_id, agreement["id"] if agreement else None, agreement_type,
                     line["billing_stream"], line["service_code"], line["service_name"], line["component_code"],
                     line["component_name"], line["charge_type"], line["quantity"], line["rate"], line["rate_unit"],
                     line["amount"], "USD"),
                )
        return {"id": doc_id, "client_id": client_id, "invoice_number": invoice_number, "period_start": start,
                "period_end": end, "billing_stream": stream, "line_count": len(lines), "status": "ingested"}
    except Exception:
        path.unlink(missing_ok=True)
        raise


def billing_history(client_id: str, start: str | None = None, end: str | None = None) -> list[dict[str, object]]:
    query = """SELECT bd.id,bd.invoice_number,bd.billing_stream AS document_stream,
                     bd.period_start,bd.period_end,bd.filename,
                     bl.service_code,bl.service_name,bl.component_code,bl.component_name,bl.charge_type,
                     bl.billing_stream,bl.quantity,bl.rate,bl.rate_unit,bl.amount,bl.currency
              FROM billing_documents bd JOIN billing_lines bl ON bl.billing_document_id=bd.id
              WHERE bd.client_id=?"""
    params: list[object] = [client_id]
    if start:
        query += " AND bd.period_start>=?"
        params.append(start)
    if end:
        query += " AND bd.period_end<=?"
        params.append(end)
    query += " ORDER BY bd.period_start DESC, bl.billing_stream, bl.service_name"
    with connect() as db:
        return [dict(row) for row in db.execute(query, params).fetchall()]


def forecast_billing(client_id: str, start: str, end: str, billing_stream: str) -> dict[str, object]:
    """
    Forecast estimated charges for a client and period based on active pricing setup.

    This is a projection from the Pricing API's active components, not actual billed data.
    For each active pricing component matching the stream, computes amount × quantity.
    """
    pricing_api = os.getenv("PRICING_API_URL", "http://127.0.0.1:8002")
    try:
        with open_service_url(f"{pricing_api}/api/clients/{client_id}/pricing", "billing-service", "AUTH_BILLING_SERVICE_SECRET") as response:
            pricing_data = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError("Billing forecast needs the Pricing API to be running locally.") from exc

    # Only use the latest active pricing request (by created_at), not historical ones.
    requests = pricing_data.get("requests", [])
    latest_active_request_id = None
    latest_created_at = None
    for req in requests:
        if req.get("status") == "active":
            created = req.get("created_at", "")
            if latest_created_at is None or created > latest_created_at:
                latest_created_at = created
                latest_active_request_id = req.get("id")
    active_components = [
        row for row in pricing_data.get("components", [])
        if row.get("status") == "active"
        and (latest_active_request_id is None or row.get("approval_request_id") == latest_active_request_id)
    ]

    # Filter by stream: SERVICE, LEASE, or COMBINED (both)
    if billing_stream.upper() != "COMBINED":
        active_components = [
            c for c in active_components
            if c.get("billing_stream", "").upper() == billing_stream.upper()
        ]

    lines = []
    total = 0.0
    for comp in active_components:
        amount = float(comp.get("amount", 0))
        quantity = float(comp.get("quantity", 1))
        line_total = amount * quantity
        total += line_total
        lines.append({
            "service_code": comp.get("service_code"),
            "service_name": comp.get("service_name"),
            "component_code": comp.get("component_code"),
            "component_name": comp.get("component_name"),
            "billing_stream": comp.get("billing_stream"),
            "charge_type": comp.get("charge_type"),
            "quantity": quantity,
            "rate": amount,
            "rate_unit": comp.get("rate_unit"),
            "amount": line_total,
            "currency": comp.get("currency", "USD"),
        })

    return {
        "client_id": client_id,
        "period_start": start,
        "period_end": end,
        "billing_stream": billing_stream.upper(),
        "lines": lines,
        "total": round(total, 2),
        "line_count": len(lines),
    }


def _component_key(service_code: object, component: object, stream: object) -> tuple[str, str, str]:
    """Canonical reconciliation key: (service code, charge component, stream).

    Contract extraction stores the snake-case component under ``component_name``
    while pricing and billing store it under ``component_code``. Normalise both
    sides to the same lower-case identifier so the comparison key does not
    depend on display casing or separators.
    """
    norm = re.sub(r"[^a-z0-9]+", "_", str(component or "").strip().lower()).strip("_")
    return (str(service_code or "").upper(), norm, str(stream or "").upper())


def _first_number(*values: object) -> float | None:
    """First value that is not None. A legitimate zero must not fall through."""
    for value in values:
        if value is not None:
            return float(value)
    return None


def _explain_mismatch(label: str, left: object, right: object) -> str:
    return f"{label}: contract/setup says {left}, other source says {right}."


def audit_client(client_id: str, start: str | None = None, end: str | None = None, persist: bool = True) -> dict[str, object]:
    lines = billing_history(client_id, start, end)
    contract_api = os.getenv("CONTRACT_API_URL", "http://127.0.0.1:8001")
    pricing_api = os.getenv("PRICING_API_URL", "http://127.0.0.1:8002")
    try:
        with open_service_url(f"{contract_api}/api/clients/{client_id}", "billing-service", "AUTH_BILLING_SERVICE_SECRET") as response:
            client = json.loads(response.read().decode("utf-8"))
        with open_service_url(f"{contract_api}/api/clients/{client_id}/agreements", "billing-service", "AUTH_BILLING_SERVICE_SECRET") as response:
            agreements = json.loads(response.read().decode("utf-8"))
        with open_service_url(f"{pricing_api}/api/clients/{client_id}/pricing", "billing-service", "AUTH_BILLING_SERVICE_SECRET") as response:
            pricing_data = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError("Billing audit needs the Contract and Pricing APIs to be running locally.") from exc
    if not client:
        raise ValueError("Client not found.")
    active = [row for row in pricing_data.get("components", []) if row.get("status") == "active"]
    pricing_map = {
        _component_key(row["service_code"], row["component_code"], row["billing_stream"]): row
        for row in active
    }
    contracts: dict[tuple[str, str, str], dict[str, object]] = {}
    for agreement in agreements:
        parsed = agreement.get("extracted", {})
        if agreement["agreement_type"] == "MSA":
            for term in parsed.get("services", []):
                if term.get("subscribed"):
                    key = _component_key(term["service_code"], term.get("component_code") or term.get("component_name"), "SERVICE")
                    contracts[key] = {**term, "agreement_effective_date": agreement.get("effective_date")}
            for term in parsed.get("components", []):
                key = _component_key(term["service_code"], term.get("component_code") or term.get("component_name"), "SERVICE")
                contracts[key] = {**term, "agreement_effective_date": agreement.get("effective_date")}
        elif parsed.get("lease"):
            term = parsed["lease"]
            key = _component_key(term["service_code"], term.get("component_code") or term.get("component_name"), "LEASE")
            contracts[key] = {**term, "agreement_effective_date": agreement.get("effective_date")}

    aggregated: dict[tuple[str, str, str, str], dict[str, object]] = {}
    billed_keys: set[tuple[str, str, str, str]] = set()
    for line in lines:
        key = _component_key(line["service_code"], line["component_code"], line["billing_stream"])
        billed_keys.add((*key, line["period_start"]))
        contract = contracts.get(key)
        price = pricing_map.get(key)
        price_terms = json.loads(price.get("terms_json") or "{}") if price else {}
        contract_quantity = _first_number(contract.get("vehicle_count"), contract.get("driver_count"),
                                         contract.get("quantity")) if contract else None
        contract_basis = contract.get("pricing_basis", "USD") if contract else None
        price_basis = price_terms.get("pricing_basis", "USD") if price else None
        row_key = (*key, line["period_start"])
        item = aggregated.setdefault(row_key, {
            "service_code": line["service_code"], "service_name": line["service_name"],
            "component_code": line["component_code"], "component_name": line["component_name"],
            "billing_stream": line["billing_stream"], "period_start": line["period_start"],
            "contracted": bool(contract), "configured": bool(price), "billed_amount": 0.0,
            "contract_rate": contract.get("contract_amount") if contract else None,
            "contract_basis": contract_basis, "pricing_basis": price_basis,
            "contract_quantity": contract_quantity,
            "configured_quantity": price["quantity"] if price else None,
            "billed_quantity": line["quantity"],
            "expected_rate": price["amount"] if price else None, "billed_rate": line["rate"],
            "rate_unit": line["rate_unit"], "issue": None, "severity": None, "category": None,
            "explanation": "", "reasons": [],
        })
        item["billed_amount"] = float(item["billed_amount"]) + float(line["amount"])

        issues = []
        reasons = []
        if not contract:
            issues.append("Billed item is not present in the uploaded contract terms")
            reasons.append("No agreement term matches this service, charge component, and billing stream.")
        if not price:
            issues.append("Missing pricing setup")
            reasons.append("The active pricing version has no component for this contracted charge.")
        elif contract:
            if contract.get("contract_amount") is not None and abs(
                float(contract["contract_amount"]) - float(price["amount"])
            ) > RATE_TOLERANCE:
                issues.append("Configured rate differs from contract")
                reasons.append(_explain_mismatch("Active rate", contract["contract_amount"], price["amount"]))
            if contract_basis and contract_basis != price_basis:
                issues.append("Configured pricing basis differs from contract")
                reasons.append(_explain_mismatch("Pricing basis", contract_basis, price_basis))
            if contract.get("rate_unit") and contract["rate_unit"] != price["rate_unit"]:
                issues.append("Configured rate unit differs from contract")
                reasons.append(_explain_mismatch("Rate unit", contract["rate_unit"], price["rate_unit"]))
            if contract_quantity is not None and abs(contract_quantity - float(price["quantity"])) > RATE_TOLERANCE:
                issues.append("Configured quantity differs from contract")
                reasons.append(_explain_mismatch("Quantity", contract_quantity, price["quantity"]))
        if price:
            if abs(float(price["amount"]) - float(line["rate"])) > RATE_TOLERANCE:
                issues.append("Billed rate differs from active pricing")
                reasons.append(_explain_mismatch("Billed rate", price["amount"], line["rate"]))
            if abs(float(price["quantity"]) - float(line["quantity"])) > RATE_TOLERANCE:
                issues.append("Billed quantity differs from active pricing")
                reasons.append(_explain_mismatch("Billed quantity", price["quantity"], line["quantity"]))
        severity, category = _classify_issues(issues)
        item["issue"] = "; ".join(issues) or None
        item["severity"] = severity
        item["category"] = category
        item["reasons"] = reasons
        item["explanation"] = (
            f"Contract rate: {contract.get('contract_amount') if contract else 'not found'} {contract_basis or ''}; "
            f"active price: {price['amount'] if price else 'not found'}; billed rate: {line['rate']}."
        )

    results = list(aggregated.values())
    # Check for an absent line in each period where the client had an invoice.
    invoice_periods: dict[str, set[str]] = {"SERVICE": set(), "LEASE": set()}
    for line in lines:
        document_stream = line["document_stream"]
        if document_stream in invoice_periods or document_stream == "COMBINED":
            invoice_periods[line["billing_stream"]].add(line["period_start"])
    for key, term in contracts.items():
        price = pricing_map.get(key)
        for period in sorted(invoice_periods[key[2]]):
            effective_date = term.get("agreement_effective_date") or term.get("effective_from")
            if effective_date and period[:7] < effective_date[:7]:
                continue
            if term.get("charge_type") == "one_time" and effective_date and period[:7] != effective_date[:7]:
                continue
            if (*key, period) in billed_keys:
                continue
            issue = "Missing billing" if price else "Missing pricing setup and billing"
            severity, category = _classify_issues([issue])
            results.append({
                "service_code": key[0], "service_name": term.get("service_name"),
                "component_code": key[1], "component_name": term.get("component_name", key[1]),
                "billing_stream": key[2], "period_start": period, "contracted": True,
                "configured": bool(price), "contract_rate": term.get("contract_amount"),
                "contract_basis": term.get("pricing_basis", "USD"),
                "pricing_basis": json.loads(price.get("terms_json") or "{}").get("pricing_basis", "USD") if price else None,
                "contract_quantity": _first_number(term.get("vehicle_count"), term.get("driver_count"), term.get("quantity")),
                "configured_quantity": price["quantity"] if price else None, "billed_quantity": None,
                "expected_rate": price["amount"] if price else None, "billed_rate": None,
                "billed_amount": 0.0, "rate_unit": term.get("rate_unit"), "issue": issue,
                "severity": severity, "category": category,
                "reasons": [f"This contracted charge has no billing line in the {period} invoice period."],
                "explanation": f"This contracted charge has no billing line in the {period} invoice period.",
            })

    if persist and start is None and end is None:
        _persist_findings(client_id, results)

    return {"client": dict(client), "rows": results, "invoice_count": len({r["id"] for r in lines}),
            "discrepancy_count": sum(1 for item in results if item["issue"])}


def _persist_findings(client_id: str, results: list[dict[str, object]]) -> None:
    """Store the latest unfiltered audit findings for client. Filtered ranges
    are exploratory and never overwrite the full picture."""
    with connect() as db:
        db.execute("DELETE FROM audit_findings WHERE client_id=?", (client_id,))
        for row in results:
            if not row["issue"]:
                continue
            db.execute(
                """INSERT INTO audit_findings
                (id,client_id,service_code,service_name,component_code,component_name,billing_stream,
                 period_start,category,severity,issue,explanation,contract_rate,configured_rate,billed_rate,
                 billed_amount,contract_basis,pricing_basis,rate_unit)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), client_id, row["service_code"], row["service_name"], row["component_code"],
                 row["component_name"], row["billing_stream"], row["period_start"], row["category"],
                 row["severity"], row["issue"], row["explanation"], row["contract_rate"], row["expected_rate"],
                 row["billed_rate"], row["billed_amount"], row["contract_basis"], row["pricing_basis"],
                 row["rate_unit"]),
            )


def stored_audit_findings(client_id: str) -> dict[str, object] | None:
    """Read the last persisted unfiltered audit, if one exists."""
    with connect() as db:
        rows = [dict(r) for r in db.execute(
            "SELECT * FROM audit_findings WHERE client_id=? ORDER BY computed_at DESC", (client_id,)
        ).fetchall()]
        stamped = db.execute(
            "SELECT computed_at FROM audit_findings WHERE client_id=? LIMIT 1", (client_id,)
        ).fetchone()
    if not stamped:
        return None
    findings = [{
        "service_code": r["service_code"], "service_name": r["service_name"],
        "component_code": r["component_code"], "component_name": r["component_name"],
        "billing_stream": r["billing_stream"], "period_start": r["period_start"],
        "issue": r["issue"], "severity": r["severity"], "category": r["category"],
        "explanation": r["explanation"], "contract_rate": r["contract_rate"],
        "expected_rate": r["configured_rate"], "billed_rate": r["billed_rate"],
        "billed_amount": r["billed_amount"], "contract_basis": r["contract_basis"],
        "pricing_basis": r["pricing_basis"], "rate_unit": r["rate_unit"],
        "contracted": True, "configured": r["configured_rate"] is not None,
    } for r in rows]
    return {"computed_at": stamped["computed_at"], "findings": findings}


def combined_billing(client_id: str, start: str | None = None, end: str | None = None) -> dict[str, object]:
    """One client-level view that keeps service and lease charges together,
    grouped by billing period with preserved stream labels and subtotals."""
    lines = billing_history(client_id, start, end)
    periods: dict[str, dict[str, object]] = {}
    for line in lines:
        period = periods.setdefault(line["period_start"], {
            "period_start": line["period_start"], "period_end": line["period_end"],
            "service_lines": [], "lease_lines": [], "service_total": 0.0, "lease_total": 0.0,
            "invoices": {},
        })
        row = {
            "invoice_number": line["invoice_number"], "service_name": line["service_name"],
            "component_name": line["component_name"], "charge_type": line["charge_type"],
            "quantity": line["quantity"], "rate": line["rate"], "rate_unit": line["rate_unit"],
            "amount": line["amount"], "billing_stream": line["billing_stream"],
        }
        if line["billing_stream"] == "LEASE":
            period["lease_lines"].append(row)
            period["lease_total"] += float(line["amount"])
        else:
            period["service_lines"].append(row)
            period["service_total"] += float(line["amount"])
        period["invoices"][line["invoice_number"]] = line["document_stream"]
    ordered = sorted(periods.values(), key=lambda p: p["period_start"], reverse=True)
    for period in ordered:
        period["period_total"] = round(period["service_total"] + period["lease_total"], 2)
        period["service_total"] = round(period["service_total"], 2)
        period["lease_total"] = round(period["lease_total"], 2)
    return {
        "client_id": client_id,
        "periods": ordered,
        "combined_total": round(sum(p["period_total"] for p in ordered), 2),
        "service_total": round(sum(p["service_total"] for p in ordered), 2),
        "lease_total": round(sum(p["lease_total"] for p in ordered), 2),
    }


def audit_summary() -> dict[str, object]:
    """Summarize open audit findings for every client on the internal overview.

    Reads the last persisted full audit per client when available, so the
    overview does not fan out to the Contract and Pricing APIs on every load.
    A client with no stored audit yet is computed once, which also persists it.
    """
    with connect() as db:
        clients = [dict(row) for row in db.execute("SELECT id,name FROM clients ORDER BY name").fetchall()]

    summaries = []
    for client in clients:
        stored = stored_audit_findings(client["id"])
        if stored is None:
            report = audit_client(client["id"])
            findings = [row for row in report["rows"] if row["issue"]]
            computed_at = "just now"
        else:
            findings = stored["findings"]
            computed_at = stored["computed_at"]
        with connect() as db:
            invoice_count = db.execute(
                "SELECT COUNT(DISTINCT period_start) FROM billing_documents WHERE client_id=?", (client["id"],)
            ).fetchone()[0]
        summaries.append({
            "client_id": client["id"],
            "client_name": client["name"],
            "invoice_count": invoice_count,
            "discrepancy_count": len(findings),
            "findings": findings,
            "computed_at": computed_at,
        })

    return {
        "clients": summaries,
        "clients_with_issues": sum(1 for item in summaries if item["discrepancy_count"]),
        "discrepancy_count": sum(item["discrepancy_count"] for item in summaries),
    }
