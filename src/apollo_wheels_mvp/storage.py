"""Local MVP operational database. PDFs live in the file store; pricing owns its records."""

from __future__ import annotations

import sqlite3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DOCUMENT_DIR = Path(os.getenv("APOLLO_DOCUMENT_DIR", str(DATA_DIR / "documents")))
DATABASE_PATH = Path(os.getenv("APOLLO_DB_PATH", str(DATA_DIR / "apollo_wheels.db")))


class ClosingConnection(sqlite3.Connection):
    """Make ``with connect()`` commit or roll back and then release the file."""

    def __exit__(self, exception_type, exception, traceback):
        try:
            return super().__exit__(exception_type, exception, traceback)
        finally:
            self.close()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH, timeout=15, factory=ClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    return db


def initialize() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                include_history_on_invoice INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS agreements (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id),
                agreement_type TEXT NOT NULL CHECK (agreement_type IN ('MSA','MLA')),
                version_label TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                effective_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'uploaded',
                uploaded_by TEXT NOT NULL,
                extracted_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pricing_approval_requests (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id),
                agreement_ids_json TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending_approval','active','superseded','rejected')),
                initiated_by TEXT NOT NULL,
                approved_by TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                approved_at TEXT,
                effective_from TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pricing_components (
                id TEXT PRIMARY KEY,
                approval_request_id TEXT NOT NULL REFERENCES pricing_approval_requests(id),
                client_id TEXT NOT NULL REFERENCES clients(id),
                agreement_id TEXT NOT NULL REFERENCES agreements(id),
                agreement_type TEXT NOT NULL,
                billing_stream TEXT NOT NULL CHECK (billing_stream IN ('SERVICE','LEASE')),
                service_code TEXT NOT NULL,
                service_name TEXT NOT NULL,
                component_code TEXT NOT NULL,
                component_name TEXT NOT NULL,
                charge_type TEXT NOT NULL CHECK (charge_type IN ('recurring','one_time')),
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                rate_unit TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 1,
                billing_frequency TEXT NOT NULL,
                billing_day TEXT,
                terms_json TEXT NOT NULL DEFAULT '{}',
                effective_from TEXT NOT NULL,
                effective_to TEXT,
                status TEXT NOT NULL CHECK (status IN ('pending_approval','active','superseded')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_pricing_client_service
                ON pricing_components(client_id, service_code, effective_from, status);

            CREATE TABLE IF NOT EXISTS billing_documents (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id),
                invoice_number TEXT NOT NULL,
                billing_stream TEXT NOT NULL CHECK (billing_stream IN ('SERVICE','LEASE','COMBINED')),
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ingested',
                uploaded_by TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS billing_lines (
                id TEXT PRIMARY KEY,
                billing_document_id TEXT NOT NULL REFERENCES billing_documents(id) ON DELETE CASCADE,
                agreement_id TEXT REFERENCES agreements(id),
                agreement_type TEXT NOT NULL,
                billing_stream TEXT NOT NULL,
                service_code TEXT NOT NULL,
                service_name TEXT NOT NULL,
                component_code TEXT NOT NULL,
                component_name TEXT NOT NULL,
                charge_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                rate REAL NOT NULL,
                rate_unit TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD'
            );

            CREATE TABLE IF NOT EXISTS audit_findings (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id),
                service_code TEXT,
                service_name TEXT,
                component_code TEXT,
                component_name TEXT,
                billing_stream TEXT,
                period_start TEXT,
                category TEXT,
                severity TEXT,
                issue TEXT NOT NULL,
                explanation TEXT,
                contract_rate REAL,
                configured_rate REAL,
                billed_rate REAL,
                billed_amount REAL,
                contract_basis TEXT,
                pricing_basis TEXT,
                rate_unit TEXT,
                computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_audit_findings_client
                ON audit_findings(client_id, computed_at DESC);

            """
        )
