"""Tests for shared role identity and error-response helpers."""

import unittest

from fastapi import HTTPException

from services.auth import Identity, require_role, require_user, verify_password
from services.common import value_error_handler
from services.test_support import run_upload


class SharedServiceHelperTests(unittest.TestCase):
    def test_require_role_allows_exact_role_and_rejects_other_role(self):
        require_role(Identity("finance.alex", "finance", "user"), "finance")
        with self.assertRaises(HTTPException) as error:
            require_role(Identity("structuring.lee", "structuring", "user"), "finance")
        self.assertEqual(error.exception.status_code, 403)
        self.assertIn("Finance", error.exception.detail)

    def test_service_account_cannot_act_as_human_user(self):
        with self.assertRaises(HTTPException) as error:
            require_user(Identity("billing-service", None, "service"))
        self.assertEqual(error.exception.status_code, 403)

    def test_demo_credentials_are_stored_as_hashes(self):
        self.assertTrue(verify_password("FinanceDemo!2026", "33cc878a97d8737128a3510474cbf2ab", "Ef8DL0Rxct0PmbKHknUpKRzDMef6yiOQkrk0Q1qzlM4"))
        self.assertFalse(verify_password("wrong", "33cc878a97d8737128a3510474cbf2ab", "Ef8DL0Rxct0PmbKHknUpKRzDMef6yiOQkrk0Q1qzlM4"))

    def test_value_error_handler_returns_client_readable_400(self):
        response = run_upload(value_error_handler(None, ValueError("bad input")))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body, b'{"detail":"bad input"}')


if __name__ == "__main__":
    unittest.main()
