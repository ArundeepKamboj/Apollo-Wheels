"""Contract intake and extraction module (kept separate for future service extraction)."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from apollo_wheels_mvp.documents import extract_pdf_pages, parse_key_values, patch_pdf_text_fragments
from apollo_wheels_mvp.extraction import detect_agreement_type, extract_agreement_terms
from apollo_wheels_mvp.storage import DOCUMENT_DIR, connect, update_client_profile


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
        values = parse_key_values(text)
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
            parties = extracted.get("parties")
            if isinstance(parties, dict):
                update_client_profile(db, client_id, parties.get("client"))
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


def _format_count(value: object) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:g}"


def _msa_quantity_basis(item: dict[str, object]) -> str:
    vehicles = item.get("vehicle_count")
    drivers = item.get("driver_count")
    if vehicles:
        return f"{_format_count(vehicles)} covered vehicles"
    if drivers:
        return f"{_format_count(drivers)} covered drivers"
    return "the Customer account"


def _msa_rate_prefix(item: dict[str, object]) -> str:
    amount = item.get("contract_amount")
    if amount is None:
        raise ValueError("An MSA rate cannot be cleared while preserving its source PDF.")
    formatted = f"{float(amount):.2f}"
    basis = item.get("pricing_basis", "USD")
    if basis == "PERCENTAGE":
        return f"{formatted} percent"
    if basis == "BASIS_POINTS":
        return f"{formatted} basis points"
    return f"{basis} {formatted}"


def _vehicle_description(item: dict[str, object]) -> str:
    make = str(item.get("vehicle_make") or "").strip()
    model = str(item.get("vehicle_model") or "").strip()
    engine = str(item.get("engine_type") or "").strip()
    name = " ".join(value for value in (make, model) if value)
    return f"{name} ({engine})" if engine else name


def _mla_row_replacements(before: dict[str, object], after: dict[str, object]) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []

    def replace_if_changed(old_text: str, new_text: str) -> None:
        if old_text != new_text:
            replacements.append((old_text, new_text))

    if before.get("quantity") != after.get("quantity") or before.get("rate_unit") != after.get("rate_unit"):
        if before.get("quantity") is None or after.get("quantity") is None:
            raise ValueError("An MLA vehicle quantity cannot be cleared while preserving its source PDF.")
        old_quantity = f"{_format_count(before['quantity'])} {str(before.get('rate_unit') or 'vehicle_month').replace('_', ' ')}"
        new_quantity = f"{_format_count(after['quantity'])} {str(after.get('rate_unit') or 'vehicle_month').replace('_', ' ')}"
        replace_if_changed(old_quantity, new_quantity)

    if before.get("contract_amount") != after.get("contract_amount") or before.get("pricing_basis") != after.get("pricing_basis"):
        for item in (before, after):
            if item.get("contract_amount") is None:
                raise ValueError("An MLA monthly rate cannot be cleared while preserving its source PDF.")
        old_rate = f"{before.get('pricing_basis', 'USD')} {float(before['contract_amount']):,.2f}"
        new_rate = f"{after.get('pricing_basis', 'USD')} {float(after['contract_amount']):,.2f}"
        replace_if_changed(old_rate, new_rate)

    if before.get("term_months") != after.get("term_months"):
        replace_if_changed(f"{before.get('term_months')} months", f"{after.get('term_months')} months")
    if before.get("effective_from") != after.get("effective_from"):
        replace_if_changed(str(before.get("effective_from") or ""), str(after.get("effective_from") or ""))
    if before.get("vehicle_make") != after.get("vehicle_make") or before.get("vehicle_model") != after.get("vehicle_model") or before.get("engine_type") != after.get("engine_type"):
        replace_if_changed(_vehicle_description(before), _vehicle_description(after))
    for field in ("billing_frequency", "billing_day"):
        if before.get(field) != after.get(field):
            raise ValueError(f"{field.replace('_', ' ').capitalize()} is not printed in this MLA schedule and cannot be changed while preserving the source PDF.")
    if before.get("service_name") != after.get("service_name"):
        raise ValueError("Vehicle schedule labels cannot be changed while preserving the source PDF.")
    return replacements


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

    A new version is made by patching only changed source-backed values in a
    copy of the current PDF. The remaining pages and template layout are kept
    intact, then terms are re-extracted to refresh their source evidence.
    """
    with connect() as db:
        old_row = db.execute("SELECT * FROM agreements WHERE id=?", (agreement_id,)).fetchone()
        if not old_row:
            raise ValueError("Agreement not found.")

        old_values = dict(old_row)
        agreement_type = old_values["agreement_type"].upper()
        client_id = old_values["client_id"]
        old_version = old_values["version"]
        new_version = old_version + 1
        version_label = str(new_version)

        new_filename = f"{agreement_type.lower()}_v{new_version}_{uuid.uuid4().hex[:8]}.pdf"
        new_path = DOCUMENT_DIR / new_filename
        if agreement_type not in {"MSA", "MLA"}:
            raise ValueError(f"Unknown agreement type: {agreement_type}")

        original_extracted = json.loads(old_values["extracted_json"])
        page_updates: dict[int, list[tuple[str, list[tuple[str, str]]]]] = {
            1: [
                ("Version", [(old_values["version_label"], version_label)]),
                ("Effective Date", []),
            ]
        }
        if agreement_type == "MSA":
            submitted_services = {
                item.get("service_code"): item for item in extracted.get("services", [])
            }
            source_services = original_extracted.get("services", [])
            if set(submitted_services) != {item.get("service_code") for item in source_services}:
                raise ValueError("MSA service rows cannot be added or removed while preserving the source PDF.")
            for previous in source_services:
                updated = submitted_services[previous["service_code"]]
                replacements: list[tuple[str, str]] = []

                def replace_if_changed(old_text: str, new_text: str) -> None:
                    if old_text != new_text:
                        replacements.append((old_text, new_text))

                if previous.get("subscribed") != updated.get("subscribed"):
                    old_status = "Included" if previous.get("subscribed") else "Not selected"
                    new_status = "Included" if updated.get("subscribed") else "Not selected"
                    replace_if_changed(f"Status: {old_status}", f"Status: {new_status}")
                if previous.get("contract_amount") != updated.get("contract_amount") or previous.get("pricing_basis") != updated.get("pricing_basis"):
                    replace_if_changed(_msa_rate_prefix(previous), _msa_rate_prefix(updated))
                    old_joiner = " per " if previous.get("pricing_basis", "USD") == "USD" else " of "
                    new_joiner = " per " if updated.get("pricing_basis", "USD") == "USD" else " of "
                    replace_if_changed(old_joiner, new_joiner)
                if previous.get("rate_unit") != updated.get("rate_unit"):
                    replace_if_changed(
                        str(previous.get("rate_unit") or "").replace("_", " "),
                        str(updated.get("rate_unit") or "").replace("_", " "),
                    )
                if previous.get("billing_frequency") != updated.get("billing_frequency") or previous.get("billing_day") != updated.get("billing_day"):
                    old_schedule = f"Billing: {previous.get('billing_frequency')} on day {previous.get('billing_day')}"
                    new_schedule = f"Billing: {updated.get('billing_frequency')} on day {updated.get('billing_day')}"
                    replace_if_changed(old_schedule, new_schedule)
                if previous.get("vehicle_count") != updated.get("vehicle_count") or previous.get("driver_count") != updated.get("driver_count"):
                    replace_if_changed(
                        f"Quantity basis: {_msa_quantity_basis(previous)}",
                        f"Quantity basis: {_msa_quantity_basis(updated)}",
                    )
                page_updates.setdefault(int(previous.get("evidence_page") or 1), []).append(
                    (f"Service code: {previous['service_code']}.", replacements)
                )
        else:
            source_lease = original_extracted.get("lease", {}) or {}
            submitted_lease = extracted.get("lease", {}) or {}
            source_rows = source_lease.get("vehicles") or [source_lease]
            submitted_rows = submitted_lease.get("vehicles") or [submitted_lease]
            source_by_code = {row.get("service_code"): row for row in source_rows}
            submitted_by_code = {row.get("service_code"): row for row in submitted_rows}
            if list(source_by_code) != list(submitted_by_code):
                raise ValueError("MLA vehicle rows cannot be added, removed, or reordered while preserving the source PDF.")
            for code, previous in source_by_code.items():
                updated = submitted_by_code[code]
                page_updates.setdefault(int(previous.get("evidence_page") or 1), []).append(
                    (code, _mla_row_replacements(previous, updated))
                )

        source_path = Path(old_values["file_path"])
        if not source_path.is_file():
            raise ValueError("The source agreement PDF is missing; the version was not saved.")
        patch_pdf_text_fragments(source_path, new_path, page_updates)

        # Re-extract from the patched source PDF so evidence always points at the new version.
        new_pages = extract_pdf_pages(new_path)
        validated_extracted = extract_agreement_terms(new_pages, agreement_type)
        if not source_path.exists() or not validated_extracted:
            raise ValueError("Could not re-extract terms from the patched source PDF.")

        # Archive the previous version so its terms remain queryable as history.
        db.execute(
            "UPDATE agreements SET is_active=0, status='archived', update_comment=? WHERE id=?",
            (update_comment, agreement_id)
        )

        # Insert the new version with the generated PDF path and validated extracted terms.
        new_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO agreements
               (id, client_id, agreement_type, version_label, filename, file_path,
                effective_date, status, uploaded_by, extracted_json, version, is_active, update_comment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_id, client_id, agreement_type, version_label, new_path.name, str(new_path),
             old_values["effective_date"], "review", actor, json.dumps(validated_extracted), new_version, 1, update_comment)
        )
        parties = validated_extracted.get("parties")
        if isinstance(parties, dict):
            update_client_profile(db, client_id, parties.get("client"))
        row = db.execute("SELECT * FROM agreements WHERE id=?", (new_id,)).fetchone()
        return agreement_dict(row)


