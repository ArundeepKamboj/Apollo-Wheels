"""Application wiring tests for the Billing/Audit service entrypoint."""

import unittest

from services.billing_service.main import app


class BillingAppRegistrationTests(unittest.TestCase):
    def test_billing_app_has_expected_name_and_routes(self):
        self.assertEqual(app.title, "Apollo Wheels Billing API")
        paths = set(app.openapi()["paths"])
        self.assertTrue({"/", "/api/clients/{client_id}/billing-documents",
                         "/api/clients/{client_id}/billing-history", "/api/clients/{client_id}/audit",
                         "/api/audit/summary", "/api/files/{document_id}"}.issubset(paths))


if __name__ == "__main__":
    unittest.main()
