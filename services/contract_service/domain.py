"""Contract intake and extraction module (kept separate for future service extraction)."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from apollo_wheels_mvp.documents import extract_pdf_pages
from apollo_wheels_mvp.extraction import detect_agreement_type, extract_agreement_terms
from apollo_wheels_mvp.storage import DOCUMENT_DIR, connect


def list_agreements(client_id: str | None = None, agreement_type: str | None = None, active_only: bool = True) -> list[dict[str, object]]:
    with connect() as db:
        query = "SELECT * FROM agreements"
        params: list[object] = []
        conditions = []
        if client_id:
            conditions.append("client_id=?")
            params.append(client_id)
        if agreement_type:
            conditions.append("agreement_type=?")
            params.append(agreement_type.upper())
        if active_only:
            conditions.append("is_active=1")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        # Latest active version first for each client+type; seeded docs first
        query += " ORDER BY CASE WHEN uploaded_by='seed' THEN 0 ELSE 1 END, version DESC, created_at DESC"
        rows = db.execute(query, params).fetchall()
        return [agreement_dict(row) for row in rows]


def agreement_dict(row) -> dict[str, object]:
    item = dict(row)
    item["extracted"] = json.loads(item.pop("extracted_json"))
    return item


async def store_upload(client_id: str, agreement_type: str | None, upload: UploadFile, uploaded_by: str) -> dict[str, object]:
    if agreement_type and agreement_type.upper() not in {"MSA", "MLA"}:
        raise ValueError("Agreement type must be MSA or MLA.")
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise ValueError("Upload a PDF file.")
    content = await upload.read()
    if not content.startswith(b"%PDF"):
        raise ValueError("The uploaded file is not a valid PDF.")
    if len(content) > 20 * 1024 * 1024:
        raise ValueError("PDF uploads must be 20 MB or smaller in this MVP.")
    with connect() as db:
        client = db.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone()
        if not client:
            raise ValueError("Select an existing client.")
    agreement_id = str(uuid.uuid4())
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(upload.filename).name)
    stored_name = f"{agreement_id}_{safe_name}"
    path = DOCUMENT_DIR / stored_name
    path.write_bytes(content)
    try:
        pages = extract_pdf_pages(path)
        text = "\n".join(pages)
        detected_type = detect_agreement_type(pages)
        if agreement_type and agreement_type.upper() != detected_type:
            raise ValueError(f"This PDF was identified as {detected_type}, not {agreement_type.upper()}.")
        agreement_type = detected_type
        values = {}
        for line in text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key.strip().upper()] = value.strip()
        extracted = extract_agreement_terms(pages, agreement_type)
        effective = values.get("EFFECTIVE_DATE", "2026-01-01")
        version = values.get("VERSION", "1.0")
        with connect() as db:
            db.execute(
                """INSERT INTO agreements
                (id,client_id,agreement_type,version_label,filename,file_path,effective_date,status,uploaded_by,extracted_json,version,is_active)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (agreement_id, client_id, agreement_type, version, upload.filename, str(path), effective,
                 "review", uploaded_by, json.dumps(extracted), 1, 1),
            )
            row = db.execute("SELECT * FROM agreements WHERE id=?", (agreement_id,)).fetchone()
        return agreement_dict(row)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def update_extracted_terms(agreement_id: str, extracted: dict[str, object]) -> dict[str, object]:
    with connect() as db:
        db.execute("UPDATE agreements SET extracted_json=?, status='review' WHERE id=?", (json.dumps(extracted), agreement_id))
        row = db.execute("SELECT * FROM agreements WHERE id=?", (agreement_id,)).fetchone()
        if row is None:
            raise ValueError("Agreement not found.")
        return agreement_dict(row)


def save_agreement_version(
    agreement_id: str,
    extracted: dict[str, object],
    update_comment: str,
    actor: str
) -> dict[str, object]:
    """Create a new version of the agreement with updated terms.

    The current version is archived (is_active=0, status='archived') and a
    new row is inserted with an incremented version number. list_agreements
    filters on is_active=1 and orders by version DESC, so the latest version
    is what callers see by default.
    """
    with connect() as db:
        old_row = db.execute("SELECT * FROM agreements WHERE id=?", (agreement_id,)).fetchone()
        if not old_row:
            raise ValueError("Agreement not found.")

        old_version = old_row["version"]
        new_version = old_version + 1

        # Archive the previous version so its terms remain queryable as history.
        db.execute(
            "UPDATE agreements SET is_active=0, status='archived', update_comment=? WHERE id=?",
            (update_comment, agreement_id)
        )

        # Insert the new version. It reuses the same stored PDF (file_path) and
        # the same client/agreement_type, so the source document stays linked.
        new_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO agreements
               (id, client_id, agreement_type, version_label, filename, file_path,
                effective_date, status, uploaded_by, extracted_json, version, is_active, update_comment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_id, old_row["client_id"], old_row["agreement_type"], str(new_version),
             old_row["filename"], old_row["file_path"], old_row["effective_date"],
             "review", actor, json.dumps(extracted), new_version, 1, update_comment)
        )
        row = db.execute("SELECT * FROM agreements WHERE id=?", (new_id,)).fetchone()
        return agreement_dict(row)


def update_agreement_identifiers(
    agreement_id: str,
    client_id: str,
    agreement_type: str,
    actor: str
) -> dict[str, object]:
    """Update client_id and agreement_type for a draft/uploaded agreement.
    Used when user corrects client name / agreement type after upload."""
    if agreement_type.upper() not in {"MSA", "MLA"}:
        raise ValueError("Agreement type must be MSA or MLA.")
    with connect() as db:
        # Verify client exists
        client = db.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone()
        if not client:
            raise ValueError("Client not found.")

        db.execute(
            "UPDATE agreements SET client_id=?, agreement_type=?, uploaded_by=?, status='review', is_active=1 WHERE id=?",
            (client_id, agreement_type.upper(), actor, agreement_id)
        )
        row = db.execute("SELECT * FROM agreements WHERE id=?", (agreement_id,)).fetchone()
        if not row:
            raise ValueError("Agreement not found.")
        return agreement_dict(row)


def get_agreement_file(agreement_id: str) -> Path:
    with connect() as db:
        row = db.execute("SELECT file_path FROM agreements WHERE id=?", (agreement_id,)).fetchone()
    if row is None:
        raise ValueError("Agreement not found.")
    return Path(row["file_path"])
