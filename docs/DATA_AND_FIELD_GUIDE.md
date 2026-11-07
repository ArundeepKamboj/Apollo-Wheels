# Data, database, sample, and code field guide

This guide describes the fields the MVP currently stores or sends, and why each exists. The data model is intentionally small. PDFs remain files; extracted facts and searchable billing lines are stored as structured records. Terms that vary by agreement are kept in JSON so the schema does not need one database column for every possible clause.

## 1. Where data lives

### Current local database

The MVP creates one SQLite file at `data/apollo_wheels.db` by default (`APOLLO_DB_PATH` can change this). The Contract, Pricing, and Billing services are separate processes and APIs, but currently use this shared file for the local demo. Tables are grouped by owner: client/agreement tables support Contract; approval/pricing tables support Pricing; billing document/line tables support Billing/Audit. This is a local convenience, not a claim that the services share a database in the target architecture.

SQLite was selected for a no-server local demo and transactions. Flexible extracted terms and price-specific attributes use JSON text (`extracted_json`, `terms_json`, `agreement_ids_json`); source PDFs are not stored in SQL. A later deployment can move PDF files to object storage and give each service its own database.

### Document files

- Checked-in demo sources: `samples/contracts/<client>/` and `samples/billing/<client>/<service-or-lease>/`.
- Runtime uploads and seeded copies: `data/documents/` by default (`APOLLO_DOCUMENT_DIR` changes it).
- Database rows store `file_path` and `filename`; the PDF bytes remain in the file system.
- `data/` is generated runtime state and is ignored by Git. `samples/` is intentional project material and is versioned.

### Per-service audit databases

Each running service writes an audit trail to its own SQLite file under `data/audit/` by default: `auth.sqlite`, `gateway.sqlite`, `contract.sqlite`, `pricing.sqlite`, and `billing.sqlite`. The common audit writer creates an `audit_events` table containing event ID, owner service, actor type/ID, HTTP action, resource path, status code, request ID, and timestamp. It does not store credentials, request bodies, or query strings. These are local MVP audit records; production should retain durable, service-owned audit records and export operational telemetry separately.

Business records still share one physical SQLite database for the MVP. Tables are grouped by owner and queried by the service that owns them. The audit stores are already physically service-specific; business database ownership can be split after the cross-service workflow/data boundaries are reviewed.

### Current seeded demo rows

The freshly initialized local database contains 3 clients: Northstar Fleet Services and Blue River Logistics are the two full billing demos; Test Client (`C-TEST`) is intentionally empty and is provided for uploading the standalone MSA/MLA test PDFs. The database has 4 seeded agreements, 2 approved pricing versions, 22 active pricing components, 12 billing documents, and 62 normalized billing lines. Each full demo client has nine subscribed recurring services, one Fuel setup charge, one monthly lease charge, and three months of SERVICE plus LEASE invoices. The February invoices include one RR rate mismatch per full demo client. Seeding is idempotent and adds the empty Test Client to existing local databases.

## 2. Database schema and purpose of every column

All IDs are strings (UUIDs for uploaded/workflow/line records; stable `C-...` values for synthetic clients). Dates use ISO `YYYY-MM-DD`; timestamps use SQLite's timestamp text format unless noted.

### `clients` — client identity and one Finance preference

| Column | Why it exists |
|---|---|
| `id` | Stable primary key used to link agreements, pricing, and billing for one client. |
| `name` | Human-readable client label for selectors and reports. |
| `include_history_on_invoice` | Finance-controlled preference requested for a future generated invoice; the UI stores it now, but client-facing PDF/email generation is not implemented. |
| `created_at` | Records when a client row was created; useful for support and audit context. |

### `agreements` — agreement metadata, file location, and extracted terms

