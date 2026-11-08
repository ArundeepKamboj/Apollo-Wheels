"""Check that the checked-in PDF samples match the documented marker fields."""

from pathlib import Path
import unittest

from apollo_wheels_mvp.documents import (
    extract_pdf_pages,
    extract_pdf_text,
    parse_billing_rows,
    parse_lease_row,
    parse_service_rows,
)
from apollo_wheels_mvp.extraction import detect_agreement_type


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLES = PROJECT_ROOT / "samples"


class SampleDocumentTests(unittest.TestCase):
    def test_agreement_pdf_is_paginated_and_contains_readable_terms_and_source_appendix(self):
        path = SAMPLES / "contracts" / "Northstar_Fleet_Services" / "northstar_msa_v1.pdf"
        pages = extract_pdf_pages(path)
        text = "\n".join(pages)

        self.assertGreaterEqual(len(pages), 3)
        self.assertIn("SECTION: 2. Definitions and interpretation", text)
        self.assertIn("SECTION: 5. Fees, invoicing and payment", text)
        self.assertIn("IN WITNESS WHEREOF", text)
        self.assertIn("PROVIDER:", text)
        self.assertNotIn("drafting template", text.lower())
        self.assertIn("Schedule 1 forms part of this Agreement", text)
        self.assertIn("Service code: FUEL", text)

    def test_each_msa_contains_all_services_and_nine_subscriptions(self):
        msa_files = list((SAMPLES / "contracts").rglob("*msa*.pdf"))
        self.assertEqual(len(msa_files), 2)

        for path in msa_files:
            services = parse_service_rows(extract_pdf_text(path))
            self.assertEqual(len(services), 13)
            self.assertEqual(sum(row["subscribed"] for row in services), 9)

    def test_msa_has_rate_types_and_driver_count(self):
        path = SAMPLES / "contracts" / "Northstar_Fleet_Services" / "northstar_msa_v1.pdf"
        services = parse_service_rows(extract_pdf_text(path))
        by_code = {row["service_code"]: row for row in services}

        self.assertEqual(by_code["MVR_SAFETY"]["driver_count"], 600)
        self.assertEqual(by_code["TELEMATICS"]["pricing_basis"], "PERCENTAGE")
        self.assertEqual(by_code["REMARKETING"]["pricing_basis"], "BASIS_POINTS")

    def test_mla_contains_lease_and_vehicle_details(self):
        path = SAMPLES / "contracts" / "Northstar_Fleet_Services" / "northstar_mla_v1.pdf"
        lease = parse_lease_row(extract_pdf_text(path))

        self.assertEqual(lease["quantity"], 500)
        self.assertEqual(lease["term_months"], 48)
        self.assertEqual(lease["vehicle_make"], "Ford")
        self.assertEqual(lease["vehicle_model"], "Transit")
        self.assertEqual(lease["engine_type"], "Hybrid")
        self.assertEqual(lease["contract_amount"], 1200.0)

    def test_test_client_upload_pdfs_detect_and_extract_as_msa_and_mla(self):
        folder = SAMPLES / "test_uploads" / "Test_Client"
        msa_pages = extract_pdf_pages(folder / "test_client_msa_v1.pdf")
        mla_pages = extract_pdf_pages(folder / "test_client_mla_v1.pdf")
        msa_text = "\n".join(msa_pages)
        mla_text = "\n".join(mla_pages)
        self.assertGreaterEqual(len(msa_pages), 10)
        self.assertGreaterEqual(len(mla_pages), 9)
        self.assertEqual(detect_agreement_type([msa_text]), "MSA")
        self.assertEqual(detect_agreement_type([mla_text]), "MLA")
        self.assertEqual(len(parse_service_rows(msa_text)), 13)
        self.assertEqual(parse_lease_row(mla_text)["quantity"], 300)

    def test_lease_invoice_matches_each_clients_mla_rate_and_quantity(self):
        for client, prefix, quantity, rate in (("Northstar_Fleet_Services", "northstar", 500, 1200.0),
                                               ("Blue_River_Logistics", "blueriver", 300, 1050.0)):
            mla = parse_lease_row(extract_pdf_text(SAMPLES / "contracts" / client / f"{prefix}_mla_v1.pdf"))
            invoice_path = next((SAMPLES / "billing" / client / "lease").glob("*jan*"))
            line = parse_billing_rows(extract_pdf_text(invoice_path))[0]
            self.assertEqual((mla["quantity"], mla["contract_amount"]), (quantity, rate))
            self.assertEqual((line["quantity"], line["rate"], line["amount"]),
                             (quantity, rate, quantity * rate))

    def test_january_service_billing_matches_msa_rates_units_and_quantities(self):
        for client, prefix in (("Northstar_Fleet_Services", "northstar"),
                               ("Blue_River_Logistics", "blueriver")):
            agreement = parse_service_rows(extract_pdf_text(
                SAMPLES / "contracts" / client / f"{prefix}_msa_v1.pdf"))
            invoice_path = next((SAMPLES / "billing" / client / "service").glob("*jan*"))
            invoice = parse_billing_rows(extract_pdf_text(invoice_path))
            terms = {row["service_code"]: row for row in agreement if row["subscribed"]}
            lines = {row["service_code"]: row for row in invoice if row["charge_type"] == "recurring"}
            self.assertEqual(set(terms), set(lines))
            for code, term in terms.items():
                line = lines[code]
                expected_quantity = term["vehicle_count"] or term["driver_count"] or 1
                self.assertEqual((line["rate"], line["rate_unit"], line["quantity"]),
                                 (term["contract_amount"], term["rate_unit"], expected_quantity))

    def test_february_service_invoice_has_intentional_rr_rate_difference(self):
        path = next((SAMPLES / "billing" / "Northstar_Fleet_Services" / "service").glob("*feb*"))
        rows = parse_billing_rows(extract_pdf_text(path))
        rr = next(row for row in rows if row["service_code"] == "RR")

        self.assertEqual(len(rows), 9)
        self.assertEqual(rr["rate"], 8.5)


if __name__ == "__main__":
    unittest.main()
