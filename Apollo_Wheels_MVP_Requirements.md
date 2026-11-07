# Apollo / Wheels -- MVP Requirements Specification

## Contract Extraction, Pricing Setup and Existing-Client Billing Audit

**Source:** Interview briefing and discussion with the Wheels
interviewer on 5 November 2026, including the supplied slide "AI Product
/ Developer Partner Activity -- Deeper Dive: Contracts / Agreements".\
**Purpose:** Capture the actual MVP requirements discussed.\
**Status:** Confirmed information is separated from assumptions and open
questions.

> **Current alignment:** This specification predates follow-up decisions.
> Section 16 below records the reconciled requirements as of 5 November
> 2026 and supersedes stale open questions or conflicting assumptions in
> earlier sections. The project context and Architecture Options files
> track the same decisions.

> This document records the interview discussion. Do not present
> proposed design choices or assumptions as confirmed requirements.

# 1. MVP objective

Build a working internal tool to improve Wheels' signed-contract
processing and contract-to-billing accuracy. The MVP has two principal
modules:

1.  **New contract processing:** Upload an executed Master Service
    Agreement (MSA) and/or Master Lease Agreement (MLA), extract
    contractual and billing information, display the original document
    alongside extracted values, allow Structuring to edit contract details,
    let Finance configure pricing, and require a distinct second Finance
    user to approve before pricing is automatically activated and stored in
    the internal pricing database.
2.  **Existing-client audit:** Compare contract information against
    Pricing Manager setup and actual billing, identify discrepancies,
    and proactively show affected clients and services.

The interviewer wants a usable working product, not just a chatbot,
document summary, conceptual POC or non-working demo.

## Business outcomes

The tool should help address: - Incorrect billing: overbilling or
underbilling due to manual interpretation or data-entry errors. - Missed
billing: a client receives a subscribed service but the service has not
been configured for billing. - Audit delays: manual, document-intensive
review slows audit work.

# 2. Business context supplied by interviewer

Wheels was described as: - Approximately 1.1 million vehicles managed. -
Approximately 70% / 750,000 vehicles owned and serviced by Wheels. -
Remaining approximately 30% owned by end clients. - Approximately US\$9
billion in assets under management. - Operations in 59 countries. - More
than 100 Fortune 500 clients.

These are background figures, not application requirements.

# 3. Contract types

Both contract types were described as legal documents.

## 3.1 Master Service Agreement (MSA)

-   Captures services a client has subscribed to receive from Wheels.
-   A client may choose some or all services.
-   Selected services and applicable contractual terms are captured in
    the MSA.
-   Important clauses, calculations and billing information may relate
    to one or more services.
-   The selected services drive onboarding and billing setup.

Example discussed: a client with 20,000 vehicles may select seven
services.

## 3.2 Master Lease Agreement (MLA)

-   Applies when vehicles are leased.
-   The interviewer explained that a lease may provide an option to own
    the vehicle at the end, unlike a normal rental.
-   The vehicle may be owned by Wheels or by the manufacturer.
-   The MLA may specify leased vehicle count, lease duration, make,
    model, engine type and price.
-   Pricing is usually monthly; quarterly pricing was also mentioned.
-   If a client owns all vehicles and has no leased vehicles, an MLA may
    not apply.

# 4. Services listed in the assessment slide

The slide lists 13 services:

1.  Fuel
2.  ITR
3.  MAP
4.  RR
5.  Toll
6.  Violation
7.  Collision
8.  Insurance
9.  Mileage + Logging
10. Telematics
11. Rentals
12. MVR + Safety
13. Remarketing

The interviewer expanded **ITR** as **Initial Title Registration**. The
full forms / meanings of MAP, RR and MVR were not confirmed; retain the
labels as written. A client can subscribe to any or all services.
Contracts may contain calculations and/or billing information for any or
all of them.

**Confirmed:** The user expects the MVP to cover all 13 services. The order
for implementing and validating service-specific rules remains to be set.

# 5. Current manual process

The interviewer described the current process:

1.  Wheels and the client negotiate the agreement through multiple
    draft/review cycles.
2.  Wheels sends a draft agreement to the client.
3.  The client and/or its legal team reviews it and sends comments or
    changes.
