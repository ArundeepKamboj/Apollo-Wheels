"""OAuth2 password and client-credentials grants for the local demo."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from services.auth import (TOKEN_TTL_SECONDS, issue_service_token, issue_user_token,
                           verify_user_credentials)

router = APIRouter()


@router.get("/")
def health():
    return {"service": "auth-api", "status": "ready", "docs": "/docs", "openapi": "/openapi.json"}


@router.post("/auth/token")
def user_token(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    try:
        user = verify_user_credentials(form.username, form.password)
    except NotImplementedError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    if not user:
        request.state.authenticated_actor = ("login_failed", form.username)
        raise HTTPException(status_code=401, detail="Incorrect username or password.", headers={"WWW-Authenticate": "Bearer"})
    request.state.authenticated_actor = ("user", user["user_id"])
    return {"access_token": issue_user_token(user), "token_type": "bearer", "expires_in": TOKEN_TTL_SECONDS,
            "user_id": user["user_id"], "display_name": user["display_name"], "role": user["role"]}


@router.post("/auth/service-token")
def service_token(request: Request, client_id: str = Form(...), client_secret: str = Form(...), grant_type: str = Form(default="client_credentials")):
    token = issue_service_token(client_id, client_secret) if grant_type == "client_credentials" else None
    if not token:
        request.state.authenticated_actor = ("service_login_failed", client_id)
        raise HTTPException(status_code=401, detail="Invalid service account credentials.", headers={"WWW-Authenticate": "Bearer"})
    request.state.authenticated_actor = ("service", client_id)
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_TTL_SECONDS}
