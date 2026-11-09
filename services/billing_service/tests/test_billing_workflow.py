"""Unit and service-layer integration coverage for billing and audit."""

from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from services.auth import Identity
from apollo_wheels_mvp.documents import extract_pdf_text, parse_billing_rows, parse_key_values
from apollo_wheels_mvp.storage import connect
from apollo_wheels_mvp.synthetic import make_text_pdf, write_demo_invoice, write_forecast_invoice
from services.billing_service import api, domain
from services.test_support import MemoryUpload, PROJECT_ROOT, run_upload, setup_demo


class JsonResponse:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self):
        return json.dumps(self.value).encode()


class BillingWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_demo(self)

    def pdf(self, filename="invoice.pdf", data=None):
        if data is None:
            path = PROJECT_ROOT / "samples/billing/Northstar_Fleet_Services/service/2026-02-01_service_inv-c-1001-feb-service.pdf"
            data = path.read_bytes()
        return MemoryUpload(filename, data)

    def upstream_responses(self, client_id="C-1001", agreements=None, components=None):
        with connect() as db:
            client = dict(db.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone())
            rows = [dict(row) for row in db.execute("SELECT * FROM agreements WHERE client_id=?", (client_id,)).fetchall()]
            for row in rows:
                row["extracted"] = json.loads(row.pop("extracted_json"))
            prices = [dict(row) for row in db.execute("SELECT * FROM pricing_components WHERE client_id=?", (client_id,)).fetchall()]
        return [JsonResponse(client), JsonResponse(agreements if agreements is not None else rows),
                JsonResponse({"components": components if components is not None else prices})]

    def test_health_and_seeded_history_has_both_billing_streams(self):
        self.assertEqual(api.health()["status"], "ready")
        rows = domain.billing_history("C-1001")
        self.assertTrue(rows)
        self.assertEqual({row["billing_stream"] for row in rows}, {"SERVICE", "LEASE"})
        self.assertTrue(all(row["amount"] >= 0 for row in rows))

    def test_history_filters_apply_start_end_and_empty_client(self):
        all_rows = domain.billing_history("C-1001")
        filtered = domain.billing_history("C-1001", "2026-02-01", "2026-02-28")
        self.assertTrue(filtered)
        self.assertTrue(all(row["period_start"] >= "2026-02-01" and row["period_end"] <= "2026-02-28" for row in filtered))
        self.assertLess(len(filtered), len(all_rows))
        self.assertEqual(domain.billing_history("missing"), [])

    def test_valid_pdf_upload_persists_document_lines_and_original_file(self):
        invoice = write_demo_invoice(
            self.root / "source",
            "C-1001",
            "Northstar Fleet Services",
            "2026-02-01",
            "2026-02-28",
            "INV-C-1001-FEB-UNIQUE",
            "SERVICE",
        )
        upload = self.pdf("invoice.pdf", invoice["path"].read_bytes())
        result = run_upload(api.upload_billing_document("C-1001", upload, Identity("finance.alex", "finance", "user")))
        self.assertEqual(result["status"], "ingested")
        self.assertEqual(result["line_count"], 9)
        self.assertTrue((self.root / "documents" / f"{result['id']}_invoice.pdf").is_file())
        with connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM billing_lines WHERE billing_document_id=?", (result["id"],)).fetchone()[0], 9)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM billing_documents WHERE id=?", (result["id"],)).fetchone()[0], 1)

    def test_upload_rejects_invalid_extension_magic_client_and_size(self):
        cases = (
            ("bad.txt", b"%PDF-x", "PDF file", "C-1001"),
            ("bad.pdf", b"not a pdf", "valid PDF", "C-1001"),
            ("large.pdf", b"%PDF" + b"x" * (20 * 1024 * 1024), "20 MB", "C-1001"),
            ("invoice.pdf", b"%PDF-x", "Client not found", "missing"),
        )
        for filename, data, message, client_id in cases:
            with self.subTest(filename=filename, client_id=client_id), self.assertRaisesRegex(ValueError, message):
                run_upload(domain.ingest_billing_pdf(client_id, self.pdf(filename, data), "u"))

    def test_corrupt_empty_scanned_and_missing_period_invoice_are_rejected(self):
        cases = (
            (b"%PDF malformed", ""),
            (make_text_pdf([""]), "selectable text"),
            (make_text_pdf(["INVOICE_NUMBER: X", "LINE|SERVICE|FUEL|Fuel|monthly_per_vehicle|recurring|10|2|vehicle_month|20"]), "billing period"),
        )
        for data, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                run_upload(domain.ingest_billing_pdf("C-1001", self.pdf("bad.pdf", data), "u"))
        self.assertEqual(list((self.root / "documents").glob("*bad.pdf")), [])

    def test_pdf_upload_filename_is_sanitized_and_saved_inside_document_directory(self):
        invoice = write_demo_invoice(
            self.root / "source",
            "C-1001",
            "Northstar Fleet Services",
            "2026-04-01",
            "2026-04-30",
            "INV-C-1001-APR-SANITIZED",
            "SERVICE",
        )
        upload = self.pdf("../../invoice.pdf", invoice["path"].read_bytes())
        result = run_upload(domain.ingest_billing_pdf("C-1001", upload, "u"))
        path = next((self.root / "documents").glob(f"{result['id']}_*.pdf"))
        self.assertTrue(path.is_file())
        self.assertEqual(path.parent, self.root / "documents")

    def test_duplicate_seeded_invoice_upload_is_rejected_without_adding_rows(self):
        with connect() as db:
            documents_before = db.execute(
                "SELECT COUNT(*) FROM billing_documents WHERE client_id='C-1001'"
            ).fetchone()[0]
            lines_before = db.execute(
                "SELECT COUNT(*) FROM billing_lines WHERE billing_document_id IN "
                "(SELECT id FROM billing_documents WHERE client_id='C-1001')"
            ).fetchone()[0]

        with self.assertRaisesRegex(ValueError, "has already been uploaded"):
            run_upload(domain.ingest_billing_pdf("C-1001", self.pdf(), "u"))

        with connect() as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM billing_documents WHERE client_id='C-1001'").fetchone()[0],
                documents_before,
            )
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM billing_lines WHERE billing_document_id IN "
                    "(SELECT id FROM billing_documents WHERE client_id='C-1001')"
                ).fetchone()[0],
                lines_before,
            )

    def test_billing_history_ignores_previously_ingested_duplicate_documents(self):
        original_rows = domain.billing_history("C-1001", "2026-02-01", "2026-02-28")
        with connect() as db:
            original = db.execute(
                "SELECT * FROM billing_documents WHERE client_id='C-1001' AND invoice_number='INV-C-1001-FEB-SERVICE'"
            ).fetchone()
            db.execute(
                """INSERT INTO billing_documents
                   (id,client_id,invoice_number,billing_stream,period_start,period_end,filename,file_path,status,uploaded_by)
                   VALUES ('duplicate-doc',?,?,?,?,?,?,?,?,?)""",
                tuple(original[key] for key in (
                    "client_id", "invoice_number", "billing_stream", "period_start", "period_end",
                    "filename", "file_path", "status", "uploaded_by",
                )),
            )
            db.execute(
                """INSERT INTO billing_lines
                   (id,billing_document_id,agreement_id,agreement_type,billing_stream,service_code,service_name,
                    component_code,component_name,charge_type,quantity,rate,rate_unit,amount,currency)
                   SELECT 'duplicate-'||id,'duplicate-doc',agreement_id,agreement_type,billing_stream,service_code,
                          service_name,component_code,component_name,charge_type,quantity,rate,rate_unit,amount,currency
                   FROM billing_lines WHERE billing_document_id=?""",
                (original["id"],),
            )

        rows = domain.billing_history("C-1001", "2026-02-01", "2026-02-28")
        self.assertEqual(len(rows), len(original_rows))

    def test_forecast_pdf_is_styled_and_keeps_uploadable_line_data(self):
        result = write_forecast_invoice(
            self.root / "documents",
            "C-1001",
            "Northstar Fleet Services",
            "2026-04-01",
            "2026-04-30",
            "FORECAST-C-1001-APR-SERVICE",
            "SERVICE",
            [{
                "billing_stream": "SERVICE",
                "service_code": "FUEL",
                "service_name": "Fuel",
                "component_code": "monthly_per_vehicle",
                "component_name": "Monthly per vehicle",
                "charge_type": "recurring",
                "quantity": 500,
                "rate": 3.5,
                "rate_unit": "vehicle_month",
                "amount": 1750,
                "currency": "USD",
            }],
            1750,
        )

        text = extract_pdf_text(result["path"])
        metadata = parse_key_values(text)
        rows = parse_billing_rows(text)
        self.assertIn("NOT AN INVOICE", text)
        self.assertIn("Northstar Fleet Services", text)
        self.assertNotIn("SAMPLE AGREEMENT", text)
        self.assertEqual(metadata["INVOICE_NUMBER"], "FORECAST-C-1001-APR-SERVICE")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["service_code"], "FUEL")
        self.assertEqual(rows[0]["amount"], 1750)

    def test_api_rejects_invalid_role_but_current_demo_allows_both_roles_to_ingest(self):
        for role in ("finance", "structuring"):
            invoice = write_demo_invoice(
                self.root / "source",
                "C-1001",
                "Northstar Fleet Services",
                "2026-04-01",
                "2026-04-30",
                f"INV-C-1001-APR-{role.upper()}",
                "SERVICE",
            )
            result = run_upload(api.upload_billing_document(
                "C-1001",
                self.pdf("invoice.pdf", invoice["path"].read_bytes()),
                Identity(f"{role}.user", role, "user"),
            ))
            self.assertEqual(result["status"], "ingested")
        with self.assertRaises(HTTPException) as error:
            run_upload(api.upload_billing_document("C-1001", self.pdf(), Identity("bad", None, "service")))
        self.assertEqual(error.exception.status_code, 403)

    def test_pdf_list_and_file_routes_return_pdf_and_not_found_errors(self):
        listing = api.client_pdf_list("C-1001")
        self.assertTrue(listing["billing"])
        response = api.stored_pdf(listing["billing"][0]["id"])
        self.assertEqual(response.media_type, "application/pdf")
        with self.assertRaises(HTTPException) as error:
            api.stored_pdf("missing")
        self.assertEqual(error.exception.status_code, 404)

    def test_missing_pdf_file_returns_not_found(self):
        with connect() as db:
            row = db.execute("SELECT id FROM billing_documents WHERE client_id='C-1001' LIMIT 1").fetchone()
            db.execute("UPDATE billing_documents SET file_path=? WHERE id=?", (str(self.root / "gone.pdf"), row["id"]))
        with self.assertRaises(HTTPException) as error:
            api.stored_pdf(row["id"])
        self.assertEqual(error.exception.status_code, 404)

    def test_audit_finds_intentional_rate_difference_and_reports_explanation(self):
        with patch.object(domain, "open_service_url", side_effect=self.upstream_responses()):
            report = domain.audit_client("C-1001")
        findings = [row for row in report["rows"] if row["issue"]]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["service_code"], "RR")
        self.assertIn("Billed rate differs", findings[0]["issue"])
        self.assertTrue(findings[0]["explanation"])

    def test_audit_flags_billed_item_missing_contract_and_missing_pricing(self):
        agreements = []
        components = []
        with patch.object(domain, "open_service_url", side_effect=self.upstream_responses(agreements=agreements, components=components)):
            report = domain.audit_client("C-1001")
        self.assertTrue(all("not present in the uploaded contract" in row["issue"] for row in report["rows"]))
        self.assertTrue(all("Missing pricing setup" in row["issue"] for row in report["rows"]))

    def test_audit_flags_missing_billing_line_for_period_with_statement(self):
        with connect() as db:
            document_id = db.execute("SELECT id FROM billing_documents WHERE client_id='C-1001' AND period_start='2026-03-01' AND billing_stream='SERVICE'").fetchone()[0]
            db.execute("DELETE FROM billing_lines WHERE billing_document_id=? AND service_code='FUEL'", (document_id,))
        with patch.object(domain, "open_service_url", side_effect=self.upstream_responses()):
            report = domain.audit_client("C-1001", "2026-03-01", "2026-03-31")
        missing = next(row for row in report["rows"] if row["service_code"] == "FUEL" and row["billing_stream"] == "SERVICE")
        self.assertEqual(missing["issue"], "Missing billing")

    def test_audit_reports_zero_invoices_when_client_has_no_billing_records(self):
        with connect() as db:
            db.execute("DELETE FROM billing_lines WHERE billing_document_id IN (SELECT id FROM billing_documents WHERE client_id='C-1001')")
            db.execute("DELETE FROM billing_documents WHERE client_id='C-1001'")
        with patch.object(domain, "open_service_url", side_effect=self.upstream_responses()):
            report = domain.audit_client("C-1001")
        self.assertEqual(report["invoice_count"], 0)
        self.assertEqual(report["rows"], [])

    def test_audit_surfaces_contract_or_pricing_api_unavailable(self):
        with patch.object(domain, "open_service_url", side_effect=OSError("offline")):
            with self.assertRaisesRegex(ValueError, "Contract and Pricing APIs"):
                domain.audit_client("C-1001")

    def test_audit_summary_covers_each_client(self):
        responses = []
        for client_id in ("C-1001", "C-1002"):
            responses.extend(self.upstream_responses(client_id))
        with patch.object(domain, "open_service_url", side_effect=responses):
            summary = api.audit_summary()
        self.assertEqual(len(summary["clients"]), 2)
        self.assertEqual(summary["clients_with_issues"], 2)


if __name__ == "__main__":
    unittest.main()
