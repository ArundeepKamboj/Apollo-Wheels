"""HTTP routes owned by the Billing and Audit service."""

import json
import os
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
from io import BytesIO

from apollo_wheels_mvp.storage import connect, DOCUMENT_DIR
from apollo_wheels_mvp.synthetic import write_forecast_invoice
from services.auth import Identity, api_access, get_identity, require_user
from services.service_client import open_service_url
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


@router.get("/api/clients/{client_id}/billing-forecast")
def client_billing_forecast(client_id: str, start: str, end: str, stream: str = "COMBINED"):
    """Forecast estimated charges for a client and period based on active pricing setup."""
    return domain.forecast_billing(client_id, start, end, stream)


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


@router.post("/api/clients/{client_id}/billing-forecast-pdf")
def generate_forecast_pdf(
    client_id: str,
    stream: str = "COMBINED",
    actor: Identity = Depends(get_identity),
    start: str | None = None,
    end: str | None = None,
):
    """
    Generate a forecast PDF for the selected client, period, and billing stream.
    Start and end are passed as query parameters.
    Returns the PDF info including download path.
    """
    if not start or not end:
        raise ValueError("Both start and end dates are required.")
    forecast = domain.forecast_billing(client_id, start, end, stream)
    # Get client name from the Contract API for display
    contract_api = os.getenv("CONTRACT_API_URL", "http://127.0.0.1:8001")
    client_name = f"Client {client_id}"
    try:
        with open_service_url(f"{contract_api}/api/clients/{client_id}", "billing-service", "AUTH_BILLING_SERVICE_SECRET") as resp:
            client_data = json.loads(resp.read().decode())
            client_name = client_data.get("name", client_name)
    except Exception:
        pass

    invoice_number = f"FORECAST-{client_id}-{start}-{stream}"
    result = write_forecast_invoice(
        DOCUMENT_DIR, client_id, client_name, start, end, invoice_number, stream,
        forecast["lines"], forecast["total"],
    )
    # Return the file info for download
    return {
        "filename": result["filename"],
        "invoice_number": result["invoice_number"],
        "period_start": start,
        "period_end": end,
        "billing_stream": stream,
        "line_count": result["line_count"],
        "total": result["total"],
        "download_url": f"/api/billing-pdfs/{result['filename']}",
    }


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


@router.get("/api/billing-pdfs/{filename}")
def download_forecast_pdf(filename: str):
    """Download a forecast PDF file by filename."""
    # Sanitize filename to prevent path traversal
    safe_name = Path(filename).name
    path = DOCUMENT_DIR / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Forecast file not found.")
    return FileResponse(path, media_type="application/pdf", filename=safe_name)
