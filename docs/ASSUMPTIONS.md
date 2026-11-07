# Assumptions and open decisions

This is the working log of choices used to make the MVP runnable while business details are unavailable. These are not confirmed Apollo Wheels policies. Confirm or revise them before treating demo behavior as production behavior. When a choice changes, update this file and the matching code/docs.

## A. Synthetic dataset assumptions

| ID | Assumption used now | Where it appears | What needs confirmation |
|---|---|---|---|
| A1 | Seeded billing-demo clients are Northstar Fleet Services (`C-1001`) and Blue River Logistics (`C-1002`). A separate empty Test Client (`C-TEST`) is available for upload demonstrations. | `seed.py`, `samples/` | All identities are synthetic. Test Client intentionally has no preloaded agreement, pricing, or billing records. |
| A2 | All rates, quantities, clients, agreement terms, invoice IDs, and dates are invented. | All generated sample PDFs | No demo amount is a real quote or contract price. |
| A3 | Both sample clients have one MSA and one MLA, version 1.0, effective 2026-01-01. | Contract samples | Real versioning/effective date policies are unknown. |
| A4 | All 13 labels appear in each MSA; FUEL, ITR, MAP, RR, TOLL, VIOLATION, COLLISION, INSURANCE, and MVR_SAFETY are marked subscribed. The other four are unsubscribed. | MSA sample generation | Actual subscription combinations vary by client and should come from contracts. |
| A5 | Most service rates use deterministic sample values from `3.50 + (catalogue row index × 1.25)`, rounded to cents. Telematics is illustrated as 1.5 percent and Remarketing as 25 basis points. | `synthetic.py` | Values and pricing bases are scenario fixtures only; taxes, discounts, and actual rate schedules are not represented. |
| A6 | Service components alternate between monthly per-vehicle and monthly account fees by catalogue row; MVR + Safety uses monthly per-driver. Northstar's sample uses 500 vehicles/600 drivers; Blue River uses 300 vehicles/360 drivers. | `synthetic.py` | Real component shapes and whether multiple charge types coexist need confirmation. |
| A6a | Service sample dates are billing day 1 and monthly; lease sample repeats monthly on day 1. | MSA/MLA marker rows | Actual monthly/quarterly dates and due-day meaning need confirmation. |
| A7 | Fuel has an additional one-time activation/setup fee of USD 250. | MSA, January invoice | This is a scenario fixture only. It does not mean all Fuel contracts have this fee. |
| A8 | Northstar's lease example has 500 Ford Transit hybrid vehicles at USD 1,200 per vehicle-month; Blue River has 300 at USD 1,050. Both use monthly billing on day 1 and a 48-month term. | Template-based MLA and matching LEASE invoices | All values are synthetic; the amount and quantity in each invoice match that client's MLA schedule. |
| A9 | Three invoice months (Jan–Mar 2026) are sufficient to illustrate history and filtering. | Billing samples and seed data | Actual billing calendar, timezone, and period boundaries are not defined. |
| A10 | Service invoices include the same nine sample services marked subscribed in each MSA; service rates and units use the same generator as the MSA schedule. February RR has a USD 1.25 rate mismatch. | Billing sample generator | The mismatch is intentionally artificial to demonstrate detection. The four unsubscribed services are not billed in these sample periods. |
| A11 | Lease and service are separate invoices by default, but line rows retain stream labels for possible combined statements. | Samples, schema | Combined invoice creation and legal document boundaries need confirmation. |
| A12 | Currency defaults to USD. | Pricing API, database, invoices | Client-specific currencies, FX conversion, and currency precision are unconfirmed. |

## B. Pricing and billing behavior assumptions

