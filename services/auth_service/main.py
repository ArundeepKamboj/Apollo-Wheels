from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api import router
from apollo_wheels_mvp.storage import initialize

@asynccontextmanager
async def lifespan(_):
    initialize()
    yield


app = FastAPI(title="Apollo Wheels Auth API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
from services.audit_middleware import add_request_audit
add_request_audit(app, "auth")
