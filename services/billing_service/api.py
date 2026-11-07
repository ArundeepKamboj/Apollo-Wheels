"""HTTP routes owned by the Billing and Audit service."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path

from apollo_wheels_mvp.storage import connect
from services.auth import Identity, api_access, get_identity, require_user
from . import domain

router = APIRouter(dependencies=[Depends(api_access("billing"))])
public_router = APIRouter()


@public_router.get("/")
def health():
    return {"service": "billing-audit-api", "status": "ready", "docs": "/docs"}


@router.post("/api/clients/{client_id}/billing-documents")
async def upload_billing_document(
    client_id: str,
    file: UploadFile = File(...),
    actor: Identity = Depends(get_identity),
):
    require_user(actor)
    return await domain.ingest_billing_pdf(client_id, file, f"{actor.role}:{actor.subject}")


@router.get("/api/clients/{client_id}/billing-history")
def client_billing_history(client_id: str, start: str | None = None, end: str | None = None):
    return domain.billing_history(client_id, start, end)


@router.get("/api/clients/{client_id}/audit")
def client_audit(client_id: str, start: str | None = None, end: str | None = None):
    return domain.audit_client(client_id, start, end)


@router.get("/api/audit/summary")
def audit_summary():
    return domain.audit_summary()


@router.get("/api/clients/{client_id}/billing-combined")
def client_combined_billing(client_id: str, start: str | None = None, end: str | None = None,
                            actor: Identity = Depends(get_identity)):
    """Finance view of all billing for a client, grouped by period across streams."""
    return domain.combined_billing(client_id, start, end)


@router.get("/api/clients/{client_id}/pdfs")
def client_pdf_list(client_id: str):
    with connect() as db:
        invoices = db.execute("SELECT id,invoice_number,filename FROM billing_documents WHERE client_id=?", (client_id,)).fetchall()
    return {"billing": [{"id": row["id"], "invoice_number": row["invoice_number"], "filename": row["filename"],
                         "url": f"/api/files/{row['id']}"} for row in invoices]}


@router.get("/api/files/{document_id}")
def stored_pdf(document_id: str):
    with connect() as db:
        row = db.execute("SELECT file_path,filename FROM billing_documents WHERE id=?", (document_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Billing document not found.")
    path = Path(row["file_path"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Document file missing from local file store.")
    return FileResponse(path, media_type="application/pdf", filename=row["filename"])