| Column | Why it exists |
|---|---|
| `id` | Stable agreement identifier used by pricing components and billing lines. |
| `client_id` | Links MSA/MLA and their service/lease data to the same client. |
| `agreement_type` | Keeps MSA and MLA distinct; constrained to `MSA` or `MLA`. |
| `version_label` | Preserves the displayed agreement version, such as `1.0`, for review and pricing references. |
| `filename` | Original or generated filename displayed to internal users. |
| `file_path` | Location of the PDF bytes in local document storage. |
| `effective_date` | Start date parsed from the agreement; used as the default effective date for derived pricing. |
| `status` | Simple lifecycle label used by the UI (`review`, `active`, or initial `uploaded` default). It is not a complete legal approval lifecycle. |
| `uploaded_by` | Verified role and stable subject from the human bearer token, or a seed marker. |
| `extracted_json` | Editable extracted fields plus source/evidence metadata; JSON allows agreement-specific fields without adding a column per clause. |
| `created_at` | Upload/creation timestamp used to order versions and select the most recent agreement. |

### `pricing_approval_requests` — versioned four-eyes workflow

| Column | Why it exists |
|---|---|
| `id` | Identifies one proposed pricing version and links its component rows. |
| `client_id` | Scopes the version and approval flow to a client. |
| `agreement_ids_json` | Records which client agreements the pricing version was based on; kept as JSON because a version can refer to MSA, MLA, or both. |
| `version` | Increasing per-client version number for pricing history and review. |
| `status` | Workflow state: `pending_approval`, `active`, `superseded`, or `rejected`. `rejected` is reserved but a reject action is not yet implemented. |
| `initiated_by` | Finance identity that submitted the request; compared with the approver to enforce the distinct-user rule. |
| `approved_by` | Second Finance identity that approved the request; empty until approval. |
| `created_at` | Submission timestamp for the approval history. |
| `approved_at` | Approval timestamp; empty while pending. |
| `effective_from` | Date from which the submitted pricing version is intended to apply. Current UI/service derives a default date; future behavior needs business confirmation. |

### `pricing_components` — each independently priced charge

| Column | Why it exists |
|---|---|
| `id` | Identifier for one charge line/component so it can be reviewed and superseded individually. |
| `approval_request_id` | Associates the component with the version and four-eyes approval that governs it. |
| `client_id` | Supports direct client filtering and indexing without walking through request rows. |
| `agreement_id` | Shows the agreement that supports this charge. |
| `agreement_type` | Preserves whether the supporting source is MSA or MLA. |
| `billing_stream` | Separates `SERVICE` and `LEASE` billing; a later combined invoice can retain this source label. |
| `service_code` | Stable catalogue key used to compare contract, price, and bill rows. |
| `service_name` | Human-readable service label for UI/history. |
| `component_code` | Stable key for a distinct charge within a service (e.g. `monthly_per_vehicle` or `activation`). |
| `component_name` | Readable charge description shown to Finance and used in reconciliation. |
| `charge_type` | Distinguishes `recurring` charges from `one_time` charges. |
| `amount` | Numeric unit rate or fixed charge amount; quantity/rate basis is stored separately. |
| `currency` | Currency code for interpreting the amount; sample data defaults to USD. |
| `rate_unit` | Basis such as `vehicle_month` or `account`; needed to interpret a rate. |
| `quantity` | Billable quantity used with the rate (e.g. vehicle count); default is one for account charges. |
| `billing_frequency` | Recurrence cadence such as `monthly` or `one_time`. |
| `billing_day` | Optional day-of-month field for a recurring charge; nullable because not every charge has a defined billing day. |
| `terms_json` | Holds optional pricing details (e.g. lease term) without rigid columns for every charge type. |
| `effective_from` | Start date for the component. |
| `effective_to` | Optional end date for a historical component; null means no end date is recorded. |
| `status` | Component state: `pending_approval`, `active`, or `superseded`. Approval changes pending rows to active and prior rows to superseded. |
| `created_at` | Timestamp useful for version history and troubleshooting. |

### `billing_documents` — one ingested invoice PDF

| Column | Why it exists |
|---|---|
| `id` | Identifier for the uploaded billing document and parent of its line rows. |
| `client_id` | Links the invoice to the selected client. |
| `invoice_number` | Source invoice identifier for display and duplicate checks in a future iteration. Duplicate rejection is not implemented yet. |
| `billing_stream` | Marks the document as `SERVICE`, `LEASE`, or `COMBINED`; sample PDFs use separate SERVICE/LEASE documents. |
| `period_start` | First day of the covered period; supports history filters and comparisons. |
| `period_end` | Last day of the covered period; supports history filters and comparisons. |
| `filename` | Original uploaded file name. |
| `file_path` | Location of the PDF file bytes. |
| `status` | Ingestion result label, currently `ingested` for accepted documents. |
| `uploaded_by` | Verified role and stable subject from the human bearer token. |
| `created_at` | Timestamp when the invoice was ingested. |

