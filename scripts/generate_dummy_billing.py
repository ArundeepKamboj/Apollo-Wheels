"""Generate sample billing PDFs for dummy test clients."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # Go up from scripts/ to project root
sys.path.insert(0, str(ROOT / "src"))

from apollo_wheels_mvp.synthetic import write_demo_invoice  # noqa: E402

# Dummy clients with IDs different from seeded clients (C-1001, C-1002)
# Use names without periods to avoid filesystem issues
DUMMY_CLIENTS = [
    ("C-9001", "Apex Transport LP"),
    ("C-9002", "Coastal Hauling LLC"),
]


def safe_folder_name(name: str) -> str:
    """Convert client name to safe folder name."""
    return name.replace(" ", "_").replace(".", "").replace(",", "")


def main() -> None:
    for client_id, client_name in DUMMY_CLIENTS:
        print(f"Generating billing for {client_name} ({client_id}):")

        # Create client-specific billing folder with service/lease subdirs
        # Use absolute path to avoid confusion
        billing_folder = (ROOT / "samples" / "billing" / safe_folder_name(client_name))

        # Service invoices for all months
        for month, start, end in [
            ("JAN", "2026-01-01", "2026-01-31"),
            ("FEB", "2026-02-01", "2026-02-28"),
            ("MAR", "2026-03-01", "2026-03-31"),
        ]:
            service_folder = billing_folder / "service"
            invoice = write_demo_invoice(service_folder, client_id, client_name, start, end,
                                         f"INV-{client_id}-{month}-SERVICE", "SERVICE")
            print(f"  {invoice['filename']}")

        # Lease invoices
        for month, start, end in [
            ("JAN", "2026-01-01", "2026-01-31"),
            ("FEB", "2026-02-01", "2026-02-28"),
            ("MAR", "2026-03-01", "2026-03-31"),
        ]:
            lease_folder = billing_folder / "lease"
            invoice = write_demo_invoice(lease_folder, client_id, client_name, start, end,
                                         f"INV-{client_id}-{month}-LEASE", "LEASE")
            print(f"  {invoice['filename']}")


if __name__ == "__main__":
    main()