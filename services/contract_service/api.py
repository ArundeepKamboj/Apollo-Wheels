"""HTTP routes owned by the Contract service."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from apollo_wheels_mvp.catalog import SERVICES
from apollo_wheels_mvp.storage import connect
from services.auth import Identity, api_access, get_identity, require_role, require_user
from . import domain

router = APIRouter(dependencies=[Depends(api_access("contract"))])
public_router = APIRouter()


class TermsUpdate(BaseModel):
    extracted: dict[str, object]


class InvoiceHistorySetting(BaseModel):
    enabled: bool


@public_router.get("/")
def health():
    return {"service": "contract-api", "status": "ready", "docs": "/docs"}


@router.get("/api/bootstrap")
def bootstrap():
    with connect() as db:
        clients = [dict(row) for row in db.execute("SELECT * FROM clients ORDER BY name").fetchall()]
        counts = {
            "clients": len(clients),
            "agreements": db.execute("SELECT COUNT(*) FROM agreements").fetchone()[0],
            "pending_approvals": db.execute("SELECT COUNT(*) FROM pricing_approval_requests WHERE status='pending_approval'").fetchone()[0],
            "active_pricing_components": db.execute("SELECT COUNT(*) FROM pricing_components WHERE status='active'").fetchone()[0],
            "billing_invoices": db.execute("SELECT COUNT(*) FROM billing_documents").fetchone()[0],
        }
    return {"clients": clients, "services": SERVICES, "counts": counts}


@router.get("/api/clients/{client_id}")
def get_client(client_id: str, actor: Identity = Depends(get_identity)):
    with connect() as db:
        row = db.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Client not found.")
    return dict(row)


@router.get("/api/clients/{client_id}/agreements")
def client_agreements(client_id: str, actor: Identity = Depends(get_identity)):
    return domain.list_agreements(client_id)


@router.get("/api/agreements/{agreement_id}/pdf")
def agreement_pdf(agreement_id: str):
    try:
        path = domain.get_agreement_file(agreement_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.post("/api/clients/{client_id}/agreements")
async def upload_agreement(
    client_id: str,
    agreement_type: str | None = Form(None),
    file: UploadFile = File(...),
    actor: Identity = Depends(get_identity),
):
    require_user(actor)
    return await domain.store_upload(client_id, agreement_type.upper() if agreement_type else None, file,
                                     f"{actor.role}:{actor.subject}")


@router.put("/api/agreements/{agreement_id}/terms")
def edit_terms(
    agreement_id: str,
    payload: TermsUpdate,
    actor: Identity = Depends(get_identity),
):
    require_role(actor, "structuring")
    return domain.update_extracted_terms(agreement_id, payload.extracted)


@router.put("/api/clients/{client_id}/invoice-history")
def set_invoice_history(
    client_id: str,
    payload: InvoiceHistorySetting,
    actor: Identity = Depends(get_identity),
):
    require_role(actor, "finance")
    with connect() as db:
        cursor = db.execute("UPDATE clients SET include_history_on_invoice=? WHERE id=?", (int(payload.enabled), client_id))
        if not cursor.rowcount:
            raise HTTPException(status_code=404, detail="Client not found.")
    return {"client_id": client_id, "include_history_on_invoice": payload.enabled}