def update_agreement_identifiers(
    agreement_id: str,
    client_id: str,
    agreement_type: str,
    actor: str,
    client_name: str | None = None,
) -> dict[str, object]:
    """Update client_id and agreement_type for a draft/uploaded agreement.
    Used when user corrects client name / agreement type after upload."""
    if agreement_type.upper() not in {"MSA", "MLA"}:
        raise ValueError("Agreement type must be MSA or MLA.")
    with connect() as db:
        draft = db.execute(
            "SELECT client_id, status FROM agreements WHERE id=?", (agreement_id,)
        ).fetchone()
        if not draft:
            raise ValueError("Agreement not found.")

        if client_name and draft["status"] == "draft":
            normalized_name = re.sub(r"[^a-z0-9]+", " ", client_name.casefold()).strip()
            clients = db.execute("SELECT id, name FROM clients").fetchall()
            matching_client = next(
                (
                    row for row in clients
                    if re.sub(r"[^a-z0-9]+", " ", row["name"].casefold()).strip()
                    == normalized_name
                ),
                None,
            )
            if matching_client:
                client_id = matching_client["id"]
            else:
                finalized_agreements = db.execute(
                    "SELECT COUNT(*) FROM agreements WHERE client_id=? AND status!='draft'",
                    (draft["client_id"],),
                ).fetchone()[0]
                if draft["client_id"] == client_id and finalized_agreements == 0:
                    db.execute(
                        "UPDATE clients SET name=? WHERE id=?",
                        (client_name.strip(), client_id),
                    )
                else:
                    client_id = str(uuid.uuid4())
                    db.execute(
                        "INSERT INTO clients (id, name, is_active) VALUES (?, ?, 1)",
                        (client_id, client_name.strip()),
                    )

        client = db.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone()
        if not client:
            raise ValueError("Client not found.")

        db.execute("UPDATE clients SET is_active=1 WHERE id=?", (client_id,))
        db.execute(
            "UPDATE agreements SET client_id=?, agreement_type=?, uploaded_by=?, status='review', is_active=1 WHERE id=?",
            (client_id, agreement_type.upper(), actor, agreement_id)
        )
        row = db.execute("SELECT * FROM agreements WHERE id=?", (agreement_id,)).fetchone()
        if not row:
            raise ValueError("Agreement not found.")
        parties = json.loads(row["extracted_json"]).get("parties", {})
        if isinstance(parties, dict):
            update_client_profile(db, client_id, parties.get("client"))
        return agreement_dict(row)


