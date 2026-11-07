"""Optional combined API host for local troubleshooting."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from services.billing_service.api import router as billing_router
from services.common import value_error_handler
from services.contract_service.api import router as contract_router
from services.pricing_service.api import router as pricing_router
from .seed import seed_demo_data
from .storage import initialize


@asynccontextmanager
async def lifespan(_):
    initialize()
    seed_demo_data()
    yield


app = FastAPI(title="Apollo Wheels Combined API", version="0.1.0", lifespan=lifespan)
app.add_exception_handler(ValueError, value_error_handler)
app.include_router(contract_router)
app.include_router(pricing_router)
app.include_router(billing_router)