"""Exercise database seeding, four-eyes approval, and audit reconciliation."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import tempfile
import unittest
import uuid
from unittest.mock import patch

from apollo_wheels_mvp import storage
from apollo_wheels_mvp import seed
from services.billing_service import domain as billing_domain
from services.pricing_service import domain as pricing_domain


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def database():
    connection = storage.connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


class JsonResponse:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self):
        return json.dumps(self.value).encode("utf-8")


class LocalWorkflowTests(unittest.TestCase):
    def setUp(self):
        test_data_dir = PROJECT_ROOT / "data"
        test_data_dir.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=test_data_dir)
        root = Path(self.temp_dir.name)
        storage.DATA_DIR = root
        storage.DATABASE_PATH = root / "test.db"
        storage.DOCUMENT_DIR = root / "documents"
        seed.DOCUMENT_DIR = storage.DOCUMENT_DIR
        storage.initialize()
        seed.seed_demo_data()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_seed_creates_a_complete_local_demo_dataset(self):
        with database() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM clients").fetchone()[0], 3)
            self.assertEqual(db.execute("SELECT name FROM clients WHERE id='C-TEST'").fetchone()[0], "Test Client")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM agreements").fetchone()[0], 4)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM pricing_components").fetchone()[0], 22)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM billing_documents").fetchone()[0], 12)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM billing_lines").fetchone()[0], 62)

    def test_pricing_initiator_cannot_approve_and_second_user_activates(self):
        with database() as db:
            msa_id = db.execute(
                "SELECT id FROM agreements WHERE client_id='C-1001' AND agreement_type='MSA'"
            ).fetchone()[0]
            request_id = str(uuid.uuid4())
            db.execute(
                """INSERT INTO pricing_approval_requests
                (id,client_id,agreement_ids_json,version,status,initiated_by,effective_from)
                VALUES (?,?,?,2,'pending_approval','finance.alex','2026-04-01')""",
                (request_id, "C-1001", json.dumps([msa_id])),
            )
            db.execute(
                """INSERT INTO pricing_components
                (id,approval_request_id,client_id,agreement_id,agreement_type,billing_stream,
                 service_code,service_name,component_code,component_name,charge_type,amount,currency,
                 rate_unit,quantity,billing_frequency,billing_day,terms_json,effective_from,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending_approval')""",
                (str(uuid.uuid4()), request_id, "C-1001", msa_id, "MSA", "SERVICE", "FUEL", "Fuel",
                 "monthly_per_vehicle", "Monthly per vehicle", "recurring", 5.0, "USD", "vehicle_month",
                 500, "monthly", "1", "{}", "2026-04-01"),
            )

        with self.assertRaisesRegex(ValueError, "cannot approve their own"):
            pricing_domain.approve_pricing(request_id, "finance.alex")

        result = pricing_domain.approve_pricing(request_id, "finance.jordan")
        self.assertEqual(result["status"], "active")
        with database() as db:
            active = db.execute(
                "SELECT COUNT(*) FROM pricing_components WHERE approval_request_id=? AND status='active'",
                (request_id,),
            ).fetchone()[0]
            self.assertEqual(active, 1)

    def test_audit_matches_contract_and_pricing_and_flags_only_rr_sample_difference(self):
        with database() as db:
            client = dict(db.execute("SELECT * FROM clients WHERE id='C-1001'").fetchone())
            agreements = [dict(row) for row in db.execute(
                "SELECT * FROM agreements WHERE client_id='C-1001'"
            ).fetchall()]
            for agreement in agreements:
                agreement["extracted"] = json.loads(agreement.pop("extracted_json"))
            pricing = [dict(row) for row in db.execute(
                "SELECT * FROM pricing_components WHERE client_id='C-1001'"
            ).fetchall()]
            pricing_response = {"components": pricing}

        responses = [JsonResponse(client), JsonResponse(agreements), JsonResponse(pricing_response)]
        with patch.object(billing_domain, "open_service_url", side_effect=responses):
            report = billing_domain.audit_client("C-1001")

        self.assertEqual(report["discrepancy_count"], 1)
        mismatch = next(row for row in report["rows"] if row["issue"])
        self.assertEqual(mismatch["service_code"], "RR")
        self.assertIn("Billed rate differs", mismatch["issue"])
        self.assertTrue(all(row["contracted"] for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()

