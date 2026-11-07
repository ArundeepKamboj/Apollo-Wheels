# Test structure and execution

## Test locations

- `services/contract_service/tests/` â€” Contract API/domain tests colocated with the service.
- `services/pricing_service/tests/` â€” Pricing API/domain and four-eyes workflow tests colocated with the service.
- `services/billing_service/tests/` â€” Billing upload, persistence, history, audit, and API/domain tests colocated with the service.
- `services/tests/` â€” shared service identity and error helpers.
- `tests/integration/` â€” cross-service workflow tests plus real HTTP API integration tests driven by Playwright.
- `src/apollo_wheels_mvp/tests/` â€” shared PDF parsing, catalog, storage, seed, and synthetic document tests.
- `frontend/tests/` â€” frontend structure tests, browser E2E scenarios, and a detailed UI edge-case checklist.

## Run all tests and build the coverage report

From the project root:

```powershell
./scripts/run_all_tests.ps1
```

The UI suite starts an isolated stack using `config/test.env.example` on ports 5174 and 8101â€“8103. Its database and generated files are under ignored `data/test/`. Python tests use disposable SQLite folders and do not mutate the local demo database.

This runs browser UI and HTTP integration scenarios first, then all Python service, shared-module, and integration tests and refreshes the report. Node.js/npm and `uv` must be installed. The steps can also be run separately with `npm --prefix frontend run test:ui` and `uv run --group dev python scripts/run_coverage.py`.

The Python step writes:

- `reports/SERVICE_TEST_COVERAGE.md` â€” test counts by service, line coverage by service/file, and missing executable line numbers.
- `reports/coverage/index.html` â€” detailed HTML coverage.
- `reports/ui-results.json` â€” browser test results used by the Markdown report when it is generated after the UI run.

Coverage measures executed Python lines and branches. Playwright scenarios are separately counted; they are not JavaScript line coverage. Full scenario intentâ€”including documented known gapsâ€”is in [the UI cases](../frontend/tests/MANUAL_CASES.md).

## Coverage intent

Tests exercise valid paths, validation failures, unknown records, role restrictions, corrupt/unsupported PDFs, API unavailability, approval boundaries, history filters, audit findings, and local browser workflows. Keep service behavior tests inside each service directory. Keep cross-service HTTP tests in this directory. Add cases for every changed behavior and new edge case; the suite is a maintained set, not a claim that arbitrary future behavior is automatically covered.

