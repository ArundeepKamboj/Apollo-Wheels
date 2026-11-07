"""Discover and run Python tests beside each service and shared code area."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
TEST_FOLDERS = (
    ROOT / "tests",
    ROOT / "services" / "tests",
    ROOT / "services" / "contract_service" / "tests",
    ROOT / "services" / "pricing_service" / "tests",
    ROOT / "services" / "billing_service" / "tests",
    ROOT / "src" / "apollo_wheels_mvp" / "tests",
    ROOT / "frontend" / "tests",
    ROOT / "scripts" / "tests",
)


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for folder in TEST_FOLDERS:
        suite.addTests(loader.discover(str(folder)))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