### `billing_lines` — normalized invoice charges extracted from a PDF

| Column | Why it exists |
|---|---|
| `id` | Identifies one normalized charge line. |
| `billing_document_id` | Links the row to the source invoice; cascade delete keeps orphan lines from remaining if that document is removed. |
| `agreement_id` | Links the charge to the latest matching client agreement where possible; nullable when no agreement is available. |
| `agreement_type` | Preserves MSA/MLA source classification for display and audit. |
| `billing_stream` | Preserves SERVICE/LEASE at line level, including when documents are combined. |
| `service_code` | Catalogue key used to match the line to contract and pricing rows. |
| `service_name` | Readable service label from the statement. |
| `component_code` | Charge key used to match the billed charge to a priced component. |
| `component_name` | Human-readable component label. |
| `charge_type` | Identifies recurring versus one-time billing. |
| `quantity` | Number of units billed. |
| `rate` | Billed price per `rate_unit`; compared with active pricing. |
| `rate_unit` | Unit for the billed rate. |
| `amount` | Total line amount stated on the invoice. It is stored independently so the UI can report the source amount; multiplication consistency is not yet validated. |
| `currency` | Currency for the amount and rate; currently defaults to USD on ingestion. |

## 3. PDF sample format: every marker and field

The checked-in agreement PDFs render the clauses from the root MSA and MLA Markdown drafting templates, omitting their field guides and analysis checklists. Fictional demo parties and selected dates are populated; unavailable terms are marked `Demo assumption (review required)`. These are not approved or execution-ready legal forms. Billing PDFs use the same service/lease rates, units, and quantities as their matching sample agreements, apart from the intentional February RR discrepancy used to demonstrate audit detection. All rates and identities are invented. Documents include readable schedules, pagination, and a final appendix of exact selectable-text fixture rows. The pipe-delimited appendix makes the first parser deterministic; these are training/demo fixtures, not examples of arbitrary client language. `|` separates fields.

### MSA header fields (`KEY: VALUE`)

| Header | Meaning / reason |
|---|---|
| `CLIENT_ID` | Connects this document to the demo client row. |
| `CLIENT_NAME` | Human-readable confirmation of the client identity. |
| `AGREEMENT_ID` | Source document identifier printed in the PDF; agreement row ID is separately generated by the app for uploaded copies. |
| `AGREEMENT_TYPE` | States MSA, which tells the parser to read service and extra component rows. |
| `VERSION` | Version label retained as agreement metadata. |
| `EFFECTIVE_DATE` | Start date from which terms are treated as effective in the sample. |

### MSA service row: `SERVICE|code|name|subscribed|stream|component|rate|unit|charge_type|pricing_basis|frequency|billing_day|vehicle_count|driver_count`

| Position | Sample field | Why included |
|---:|---|---|
| 1 | `SERVICE` | Row type lets the parser distinguish service terms from headers/components. |
| 2 | `code` | Stable catalogue key used to match the same service across contract, pricing, and bill. |
| 3 | `name` | Human label displayed to users. |
| 4 | `subscribed` (`true`/`false`) | Indicates whether the client bought this catalogue service; false rows are retained to show all 13 choices. |
| 5 | `stream` (`SERVICE`) | Explicitly identifies service billing rather than lease billing. |
| 6 | `component` | Identifies the pricing component/basis, e.g. `monthly_per_vehicle` or `monthly_account_fee`. |
| 7 | `rate` | Synthetic contract rate for the component. |
| 8 | `unit` | Gives the rate basis, e.g. `vehicle_month` or `account_month`. |
| 9 | `charge_type` | Indicates recurring or one-time treatment. |
| 10 | `pricing_basis` | Identifies whether the numeric rate is a currency amount (`USD`), a percentage (`PERCENTAGE`), or basis points (`BASIS_POINTS`). This prevents a numeric 25 basis-points value from being mistaken for USD 25. |
| 11 | `frequency` | States the planned cadence, such as monthly or quarterly. |
| 12 | `billing_day` | States a simple billing-day value (for example `1`, `20`, or `last_day`); retained as text because formats can vary. |
| 13 | `vehicle_count` | Optional example fleet quantity for vehicle-based services. Blank means no count is supplied for that row. |
| 14 | `driver_count` | Optional example driver quantity for driver-based services. Blank means no count is supplied for that row. |

