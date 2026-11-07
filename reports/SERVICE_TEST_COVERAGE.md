# Service-level test coverage report

Generated from 100 Python test cases. Result: **PASS**; failures: 0; errors: 0.

Python coverage measures executed backend/shared Python statements. Browser scenario counts are reported separately; they are not JavaScript line coverage.

## Test cases by area

| Area | Cases |
|---|---:|
| Contract service | 14 |
| Pricing service | 14 |
| Billing service | 17 |
| Auth service | 9 |
| API gateway | 1 |
| Shared services | 4 |
| Shared data / documents | 18 |
| Cross-service integration | 3 |
| Frontend structure | 6 |
| Playwright HTTP/UI scenarios | 13 |

Latest Playwright execution: **0 passed, 0 failed, 0 skipped**. Browser results are written to ignored `reports/ui-results.json` by the UI test runner.

## Python line coverage by service

| Service/module | Statements | Covered | Missing | Coverage |
|---|---:|---:|---:|---:|
| Contract service | 148 | 144 | 4 | 97.3% |
| Pricing service | 110 | 106 | 4 | 96.4% |
| Billing service | 210 | 199 | 11 | 94.8% |
| Auth service | 40 | 37 | 3 | 92.5% |
| API gateway | 54 | 27 | 27 | 50.0% |
| Shared service helpers | 1 | 1 | 0 | 100.0% |
| Shared domain/PDF/data modules | 496 | 458 | 38 | 92.3% |
| Build scripts | 227 | 157 | 70 | 69.2% |
| **Total** | **1476** | **1255** | **221** | **85.0%** |

## Files and uncovered executable lines

| File | Statements | Covered | Missing | Coverage | Missing line numbers |
|---|---:|---:|---:|---:|---|
| `services/contract_service/__init__.py` | 0 | 0 | 0 | 100.0% | — |
| `services/contract_service/api.py` | 56 | 55 | 1 | 96.8% | 66 |
| `services/contract_service/domain.py` | 73 | 73 | 0 | 100.0% | — |
| `services/contract_service/main.py` | 19 | 16 | 3 | 84.2% | 14, 15, 16 |
| `services/pricing_service/__init__.py` | 0 | 0 | 0 | 100.0% | — |
| `services/pricing_service/api.py` | 31 | 31 | 0 | 100.0% | — |
| `services/pricing_service/domain.py` | 60 | 59 | 1 | 97.5% | 62 |
| `services/pricing_service/main.py` | 19 | 16 | 3 | 84.2% | 14, 15, 16 |
| `services/billing_service/__init__.py` | 0 | 0 | 0 | 100.0% | — |
| `services/billing_service/api.py` | 39 | 37 | 2 | 95.3% | 32, 37 |
| `services/billing_service/domain.py` | 152 | 146 | 6 | 93.2% | 106, 166, 168, 170, 172, 196 |
| `services/billing_service/main.py` | 19 | 16 | 3 | 84.2% | 14, 15, 16 |
| `services/auth_service/__init__.py` | 0 | 0 | 0 | 100.0% | — |
| `services/auth_service/api.py` | 26 | 25 | 1 | 96.7% | 14 |
| `services/auth_service/main.py` | 14 | 12 | 2 | 85.7% | 10, 11 |
| `services/api_gateway/__init__.py` | 0 | 0 | 0 | 100.0% | — |
| `services/api_gateway/main.py` | 54 | 27 | 27 | 48.4% | 24, 38, 40, 41, 42, 43, 44, 45, 46, 47, 50, 51, 53, 54, 59, 60, 61, 66, 67, 68, 70, 71, 72, 73, 74, 75, 76 |
| `services/common.py` | 1 | 1 | 0 | 100.0% | — |
| `src/apollo_wheels_mvp/__init__.py` | 3 | 2 | 1 | 66.7% | 2 |
| `src/apollo_wheels_mvp/catalog.py` | 2 | 2 | 0 | 100.0% | — |
| `src/apollo_wheels_mvp/documents.py` | 66 | 64 | 2 | 97.8% | 20, 21 |
| `src/apollo_wheels_mvp/extraction.py` | 103 | 90 | 13 | 83.4% | 36, 88, 98, 100, 104, 118, 139, 141, 147, 149, 151, 155, 159 |
| `src/apollo_wheels_mvp/main.py` | 18 | 0 | 18 | 0.0% | 3, 4, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25 |
| `src/apollo_wheels_mvp/seed.py` | 52 | 52 | 0 | 100.0% | — |
| `src/apollo_wheels_mvp/storage.py` | 25 | 25 | 0 | 100.0% | — |
| `src/apollo_wheels_mvp/synthetic.py` | 227 | 223 | 4 | 97.7% | 222, 230, 231, 241 |
| `scripts/__init__.py` | 0 | 0 | 0 | 100.0% | — |
| `scripts/generate_sample_documents.py` | 18 | 17 | 1 | 92.3% | 46 |
| `scripts/run_coverage.py` | 95 | 38 | 57 | 40.0% | 12, 13, 14, 64, 76, 77, 78, 79, 80, 82, 83, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 105, 106, 107, 108, 109, 110, 111, 112, 114, 115, 128, 134, 138, 139, 140, 141, 142, 143, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 166 |
| `scripts/run_local.py` | 97 | 92 | 5 | 92.9% | 38, 113, 127, 128, 135 |
| `scripts/run_tests.py` | 17 | 10 | 7 | 52.4% | 26, 27, 28, 29, 30, 31, 35 |

HTML detail report: [`coverage/index.html`](coverage/index.html).

Coverage is evidence about tests executed, not proof that every business requirement is correct. Review uncovered lines and the UI edge-case matrix alongside this report.
