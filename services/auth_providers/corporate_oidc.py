"""Configuration boundary for a future corporate OpenID Connect provider."""

import os


class CorporateOidcProvider:
    name = "oidc"

    def __init__(self):
        self.issuer = os.getenv("AUTH_OIDC_ISSUER", "")
        self.client_id = os.getenv("AUTH_OIDC_CLIENT_ID", "")
        self.client_secret = os.getenv("AUTH_OIDC_CLIENT_SECRET", "")
        if not self.issuer or not self.client_id:
            raise RuntimeError("Set AUTH_OIDC_ISSUER and AUTH_OIDC_CLIENT_ID to configure corporate OIDC.")

    def authenticate(self, username: str, password: str) -> dict | None:
        # OIDC uses a browser redirect and authorization-code exchange, not password collection here.
        raise NotImplementedError("Corporate OIDC authorization-code login is not implemented in this MVP.")