4.  The agreement may move back and forth several times.
5.  Once finalised, the client signs and dates it.
6.  The client emails a scanned / executed copy to Wheels and may also
    send the original physical document for records.
7.  Wheels' onboarding / sales team forwards the documents by email to
    Finance.
8.  Finance manually reviews pages and clauses.
9.  Finance determines subscribed services and interprets contractual
    and billing information.
10. Finance manually enters information into the pricing system /
    Pricing Manager.
11. Once the client is live, the configuration supports onward billing.

Documents are mostly PDFs. Verbal discussion described approximately
10--30 pages; the slide appears to say approximately 16--20 pages. The
exact range is unconfirmed.

# 6. MVP module 1 -- New contract processing and Pricing Manager setup

## 6.1 Manual upload

-   User uploads an executed contract document.
-   Immediate MVP uses manual upload.
-   Documents are primarily PDFs.
-   User may upload an MSA and/or MLA.
-   Application starts processing the uploaded document.
-   This is a standalone internal tool for the assessment.

**Not in immediate MVP:** connecting to the existing contract repository
and automatically retrieving documents. The interviewer described this
as a future integration that could enable systematic ingestion, mass
upload and mass extraction.

## 6.2 Side-by-side review screen

This is an explicit requirement.

### Left side -- Original document

-   Display the original uploaded PDF.
-   Allow scrolling through the document.
-   Preserve it as the reference for review.

### Right side -- Extracted information

-   Display extracted values in a structured format.
-   Show a confidence score for each extracted field.
-   Allow the user to edit extracted values.

### Source highlighting

-   Hovering over an extracted field should highlight the corresponding
    source section in the original document.
-   This helps Finance verify the value against the document without
    manually searching through pages.
-   Page/source-text evidence should be retained. Exact implementation
    (e.g. coordinates or bounding boxes) is a technical design choice.

## 6.3 Information explicitly mentioned for extraction

-   Service.
-   Number of vehicles.
-   Amount / price.
-   Price may be expressed in dollars, basis points or percentage.
-   Billing period / frequency.
-   Billing date, e.g. 20th of the month, first day of the month or last
    day of the month.
-   Number of drivers for driver-related services.

For MLA, the interviewer also mentioned: - Number of leased vehicles. -
Lease duration. - Vehicle make. - Vehicle model. - Engine type. - Price,
usually monthly and sometimes quarterly.

Additional fields may be needed after inspecting sample documents, but
should not be described as confirmed until verified.

## 6.4 Confidence scores

-   Confidence scores are explicitly requested.
-   They should be associated with individual extracted fields, not just
    the entire document.
-   Exact calculation / calibration method was not specified.
-   A model-generated confidence value is not automatically a
    statistically calibrated probability. Explain how the score is
    derived; label heuristic scores accordingly.

## 6.5 Review and editing

-   User can edit extracted values.
-   Original PDF remains visible for reference.
-   User reviews the extracted information and clicks Submit.
-   The interviewer was asked about editing the legal agreement or
    sending it back for changes. The interviewer said not to add that to
    the current scope.

Therefore, contract negotiation, editing the legal agreement itself and
a send-back-to-client workflow are out of scope.

## 6.6 Pricing API and activation

- Finance enters pricing after contract details are reviewed. One Finance user initiates/enables the setup; a different Finance user approves it (four-eyes check).
- The second approval automatically activates/applies the pricing to the client and persists it in an internal database for internal viewing and history.
- The prototype uses a distinct internal Pricing service/API; no real Pricing Manager API, credentials, or source data are available.
- Do not describe the prototype Pricing service as a real integration to Wheels' Pricing Manager.
- Client-facing pricing PDFs/emails are a later-phase flow, not part of the first MVP. A production integration to the actual Pricing Manager can be considered if API access and requirements are supplied later.
- Show activation status and preserve a clear approval/audit history.
## 7.1 Data to compare

1.  **Contract:** what the signed agreement says the client has
    subscribed to.
2.  **Pricing setup:** what has been configured in Pricing Manager.
3.  **Billing:** what has actually been billed.

The interviewer encouraged this capability. The user confirmed that no
source data is available: create synthetic contract PDFs, billing PDFs,
clients, and initial pricing records for the prototype. Billing PDFs must
be ingested and parsed; do not assume pre-structured billing rows.

## 7.2 Discrepancies explicitly mentioned

