"""HTTP request auditing without recording credentials, query strings, or bodies."""

import uuid

import jwt
from fastapi import FastAPI, Request

from services.audit import record_request
from services.auth import _secret


def add_request_audit(app: FastAPI, service_name: str) -> None:
    @app.middleware("http")
    async def request_audit(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        actor_type, actor_id = "anonymous", None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                claims = jwt.decode(auth_header[7:], _secret(), algorithms=["HS256"], audience="apollo-wheels")
                actor_type, actor_id = claims.get("typ", "unknown"), claims.get("sub")
            except jwt.PyJWTError:
                actor_type = "invalid_token"
        try:
            response = await call_next(request)
        except Exception:
            record_request(service_name, actor_type, actor_id, request.method, request.url.path, 500, request_id)
            raise
        # Auth endpoints set this after credential verification; never record form bodies.
        if getattr(request.state, "authenticated_actor", None):
            actor_type, actor_id = request.state.authenticated_actor
        response.headers["X-Request-ID"] = request_id
        record_request(service_name, actor_type, actor_id, request.method, request.url.path, response.status_code, request_id)
        return response