### MSA extra component row: `COMPONENT|service_code|component_code|display_name|charge_type|amount|unit|quantity`

| Position | Sample field | Why included |
|---:|---|---|
| 1 | `COMPONENT` | Identifies an additional charge row. |
| 2 | `service_code` (`FUEL`) | Attaches this charge to the Fuel service. |
| 3 | `component_code` (`activation`) | Stable key for this extra charge, separate from recurring Fuel rates. |
| 4 | `display_name` | Label shown to Finance (One-time setup). |
| 5 | `charge_type` (`one_time`) | Distinguishes setup fee from monthly pricing. |
| 6 | `amount` | Synthetic setup amount. |
| 7 | `unit` (`account`) | Indicates a per-account rather than per-vehicle amount. |
| 8 | `quantity` | Number of billed units, set to one for this account setup fee. |

### MLA header and lease row: `LEASE|code|name|quantity|unit|amount|term_months|effective_from|frequency|billing_day|vehicle_make|vehicle_model|engine_type|pricing_basis`

| Position | Sample field | Why included |
|---:|---|---|
| Header | `CLIENT_ID`, `CLIENT_NAME`, `AGREEMENT_ID`, `AGREEMENT_TYPE`, `VERSION`, `EFFECTIVE_DATE` | Same identity/version/effective-date purpose as the MSA; `AGREEMENT_TYPE=MLA` signals lease extraction. |
| 1 | `LEASE` | Identifies the lease charge record. |
| 2 | `code` (`LEASE-01`) | Stable lease service identifier for matching invoice and pricing. |
| 3 | `name` | Human-readable lease description. |
| 4 | `quantity` | Synthetic number of vehicles in the leased fleet. |
| 5 | `unit` (`vehicle_month`) | Rate basis for the lease. |
| 6 | `amount` | Synthetic monthly lease rate per vehicle. |
| 7 | `term_months` | Illustrative lease duration; retained in flexible terms JSON. |
| 8 | `effective_from` | Lease-specific effective date. |
| 9 | `frequency` | Illustrative billing cadence (monthly in the samples). |
| 10 | `billing_day` | Illustrative billing day. |
| 11 | `vehicle_make` | Example make to represent the vehicle detail requested for MLA extraction. |
| 12 | `vehicle_model` | Example model to represent the vehicle detail requested for MLA extraction. |
| 13 | `engine_type` | Example engine/fuel type; values are synthetic. |
| 14 | `pricing_basis` | Explains whether the numeric amount is a currency amount, percentage, or basis points. |

### Billing header fields (`KEY: VALUE`)

| Header | Meaning / reason |
|---|---|
| `CLIENT_ID`, `CLIENT_NAME` | Establish which client the invoice belongs to. Upload still associates it with the client selected in the app; the parser does not yet reject a mismatch. |
| `INVOICE_NUMBER` | Source invoice reference shown in history. |
| `BILLING_STREAM` | States SERVICE or LEASE so the document remains distinct by default. |
| `PERIOD_START`, `PERIOD_END` | Bound the invoice period for history and date filtering. |

### Billing line: `LINE|stream|service_code|service_name|component_code|charge_type|quantity|rate|rate_unit|amount`