-   Missing pricing.
-   Incorrect pricing.
-   Missing services.

The wider business problem also includes overbilling, underbilling and a
service being provided but not configured for billing.

## 7.3 Candidate-proposed comparison rules

These are logical implementation rules based on the three-stage
comparison; validate them against actual sample data and business
rules: - Contract service exists but Pricing Manager setup is absent. -
Contract service and setup exist but billing is absent. - Contract price
differs from configured price. - Configured price differs from billed /
expected amount. - Vehicle quantity differs across contract, setup and
billing. - Driver quantity differs where applicable. - Billing frequency
or billing date differs. - Pricing unit differs (per vehicle, per
driver, fixed, percentage, basis points). - A service is configured or
billed but not supported by the contract. - A contract amendment has not
been reflected in setup or billing.

These are proposed comparison rules, not confirmed business rules.

## 7.4 Explainability

The interviewer wants the tool to **scientifically pinpoint the issue**.
He does not expect 100% accuracy; he wants to see a systematic approach.

Example explanation: - Contract says a service is subscribed. - Pricing
Manager has no configuration for it. - Billing records show no charge. -
Tool flags a possible missed-billing issue.

Where possible, show source contract evidence and the compared values.

## 7.5 Financial impact

Financial impact calculation could be useful (e.g. potential missed
revenue or overbilling), but the interviewer has not confirmed: -
Whether it is mandatory. - Exact formulas. - How proration, discounts,
tax, rounding, effective dates or partial billing periods should be
handled.

Treat this as an open question / optional enhancement until clarified.
Do not invent precise financial impact values without the required data
and rules.

## 7.6 Accuracy

The interviewer explicitly said 100% accuracy is not expected. The goal
is to demonstrate a systematic approach to identifying discrepancies.
Distinguish a detected discrepancy from a potential issue requiring
human investigation.

# 8. Scope boundaries

## In current MVP

-   Internal users only.
-   Manual document upload.
-   MSA / MLA processing.
-   Side-by-side original PDF and extracted values.
-   Source highlighting on hover.
-   Field-level confidence scores.
-   Editable extracted values.
-   Submit Finance-approved setup through the internal prototype Pricing API; do not imply a production Pricing Manager integration.
-   Existing-client audit view.
-   Contract vs Pricing Setup vs Billing comparison.
-   Detection of missing services and missing/incorrect pricing.
-   All 13 listed services represented; implementation priority remains
    to be set.
-   Synthetic billing PDF ingestion, service-level history with
    billing-period/date filters, and discrepancy reporting.
-   MSA and MLA linked to one client but retained as separate agreements.
    Identify service and lease streams separately; generate separate
    billing by default and support combining them while retaining labels.
-   Role boundaries: either Structuring or Finance can upload and inspect
    documents; Structuring edits extracted contract details; Finance views
    those details read-only and owns pricing setup.
-   Four-eyes pricing activation: second, distinct Finance user approves;
    approval automatically activates the setup.
-   Environment templates for local, test, and production; separate
    frontend and backend service directories; REST communication and
    one-command local startup.
-   MVP PDF samples have selectable text; scanned PDF OCR is future scope.
-   Client-facing pricing PDF/email delivery is future scope.
-   Working local demonstration.
-   Presentation deck and test cases.

## Explicitly out of current MVP

-   Client-facing contract negotiation portal.
-   Client users logging into or using the tool.
-   Full contract lifecycle management system.
-   Editing the legal contract itself.
-   Send-back-to-client negotiation workflow.
-   Automatic connection to the existing contract repository.
-   Mass ingestion / mass extraction from the repository.

## Future direction mentioned

The interviewer described connecting the tool to an existing contract
repository so that it can systematically retrieve documents and support
bulk / mass upload and extraction. This is future integration, not
immediate MVP scope.

### Future-state agreement templates and negotiation workspace

The user has proposed a future client-facing workflow; it is explicitly
outside the current internal MVP:

- Maintain versioned default templates for each agreement type (initially
  MSA and MLA), with approved clauses and configurable fields.
- Provide a shared browser workspace for Structuring and the client to
  review the proposed agreement terms, discuss changes in context, and
  retain the negotiation conversation against the agreement record.
- Preserve document/template versions and a reviewable history of proposed
  terms, comments, decisions, and the client's go-ahead.
