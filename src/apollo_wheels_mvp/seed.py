"""Idempotent seed data and generated selectable-text PDF samples."""

from __future__ import annotations

import json
import uuid
from datetime import date

from .catalog import SERVICES
from .documents import extract_pdf_text, extract_pdf_pages
from .extraction import extract_agreement_terms
from .storage import DOCUMENT_DIR, connect
from .synthetic import write_demo_agreements, write_demo_invoice


def seed_demo_data() -> None:
    demo_clients = [
        ("C-1001", "Northstar Fleet Services", "NORTHSTAR"),
        ("C-1002", "Blue River Logistics", "BLUERIVER"),
    ]
    with connect() as db:
        demo_ids = tuple(client[0] for client in demo_clients)
        placeholders = ",".join("?" for _ in demo_ids)
        seeded_clients = db.execute(
            f"SELECT COUNT(*) FROM clients WHERE id IN ({placeholders})", demo_ids
        ).fetchone()[0]
        if seeded_clients:
            db.execute("INSERT OR IGNORE INTO clients(id,name,include_history_on_invoice) VALUES ('C-TEST','Test Client',0)")
            # Refresh only the four approved seeded documents and their parsed
            # terms. Later user-uploaded agreement files remain untouched.
            for client_id, client_name, prefix in demo_clients:
                for item in write_demo_agreements(DOCUMENT_DIR, client_id, client_name, prefix):
                    pages = extract_pdf_pages(item["path"])
                    extracted = extract_agreement_terms(pages, item["type"])
                    db.execute(
                        "UPDATE agreements SET file_path=?, extracted_json=? WHERE id=? AND uploaded_by='seed'",
                        (str(item["path"]), json.dumps(extracted), item["id"]),
                    )
            return
        db.execute("INSERT OR IGNORE INTO clients(id,name,include_history_on_invoice) VALUES ('C-TEST','Test Client',0)")
        agreements_by_client: dict[str, dict[str, dict[str, object]]] = {}
        for client_id, client_name, prefix in demo_clients:
            db.execute("INSERT INTO clients(id,name,include_history_on_invoice) VALUES (?,?,0)", (client_id, client_name))
            agreement_map: dict[str, dict[str, object]] = {}
            for item in write_demo_agreements(DOCUMENT_DIR, client_id, client_name, prefix):
                text = extract_pdf_text(item["path"])
                extracted = extract_agreement_terms(extract_pdf_pages(item["path"]), item["type"])
                db.execute(
                    """INSERT INTO agreements
                    (id,client_id,agreement_type,version_label,filename,file_path,effective_date,status,uploaded_by,extracted_json)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (item["id"], client_id, item["type"], "1.0", item["filename"], str(item["path"]),
                     "2026-01-01", "review", "seed", json.dumps(extracted)),
                )
                agreement_map[item["type"]] = {**item, "text": text, "extracted": extracted}
            agreements_by_client[client_id] = agreement_map

        # Seed an already-active pricing history for the audit screen.
        for client_id, client_name, _ in demo_clients:
            agreement_map = agreements_by_client[client_id]
            version_id = str(uuid.uuid4())
            db.execute(
                """INSERT INTO pricing_approval_requests
                (id,client_id,agreement_ids_json,version,status,initiated_by,approved_by,approved_at,effective_from)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (version_id, client_id, json.dumps([agreement_map["MSA"]["id"], agreement_map["MLA"]["id"]]),
                 1, "active", "finance.alex", "finance.jordan", "2026-01-01T10:00:00", "2026-01-01"),
            )
            components: list[dict[str, object]] = []
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
                    "terms": {"source": "synthetic_demo", "pricing_basis": term.get("pricing_basis", "USD")},
                })
            for term in agreement_map["MSA"]["extracted"]["components"]:
                components.append({
                    "agreement_id": agreement_map["MSA"]["id"], "agreement_type": "MSA", "billing_stream": "SERVICE",
                    "service_code": term["service_code"], "service_name": "Fuel",
                    "component_code": term["component_name"], "component_name": term["display_name"],
                    "charge_type": term["charge_type"], "amount": term["contract_amount"], "currency": "USD",
                    "rate_unit": term["rate_unit"], "quantity": term["quantity"], "billing_frequency": "one_time",
                    "billing_day": None, "effective_from": "2026-01-01",
                    "terms": {"source": "synthetic_demo", "pricing_basis": term.get("pricing_basis", "USD")},
                })
            lease = agreement_map["MLA"]["extracted"]["lease"]
            components.append({
                "agreement_id": agreement_map["MLA"]["id"], "agreement_type": "MLA", "billing_stream": "LEASE",
                "service_code": lease["service_code"], "service_name": lease["service_name"],
                "component_code": lease["component_name"], "component_name": "Monthly Lease",
                "charge_type": "recurring", "amount": lease["contract_amount"], "currency": "USD",
                "rate_unit": lease["rate_unit"], "quantity": lease["quantity"],
                "billing_frequency": lease["billing_frequency"], "billing_day": lease["billing_day"],
                "effective_from": lease["effective_from"],
                "terms": {"term_months": lease["term_months"], "vehicle_make": lease["vehicle_make"],
                          "vehicle_model": lease["vehicle_model"], "engine_type": lease["engine_type"],
                          "pricing_basis": lease["pricing_basis"]},
            })
            for comp in components:
                db.execute(
                    """INSERT INTO pricing_components
                    (id,approval_request_id,client_id,agreement_id,agreement_type,billing_stream,service_code,service_name,
                     component_code,component_name,charge_type,amount,currency,rate_unit,quantity,billing_frequency,
                     billing_day,terms_json,effective_from,status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'active')""",
                    (str(uuid.uuid4()), version_id, client_id, comp["agreement_id"], comp["agreement_type"],
                     comp["billing_stream"], comp["service_code"], comp["service_name"], comp["component_code"],
                     comp["component_name"], comp["charge_type"], comp["amount"], comp["currency"], comp["rate_unit"],
                     comp["quantity"], comp["billing_frequency"], comp["billing_day"], json.dumps(comp["terms"]), comp["effective_from"]),
                )

            # Three periods per client; February intentionally has one rate mismatch for the audit demonstration.
            for month, start, end in (
                ("JAN", "2026-01-01", "2026-01-31"),
                ("FEB", "2026-02-01", "2026-02-28"),
                ("MAR", "2026-03-01", "2026-03-31"),
            ):
                for stream in ("SERVICE", "LEASE"):
                    invoice = write_demo_invoice(
                        DOCUMENT_DIR, client_id, client_name, start, end, f"INV-{client_id}-{month}-{stream}", stream
                    )
                    invoice_text = extract_pdf_text(invoice["path"])
                    from .documents import parse_billing_rows
                    billing_lines = parse_billing_rows(invoice_text)
                    doc_id = str(uuid.uuid4())
                    db.execute(
                        """INSERT INTO billing_documents
                        (id,client_id,invoice_number,billing_stream,period_start,period_end,filename,file_path,status,uploaded_by)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (doc_id, client_id, invoice["invoice_number"], stream, start, end, invoice["filename"],
                         str(invoice["path"]), "ingested", "seed"),
                    )
                    for line in billing_lines:
                        matching = next((c for c in components if c["service_code"] == line["service_code"]
                                         and c["billing_stream"] == line["billing_stream"]), None)
                        db.execute(
                            """INSERT INTO billing_lines
                            (id,billing_document_id,agreement_id,agreement_type,billing_stream,service_code,service_name,
                             component_code,component_name,charge_type,quantity,rate,rate_unit,amount,currency)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (str(uuid.uuid4()), doc_id, matching["agreement_id"] if matching else None,
                             "MLA" if stream == "LEASE" else "MSA", line["billing_stream"], line["service_code"],
                             line["service_name"], line["component_code"], line["component_name"], line["charge_type"],
                             line["quantity"], line["rate"], line["rate_unit"], line["amount"], "USD"),
                        )
