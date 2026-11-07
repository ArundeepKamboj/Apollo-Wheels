import sqlite3
import unittest
from contextlib import closing

from services.audit import record_request
from services.test_support import setup_demo


class ServiceAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_demo(self)

    def test_request_audit_is_written_to_owning_service_database(self):
        record_request("pricing", "user", "finance.alex", "POST", "/api/pricing/requests", 201, "request-123")
        path = self.root / "audit" / "pricing.sqlite"
        with closing(sqlite3.connect(path)) as db:
            event = db.execute("SELECT service_name,actor_type,actor_id,action,resource,status_code,request_id FROM audit_events").fetchone()
        self.assertEqual(event, ("pricing", "user", "finance.alex", "POST", "/api/pricing/requests", 201, "request-123"))
        self.assertFalse((self.root / "audit" / "billing.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
