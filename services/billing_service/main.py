from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.common import value_error_handler
from .api import public_router, router
from apollo_wheels_mvp.seed import seed_demo_data
from apollo_wheels_mvp.storage import initialize


@asynccontextmanager
async def lifespan(_):
    initialize()
    seed_demo_data(include_workflow_history=True)
    yield


app = FastAPI(title="Apollo Wheels Billing API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://(localhost|127\.0.0.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])
app.add_exception_handler(ValueError, value_error_handler)
app.include_router(public_router)
app.include_router(router)
from services.audit_middleware import add_request_audit
add_request_audit(app, "billing")