| ID | Assumption used now | Consequence / open business rule |
|---|---|---|
| B1 | `amount` means the unit rate, while `quantity` and `rate_unit` supply the rate basis; a one-time amount uses account × 1. | Verify whether source contracts express unit rates, total amounts, tiering, or minimum commitments differently. |
| B2 | Billing totals are provided in invoice lines and are not currently recomputed/validated as `quantity × rate`. | Define line rounding, subtotal, tax, discounts, credits, proration, minimums, and adjustments before financial audit acceptance. |
| B3 | A fixed 0.005 difference threshold is used when comparing billed and configured rate. | Finance should set rate tolerance and currency rounding rules. |
| B4 | A single latest active pricing version applies per client; activating a new version marks all previous active components for that client superseded. | Confirm whether effective-dated concurrent service/lease pricing versions are allowed. |
| B5 | Pricing effective date defaults to the server's current date for a new submission. | Current pricing UI also has default date values; decide effective-date entry, timezone, backdating, and future dating rules. |
| B6 | Pricing components may have optional billing day/frequency but validation does not yet enforce full compatibility across fields. | Define valid combinations for recurring, one-time, usage, and lease charges. |
| B7 | A `COMBINED` billing-document stream is allowed by the database model; sample PDFs are single-stream. | Combined invoice upload parsing and stream inference need confirmed rules. |
| B8 | History filters compare `start` to invoice start and `end` to invoice end. | Confirm whether overlapping invoice periods should be included instead. |
| B9 | `include_history_on_invoice` is stored now but no generated invoice/pricing PDF or delivery is implemented. | The preference is a future setting only; Finance controls it in the internal prototype. |
| B10 | Contract audit matching uses service, component, and stream keys; a rate difference above tolerance is a discrepancy. | Define quantity mismatches, wrong periods, duplicates, taxes, missing/extra charges, credits, and discrepancy severity/financial impact. |
| B11 | A line's `amount` is trusted from the source document, and `rate` is compared to active configuration. | Clarify if audit should also compare total amount and expected quantity. |

## C. Parsing, extraction, and evidence assumptions

| ID | Assumption used now | Consequence / open business rule |
|---|---|---|
| C1 | Initial parser recognizes explicit `SERVICE`, `COMPONENT`, `LEASE`, and `LINE` pipe-delimited markers in generated PDFs. | It is not general legal-language extraction and will not reliably read arbitrary client PDFs. |
| C2 | Contract uploads must be PDFs with selectable text; image-only scans, OCR, encrypted PDFs, and PDFs larger than 20 MB are rejected. | Confirm file limits, document types, OCR requirements, and retention/security rules. |
| C3 | Field evidence points to exact, selectable marker rows in a dedicated appendix of each generated sample agreement; the page number is computed from the source PDF. | General documents need page-aware source spans/coordinates and trustworthy provenance. |
| C4 | Confidence `0.99` means exact marker-row matching, not calibrated probability or legal interpretation quality. | Calibrate field-level confidence on labelled human-reviewed documents before using thresholds. |
| C5 | Header `CLIENT_ID`/`CLIENT_NAME` in billing PDF are parsed as metadata but the upload flow currently uses the selected UI client without rejecting mismatches. | Add cross-check/confirmation before accepting uploads for real use. |
| C6 | Missing agreement `EFFECTIVE_DATE` and `VERSION` fall back to 2026-01-01 and 1.0 in upload parsing. | Avoid silent production defaults; require review or explicit missing-value state. |
| C7 | Unsupported or absent service/component rows may be ignored by the deterministic parser rather than returned as unknown text. | Add unknown-row review handling before broad document support. |

## D. Architecture, identity, and runtime assumptions

