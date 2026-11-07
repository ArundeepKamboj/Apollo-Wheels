# Project reference

This folder is the reference for the implemented MVP data, sample files, and unresolved design choices. It explains the purpose of persisted fields and sample PDF tags so a developer can understand the data without reverse-engineering every query.

## Documents

- [High-level architecture and access control](HIGH_LEVEL_ARCHITECTURE.md) — MVP service topology and data flows, active local demo identities, and future authentication/authorization controls.
- [Authentication accounts](../config/demo_accounts.json) — local-demo PBKDF2 hashes and least-privilege service-account scopes; demo credentials are documented in the high-level architecture.
- [Data and field guide](DATA_AND_FIELD_GUIDE.md) — database tables and columns, API payloads, PDF sample fields, configuration values, and source-code map.
- [Assumptions and open decisions](ASSUMPTIONS.md) — synthetic values, behavior chosen where business rules are not yet defined, and decisions still needing review.
- [LLM selection and trade-offs](LLM_TRADEOFFS.md) — local model candidates, hardware fit, proposed evaluation, and the current provider approach.
- [MVP coverage and build checklist](MVP_COVERAGE_AND_BUILD_CHECKLIST.md) — acceptance criteria, implemented/partial status, remaining work, and deferred capabilities.
- [Sample documents](../samples/README.md) — PDF inventory, folder layout, scenarios, and regeneration command.

The requirements file is the product scope; [Architecture Options.md](../Architecture%20Options.md) is the architecture comparison. A sample value is not a confirmed Apollo Wheels business rule. See the assumptions file before treating demo data as a target price or contract term.
