"""Get OAuth2 client-credentials tokens for authenticated REST calls."""

from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def open_service_url(url: str, account: str, secret_env: str):
    auth_api = os.getenv("AUTH_API_URL", "http://127.0.0.1:8004")
    secret = os.getenv(secret_env, "")
    if not secret:
        raise OSError(f"Missing service credential setting {secret_env}.")
    form = urlencode({"grant_type": "client_credentials", "client_id": account, "client_secret": secret}).encode()
    token_request = Request(f"{auth_api}/auth/service-token", data=form,
                            headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(token_request, timeout=5) as response:
        token = json.loads(response.read().decode())["access_token"]
    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    return urlopen(request, timeout=5)
