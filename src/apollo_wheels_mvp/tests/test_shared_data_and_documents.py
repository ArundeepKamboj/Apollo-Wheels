"""Regression coverage for shared catalogue, PDF, persistence, and seed modules."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from pypdf import PdfWriter

from apollo_wheels_mvp.catalog import SERVICES
from apollo_wheels_mvp.documents import (
    extract_pdf_pages, extract_pdf_text, parse_billing_rows, parse_extra_components,
    parse_key_values, parse_lease_row, parse_service_rows,
)
from apollo_wheels_mvp.seed import seed_demo_data
from apollo_wheels_mvp.storage import connect, initialize
from apollo_wheels_mvp.synthetic import make_text_pdf, write_demo_agreements, write_demo_invoice
from services.test_support import PROJECT_ROOT, setup_demo


class SharedDataAndDocumentTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_demo(self)

    def test_service_catalogue_has_thirteen_unique_codes_and_names(self):
        self.assertEqual(len(SERVICES), 13)
        self.assertEqual(len({item["code"] for item in SERVICES}), 13)
        self.assertEqual(len({item["name"] for item in SERVICES}), 13)

    def test_pdf_text_extractors_return_page_aware_and_joined_text(self):
        path = self.root / "small.pdf"
        path.write_bytes(make_text_pdf(["FIRST: value", "second line"]))
        self.assertIn("FIRST: value", extract_pdf_text(path))
        self.assertEqual(len(extract_pdf_pages(path)), 1)

    def test_key_value_parser_ignores_lines_without_colon_and_normalizes_keys(self):
        self.assertEqual(parse_key_values("invoice_number: 7\nnot metadata\nPeriod_Start: 2026-01-01"),
                         {"INVOICE_NUMBER": "7", "PERIOD_START": "2026-01-01"})

    def test_service_rows_parse_subscription_basis_quantity_and_ignore_unrecognized_rows(self):
        row = "SERVICE|MVR_SAFETY|MVR and Safety|true|SERVICE|monthly_per_driver|2.50|driver_month|recurring|USD|monthly|20||600"
        results = parse_service_rows(row + "\nSERVICE|too|short")
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["subscribed"])
        self.assertEqual(results[0]["driver_count"], 600)
        self.assertEqual(results[0]["evidence_page"], 1)
        self.assertIn("not calibrated", results[0]["confidence_method"])

    def test_service_parser_defaults_legacy_row_and_rejects_bad_number(self):
        legacy = "SERVICE|FUEL|Fuel|false|SERVICE|fixed|0|account|one_time"
        self.assertEqual(parse_service_rows(legacy)[0]["billing_day"], "1")
        with self.assertRaises(ValueError):
            parse_service_rows("SERVICE|FUEL|Fuel|true|SERVICE|fee|bad|account|recurring")

    def test_extra_components_and_lease_parser_cover_valid_missing_and_malformed_rows(self):
        component = "COMPONENT|FUEL|activation|Setup fee|one_time|250.00|account|1"
        self.assertEqual(parse_extra_components(component)[0]["charge_type"], "one_time")
        lease = "LEASE|LEASE-01|Lease|500|vehicle_month|650.00|48|2026-01-01|monthly|1|Ford|Transit|Hybrid|USD"
        parsed = parse_lease_row(lease)
        self.assertEqual(parsed["term_months"], 48)
        self.assertEqual(parsed["vehicle_model"], "Transit")
        self.assertIsNone(parse_lease_row("LEASE|short"))
        with self.assertRaises(ValueError):
            parse_lease_row("LEASE|LEASE-01|Lease|bad|vehicle_month|650|48|2026-01-01")

    def test_billing_parser_reads_all_fields_and_skips_malformed_line(self):
        line = "LINE|LEASE|LEASE-01|Lease|monthly_lease|recurring|500|650.00|vehicle_month|325000.00"
        rows = parse_billing_rows(line + "\nLINE|too|short")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["billing_stream"], "LEASE")
        self.assertEqual(rows[0]["amount"], 325000)
        with self.assertRaises(ValueError):
            parse_billing_rows("LINE|SERVICE|FUEL|Fuel|monthly_per_vehicle|recurring|many|2|vehicle_month|20")

    def test_encrypted_pdf_is_rejected(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("secret")
        path = self.root / "encrypted.pdf"
        with path.open("wb") as handle:
            writer.write(handle)
        with self.assertRaisesRegex(ValueError, "Encrypted PDFs"):
            extract_pdf_pages(path)

    def test_storage_enforces_foreign_keys_and_allowed_streams(self):
        with connect() as db:
            with self.assertRaises(Exception):
                db.execute("INSERT INTO agreements(id,client_id,agreement_type,version_label,filename,file_path,effective_date,uploaded_by,extracted_json) VALUES ('x','missing','MSA','1','a','a','2026-01-01','u','{}')")
            with self.assertRaises(Exception):
                db.execute("INSERT INTO billing_documents(id,client_id,invoice_number,billing_stream,period_start,period_end,filename,file_path,uploaded_by) VALUES ('x','C-1001','x','BAD','2026-01-01','2026-01-31','x','x','u')")

    def test_seed_is_idempotent(self):
        with connect() as db:
            before = [db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                      for table in ("clients", "agreements", "pricing_components", "billing_documents", "billing_lines")]
        seed_demo_data()
        with connect() as db:
            after = [db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                     for table in ("clients", "agreements", "pricing_components", "billing_documents", "billing_lines")]
        self.assertEqual(before, after)

    def test_synthetic_writers_create_named_selectable_pdfs(self):
        folder = self.root / "generated"
        agreements = write_demo_agreements(folder, "C-X", "Test Client")
        invoice = write_demo_invoice(folder, "C-X", "Test Client", "2026-01-01", "2026-01-31", "INV-X", "LEASE")
        self.assertEqual({item["type"] for item in agreements}, {"MSA", "MLA"})
        self.assertTrue(all(item["path"].is_file() for item in agreements))
        self.assertIn("Client Id\nC-X", extract_pdf_text(invoice["path"]))


if __name__ == "__main__":
    unittest.main()