| ID | Assumption used now | Consequence / open decision |
|---|---|---|
| D1 | One shared SQLite file simplifies the local demo, while APIs and domain modules are separated by service. | Choose separate production stores, backups, migrations, and ownership boundaries before deployment. |
| D2 | PDFs are local filesystem files; database rows store paths. | Production needs object storage, access control, encryption, retention, and malware scanning decisions. |
| D3 | Four-eyes approval uses distinct stable subjects from locally issued signed JWTs; the Pricing service enforces the same-subject rejection. | Production must map the company's immutable OIDC subject and retain both identities/timestamps in service audit records. |
| D4 | Local Auth uses three seeded human demo accounts and two scoped service accounts; their credentials are public demo values and password/client-secret hashes are stored in the account file. | Never reuse these credentials. Production should use corporate OIDC/MFA for humans and managed secrets or workload identity for services. |
| D5 | The local browser enters through one API Gateway; each backend also verifies bearer tokens and enforces roles/scopes. Health endpoints are public for process readiness. | Production requires TLS, a load balancer/WAF, gateway policy, private backend networking, secrets, rate limits, and deployment-level health controls. |
| D6 | Test and production `.env.example` files are templates only. | Neither an isolated test stack nor production deployment is ready. |
| D7 | Client-facing email/PDF generation, notifications, and automatic scheduling are later scope. | Define recipients, timing, consent, retry, and approval requirements before enabling delivery. |
| D8 | Each service records HTTP request audit events in its own SQLite file under `data/audit/`; business data remains in a shared local SQLite DB. | Production audit retention/immutability and service-owned business stores must be designed before deployment. |
| D9 | Future observability should use OpenTelemetry for traces, metrics, and structured logs, exported through an OTLP collector to a selected Grafana or ELK stack. | Instrumentation/exporters/collector are intentionally deferred; select retention, access, dashboards, and alerts with platform/security teams. A CDN is not planned for the internal API-heavy app. |

## E. LLM decision status

- An optional Ollama HTTP extraction provider is now wired for agreement uploads, but no LLM runtime is installed or called by default. The synthetic parser remains the current default and keeps the demo runnable without model downloads.
- Candidate for local evaluation: Ollama with a quantized Qwen3.5 4B model, chosen as a smaller open-weights starting point; this is not yet an approved quality result. The machine's NVIDIA GTX 1050 has 4 GB VRAM, so even the listed 4B package size is close to GPU capacity. It may require CPU/RAM offload and may be too slow. Larger 9B weights are beyond the GPU memory budget.
- The model must return typed JSON and source evidence; deterministic code validates numeric fields, stream/category values, and totals. Finance/Structuring continue to review the proposed terms before activation.
- Evaluate on varied natural-language synthetic contracts with labelled expected values, including missing, ambiguous, conflicting, and amended terms. The tagged sample rows alone are too easy to prove real agreement understanding.
- Keep `LLM_PROVIDER=synthetic` as default until an actual local runtime is installed, performance is measured, and the user accepts the quality/latency trade-off. See [LLM trade-offs](LLM_TRADEOFFS.md).

## F. Still-open business questions

1. What are the exact pricing components and calculation rules for each of the 13 services?
2. Are usage tiers, minimums, discounts, credits, taxes, proration, and one-off adjustments in scope?
3. Is approval/versioning per client, per agreement, per service, or another unit?
4. How should amendments, renewals, overlapping terms, and backdated changes affect active pricing?
5. Should invoice history use inclusive overlap filtering or fully-contained-period filtering?
6. Which client/billing identities and document retention/security rules will apply beyond the demo?
7. What extraction accuracy and review time are acceptable before AI-extracted fields can be enabled?

## G. Future-state agreement workspace (not MVP scope)

The user has proposed reusable agreement templates and a shared Structuring/client negotiation workspace. In that future state, negotiation comments and agreed term versions are retained against the agreement; the client can view an informational billing preview; and a completed agreement document is generated from the selected template after client go-ahead. This does not include the current MVP.

Before implementation, decide template ownership and approval, clause-level editing rights, client identity and access boundaries, comment resolution, decision/audit retention, the meaning of client go-ahead, whether generated documents are drafts or routed for e-signature, and how a preview remains tied to the pricing version shown. Do not treat client go-ahead alone as legal execution until legal and signing controls are defined. Finance's pricing ownership and distinct-user approval remain separate from Structuring's agreement editing.
