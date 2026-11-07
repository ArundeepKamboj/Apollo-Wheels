"""Application wiring tests for the Pricing service entrypoint."""

import unittest

from services.pricing_service.main import app


class PricingAppRegistrationTests(unittest.TestCase):
    def test_pricing_app_has_expected_name_and_routes(self):
        self.assertEqual(app.title, "Apollo Wheels Pricing API")
        paths = set(app.openapi()["paths"])
        self.assertTrue({"/", "/api/clients/{client_id}/pricing", "/api/pricing/requests",
                         "/api/pricing/requests/{request_id}/approve"}.issubset(paths))


if __name__ == "__main__":
    unittest.main()
