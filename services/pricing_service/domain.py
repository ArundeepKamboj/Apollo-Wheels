"""Pricing API/domain module with four-eyes activation and pricing-owned records."""

from __future__ import annotations

import json
import os
import uuid
from datetime import date
from urllib.error import URLError
from services.service_client import open_service_url

from apollo_wheels_mvp.storage import connect


def list_client_pricing(client_id: str) -> dict[str, object]:
    with connect() as db:
        requests = db.execute(
            "SELECT * FROM pricing_approval_requests WHERE client_id=? ORDER BY version DESC", (client_id,)
        ).fetchall()
        components = db.execute(
            """SELECT pc.*, par.status AS request_status, par.version, par.initiated_by, par.approved_by,
                      par.approved_at, par.created_at AS request_created_at
               FROM pricing_components pc JOIN pricing_approval_requests par ON par.id=pc.approval_request_id
               WHERE pc.client_id=? ORDER BY par.version DESC, pc.service_name, pc.component_name""",
            (client_id,),
        ).fetchall()
    return {"requests": [dict(row) for row in requests], "components": [dict(row) for row in components]}


def submit_pricing(client_id: str, agreement_ids: list[str], components: list[dict[str, object]], initiated_by: str) -> dict[str, object]:
    if not agreement_ids or not components:
        raise ValueError("Add at least one agreement and one pricing component before requesting approval.")
    contract_api = os.getenv("CONTRACT_API_URL", "http://127.0.0.1:8001")
    try:
        with open_service_url(f"{contract_api}/api/clients/{client_id}", "pricing-service", "AUTH_PRICING_SERVICE_SECRET") as response:
            client = json.loads(response.read().decode("utf-8"))
        with open_service_url(f"{contract_api}/api/clients/{client_id}/agreements", "pricing-service", "AUTH_PRICING_SERVICE_SECRET") as response:
            agreements = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError("Pricing could not reach the Contract API to validate the client and agreement references.") from exc
    if not client:
        raise ValueError("Client not found.")
    agreement_map = {row["id"]: row["agreement_type"] for row in agreements if row["id"] in agreement_ids}
    if len(agreement_map) != len(set(agreement_ids)):
        raise ValueError("Every pricing component must reference an agreement for this client.")
    with connect() as db:
        version = db.execute(
            "SELECT COALESCE(MAX(version),0)+1 FROM pricing_approval_requests WHERE client_id=?", (client_id,)
        ).fetchone()[0]
        request_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO pricing_approval_requests
            (id,client_id,agreement_ids_json,version,status,initiated_by,effective_from)
            VALUES (?,?,?,?,?,?,?)""",
            (request_id, client_id, json.dumps(agreement_ids), version, "pending_approval", initiated_by,
             str(date.today())),
        )
        for item in components:
            agreement_id = str(item.get("agreement_id", ""))
            agreement_type = agreement_map.get(agreement_id)
            if not agreement_type:
                raise ValueError("Each pricing component needs a selected client agreement.")
            amount = float(item.get("amount", 0))
            quantity = float(item.get("quantity", 1))
            if amount < 0 or quantity < 0:
                raise ValueError("Amount and quantity cannot be negative.")
            db.execute(
                """INSERT INTO pricing_components
                (id,approval_request_id,client_id,agreement_id,agreement_type,billing_stream,service_code,service_name,
                 component_code,component_name,charge_type,amount,currency,rate_unit,quantity,billing_frequency,
                 billing_day,terms_json,effective_from,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending_approval')""",
                (str(uuid.uuid4()), request_id, client_id, agreement_id, agreement_type,
                 str(item.get("billing_stream", "SERVICE")), str(item["service_code"]), str(item["service_name"]),
                 str(item.get("component_code", "recurring")), str(item.get("component_name", "Recurring charge")),
                 str(item.get("charge_type", "recurring")), amount, str(item.get("currency", "USD")),
                 str(item.get("rate_unit", "vehicle_month")), quantity, str(item.get("billing_frequency", "monthly")),
                 item.get("billing_day"), json.dumps(item.get("terms", {})), str(item.get("effective_from", date.today())),
                 ),
            )
    return {"id": request_id, "client_id": client_id, "version": version, "status": "pending_approval"}


def approve_pricing(request_id: str, approver: str) -> dict[str, object]:
    with connect() as db:
        request = db.execute("SELECT * FROM pricing_approval_requests WHERE id=?", (request_id,)).fetchone()
        if request is None:
            raise ValueError("Pricing approval request not found.")
        if request["status"] != "pending_approval":
            raise ValueError("This pricing request is no longer awaiting approval.")
        if request["initiated_by"] == approver:
            raise ValueError("Four-eyes control: the initiator cannot approve their own pricing request.")
        # Retain previous records as historical versions, while marking only the latest as active.
        db.execute(
            "UPDATE pricing_approval_requests SET status='superseded' WHERE client_id=? AND status='active'",
            (request["client_id"],),
        )
        db.execute(
            "UPDATE pricing_components SET status='superseded' WHERE client_id=? AND status='active'",
            (request["client_id"],),
        )
        db.execute(
            "UPDATE pricing_approval_requests SET status='active',approved_by=?,approved_at=CURRENT_TIMESTAMP WHERE id=?",
            (approver, request_id),
        )
        db.execute("UPDATE pricing_components SET status='active' WHERE approval_request_id=?", (request_id,))
        for agreement_id in json.loads(request["agreement_ids_json"]):
            db.execute("UPDATE agreements SET status='active' WHERE id=?", (agreement_id,))
    return {"id": request_id, "client_id": request["client_id"], "status": "active", "approved_by": approver}
