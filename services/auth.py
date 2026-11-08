"""Small local OAuth2/JWT issuer and verifier for demo users and API clients."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

ROOT = Path(__file__).resolve().parents[1]
TOKEN_URL = "/auth/token"
TOKEN_TTL_SECONDS = 1800
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{os.getenv('AUTH_API_URL', 'http://127.0.0.1:8004')}/auth/token")


@dataclass(frozen=True)
class Identity:
    subject: str
    role: str | None
    account_type: str
    scopes: tuple[str, ...] = ()


def accounts() -> dict:
    path = Path(os.getenv("AUTH_ACCOUNTS_FILE", ROOT / "config/demo_accounts.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def _secret() -> str:
    secret = os.getenv("AUTH_JWT_SECRET", "apollo-local-demo-only-signing-key-change-before-sharing")
    if len(secret) < 32:
        raise RuntimeError("AUTH_JWT_SECRET must contain at least 32 characters.")
    return secret


def verify_password(password: str, salt_hex: str, expected: str) -> bool:
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310_000)
    encoded = base64.urlsafe_b64encode(actual).decode().rstrip("=")
    return hmac.compare_digest(encoded, expected)


def find_user(username: str) -> dict | None:
    return next((user for user in accounts()["users"] if user["username"] == username), None)


def issue_token(claims: dict) -> str:
    now = int(time.time())
    return jwt.encode({**claims, "iat": now, "exp": now + TOKEN_TTL_SECONDS, "aud": "apollo-wheels"}, _secret(), algorithm="HS256")


def verify_user_credentials(username: str, password: str) -> dict | None:
    from services.auth_providers.factory import identity_provider
    return identity_provider().authenticate(username, password)


def issue_user_token(user: dict) -> str:
    return issue_token({"sub": user["user_id"], "username": user["username"], "role": user["role"], "typ": "user"})


def issue_service_token(client_id: str, secret: str) -> str | None:
    account = next((item for item in accounts()["services"] if item["client_id"] == client_id), None)
    if not account or not verify_password(secret, account["salt"], account["secret_hash"]):
        return None
    return issue_token({"sub": client_id, "typ": "service", "scope": account["scopes"]})


async def get_identity(token: str = Depends(oauth2_scheme)) -> Identity:
    try:
        claims = jwt.decode(token, _secret(), algorithms=["HS256"], audience="apollo-wheels")
        subject, account_type = claims["sub"], claims["typ"]
        if account_type == "user":
            user = next((item for item in accounts()["users"] if item["user_id"] == subject), None)
            if not user or user["role"] != claims.get("role"):
                raise ValueError("Unknown user")
            return Identity(subject, user["role"], "user")
        if account_type == "service":
            service = next((item for item in accounts()["services"] if item["client_id"] == subject), None)
            if not service or not set(claims.get("scope", [])).issubset(service["scopes"]):
                raise ValueError("Unknown service account")
            return Identity(subject, None, "service", tuple(claims.get("scope", [])))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        pass
    raise HTTPException(status_code=401, detail="Valid bearer token required.", headers={"WWW-Authenticate": "Bearer"})


def require_user(identity: Identity) -> Identity:
    if identity.account_type != "user":
        raise HTTPException(status_code=403, detail="A human user account is required for this action.")
    return identity


def require_access(identity: Identity, scope: str) -> None:
    if identity.account_type == "service" and scope not in identity.scopes:
        raise HTTPException(status_code=403, detail=f"Service account is missing the {scope} scope.")


def api_access(service_name: str):
    """Limit service tokens to explicit internal read APIs; people use role rules."""
    async def check(request: Request, identity: Identity = Depends(get_identity)) -> None:
        if identity.account_type == "user":
            return
        path = request.url.path
        method = request.method
        allowed = {
            ("contract", "GET", "/api/clients/", "contract:read"),
            ("pricing", "GET", "/api/clients/", "pricing:read"),
            ("billing", "GET", "/api/clients/", "billing:read"),
            ("billing", "POST", "/api/clients/", "billing:read"),
            ("billing", "GET", "/api/billing-pdfs/", "billing:read"),
        }
        for owner, verb, prefix, scope in allowed:
            if service_name == owner and method == verb and path.startswith(prefix):
                require_access(identity, scope)
                return
        # Billing currently has no downstream API consumers. Contract/Pricing
        # service accounts are likewise restricted to their declared reads.
        if service_name == "contract" and method == "GET" and path.startswith("/api/agreements/") and "contract:read" in identity.scopes:
            return
        raise HTTPException(status_code=403, detail="Service account is not authorized for this API operation.")
    return check


def require_role(identity: Identity, expected: str) -> None:
    require_user(identity)
    # The demo admin role carries both Structuring and Finance permissions so
    # one person can exercise either workflow. Four-eyes is still enforced by
    # subject: an admin cannot approve their own pricing request.
    if identity.role != expected and identity.role != "admin":
        raise HTTPException(status_code=403, detail=f"This action is reserved for {expected.title()} users.")


async def value_error_handler(_, exc: ValueError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=400, content={"detail": str(exc)})