| Position | Sample field | Why included |
|---:|---|---|
| 1 | `LINE` | Identifies a billable line row. |
| 2 | `stream` | Separates SERVICE from LEASE during reconciliation. |
| 3 | `service_code` | Matches a catalogue service/lease to contract and pricing. |
| 4 | `service_name` | Readable service label. |
| 5 | `component_code` | Matches a distinct charge under the service. |
| 6 | `charge_type` | Identifies recurring versus one-time billing. |
| 7 | `quantity` | Number of billed units. |
| 8 | `rate` | Billed per-unit rate for comparison to the approved price. |
| 9 | `rate_unit` | Unit that gives meaning to the rate. |
| 10 | `amount` | Total charged amount on that line. |

## 4. Extracted JSON fields

`agreements.extracted_json` stores an object with `services`, `components`, `lease`, and `evidence_page` keys. MSA rows populate `services` and `components`; an MLA populates `lease`. Provider metadata `extraction_provider` records `synthetic` or `ollama`; `extraction_model` stores the configured model name when Ollama is used.

- Service-term object: `service_code`, `service_name`, `subscribed`, `billing_stream`, `component_name`, `contract_amount`, `rate_unit`, `charge_type`, `pricing_basis`, `billing_frequency`, `billing_day`, `vehicle_count`, `driver_count`, `source_text`, `evidence_page`, `confidence_method`, and `field_confidence`.
- Extra-component object: `service_code`, `component_name`, `display_name`, `charge_type`, `contract_amount`, `rate_unit`, `quantity`, `billing_stream`, `subscribed`, `source_text`, `evidence_page`, `confidence_method`, and `field_confidence`.
- Lease object: `service_code`, `service_name`, `subscribed`, `billing_stream`, `component_name`, `contract_amount`, `rate_unit`, `quantity`, `term_months`, `effective_from`, `billing_frequency`, `billing_day`, `vehicle_make`, `vehicle_model`, `engine_type`, `pricing_basis`, `source_text`, `evidence_page`, `confidence_method`, and `field_confidence`.
- `field_confidence` is currently a deterministic marker-match score for selected parsed fields. `0.99` means the marker matched the expected row format; it is not an accuracy probability and does not measure whether the contract's legal meaning was interpreted correctly.
- `source_text` stores the matched raw marker row; `evidence_page` is located from the page containing that row in the generated agreement appendix. Both exist so the UI can show evidence and later support exact source linking.
- `confidence_method` explains how the score was obtained rather than presenting a bare number.

## 5. Pricing request API fields

`POST /api/pricing/requests` accepts:

- Request: `client_id` scopes the client; `agreement_ids` records the source agreements; `components` contains one or more charge objects.
- Component: `agreement_id` identifies its evidence; `billing_stream` preserves SERVICE/LEASE; `service_code` and `service_name` identify the catalogue item; `component_code` and `component_name` distinguish charge types; `charge_type` identifies recurring/one-time; `amount`, `currency`, `rate_unit`, and `quantity` define the price; `billing_frequency` and optional `billing_day` define cadence; `effective_from` defines start date; `terms` holds optional type-specific terms.
- `amount` and `quantity` cannot be negative. Other combinations are not yet fully validated against the source contract.

`POST /api/agreements/{agreement_id}/terms` accepts `extracted`, the whole editable extracted-terms object. Structuring edits it; Finance receives a read-only display.

`PUT /api/clients/{client_id}/invoice-history` accepts `enabled`, the Finance-controlled future invoice-history preference.

Billing history/audit accepts optional `start` and `end` ISO dates. `start` limits by invoice `period_start`; `end` limits by `period_end`.

### API response fields