- After the client confirms agreement, generate a complete document from
  the approved template and agreed terms. E-signature, legal approval,
  execution status, and the exact meaning of "go-ahead" remain to be
  defined; do not imply this workflow itself creates a legally executed
  agreement.
- Show a billing/pricing preview in the same workspace so both parties can
  see the expected charges before confirmation. The preview should use the
  relevant agreement terms and pricing rules and be clearly distinguished
  from an issued invoice.
- Keep client access scoped to that client's agreements and messages.
  Structuring can negotiate and manage agreement drafts; Finance continues
  to own pricing configuration and its separate four-eyes approval.

This future capability extends the current negotiation-out-of-scope
boundary; it does not add negotiation, client accounts, or document
generation to the MVP. Design review should later decide template
governance, client identity/access, clause permissions, comment resolution,
retention/audit policy, generated format, signing integration, and how
previewed charges are versioned against pricing changes.

# 9. Synthetic data and assumptions

The interviewer explicitly said synthetic documents and synthetic data
are acceptable and encouraged. The interviewer wants to assess whether
the candidate makes sensible assumptions and keeps progressing when all
details are not provided.

Potential synthetic data: - Synthetic MSA documents. - Synthetic MLA
documents. - Synthetic clients. - Contracted services and service-level
pricing terms. - Vehicle counts. - Driver counts for applicable
services. - Pricing Manager setup records. - Actual billing records. -
Deliberately seeded examples of missing service setup, missing billing,
incorrect price, incorrect quantity, billing-period mismatch and service
billed without contractual entitlement.

Exact number of clients/documents and dataset format have not been
specified.

# 10. Technology, architecture and resiliency considerations

No specific programming language, frontend framework, database, OCR
provider or LLM provider was mandated in the discussion.

Current implementation direction: Python/FastAPI for separately runnable
backend APIs, a separate low-tooling frontend directory, local REST
communication, and one-command local startup. Keep config templates for
local/test/production and do not commit secrets. The storage design is
being compared: PDFs stay in file/object storage, while operational
records use relational fields plus flexible JSON terms unless review
selects a document database. A local open-source LLM is an option only
after local hardware and extraction quality are assessed.

The interviewer wants the candidate to explain: - Why the chosen OCR
tool was selected. - Why the chosen LLM was selected. - Why alternatives
were not selected. - Tool limitations and trade-offs. - How the design
considers future scale. - What happens when the LLM service is
unavailable.

A possible candidate-proposed implementation: - Frontend: separate
frontend directory (current code uses plain HTML/CSS/JavaScript to reduce
setup). - Backend: Python / FastAPI. - PDF parsing: native text
extraction for digitally generated PDFs. - OCR: OCR for scanned PDFs if
required. - AI: LLM for interpreting clauses and extracting structured
values. - Validation: deterministic backend validation and business
rules. - Persistence: store documents, extracted fields, review edits,
setup records, billing records and audit results. - Integration: Pricing
Manager API or clearly labelled mock API if real access is not supplied.

## 10.1 LLM resiliency

The interviewer specifically asked what happens if the LLM provider
(examples included ChatGPT, Copilot or Claude) is down and whether that
could bring down the service.

Consider: - Upload should not depend on an immediate successful LLM
call. - Preserve the uploaded document. - Maintain processing status /
job state. - Use request timeouts. - Use bounded retries. - Allow failed
processing to be retried. - Do not lose user work if the LLM is
unavailable. - Consider a fallback provider only if practical and
justified. - Show failure state clearly to the user.

These are design considerations, not requirements for a specific queue,
cloud service or fallback model.

## 10.2 Deterministic validation

Recommended principle: - LLM interprets legal language and extracts
structured data. - Deterministic code handles numerical comparisons,
required-field checks, supported-service checks and known billing
calculations. - Human review happens before submission. - Audit
discrepancies show the rule and evidence that triggered the alert.

# 11. Testing

The interviewer confirmed test cases are expected and mentioned
functional and integration tests. A complete test strategy or coverage
target was not specified.

Unit and integration tests now cover sample parsing, seeded data,
four-eyes activation, and billing audit reconciliation. Browser/UI
functional coverage and broader error-path coverage remain outstanding.
See [the MVP coverage and build checklist](docs/MVP_COVERAGE_AND_BUILD_CHECKLIST.md)
for implementation status and remaining test work.

