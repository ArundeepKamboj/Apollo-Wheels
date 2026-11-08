"""HTTP routes owned by the Contract service."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from apollo_wheels_mvp.catalog import SERVICES
from apollo_wheels_mvp.documents import parse_key_values
from apollo_wheels_mvp.storage import connect
from services.auth import Identity, api_access, get_identity, require_role, require_user
from . import domain

router = APIRouter(dependencies=[Depends(api_access("contract"))])
public_router = APIRouter()


class TermsUpdate(BaseModel):
    extracted: dict[str, object]


class InvoiceHistorySetting(BaseModel):
    enabled: bool


class VersionSave(BaseModel):
    extracted: dict[str, object]
    update_comment: str


class IdentifiersUpdate(BaseModel):
    client_id: str
    agreement_type: str
    client_name: str | None = None


@public_router.get("/")
def health():
    return {"service": "contract-api", "status": "ready", "docs": "/docs"}


@router.get("/api/bootstrap")
def bootstrap():
    with connect() as db:
        client_rows = db.execute(
            """SELECT c.*, a.file_path FROM clients c
               JOIN agreements a ON a.client_id=c.id
               WHERE a.is_active=1 ORDER BY c.name"""
        ).fetchall()
        clients_by_id = {}
        for row in client_rows:
            if Path(row["file_path"]).is_file():
                clients_by_id.setdefault(
                    row["id"], {key: row[key] for key in row.keys() if key != "file_path"}
                )
        clients = list(clients_by_id.values())
        counts = {
            "clients": len(clients),
            "agreements": db.execute("SELECT COUNT(*) FROM agreements WHERE is_active=1").fetchone()[0],
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
def client_agreements(client_id: str, actor: Identity = Depends(get_identity), type: str | None = None):
    return domain.list_agreements(client_id, type)


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


@router.post("/api/agreements/upload-draft")
async def upload_draft(
    file: UploadFile = File(...),
    actor: Identity = Depends(get_identity),
):
    """Upload a PDF without specifying client/agreement_type upfront.
    Returns extracted terms with detected client name and agreement type.
    A draft record is created in the DB (status='draft', is_active=0); call
    update_identifiers to finalize with client/agreement_type."""
    require_user(actor)
    import uuid, re, json
    from pathlib import Path
    from apollo_wheels_mvp.storage import DOCUMENT_DIR, connect
    from apollo_wheels_mvp.documents import extract_pdf_pages
    from apollo_wheels_mvp.extraction import detect_agreement_type, extract_agreement_terms

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF file.")
    content = await file.read()
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF uploads must be 20 MB or smaller in this MVP.")

    draft_id = str(uuid.uuid4())
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(file.filename).name)
    stored_name = f"draft_{draft_id}_{safe_name}"
    path = DOCUMENT_DIR / stored_name
    path.write_bytes(content)

    try:
        pages = extract_pdf_pages(path)
        text = "\n".join(pages)
        detected_type = detect_agreement_type(pages)
        extracted = extract_agreement_terms(pages, detected_type)

        # Try to find client name from text
        values = parse_key_values(text)
        client_name = values.get("CLIENT_NAME", "").strip()
        if not client_name:
            parties = extracted.get("parties")
            client_party = parties.get("client") if isinstance(parties, dict) else None
            if isinstance(client_party, dict):
                client_name = str(client_party.get("legal_name") or "").strip()
        if not client_name:
            raise HTTPException(
                status_code=422,
                detail="Could not detect a client name in this agreement.",
            )

        # Reuse an existing client when names match, otherwise stage a new one
        # so the inactive agreement draft can retain its required client link.
        with connect() as db:
            clients = db.execute("SELECT id, name FROM clients").fetchall()
            normalize = lambda value: re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
            client = next(
                (row for row in clients if normalize(row["name"]) == normalize(client_name)),
                None,
            )
            if client is None:
                client_id = str(uuid.uuid4())
                db.execute(
                    "INSERT INTO clients (id, name) VALUES (?, ?)",
                    (client_id, client_name),
                )
            else:
                client_id = client["id"]
            # Store draft in DB (inactive, so it doesn't appear in normal listings).
            db.execute(
                """INSERT INTO agreements
                   (id, client_id, agreement_type, version_label, filename, file_path,
                    effective_date, status, uploaded_by, extracted_json, version, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (draft_id, client_id, detected_type, values.get("VERSION", "1.0"), file.filename, str(path),
                 values.get("EFFECTIVE_DATE", "2026-01-01"), "draft", f"{actor.role}:{actor.subject}",
                 json.dumps(extracted), 1, 0),
            )

        return {
            "id": draft_id,
            "draft_id": draft_id,
            "temp_file_path": str(path),
            "detected_client_id": client_id,
            "detected_client_name": client_name,
            "is_new_client": client is None,
            "detected_agreement_type": detected_type,
            "extracted": extracted,
            "agreement_type": detected_type,
            "version_label": "1.0",
            "status": "draft",
            "client_id": client_id,
        }
    except Exception:
        path.unlink(missing_ok=True)
        raise


@router.put("/api/agreements/{agreement_id}/identifiers")
def update_identifiers(
    agreement_id: str,
    payload: IdentifiersUpdate,
    actor: Identity = Depends(get_identity),
):
    """Update client_id and agreement_type for an uploaded agreement (draft or final)."""
    require_user(actor)
    return domain.update_agreement_identifiers(
        agreement_id, payload.client_id, payload.agreement_type, f"{actor.role}:{actor.subject}",
        payload.client_name,
    )


@router.put("/api/agreements/{agreement_id}/terms")
def edit_terms(
    agreement_id: str,
    payload: TermsUpdate,
    actor: Identity = Depends(get_identity),
):
    require_role(actor, "structuring")
    return domain.update_extracted_terms(agreement_id, payload.extracted)


@router.put("/api/agreements/{agreement_id}/save-version")
def save_version(
    agreement_id: str,
    payload: VersionSave,
    actor: Identity = Depends(get_identity),
):
    """Save a new version of the agreement with an update comment (audit trail)."""
    require_role(actor, "structuring")
    return domain.save_agreement_version(
        agreement_id, payload.extracted, payload.update_comment, f"{actor.role}:{actor.subject}"
    )


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
