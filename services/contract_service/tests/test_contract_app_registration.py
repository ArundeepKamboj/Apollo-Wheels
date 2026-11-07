"""Application wiring tests for the Contract service entrypoint."""

import unittest

from services.contract_service.main import app


class ContractAppRegistrationTests(unittest.TestCase):
    def test_contract_app_has_expected_name_and_routes(self):
        self.assertEqual(app.title, "Apollo Wheels Contract API")
        paths = set(app.openapi()["paths"])
        self.assertTrue({"/", "/api/bootstrap", "/api/clients/{client_id}/agreements",
                         "/api/agreements/{agreement_id}/terms", "/api/clients/{client_id}/invoice-history"}.issubset(paths))


if __name__ == "__main__":
    unittest.main()
