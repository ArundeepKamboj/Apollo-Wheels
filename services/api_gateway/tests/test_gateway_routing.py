import unittest

from fastapi.testclient import TestClient

from services.api_gateway.main import app, target_service


class GatewayRoutingTests(unittest.TestCase):
    def test_paths_route_to_their_owning_service(self):
        self.assertEqual(target_service("/api/bootstrap"), "CONTRACT_API_URL")
        self.assertEqual(target_service("/api/clients/C-1001/pricing"), "PRICING_API_URL")
        self.assertEqual(target_service("/api/pricing/requests"), "PRICING_API_URL")
        self.assertEqual(target_service("/api/clients/C-1001/audit"), "BILLING_API_URL")
        self.assertEqual(target_service("/api/clients/C-1001/billing-history"), "BILLING_API_URL")
        self.assertEqual(target_service("/api/agreements/A-1/pdf"), "CONTRACT_API_URL")

    def test_browser_pdf_preflight_allows_local_frontend_origin(self):
        response = TestClient(app).options(
            "/api/agreements/A-1/pdf",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://127.0.0.1:5173")


if __name__ == "__main__":
    unittest.main()
