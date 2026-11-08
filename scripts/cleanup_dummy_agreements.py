"""Remove dummy test agreements from the database and delete generated PDFs.

Usage:
    uv run python scripts/cleanup_dummy_agreements.py [--config config/local.env]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Environment file whose APOLLO_DB_PATH to clean.")
    args = parser.parse_args()

    config_path = (ROOT / args.config) if args.config else ROOT / "config" / "local.env"
    settings = load_env(config_path)
    db_path = ROOT / settings.get("APOLLO_DB_PATH", "data/apollo_wheels.db")
    if not db_path.is_file():
        print(f"Database not found at {db_path}; nothing to clean.")
        return 0

    sys.path.insert(0, str(ROOT / "src"))
    from apollo_wheels_mvp.storage import connect  # noqa: E402

    dummy_ids = ("C-9001", "C-9002")
    with connect() as db:
        agreements = db.execute(
            "SELECT id, file_path FROM agreements WHERE client_id IN (?,?)", dummy_ids
        ).fetchall()
        for row in agreements:
            db.execute("DELETE FROM agreements WHERE id=?", (row["id"],))
            print(f"  deleted agreement {row['id']}")
        db.commit()

    # Delete the generated PDF files (keep the seeded test_uploads/Test_Client files).
    folder = ROOT / "samples" / "test_uploads"
    for client_id, client_name, prefix in (("C-9001", "Apex Transport", "apex"),
                                           ("C-9002", "Coastal Hauling", "coastal")):
        for kind in ("msa", "mla"):
            path = folder / f"{prefix}_{kind}_v1.pdf"
            if path.is_file():
                path.unlink()
                print(f"  removed {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())