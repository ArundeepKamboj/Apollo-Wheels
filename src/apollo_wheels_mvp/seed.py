"""Idempotent seed data and generated selectable-text PDF samples."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from .documents import extract_pdf_pages, extract_pdf_text, parse_billing_rows, parse_key_values
from .extraction import extract_agreement_terms
from .storage import DOCUMENT_DIR, connect, update_client_profile
from .synthetic import write_demo_invoice


def seed_demo_data(include_workflow_history: bool = False) -> None:
    root = Path(__file__).resolve().parents[2]
    demo_clients = [
        ("C-1001", "Northstar Fleet Services", "Northstar_Fleet_Services", "northstar"),
        ("C-1002", "Blue River Logistics", "Blue_River_Logistics", "blueriver"),
    ]
    agreements_by_client: dict[str, dict[str, dict[str, object]]] = {}
    with connect() as db:
        for client_id, client_name, folder, prefix in demo_clients:
            db.execute(
                "INSERT OR IGNORE INTO clients(id,name,include_history_on_invoice) VALUES (?,?,0)",
                (client_id, client_name),
            )
            for agreement_type in ("MSA", "MLA"):
                filename = f"{prefix}_{agreement_type.lower()}_v1.pdf"
                source_path = root / "samples" / "contracts" / folder / filename
                target_path = DOCUMENT_DIR / filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(source_path.read_bytes())
                pages = extract_pdf_pages(target_path)
                extracted = extract_agreement_terms(pages, agreement_type)
                metadata = parse_key_values("\n".join(pages))
                agreement_id = metadata.get("AGREEMENT_ID") or f"{prefix.upper()}-{agreement_type}-001"
                version_label = metadata.get("VERSION", "1.0")
                effective_date = metadata.get("EFFECTIVE_DATE", "2026-01-01")
                db.execute(
                    """INSERT INTO agreements
                       (id,client_id,agreement_type,version_label,filename,file_path,effective_date,status,
                        uploaded_by,extracted_json,version,is_active)
                       VALUES (?,?,?,?,?,?,?,?,?,?,1,1)
                       ON CONFLICT(id) DO UPDATE SET client_id=excluded.client_id,
                         agreement_type=excluded.agreement_type,version_label=excluded.version_label,
                         filename=excluded.filename,file_path=excluded.file_path,effective_date=excluded.effective_date,
                         status=excluded.status,extracted_json=excluded.extracted_json,version=1,is_active=1
                       WHERE agreements.uploaded_by='seed'""",
                    (agreement_id, client_id, agreement_type, version_label, filename, str(target_path),
                     effective_date, "review", "seed", json.dumps(extracted)),
                )
                if agreement_type == "MSA":
                    update_client_profile(db, client_id, extracted["parties"].get("client"))
                agreements_by_client.setdefault(client_id, {})[agreement_type] = {
                    "id": agreement_id,
                    "extracted": extracted,
                    "effective_date": effective_date,
                }
        if include_workflow_history:
            seed_workflow_history(db, demo_clients, agreements_by_client)


def seed_workflow_history(db, demo_clients, agreements_by_client) -> None:
    """Populate optional two-client pricing and billing fixtures for workflow tests."""
    for client_id, client_name, _folder, _prefix in demo_clients:
        agreement_map = agreements_by_client[client_id]

        # Check if pricing data already exists for this client
        existing_pricing = db.execute(
            "SELECT COUNT(*) FROM pricing_approval_requests WHERE client_id=? AND status='active'",
            (client_id,)
        ).fetchone()[0]

        components: list[dict[str, object]] = []
        if existing_pricing == 0:
            request_id = str(uuid.uuid4())
            agreement_ids = [agreement_map["MSA"]["id"], agreement_map["MLA"]["id"]]
            db.execute(
                """INSERT INTO pricing_approval_requests
                   (id,client_id,agreement_ids_json,version,status,initiated_by,approved_by,approved_at,effective_from)
                   VALUES (?,?,?,1,'active','finance.alex','finance.jordan','2026-01-01T10:00:00','2026-01-01')""",
                (request_id, client_id, json.dumps(agreement_ids)),
            )
            for term in agreement_map["MSA"]["extracted"]["services"]:
                if not term["subscribed"]:
                    continue
                components.append({
                    "agreement_id": agreement_map["MSA"]["id"], "agreement_type": "MSA", "billing_stream": "SERVICE",
                    "service_code": term["service_code"], "service_name": term["service_name"],
                    "component_code": term["component_name"], "component_name": term["component_name"].replace("_", " ").title(),
                    "charge_type": "recurring", "amount": term["contract_amount"], "currency": "USD",
                    "rate_unit": term["rate_unit"],
                    "quantity": term.get("vehicle_count") or term.get("driver_count") or 1,
                    "billing_frequency": term.get("billing_frequency") or "monthly",
                    "billing_day": term.get("billing_day"), "effective_from": "2026-01-01",
                    "terms": {"pricing_basis": term.get("pricing_basis", "USD")},
                })
            components.append({
                "agreement_id": agreement_map["MSA"]["id"], "agreement_type": "MSA", "billing_stream": "SERVICE",
                "service_code": "FUEL", "service_name": "Fuel", "component_code": "activation",
                "component_name": "One-time setup", "charge_type": "one_time", "amount": 250.0,
                "currency": "USD", "rate_unit": "account", "quantity": 1,
                "billing_frequency": "one_time", "billing_day": None, "effective_from": "2026-01-01",
                "terms": {"pricing_basis": "USD"},
            })
            lease = agreement_map["MLA"]["extracted"]["lease"]
            for vehicle in lease.get("vehicles") or [lease]:
                vehicle_type = vehicle.get("vehicle_type") or " ".join(
                    value for value in (vehicle.get("vehicle_make"), vehicle.get("vehicle_model")) if value
                )
                components.append({
                    "agreement_id": agreement_map["MLA"]["id"], "agreement_type": "MLA", "billing_stream": "LEASE",
                    "service_code": vehicle["service_code"], "service_name": vehicle["service_name"],
                    "component_code": vehicle["component_name"], "component_name": f"Monthly Lease - {vehicle_type}",
                    "charge_type": "recurring", "amount": vehicle["contract_amount"],
                    "currency": vehicle.get("pricing_basis", "USD"), "rate_unit": vehicle["rate_unit"],
                    "quantity": vehicle["quantity"], "billing_frequency": vehicle["billing_frequency"],
                    "billing_day": vehicle["billing_day"], "effective_from": vehicle["effective_from"],
                    "terms": {"term_months": vehicle["term_months"], "vehicle_type": vehicle_type,
                              "vehicle_make": vehicle["vehicle_make"], "vehicle_model": vehicle["vehicle_model"],
                              "engine_type": vehicle["engine_type"], "pricing_basis": vehicle["pricing_basis"]},
                })
            for component in components:
                db.execute(
                    """INSERT INTO pricing_components
                       (id,approval_request_id,client_id,agreement_id,agreement_type,billing_stream,service_code,service_name,
                        component_code,component_name,charge_type,amount,currency,rate_unit,quantity,billing_frequency,
                        billing_day,terms_json,effective_from,status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'active')""",
                    (str(uuid.uuid4()), request_id, client_id, component["agreement_id"], component["agreement_type"],
                     component["billing_stream"], component["service_code"], component["service_name"],
                     component["component_code"], component["component_name"], component["charge_type"],
                     component["amount"], component["currency"], component["rate_unit"], component["quantity"],
                     component["billing_frequency"], component["billing_day"], json.dumps(component["terms"]),
                     component["effective_from"]),
                )
        else:
            # Pricing already exists; load components from DB for billing line matching
            rows = db.execute(
                """SELECT agreement_id, agreement_type, billing_stream, service_code, service_name,
                          component_code, component_name, charge_type, amount, currency, rate_unit, quantity,
                          billing_frequency, billing_day, terms_json, effective_from
                   FROM pricing_components WHERE client_id=? AND status='active'""",
                (client_id,)
            ).fetchall()
            for row in rows:
                components.append({
                    "agreement_id": row[0], "agreement_type": row[1], "billing_stream": row[2],
                    "service_code": row[3], "service_name": row[4],
                    "component_code": row[5], "component_name": row[6], "charge_type": row[7],
                    "amount": row[8], "currency": row[9], "rate_unit": row[10], "quantity": row[11],
                    "billing_frequency": row[12], "billing_day": row[13],
                    "terms": json.loads(row[14]), "effective_from": row[15],
                })

        for month, start, end in (
            ("JAN", "2026-01-01", "2026-01-31"),
            ("FEB", "2026-02-01", "2026-02-28"),
            ("MAR", "2026-03-01", "2026-03-31"),
        ):
            for stream in ("SERVICE", "LEASE"):
                # Check if billing documents already exist for this client/period/stream
                existing = db.execute(
                    "SELECT COUNT(*) FROM billing_documents WHERE client_id=? AND period_start=? AND billing_stream=?",
                    (client_id, start, stream)
                ).fetchone()[0]
                if existing > 0:
                    continue  # Skip seeding for this period/stream

                invoice = write_demo_invoice(
                    DOCUMENT_DIR, client_id, client_name, start, end,
                    f"INV-{client_id}-{month}-{stream}", stream,
                )
                target_path = invoice["path"]
                fixture_text = "\n".join(invoice["lines"])
                metadata = parse_key_values(fixture_text)
                billing_lines = parse_billing_rows(fixture_text)
                document_id = str(uuid.uuid4())
                db.execute(
                    """INSERT INTO billing_documents
                       (id,client_id,invoice_number,billing_stream,period_start,period_end,filename,file_path,status,uploaded_by)
                       VALUES (?,?,?,?,?,?,?,?,?,'seed')""",
                    (document_id, client_id, metadata["INVOICE_NUMBER"], stream, metadata["PERIOD_START"],
                     metadata["PERIOD_END"], invoice["filename"], str(target_path), "ingested"),
                )
                for line in billing_lines:
                    matching = next((item for item in components if item["service_code"] == line["service_code"]
                                     and item["billing_stream"] == line["billing_stream"]), None)
                    db.execute(
                        """INSERT INTO billing_lines
                           (id,billing_document_id,agreement_id,agreement_type,billing_stream,service_code,service_name,
                            component_code,component_name,charge_type,quantity,rate,rate_unit,amount,currency)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (str(uuid.uuid4()), document_id, matching["agreement_id"] if matching else None,
                         "MLA" if stream == "LEASE" else "MSA", line["billing_stream"], line["service_code"],
                         line["service_name"], line["component_code"], line["component_name"], line["charge_type"],
                         line["quantity"], line["rate"], line["rate_unit"], line["amount"], "USD"),
                    )
