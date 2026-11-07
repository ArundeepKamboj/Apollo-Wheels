"""Shared request-audit writer; service business records remain service-owned."""

import os
import sqlite3
import uuid
from pathlib import Path


def record_request(service: str, actor_type: str, actor_id: str | None, action: str,
                   resource: str, status: int, request_id: str) -> None:
    audit_dir = Path(os.getenv("APOLLO_AUDIT_DIR", "data/audit"))
    if not audit_dir.is_absolute():
        audit_dir = Path(__file__).resolve().parents[1] / audit_dir
    audit_dir.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(audit_dir / f"{service}.sqlite")
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY, service_name TEXT NOT NULL, actor_type TEXT NOT NULL,
            actor_id TEXT, action TEXT NOT NULL, resource TEXT NOT NULL,
            status_code INTEGER NOT NULL, request_id TEXT NOT NULL,
            occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_audit_service_time ON audit_events(service_name, occurred_at)")
        db.execute(
            """INSERT INTO audit_events
               (id,service_name,actor_type,actor_id,action,resource,status_code,request_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), service, actor_type, actor_id, action, resource, status, request_id),
        )
        db.commit()
    finally:
        db.close()
