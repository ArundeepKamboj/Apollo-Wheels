"""Shared isolated database setup for service-owned tests."""

from __future__ import annotations

import tempfile
import os
from pathlib import Path

from apollo_wheels_mvp import seed, storage
from services.billing_service import domain as billing_domain
from services.contract_service import domain as contract_domain


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MemoryUpload:
    """Tiny async upload double that avoids OS event-loop/socket requirements."""

    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content = content

    async def read(self):
        return self.content


def run_upload(coroutine):
    """Run upload coroutines whose in-memory read completes immediately."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()
    raise AssertionError("The in-memory upload coroutine unexpectedly performed asynchronous I/O.")


def setup_demo(test_case):
    """Point all services at a disposable database and seed known demo rows."""
    data_root = PROJECT_ROOT / "data"
    data_root.mkdir(exist_ok=True)
    folder = tempfile.TemporaryDirectory(dir=data_root)
    test_case.addCleanup(folder.cleanup)
    root = Path(folder.name)
    os.environ.setdefault("AUTH_JWT_SECRET", "apollo-local-test-signing-key-change-before-sharing")
    os.environ.setdefault("AUTH_ACCOUNTS_FILE", str(PROJECT_ROOT / "config" / "demo_accounts.json"))
    os.environ.setdefault("AUTH_PRICING_SERVICE_SECRET", "pricing-demo-secret")
    os.environ.setdefault("AUTH_BILLING_SERVICE_SECRET", "billing-demo-secret")
    os.environ.setdefault("AUTH_API_URL", "http://127.0.0.1:8004")
    os.environ["APOLLO_AUDIT_DIR"] = str(root / "audit")

    paths = (
        (storage, "DATA_DIR", root),
        (storage, "DATABASE_PATH", root / "test.db"),
        (storage, "DOCUMENT_DIR", root / "documents"),
        (seed, "DOCUMENT_DIR", root / "documents"),
        (contract_domain, "DOCUMENT_DIR", root / "documents"),
        (billing_domain, "DOCUMENT_DIR", root / "documents"),
    )
    for module, name, value in paths:
        original = getattr(module, name)
        setattr(module, name, value)
        test_case.addCleanup(setattr, module, name, original)

    storage.initialize()
    seed.seed_demo_data()
    return root