def get_agreement_file(agreement_id: str) -> Path:
    with connect() as db:
        row = db.execute("SELECT file_path FROM agreements WHERE id=?", (agreement_id,)).fetchone()
    if row is None:
        raise ValueError("Agreement not found.")
    return Path(row["file_path"])


def delete_agreement(agreement_id: str, actor: str) -> dict[str, object]:
    """Archive an agreement and delete the client record if no agreements remain.

    When a client has no more active agreements, we delete the client record entirely
    instead of deactivating it. This simplifies the draft upload flow - if a client
    name matches a deleted client, we create a fresh record with is_active=1.

    Returns: {"archived": True, "client_deleted": bool, "client_id": str}
    """
    with connect() as db:
        # Get the agreement and client info
        agreement = db.execute(
            "SELECT client_id, agreement_type FROM agreements WHERE id=?", (agreement_id,)
        ).fetchone()
        if not agreement:
            raise ValueError("Agreement not found.")

        client_id = agreement["client_id"]
        agreement_type = agreement["agreement_type"]

        # Archive the agreement
        db.execute(
            "UPDATE agreements SET is_active=0, status='archived', update_comment=?, uploaded_by=? WHERE id=?",
            (f"Deleted by {actor}", actor, agreement_id)
        )

        # Check if client has any other active agreements (MSA or MLA)
        active_count = db.execute(
            "SELECT COUNT(*) FROM agreements WHERE client_id=? AND is_active=1",
            (client_id,)
        ).fetchone()[0]

        client_deleted = False
        if active_count == 0:
            remaining_agreements = db.execute(
                "SELECT COUNT(*) FROM agreements WHERE client_id=? AND status!='archived'",
                (client_id,),
            ).fetchone()[0]
            if remaining_agreements == 0:
                # Preserve the client and its related records while any draft or
                # other non-archived agreement still references it.
                db.execute("DELETE FROM billing_documents WHERE client_id=?", (client_id,))
                db.execute("DELETE FROM audit_findings WHERE client_id=?", (client_id,))
                db.execute("DELETE FROM pricing_components WHERE client_id=?", (client_id,))
                db.execute("DELETE FROM pricing_approval_requests WHERE client_id=?", (client_id,))
                db.execute(
                    "DELETE FROM agreements WHERE client_id=? AND status='archived'",
                    (client_id,),
                )
                db.execute("DELETE FROM clients WHERE id=?", (client_id,))
                client_deleted = True

        return {
            "archived": True,
            "client_deleted": client_deleted,
            "client_id": client_id
        }