## 11.1 Functional test cases

1.  Upload a valid MSA PDF.
2.  Upload a valid MLA PDF.
3.  Display original PDF on left.
4.  Display extracted values on right.
5.  Scroll original PDF.
6.  Hover over extracted field and highlight source.
7.  Display field-level confidence.
8.  Edit extracted field.
9.  Submit reviewed information.
10. Display successful Pricing Manager submission.
11. Display failed Pricing Manager submission.
12. Display existing-client audit dashboard.
13. Detect contract service missing from pricing setup.
14. Detect contract service missing from billing.
15. Detect incorrect configured price.
16. Detect incorrect billed amount / mismatch where data and formula
    exist.
17. Detect vehicle / driver count mismatch where applicable.
18. Detect billing-period mismatch where applicable.

## 11.2 Integration tests

-   Frontend to backend document upload.
-   Backend to PDF parser.
-   Backend to OCR service, if used.
-   Backend to LLM provider or test double.
-   Backend to persistence layer.
-   Backend to Pricing Manager API or mock.
-   Retry after API failure.
-   Verify no duplicate setup on retry, if idempotency is implemented.

## 11.3 AI extraction tests

-   Compare extracted values with known expected values from synthetic
    contracts.
-   Test currency, percentage, basis points, quantity and billing date
    formats.
-   Test missing fields.
-   Test ambiguous clauses.
-   Test conflicting values in different sections.
-   Verify source page/text evidence.
-   Report measured field-level accuracy; do not claim unmeasured
    accuracy.

## 11.4 Resilience tests

-   LLM provider unavailable / timeout.
-   OCR failure.
-   Invalid or malformed model output.
-   Corrupt PDF.
-   Missing required values.
-   Pricing Manager API timeout or error.
-   Retry failed process.
-   Duplicate upload / duplicate submit behaviour.

# 12. Deliverables and presentation

The interviewer asked for: - Working local application. -
Four-to-five-slide presentation deck. - High-level architecture /
design. - Test cases, including functional and integration tests. - Live
demonstration. - Explanation of assumptions, tool choices and design
decisions.

Suggested slide structure:

1.  **Problem and understanding:** Current manual process, MSA/MLA,
    services, incorrect billing, missed billing and audit delays.
2.  **Product approach:** New contract processing and existing-client
    audit.
3.  **Assumptions and decisions:** Synthetic data, scope boundaries,
    tool choices, human review and deterministic validation.
4.  **Architecture:** Frontend, backend, PDF/OCR, LLM extraction,
    validation, persistence, Pricing Manager integration, audit flow and
    resiliency.
5.  **Demo / outcomes / limitations:** Working workflows, test results
    and known limitations.

The interviewer may prefer to move to the demo early. Make sure the
application and demo data work before spending too much time polishing
slides.

# 13. Remaining open decisions

These questions remain genuinely unresolved after the user's follow-up answers. Ask one at a time when the user returns to requirement clarification; do not ask the previously answered questions from the original draft.

1. What order/priority should be used to implement and validate all 13 services?
2. What exact pricing fields and authoritative semantics apply to rates, units, counts, billing dates/frequency, effective dates, and charge formulas?
3. What do MAP, RR, and MVR mean in Wheels' service catalogue? Retain the slide labels until confirmed.
4. Does the optional Ollama + Qwen3.5 4B candidate meet the required agreement-extraction accuracy and latency on representative documents? It has not been run; larger models exceed this machine's GPU memory.
5. Which storage mix should be finalized after reviewing SQL, document-store, and hybrid trade-offs?
6. Should amendments and agreement versions be represented in the first synthetic data set?
7. What billing/pricing retention period and exact history view should the future database support?
8. What measurable 30-day targets and business baselines should be used in the leadership presentation?
9. What exact build window/presentation duration should be optimized for, given the deck and follow-up notes differ?
10. What test evidence and acceptance thresholds are expected? The user wants test suites created later.
11. How should the future client-facing pricing PDF/email flow be configured (recipients, controls, or external destination)? This is not first-MVP scope.
# 14. MVP acceptance checklist

This is the desired acceptance scope, not a claim that every item is
already implemented. Use [docs/MVP_COVERAGE_AND_BUILD_CHECKLIST.md](docs/MVP_COVERAGE_AND_BUILD_CHECKLIST.md)
for current implementation status and remaining build work.

