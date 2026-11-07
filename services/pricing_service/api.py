"""HTTP routes owned by the Pricing service."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.auth import Identity, api_access, get_identity, require_role
from . import domain

router = APIRouter(dependencies=[Depends(api_access("pricing"))])
public_router = APIRouter()


class PricingComponent(BaseModel):
    agreement_id: str
    billing_stream: str
    service_code: str
    service_name: str
    component_code: str
    component_name: str
    charge_type: str = "recurring"
    amount: float = Field(ge=0)
    currency: str = "USD"
    rate_unit: str = "vehicle_month"
    quantity: float = Field(default=1, ge=0)
    billing_frequency: str = "monthly"
    billing_day: str | None = None
    effective_from: str = "2026-01-01"
    terms: dict[str, object] = Field(default_factory=dict)


class PricingSubmission(BaseModel):
    client_id: str
    agreement_ids: list[str]
    components: list[PricingComponent]


@public_router.get("/")
def health():
    return {"service": "pricing-api", "status": "ready", "docs": "/docs"}


@router.get("/api/clients/{client_id}/pricing")
def client_pricing(client_id: str, actor: Identity = Depends(get_identity)):
    return domain.list_client_pricing(client_id)


@router.post("/api/pricing/requests")
def request_pricing_approval(
    payload: PricingSubmission,
    actor: Identity = Depends(get_identity),
):
    require_role(actor, "finance")
    return domain.submit_pricing(
        payload.client_id, payload.agreement_ids,
        [component.model_dump() for component in payload.components], actor.subject,
    )


@router.post("/api/pricing/requests/{request_id}/approve")
def approve_pricing_request(
    request_id: str,
    actor: Identity = Depends(get_identity),
):
    require_role(actor, "finance")
    return domain.approve_pricing(request_id, actor.subject)
