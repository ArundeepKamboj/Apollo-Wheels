# Sample documents

These 18 selectable-text PDFs are synthetic examples for local development and manual workflow checks. They contain no real client data.

## Contracts

`contracts/<client>/` contains one MSA and one MLA for each demo client. Their legal clause wording is rendered from the supplied project templates: [MSA template](../master_service_agreement_Template_and_Field_Guide.md) and [MLA template](../master_lease_agreement_template_and_field_guide.md). Field guides and analysis checklists are excluded. Unavailable transaction-specific or legal values are visibly marked `Synthetic demo value (review required)`; these are prototype drafts, not approved or execution-ready agreements. The generated files include formatted headings, client and agreement details, readable schedules, and page numbers. The MSA includes all 13 service catalogue entries, with nine marked as subscribed, plus a one-time Fuel setup charge. The checked-in MLAs currently use one vehicle type each; the extraction, editor, save, and pricing paths support multiple vehicle rows with distinct quantities and rates. See [the field guide](../docs/DATA_AND_FIELD_GUIDE.md) and [assumptions log](../docs/ASSUMPTIONS.md) for field meanings and caveats.

## Billing

`billing/<client>/<service-or-lease>/` contains statements for January, February, and March 2026. SERVICE statements include the nine services marked subscribed in the matching MSA; their rates, units and quantities align with its schedule, except for the intentional February RR rate difference so the audit screen has a discrepancy to find. The lease statement quantity and per-vehicle monthly rate match that client's MLA. January also includes the one-time Fuel setup charge.

## Upload parser fixtures

`test_uploads/Test_Client/test_client_msa_v1.pdf` and `test_client_mla_v1.pdf` are standalone synthetic parser fixtures. They are used by extraction tests and can also be uploaded to exercise creating a new client from a parsed agreement.

The samples can be regenerated from the project root with:

```powershell
uv run python scripts/generate_sample_documents.py
```

Generated sample names include the effective period, billing stream, client/invoice identifier, or agreement type/version. Runtime contract seeding copies the four agreements from `contracts/<client>/` into the document store; the app starts with no billing history.
