# UI tests

Browser tests live beside the frontend in `frontend/tests/` and use Playwright. They cover the overview, contract review and role behavior, upload validation, Finance four-eyes pricing, billing PDF ingestion/history filtering, the invoice-history permission, and an API failure state.

Run the Python and UI suites separately:

```powershell
uv run python scripts/run_tests.py
cd frontend
npm ci
npx playwright install chromium
npm run test:ui
```

The Playwright config starts an isolated local stack from `config/test.env.example`. Test database and generated PDFs stay under the ignored `data/test/` directory. UI tests mutate this disposable dataset. Do not point the test config at local demo or production data.
