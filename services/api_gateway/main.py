"""Small local reverse proxy: one browser origin and JWT checks at ingress."""

from __future__ import annotations

import asyncio
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from services.auth import Identity, get_identity

app = FastAPI(title="Apollo Wheels API Gateway", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"service": "api-gateway", "status": "ready", "docs": "/docs", "openapi": "/openapi.json"}


def target_service(path: str) -> str:
    if path.startswith("/api/pricing/") or path.endswith("/pricing"):
        return "PRICING_API_URL"
    if path.startswith(("/api/audit/", "/api/files/")) or any(
        marker in path for marker in ("/billing-history", "/billing-documents", "/billing-combined", "/pdfs", "/audit")
    ):
        return "BILLING_API_URL"
    return "CONTRACT_API_URL"


def _forward(target: str, request: Request, body: bytes, request_id: str):
    headers = {key: value for key, value in request.headers.items()
               if key.lower() not in {"host", "connection", "content-length", "x-request-id"}}
    headers["X-Request-ID"] = request_id
    url = f"{target}{request.url.path}"
    if request.url.query:
        url += f"?{request.url.query}"
    outbound = UrlRequest(url, data=body or None, headers=headers, method=request.method)
    try:
        with urlopen(outbound, timeout=30) as upstream:
            return Response(upstream.read(), status_code=upstream.status,
                            headers={key: value for key, value in upstream.headers.items()
                                     if key.lower() in {"content-type", "content-disposition", "cache-control"}})
    except HTTPError as error:
        return Response(error.read(), status_code=error.code,
                        headers={"Content-Type": error.headers.get("Content-Type", "application/json")})
    except (URLError, TimeoutError, OSError) as error:
        raise HTTPException(status_code=502, detail="The requested service is unavailable.") from error


@app.api_route("/auth/{path:path}", methods=["GET", "POST"])
async def auth_proxy(path: str, request: Request):
    auth_url = os.getenv("AUTH_API_URL", "http://127.0.0.1:8004")
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    return await asyncio.to_thread(_forward, auth_url, request, await request.body(), request_id)


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def api_proxy(path: str, request: Request, actor: Identity = Depends(get_identity)):
    route_path = f"/api/{path}"
    if actor.account_type == "service":
        service = "pricing" if target_service(route_path) == "PRICING_API_URL" else (
            "billing" if target_service(route_path) == "BILLING_API_URL" else "contract")
        from services.auth import api_access
        await api_access(service)(request, actor)
    target = os.getenv(target_service(route_path), "")
    if not target:
        raise HTTPException(status_code=503, detail="Target service URL is not configured.")
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    return await asyncio.to_thread(_forward, target, request, await request.body(), request_id)


from services.audit_middleware import add_request_audit
add_request_audit(app, "gateway")
