import unittest

import jwt
from fastapi import HTTPException
from starlette.requests import Request

from services.auth import _secret, accounts, issue_service_token, issue_user_token, require_role, verify_password, verify_user_credentials


class AuthFlowTests(unittest.TestCase):
    @staticmethod
    def request():
        return Request({"type": "http", "headers": [], "method": "POST", "path": "/auth/token", "query_string": b"", "server": ("test", 80), "client": ("test", 1), "scheme": "http", "http_version": "1.1"})

    def test_auth_endpoints_issue_tokens_and_record_audit_actor(self):
        from fastapi.security import OAuth2PasswordRequestForm
        from services.auth_service.api import user_token, service_token

        request = self.request()
        result = user_token(request, OAuth2PasswordRequestForm(username="testfinance", password="FinanceDemo!2026"))
        self.assertEqual(result["role"], "finance")
        self.assertEqual(request.state.authenticated_actor, ("user", "finance.alex"))

        from unittest.mock import patch
        request = self.request()
        with patch("services.auth_service.api.issue_service_token", return_value="signed-token"):
            result = service_token(request, "pricing-service", "pricing-demo-secret", grant_type="client_credentials")
        self.assertEqual(result["token_type"], "bearer")
        self.assertEqual(request.state.authenticated_actor, ("service", "pricing-service"))

    def test_auth_endpoints_reject_bad_credentials_and_wrong_grant(self):
        from fastapi.security import OAuth2PasswordRequestForm
        from services.auth_service.api import user_token, service_token

        with self.assertRaises(HTTPException) as error:
            user_token(self.request(), OAuth2PasswordRequestForm(username="testfinance", password="bad"))
        self.assertEqual(error.exception.status_code, 401)
        with self.assertRaises(HTTPException) as error:
            service_token(self.request(), "pricing-service", "pricing-demo-secret", grant_type="password")
        self.assertEqual(error.exception.status_code, 401)

    def test_auth_endpoint_surfaces_unimplemented_provider(self):
        from unittest.mock import patch
        from fastapi.security import OAuth2PasswordRequestForm
        from services.auth_service.api import user_token

        with patch("services.auth_service.api.verify_user_credentials", side_effect=NotImplementedError("OIDC flow pending")):
            with self.assertRaises(HTTPException) as error:
                user_token(self.request(), OAuth2PasswordRequestForm(username="user", password="pass"))
        self.assertEqual(error.exception.status_code, 501)

    def test_auth_app_registers_health_and_token_routes(self):
        from services.auth_service.main import app

        self.assertEqual(app.title, "Apollo Wheels Auth API")
        paths = set(app.openapi()["paths"])
        self.assertTrue({"/", "/auth/token", "/auth/service-token"}.issubset(paths))

    def test_three_demo_users_authenticate_with_distinct_roles_and_stable_ids(self):
        finance = verify_user_credentials("testfinance", "FinanceDemo!2026")
        second_finance = verify_user_credentials("testfinance2", "FinanceSecondDemo!2026")
        structuring = verify_user_credentials("teststructurer", "StructuringDemo!2026")
        self.assertEqual(finance["role"], "finance")
        self.assertEqual(second_finance["role"], "finance")
        self.assertNotEqual(finance["user_id"], second_finance["user_id"])
        self.assertEqual(structuring["role"], "structuring")
        self.assertIsNone(verify_user_credentials("testfinance", "incorrect"))
        self.assertIsNone(verify_user_credentials("unknown", "FinanceDemo!2026"))

    def test_user_jwt_has_stable_subject_role_audience_and_expiry(self):
        token = issue_user_token(verify_user_credentials("testfinance", "FinanceDemo!2026"))
        claims = jwt.decode(token, _secret(), algorithms=["HS256"], audience="apollo-wheels")
        self.assertEqual((claims["sub"], claims["role"], claims["typ"]), ("finance.alex", "finance", "user"))
        self.assertGreater(claims["exp"], claims["iat"])

    def test_service_tokens_have_only_configured_scopes_and_reject_bad_secrets(self):
        pricing_token = issue_service_token("pricing-service", "pricing-demo-secret")
        self.assertIsNotNone(pricing_token)
        claims = jwt.decode(pricing_token, _secret(), algorithms=["HS256"], audience="apollo-wheels")
        self.assertEqual(claims["scope"], ["contract:read"])
        self.assertIsNone(issue_service_token("pricing-service", "bad-secret"))
        service = next(row for row in accounts()["services"] if row["client_id"] == "pricing-service")
        self.assertTrue(verify_password("pricing-demo-secret", service["salt"], service["secret_hash"]))

    def test_identity_provider_selection_is_configurable_and_fails_closed(self):
        from unittest.mock import patch
        from services.auth_providers.factory import identity_provider
        with patch.dict("os.environ", {"AUTH_PROVIDER": "local", "AUTH_LOCAL_DEMO_ENABLED": "true"}):
            self.assertEqual(identity_provider().name, "local")
        with patch.dict("os.environ", {"AUTH_PROVIDER": "local", "AUTH_LOCAL_DEMO_ENABLED": "false"}):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                identity_provider()
        with patch.dict("os.environ", {"AUTH_PROVIDER": "oidc", "AUTH_OIDC_ENABLED": "false"}):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                identity_provider()

    def test_service_token_does_not_pass_human_role_checks(self):
        service_identity = type("ServiceIdentity", (), {"account_type": "service", "role": None, "subject": "billing-service"})()
        with self.assertRaises(HTTPException) as error:
            require_role(service_identity, "finance")
        self.assertEqual(error.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
