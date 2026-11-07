"""Run Python tests and generate service-level line/branch coverage reports."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

try:
    import coverage
except ImportError:
    print("Coverage is not installed. Run: uv sync --group dev", file=sys.stderr)
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
REPORTS = ROOT / "reports"
TEST_FOLDERS = (
    ROOT / "tests",
    ROOT / "services" / "tests",
    ROOT / "services" / "contract_service" / "tests",
    ROOT / "services" / "pricing_service" / "tests",
    ROOT / "services" / "billing_service" / "tests",
    ROOT / "services" / "auth_service" / "tests",
    ROOT / "services" / "api_gateway" / "tests",
    ROOT / "src" / "apollo_wheels_mvp" / "tests",
    ROOT / "frontend" / "tests",
    ROOT / "scripts" / "tests",
)


def discover_tests() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for folder in TEST_FOLDERS:
        suite.addTests(loader.discover(str(folder)))
    return suite


def collect_cases(suite, output: list[unittest.TestCase]) -> None:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            collect_cases(item, output)
        else:
            output.append(item)


def sum_files(files: dict, prefix: str) -> tuple[int, int, int]:
    matching = [data["summary"] for name, data in files.items() if name.replace("\\", "/").startswith(prefix)]
    statements = sum(item["num_statements"] for item in matching)
    covered = sum(item["covered_lines"] for item in matching)
    missing = sum(item["missing_lines"] for item in matching)
    return statements, covered, missing


def percent(covered: int, statements: int) -> str:
    return f"{covered / statements * 100:.1f}%" if statements else "n/a"


def write_markdown_report(result: unittest.TestResult, cases: list[unittest.TestCase], coverage_data: dict) -> None:
    buckets = {
        "Contract service": lambda name: "test_contract_" in name or "contract_service.tests" in name,
        "Pricing service": lambda name: "test_pricing_" in name or "pricing_service.tests" in name,
        "Billing service": lambda name: "test_billing_" in name or "billing_service.tests" in name,
        "Auth service": lambda name: "auth_service.tests" in name or name.startswith("test_auth_"),
        "API gateway": lambda name: "api_gateway.tests" in name or name.startswith("test_gateway_"),
        "Shared services": lambda name: name.startswith("test_common"),
        "Shared data / documents": lambda name: "test_shared_data_and_documents" in name or name.startswith("unit."),
        "Cross-service integration": lambda name: "integration." in name,
        "Frontend structure": lambda name: "test_frontend_contract" in name,
        "Build tooling": lambda name: "scripts.tests" in name or name.startswith("test_scripts"),
    }
    suite_rows = []
    for label, matches in buckets.items():
        count = sum(1 for case in cases if matches(case.__class__.__module__))
        if count:
            suite_rows.append(f"| {label} | {count} |")

    files = coverage_data.get("files", {})
    service_groups = (
        ("Contract service", "services/contract_service/"),
        ("Pricing service", "services/pricing_service/"),
        ("Billing service", "services/billing_service/"),
        ("Auth service", "services/auth_service/"),
        ("API gateway", "services/api_gateway/"),
        ("Shared service helpers", "services/common.py"),
        ("Shared domain/PDF/data modules", "src/apollo_wheels_mvp/"),
        ("Build scripts", "scripts/"),
    )
    coverage_rows = []
    file_rows = []
    for label, prefix in service_groups:
        statements, covered, missing = sum_files(files, prefix)
        coverage_rows.append(f"| {label} | {statements} | {covered} | {missing} | {percent(covered, statements)} |")
        for filename, data in sorted(files.items()):
            normalized = filename.replace("\\", "/")
            if normalized.startswith(prefix):
                summary = data["summary"]
                uncovered = ", ".join(map(str, data.get("missing_lines", []))) or "—"
                file_rows.append(f"| `{normalized}` | {summary['num_statements']} | {summary['covered_lines']} | {summary['missing_lines']} | {summary['percent_covered']:.1f}% | {uncovered} |")

    total = coverage_data.get("totals", {})
    statements = total.get("num_statements", 0)
    covered = total.get("covered_lines", 0)
    ui_spec = ROOT / "frontend" / "tests" / "ui_workflows.spec.js"
    api_spec = ROOT / "tests" / "integration" / "api_services.spec.js"
    browser_cases = count_playwright_cases(ui_spec) + count_playwright_cases(api_spec)
    ui_result_path = REPORTS / "ui-results.json"
    browser_status = "Not run in this report generation" if not ui_result_path.exists() else read_ui_status(ui_result_path)

    REPORTS.mkdir(exist_ok=True)
    report = [
        "# Service-level test coverage report", "",
        f"Generated from {result.testsRun} Python test cases. Result: **{'PASS' if result.wasSuccessful() else 'FAIL'}**; failures: {len(result.failures)}; errors: {len(result.errors)}.",
        "", "Python coverage measures executed backend/shared Python statements. Browser scenario counts are reported separately; they are not JavaScript line coverage.",
        "", "## Test cases by area", "", "| Area | Cases |", "|---|---:|", *suite_rows,
        f"| Playwright HTTP/UI scenarios | {browser_cases} |", "",
        f"Latest Playwright execution: **{browser_status}**. Browser results are written to ignored `reports/ui-results.json` by the UI test runner.",
        "", "## Python line coverage by service", "", "| Service/module | Statements | Covered | Missing | Coverage |", "|---|---:|---:|---:|---:|", *coverage_rows,
        f"| **Total** | **{statements}** | **{covered}** | **{total.get('missing_lines', 0)}** | **{percent(covered, statements)}** |", "",
        "## Files and uncovered executable lines", "", "| File | Statements | Covered | Missing | Coverage | Missing line numbers |", "|---|---:|---:|---:|---:|---|", *file_rows,
        "", "HTML detail report: [`coverage/index.html`](coverage/index.html).", "",
        "Coverage is evidence about tests executed, not proof that every business requirement is correct. Review uncovered lines and the UI edge-case matrix alongside this report.", "",
    ]
    (REPORTS / "SERVICE_TEST_COVERAGE.md").write_text("\n".join(report), encoding="utf-8")


def count_playwright_cases(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("test('"))


def read_ui_status(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stats = data.get("stats", {})
        return f"{stats.get('expected', 0)} passed, {stats.get('unexpected', 0)} failed, {stats.get('skipped', 0)} skipped"
    except (OSError, json.JSONDecodeError):
        return "Result JSON could not be read"


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    coverage_run = coverage.Coverage(config_file=str(ROOT / ".coveragerc"), data_file=str(REPORTS / ".coverage"))
    coverage_run.start()
    suite = discover_tests()
    cases: list[unittest.TestCase] = []
    collect_cases(suite, cases)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    coverage_run.stop()
    coverage_run.save()
    coverage_run.json_report(outfile=str(REPORTS / "coverage.json"), pretty_print=True)
    coverage_run.html_report(directory=str(REPORTS / "coverage"))
    coverage_data = json.loads((REPORTS / "coverage.json").read_text(encoding="utf-8"))
    write_markdown_report(result, cases, coverage_data)
    print(f"Service coverage report: {REPORTS / 'SERVICE_TEST_COVERAGE.md'}")
    print(f"HTML coverage detail: {REPORTS / 'coverage' / 'index.html'}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
