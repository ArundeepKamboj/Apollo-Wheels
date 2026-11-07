# Apollo Wheels Contract & Billing MVP

Internal prototype for contract review, Finance pricing setup, four-eyes activation, billing PDF ingestion, and service-level billing audit/history.

## Run the full local stack with one command

Requires Python 3.14+ and `uv` for the current local environment.

```powershell
uv run python scripts/run_local.py
```

`uv run` syncs the locked dependencies on first use; subsequent runs use the same command.

Open `http://127.0.0.1:5173`. The runner starts the frontend, Auth service, API Gateway, and separate Contract, Pricing, and Billing APIs on local ports. The browser sends business API requests through the gateway; backend service ports also require JWTs. The runner stops all child processes with Ctrl+C. Service logs are written to `logs/`.

## Swagger / OpenAPI

Each FastAPI application publishes Swagger UI at `/docs` and its schema at `/openapi.json`. With the default local configuration, the endpoints are:

- API Gateway: `http://127.0.0.1:8000/docs`
- Auth: `http://127.0.0.1:8004/docs`
- Contract: `http://127.0.0.1:8001/docs`
- Pricing: `http://127.0.0.1:8002/docs`
- Billing: `http://127.0.0.1:8003/docs`

Use the service-specific Swagger page to inspect that service's API. The API Gateway page documents the gateway routes; it does not merge the downstream OpenAPI schemas. Authenticate with a local user token in Swagger's Authorize control before calling protected business routes.

The repository includes named, selectable-text sample PDFs under `samples/`; see [samples/README.md](samples/README.md) for the document list and scenarios. The project data model, every persisted/sample field, assumptions, LLM trade-offs, and current MVP coverage/gaps are documented in [docs/](docs/README.md). The first launch also creates a local SQLite database and runtime copies under `data/`. Runtime data is git-ignored. Regenerate the checked-in sample set with `uv run python scripts/generate_sample_documents.py`. Copy `config/local.env.example` to `config/local.env` to change local ports, storage paths, or LLM settings. Separate test and production templates are in `config/`.

Run all UI, HTTP integration, service-local Python, and shared Python tests and generate service-level coverage with `./scripts/run_all_tests.ps1`. The current report is [reports/SERVICE_TEST_COVERAGE.md](reports/SERVICE_TEST_COVERAGE.md), with line-by-line HTML details in [reports/coverage/index.html](reports/coverage/index.html).

Sign in with `testfinance` / `FinanceDemo!2026`, `testfinance2` / `FinanceSecondDemo!2026`, or `teststructurer` / `StructuringDemo!2026`. Use the first Finance account to prepare pricing and the second to approve it. These are public local-demo credentials only. See [the high-level architecture and authentication notes](docs/HIGH_LEVEL_ARCHITECTURE.md) for the OAuth2/JWT flow, service accounts, API Gateway, role ownership, and future OIDC approach.

## Current architecture

- `frontend/` contains the UI independently from backend services.
- `services/contract_service`, `services/pricing_service`, and `services/billing_service` each have their own FastAPI entrypoint and domain module.
- `src/apollo_wheels_mvp/` contains shared PDF, catalogue, synthetic fixture, and local persistence utilities.
- The MVP APIs communicate over REST. The first local implementation uses a shared SQLite file for a simple demo; the domain ownership and API boundaries allow service-owned databases to be introduced when deployment is split.
- Source PDFs live in a local file store; the database keeps file references, workflow metadata, extracted terms, pricing components, and normalized billing lines. Flexible contract/pricing attributes are held in JSON payloads.
- `scripts/run_local.py` starts the full stack with one command. `config/` holds environment-specific templates; local overrides and secrets are ignored.
- `tests/` separates unit, integration, and fixture locations. Run the current test suite with `uv run python -m unittest discover -s tests -v`.

## Code style

Keep the implementation small and direct. Use readable names, short functions, and ordinary Python and JavaScript instead of clever abstractions or compressed source. Add a dependency or another layer only when a confirmed requirement needs it. Keep each service's logic in its own domain module and shared helpers limited to code the services actually reuse.

The sample PDF format contains explicit synthetic rows, so deterministic parsing is the default. An optional Ollama agreement-extraction path is available with `LLM_PROVIDER=ollama`; the model is not downloaded automatically. See [docs/LLM_TRADEOFFS.md](docs/LLM_TRADEOFFS.md) for the hardware fit and evaluation plan. Neither path is a production accuracy claim. OCR for scanned PDFs and client-facing pricing email/PDF delivery are later roadmap items.

See [Architecture Options.md](Architecture%20Options.md) for the service topology and SQL/document-store comparison. The current storage implementation is a local MVP decision and can be adapted behind the domain boundaries if the architecture review selects a document database or hybrid production setup.