## New contract processing

-   [ ] User can upload a PDF contract.
-   [ ] Application accepts MSA and MLA.
-   [ ] Original PDF appears on left.
-   [ ] PDF can be scrolled.
-   [ ] Extracted fields appear on right.
-   [ ] Extracted values include services and applicable pricing /
    quantity / billing details found in the document.
-   [ ] Field-level confidence score is visible.
-   [ ] Hovering/selecting a field highlights its source in the PDF.
-   [ ] User can edit extracted values.
-   [ ] Structuring user can edit contract fields; Finance view of those fields is read-only.
-   [ ] Finance can create pricing components based on the contract terms.
-   [ ] A distinct second Finance user can approve; initiator cannot approve own request.
-   [ ] Second approval automatically activates and persists pricing for the client.
-   [ ] Active pricing is visible internally with version/history information.
-   [ ] Pricing is submitted to the internal prototype Pricing API; no claim of real Pricing Manager integration.

## Existing-client audit

-   [ ] Separate audit page / dashboard exists.
-   [ ] Dashboard identifies clients with issues.
-   [ ] Dashboard identifies affected services.
-   [ ] Synthetic contract data, internal pricing setup, and ingested billing PDF lines are compared.
-   [ ] Missing service / missing pricing can be detected.
-   [ ] Incorrect pricing can be detected where comparison data is
    available.
-   [ ] Missing billing can be detected where billing data is available.
-   [ ] Each discrepancy explains why it was flagged.
-   [ ] Financial impact is shown only if required data and calculation
    rules are available.

## Quality and delivery

-   [ ] Synthetic data is clearly identified as synthetic.
-   [ ] Unit and integration tests cover current sample, seed, approval, and reconciliation paths; functional/UI coverage and agreed acceptance thresholds remain to be added.
-   [ ] LLM / API failure behaviour is handled or clearly demonstrated.
-   [ ] Application runs locally.
-   [ ] Four-to-five-slide deck is ready.
-   [ ] Architecture diagram is ready.
-   [ ] Assumptions and limitations are documented.
-   [ ] Candidate can explain tool choices and trade-offs.

# 15. Clarification sequencing and current work

The user asked that clarifications be handled one at a time. Most foundational scope questions have now been answered and recorded in Section 16. The user has approved Option A as the working architecture direction and authorized coding. Do not restart the old audit-dataset question. Continue with the service/configuration requirements and implement the agreed local-first structure; return to the remaining open decisions only when they affect the next design step.

# 16. Reconciled requirements and current build alignment

This section is the current source of truth where earlier parts of this draft contain stale wording.

## 16.1 Confirmed current MVP

- Build both major workflows sequentially: (1) contract upload, review, Structuring edits, Finance pricing entry, four-eyes approval, automatic activation and internal persistence; (2) billing PDF ingestion, comparison with contract and pricing, discrepancy review, and billing history.
- All 13 services must be covered. Their implementation priority is still open. Do not invent MAP, RR, or MVR expansions.
- No business datasets are available. Generate all clients, MSA/MLA contracts, pricing setups, history, and billing records synthetically.
- Generate selectable-text PDFs for the first leg. OCR for scanned/image-only PDFs is later roadmap scope.
- Keep named synthetic sample PDFs in `samples/contracts/` and `samples/billing/`, separated by client and agreement/billing stream. Include an intentional mismatch document for manual audit review and a simple regeneration command.
- Link MSA and MLA under a client while retaining each agreement and its evidence. Identify service billing from MSA and lease billing from MLA. Separate streams by default; allow combining them while preserving stream/source labels.
- Both Structuring and Finance can upload and inspect contracts. Structuring owns extracted contract-detail edits. Finance can view those fields read-only and owns pricing setup.
- Finance user 1 initiates/enables pricing. A distinct Finance user 2 approves. Approval automatically applies the pricing to the client and persists it for internal viewing/history.
- Finance controls whether future generated invoices include prior billing history. The internal billing-history view supports a period or date range and service-level amounts. Client-facing pricing PDF/email delivery is a later-phase flow.
- The first local build has separate frontend, Contract API, Pricing API, and Billing/Audit API directories and entrypoints. APIs run locally and communicate by REST. A single runner command starts all processes. Option B deployment/broker choices remain future architecture review.
- Keep local, test, and production configuration templates separate; do not commit secrets. The user is open to a local OSS LLM if measured quality is acceptable. Current generated PDFs use deterministic parsing as a no-credential demo fallback; this must not be described as production AI extraction.
- Keep code minimal and straightforward: separate service entrypoints, small domain modules, direct REST, and readable frontend source. Avoid extra abstractions/libraries unless needed for a confirmed requirement; do not minify source to make it shorter.
- Storage is a comparison, not a settled SQL-only requirement. Source PDFs live in file/object storage. Current recommendation is relational workflow/identity/reconciliation fields plus flexible JSON for variable terms; MongoDB remains an option. The local implementation uses SQLite + JSON-shaped fields for low-code demonstration, with service ownership boundaries preserved for later data-store separation.
- Code and tests are organized separately. Unit and integration tests cover the synthetic PDF samples, seed dataset, four-eyes activation, and billing reconciliation. Functional/UI coverage and broader acceptance thresholds remain future work.