- `GET /api/bootstrap` returns `clients`, `services`, and `counts`. Count keys are `clients`, `agreements`, `pending_approvals`, `active_pricing_components`, and `billing_invoices`; they feed the overview cards and navigation badge.
- Agreement list/upload returns agreement columns from the `agreements` table plus `extracted` (decoded from `extracted_json`). The PDF route returns the file bytes, not a JSON record.
- Agreement upload requires a selected `client_id`, but does not require the user to choose an agreement type. The Contract service detects MSA/MLA from a declared type marker or strong agreement-title terms; ambiguous PDFs are rejected for review. The UI renders the original PDF pages beside named metadata and extracted MSA service or MLA lease fields. PDF preview uses PDF.js and reports load failures with a retry action.
- `GET /api/clients/{id}/pricing` returns `requests` and `components`. Requests use the `pricing_approval_requests` columns; components use `pricing_components` columns plus `request_status`, `version`, `initiated_by`, `approved_by`, `approved_at`, and `request_created_at` from the joined approval request.
- Pricing submission returns `id`, `client_id`, `version`, and `status`; approval returns `id`, `client_id`, `status`, and `approved_by`.
- Billing upload returns `id`, `client_id`, `invoice_number`, `period_start`, `period_end`, `billing_stream`, `line_count`, and `status` so the UI can report ingestion outcome.
- Billing history returns `id`, `invoice_number`, `billing_stream` (the line's stream), `document_stream` (SERVICE/LEASE/COMBINED at the PDF level), `period_start`, `period_end`, `filename`, `service_code`, `service_name`, `component_code`, `component_name`, `charge_type`, `quantity`, `rate`, `rate_unit`, `amount`, and `currency`. Both stream fields are retained because a combined invoice can contain separately classified lines.
- Audit returns `client`, `rows`, `invoice_count`, and `discrepancy_count`. Each row contains service/component identity, stream and period, `contracted`, `configured`, contract/configured/billed rates and pricing basis, contract/configured/billed quantities, billed total, `rate_unit`, `issue`, and `explanation`. These compare fields help a human see why a row was flagged; they are not a final financial-impact calculation.
- `PUT /api/clients/{id}/invoice-history` returns `client_id` and `include_history_on_invoice` after saving the Finance preference.

### Frontend state fields

The static UI keeps a small in-memory state object. `page` selects the current view; `clientId` is the selected client; `role` and `userId` drive the demo permission checks; `clients` and `services` cache bootstrap lists; `agreements` and `selectedAgreement` drive contract review; `pricingDraft` holds unsent charge components; and `apiData` caches the latest overview/bootstrap response. None of these UI values is authoritative; the backend/database owns persisted records.

## 6. Configuration fields

| Setting | Purpose |
|---|---|
| `HOST` | Local bind address; `127.0.0.1` keeps the demo local. Production template shows `0.0.0.0` as a container bind example. |
| `FRONTEND_PORT` | Port for the static UI server. |
| `API_GATEWAY_PORT`, `API_GATEWAY_URL` | Browser-facing local API gateway address; it verifies JWTs and routes business API requests. |
| `AUTH_API_PORT`, `AUTH_API_URL` | Local Auth service endpoint for OAuth2 user and service-account tokens. |
| `CONTRACT_API_PORT`, `PRICING_API_PORT`, `BILLING_API_PORT` | Local listening ports for each backend API process. |
| `APOLLO_DB_PATH` | Path for the shared MVP SQLite database. |
| `APOLLO_DOCUMENT_DIR` | Path for runtime PDF uploads/copies. |
| `APOLLO_AUDIT_DIR` | Path for individual service audit SQLite files; defaults to `data/audit/`. |
| `CONTRACT_API_URL`, `PRICING_API_URL`, `BILLING_API_URL` | Backend service base URLs used by authenticated REST service calls. They are not sent to the browser. |
| `AUTH_ACCOUNTS_FILE` | Local user/service account hashes and service scopes. |
| `AUTH_JWT_SECRET` | Shared local-only HS256 signing secret; replace it before any shared deployment. |
| `AUTH_PROVIDER`, `AUTH_LOCAL_DEMO_ENABLED`, `AUTH_OIDC_ENABLED` | Select/toggle the configured identity-provider adapter. Corporate OIDC login and external JWT validation are future work. |
| `AUTH_OIDC_ISSUER`, `AUTH_OIDC_CLIENT_ID`, `AUTH_OIDC_CLIENT_SECRET` | Future corporate OIDC configuration values. Keep actual secrets only in ignored local config or managed secret storage. |
| `AUTH_PRICING_SERVICE_SECRET`, `AUTH_BILLING_SERVICE_SECRET` | Local demo OAuth2 client secrets; never use outside this demo. |
| `LLM_PROVIDER` | Agreement extraction provider selector. `synthetic` is the default deterministic sample parser; `ollama` uses the optional local HTTP model path. |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `LLM_TIMEOUT_SECONDS` | Ollama endpoint, model name (candidate default `qwen3.5:4b`), and request timeout. Ollama/model weights are not installed by this repository. |
| `LOG_LEVEL` | Intended runtime log verbosity; not yet applied consistently to the application. |
| `CONTRACT_DATABASE_URL`, `PRICING_DATABASE_URL`, `BILLING_DATABASE_URL`, `DOCUMENT_STORE_URL` | Future deployment settings for service-owned stores; currently unused placeholders. |
| `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` | Future provider-neutral deployment settings. Do not put real keys in checked-in files. |

`config/local.env.example` supplies local defaults. `config/test.env.example` supplies isolated ports and data paths for the test runner. `production.env.example` is a deployment template, not a runnable production configuration.

## 7. Authentication, authorization, audit, and service map

Human credentials are in `config/demo_accounts.json` as salted PBKDF2 hashes; see [the high-level architecture](HIGH_LEVEL_ARCHITECTURE.md) for demo passwords. The Auth service issues short-lived signed JWTs. Browser API traffic passes through the API Gateway, then each backend validates the token and applies its own role/scope checks. There is no default user and caller-supplied `X-User-Role` / `X-User-Id` headers are ignored.

Service-to-service REST clients use OAuth2 client-credentials grants with limited scopes. The service audit writer records every HTTP request (including failed requests) in its owner's local audit database. Health endpoints remain public for process readiness; business endpoints require a bearer token.

| Code location | Why it exists |
|---|---|
| `src/apollo_wheels_mvp/catalog.py` | One catalogue of 13 user-provided service labels and stable sample keys. MAP, RR, and MVR are kept unexpanded. |
| `src/apollo_wheels_mvp/documents.py` | Extracts selectable PDF text and parses the explicit sample marker rows. |
| `src/apollo_wheels_mvp/synthetic.py` | Creates selectable-text example agreements and invoices for the demo. |
| `src/apollo_wheels_mvp/seed.py` | Creates two sample clients, agreements, active pricing history, and six periods/streams per client once for the local DB. |
| `src/apollo_wheels_mvp/storage.py` | Defines SQLite tables, file-store paths, foreign keys, and connection behavior. |
| `services/contract_service/` | Agreement upload/review API, extracted field editing, and client settings. |
| `services/pricing_service/` | Pricing submission, versioning, second-person approval, activation, and pricing history API. |
| `services/billing_service/` | Billing PDF ingestion, line storage, date history, file serving, and contract/pricing comparison. |
| `services/auth.py`, `services/auth_providers/` | JWT verification, role/scope enforcement, and configurable Local/OIDC provider adapter boundary. |
| `services/auth_service/` | OAuth2 password and client-credentials token endpoints. |
| `services/api_gateway/` | Single browser API entry point, token verification, routing, and request-ID propagation. |
| `services/service_client.py` | Shared client-credentials token acquisition for backend REST calls. |
| `services/audit.py`, `services/audit_middleware.py` | Shared request-audit writer and middleware; each service writes to a separate audit file. |
| `scripts/run_local.py` | Loads config, starts separate local processes, waits for service readiness, and stops child processes together. |
| `scripts/generate_sample_documents.py` | Regenerates checked-in sample PDFs without resetting the runtime database. |
| `frontend/` | Separate static internal UI for contract review, pricing approval, and billing history/audit. |

## 8. Service catalogue values

The catalogue `code` is a stable matching key; `name` is the displayed business label; `stream` is the broad billing stream. Every currently listed service is classified as SERVICE. Lease is represented separately through an MLA lease row with code `LEASE-01`.

| Code | Display label |
|---|---|
| `FUEL` | Fuel |
| `ITR` | ITR |
| `MAP` | MAP |
| `RR` | RR |
| `TOLL` | Toll |
| `VIOLATION` | Violation |
| `COLLISION` | Collision |
| `INSURANCE` | Insurance |
| `MILEAGE_LOGGING` | Mileage + Logging |
| `TELEMATICS` | Telematics |
| `RENTALS` | Rentals |
| `MVR_SAFETY` | MVR + Safety |
| `REMARKETING` | Remarketing |
