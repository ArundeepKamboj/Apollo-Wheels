import unittest

from services.api_gateway.main import target_service


class GatewayRoutingTests(unittest.TestCase):
    def test_paths_route_to_their_owning_service(self):
        self.assertEqual(target_service("/api/bootstrap"), "CONTRACT_API_URL")
        self.assertEqual(target_service("/api/clients/C-1001/pricing"), "PRICING_API_URL")
        self.assertEqual(target_service("/api/pricing/requests"), "PRICING_API_URL")
        self.assertEqual(target_service("/api/clients/C-1001/audit"), "BILLING_API_URL")
        self.assertEqual(target_service("/api/clients/C-1001/billing-history"), "BILLING_API_URL")
        self.assertEqual(target_service("/api/agreements/A-1/pdf"), "CONTRACT_API_URL")


if __name__ == "__main__":
    unittest.main()