## 16.3 Future-state roadmap addition: templates, negotiation, and billing preview

- The user has proposed a client-facing agreement workspace after the MVP. It is not part of the current build.
- Maintain approved, versioned default templates for each agreement type (initially MSA and MLA).
- Allow the relevant client and Structuring users to review proposed terms and discuss or negotiate changes in the same workspace. Store the conversation, term revisions, and decisions against that agreement with a traceable history.
- After explicit client go-ahead, generate the complete agreement document from the chosen template and agreed terms. Whether that document is a final draft for signature or legally executed is unresolved; e-signature and legal approval are not implied.
- Show an informational billing/pricing preview in the workspace before confirmation. Tie the preview to the terms and pricing version it used, and distinguish it from an issued invoice.
- Enforce client-specific access. Structuring owns agreement editing and negotiation; Finance owns pricing and retains the separate four-eyes approval workflow.
- Before implementation, define template governance, editing permissions, client identity/access, comment resolution, retention/audit rules, what constitutes go-ahead, signing, and how pricing changes during negotiation affect the preview.

## 16.2 Current implementation alignment

The specification's original scope largely matches what we have analyzed, but sections drafted before the follow-up discussion contained stale open questions and the inaccurate assumption that an existing Pricing Manager API/data source might be available. Section 16.1 now records the agreed current requirements and overrides that earlier wording.

The code scaffold includes Python/FastAPI Contract, Pricing, and Billing/Audit API entrypoints; a separate frontend directory; named selectable-text sample PDFs under `samples/` for manual workflow checks; a local file store; persistent pricing approval/history records; a four-eyes workflow; environment templates; and a one-command local runner. Pricing validates client/agreement references through the Contract REST API, and Billing/Audit obtains contract and active-pricing data through REST. The current services share one local SQLite file for MVP convenience; the future architecture can move to service-owned stores/object storage. No production Pricing Manager integration or client-facing email/PDF delivery is implemented.

Current code is an MVP implementation in progress, not yet complete acceptance. The UI shows field-level marker confidence and source excerpts, but does not draw source highlights over the PDF itself. Audit now matches contract/pricing/billing by service, component, stream, and period; it flags missing pricing/billing, rate/basis/unit differences, and quantity differences, while taxes/proration/totals remain undefined. Error/retry behavior and UI polish still need work. Synthetic PDFs use deterministic markers. An optional Ollama agreement-extraction provider is wired but has not been run; Qwen3.5 4B is only a local candidate and has not been evaluated for contract accuracy. No Ollama runtime/model weights or OCR runtime are installed. The app must not claim production-grade AI extraction until it is measured.

## 16.4 Requirements not yet implemented or verified

- Run and evaluate the optional Ollama/Qwen candidate on varied synthetic natural-language contracts; define a reviewed accuracy threshold before considering it enabled by default.
- OCR for scanned PDFs.
- Production authentication and authorization (the demo role selector is not production auth).
- Financial-impact calculations, taxes, proration, discounts, rounding, and other unconfirmed billing semantics.
- Client-facing pricing PDF/email delivery.
- Production deployment, per-service database separation, and pub-sub/Kafka.
- Functional/UI test coverage and measured acceptance/accuracy results.
