import json
import os
import unittest
from unittest.mock import patch

from services.service_client import open_service_url


class FakeResponse:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *_): return None
    def read(self): return json.dumps(self.data).encode()


class ServiceClientTests(unittest.TestCase):
    def test_service_client_requests_token_then_sends_bearer(self):
        responses = [FakeResponse({"access_token": "signed-token"}), FakeResponse({"ok": True})]
        with patch.dict(os.environ, {"AUTH_API_URL": "http://auth.local", "AUTH_BILLING_SERVICE_SECRET": "billing-demo-secret"}), \
             patch("services.service_client.urlopen", side_effect=responses) as open_url:
            with open_service_url("http://pricing.local/api/pricing", "billing-service", "AUTH_BILLING_SERVICE_SECRET") as response:
                self.assertEqual(json.loads(response.read()), {"ok": True})
        self.assertEqual(open_url.call_count, 2)
        self.assertIn("/auth/service-token", open_url.call_args_list[0].args[0].full_url)
        self.assertEqual(open_url.call_args_list[1].args[0].get_header("Authorization"), "Bearer signed-token")


if __name__ == "__main__":
    unittest.main()
