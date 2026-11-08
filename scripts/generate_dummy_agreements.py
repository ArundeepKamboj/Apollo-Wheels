"""Generate selectable-text sample agreement PDFs for dummy test clients.

These files are for manual upload testing only. They are NOT loaded by the
seed, so the demo database keeps only the two approved seeded clients
(Northstar Fleet Services, Blue River Logistics). After testing, delete the
dummy rows and the generated PDFs with `scripts/cleanup_dummy_agreements.py`.

Usage:
    uv run python scripts/generate_dummy_agreements.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apollo_wheels_mvp.synthetic import write_demo_agreements  # noqa: E402

DUMMY_CLIENTS = [
    ("C-9001", "Apex Transport", "apex"),
    ("C-9002", "Coastal Hauling", "coastal"),
]


def main() -> None:
    folder = ROOT / "samples" / "test_uploads"
    for client_id, client_name, prefix in DUMMY_CLIENTS:
        items = write_demo_agreements(folder, client_id, client_name, prefix)
        for item in items:
            print(f"  {item['filename']}")


if __name__ == "__main__":
    main()