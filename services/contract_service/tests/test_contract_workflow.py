"""Unit and service-layer integration coverage for contract intake and review."""

from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from services.auth import Identity
from apollo_wheels_mvp.synthetic import make_text_pdf
from apollo_wheels_mvp.extraction import detect_agreement_type
from services.contract_service import api, domain
from services.contract_service.api import TermsUpdate
from services.test_support import MemoryUpload, PROJECT_ROOT, run_upload, setup_demo


class ContractWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_demo(self)

    def upload(self, filename="agreement.pdf", data=None):
        if data is None:
            data = (PROJECT_ROOT / "samples/contracts/Northstar_Fleet_Services/northstar_msa_v1.pdf").read_bytes()
        return MemoryUpload(filename, data)

    def test_health_and_bootstrap_expose_services_and_seed_counts(self):
        self.assertEqual(api.health()["status"], "ready")
        result = api.bootstrap()
        self.assertEqual(result["counts"]["clients"], 3)
        self.assertEqual(len(result["services"]), 13)

    def test_client_lookup_and_not_found(self):
        actor = Identity("finance.alex", "finance", "user")
        self.assertEqual(api.get_client("C-1001", actor)["name"], "Northstar Fleet Services")
        with self.assertRaises(HTTPException) as error:
            api.get_client("missing", actor)
        self.assertEqual(error.exception.status_code, 404)

    def test_agreement_listing_is_scoped_to_client(self):
        actor = Identity("finance.alex", "finance", "user")
        self.assertEqual(len(api.client_agreements("C-1001", actor)), 2)
        self.assertEqual(api.client_agreements("unknown", actor), [])

    def test_pdf_endpoint_returns_file_response_and_missing_id_is_404(self):
        agreement = domain.list_agreements("C-1001")[0]
        response = api.agreement_pdf(agreement["id"])
        self.assertTrue(Path(response.path).is_file())
        with self.assertRaises(HTTPException) as error:
            api.agreement_pdf("missing")
        self.assertEqual(error.exception.status_code, 404)

    def test_upload_msa_and_mla_and_persist_extracted_values(self):
        msa = run_upload(domain.store_upload("C-1001", None, self.upload(), "structuring:lee"))
        self.assertEqual(msa["agreement_type"], "MSA")
        self.assertEqual(len(msa["extracted"]["services"]), 13)
        mla_bytes = (PROJECT_ROOT / "samples/contracts/Northstar_Fleet_Services/northstar_mla_v1.pdf").read_bytes()
        mla = run_upload(domain.store_upload("C-1001", None, self.upload("lease.pdf", mla_bytes), "finance:alex"))
        self.assertEqual(mla["agreement_type"], "MLA")
        self.assertEqual(mla["extracted"]["lease"]["vehicle_model"], "Transit")
        self.assertIn(msa["id"], {row["id"] for row in domain.list_agreements("C-1001")})

    def test_test_client_accepts_both_standalone_upload_samples(self):
        folder = PROJECT_ROOT / "samples/test_uploads/Test_Client"
        msa = run_upload(domain.store_upload(
            "C-TEST", None, self.upload("test_client_msa_v1.pdf", (folder / "test_client_msa_v1.pdf").read_bytes()),
            "structuring:lee",
        ))
        mla = run_upload(domain.store_upload(
            "C-TEST", None, self.upload("test_client_mla_v1.pdf", (folder / "test_client_mla_v1.pdf").read_bytes()),
            "structuring:lee",
        ))
        self.assertEqual((msa["agreement_type"], mla["agreement_type"]), ("MSA", "MLA"))
        self.assertEqual(len(msa["extracted"]["services"]), 13)
        self.assertEqual(mla["extracted"]["lease"]["quantity"], 300)

    def test_agreement_type_is_detected_from_titles_when_not_declared(self):
        self.assertEqual(detect_agreement_type(["MASTER SERVICES AGREEMENT", "Fleet service charges"]), "MSA")
        self.assertEqual(detect_agreement_type(["MASTER LEASE AGREEMENT", "Lessor and Lessee"]), "MLA")
        with self.assertRaisesRegex(ValueError, "Could not determine"):
            detect_agreement_type(["Commercial agreement", "No service or lease title"])

    def test_explicit_agreement_type_cannot_override_pdf_classification(self):
        mla_bytes = (PROJECT_ROOT / "samples/contracts/Northstar_Fleet_Services/northstar_mla_v1.pdf").read_bytes()
        with self.assertRaisesRegex(ValueError, "identified as MLA"):
            run_upload(domain.store_upload("C-1001", "MSA", self.upload("lease.pdf", mla_bytes), "structuring:lee"))

    def test_api_allows_both_internal_roles_to_upload(self):
        for role, user in (("structuring", "structuring.lee"), ("finance", "finance.alex")):
            result = run_upload(api.upload_agreement("C-1001", "MSA", self.upload(), Identity(user, role, "user")))
            self.assertEqual(result["uploaded_by"], f"{role}:{user}")

    def test_invalid_agreement_type_extension_magic_and_client_are_rejected(self):
        for agreement_type, filename, data, client_id, message in (
            ("SOW", "a.pdf", b"%PDF-x", "C-1001", "MSA or MLA"),
            ("MSA", "a.txt", b"%PDF-x", "C-1001", "PDF file"),
            ("MSA", "a.pdf", b"not pdf", "C-1001", "valid PDF"),
            ("MSA", "a.pdf", b"%PDF-x", "missing", "existing client"),
        ):
            with self.subTest(agreement_type=agreement_type, filename=filename, client=client_id):
                with self.assertRaisesRegex(ValueError, message):
                    run_upload(domain.store_upload(client_id, agreement_type, self.upload(filename, data), "u"))

    def test_upload_rejects_file_larger_than_20_megabytes(self):
        with self.assertRaisesRegex(ValueError, "20 MB"):
            run_upload(domain.store_upload("C-1001", "MSA", self.upload(data=b"%PDF" + b"x" * (20 * 1024 * 1024)), "u"))

    def test_corrupt_or_image_only_pdf_is_rejected_and_temporary_file_removed(self):
        with self.assertRaises(Exception):
            run_upload(domain.store_upload("C-1001", "MSA", self.upload(data=b"%PDF broken"), "u"))
        with self.assertRaisesRegex(ValueError, "no selectable text"):
            run_upload(domain.store_upload("C-1001", "MSA", self.upload(data=make_text_pdf([""])), "u"))
        self.assertEqual(list((self.root / "documents").glob("*agreement.pdf")), [])

    def test_extraction_failure_removes_saved_upload(self):
        with patch.object(domain, "extract_agreement_terms", side_effect=ValueError("provider failed")):
            with self.assertRaisesRegex(ValueError, "provider failed"):
                run_upload(domain.store_upload("C-1001", "MSA", self.upload(), "u"))
        self.assertEqual(list((self.root / "documents").glob("*agreement.pdf")), [])

    def test_structuring_can_edit_and_finance_is_read_only(self):
        agreement_id = domain.list_agreements("C-1001")[0]["id"]
        edited = api.edit_terms(agreement_id, TermsUpdate(extracted={"services": [], "components": [], "lease": None}), Identity("structuring.lee", "structuring", "user"))
        self.assertEqual(edited["extracted"]["services"], [])
        with self.assertRaises(HTTPException) as error:
            api.edit_terms(agreement_id, TermsUpdate(extracted={}), Identity("finance.alex", "finance", "user"))
        self.assertEqual(error.exception.status_code, 403)

    def test_edit_of_unknown_agreement_returns_value_error(self):
        with self.assertRaisesRegex(ValueError, "Agreement not found"):
            domain.update_extracted_terms("missing", {})

    def test_save_version_archives_old_and_creates_new_version_with_regenerated_pdf(self):
        agreements = domain.list_agreements("C-1001")
        agreement = agreements[0]  # This is an MSA
        original_path = Path(agreement["file_path"])
        self.assertTrue(original_path.is_file())

        new_terms = dict(agreement["extracted"])
        new_terms["services"] = [dict(new_terms["services"][0], contract_amount=9.99)]

        saved = domain.save_agreement_version(
            agreement["id"], new_terms, "regen-test", "structuring:lee",
        )

        # New version is active, old version is archived, version incremented.
        self.assertEqual(saved["version"], agreement["version"] + 1)
        self.assertEqual(saved["status"], "review")
        self.assertEqual(saved["uploaded_by"], "structuring:lee")
        self.assertEqual(saved["update_comment"], "regen-test")
        self.assertEqual(saved["extracted"]["services"][0]["contract_amount"], 9.99)
        self.assertTrue(Path(saved["file_path"]).is_file())

        all_versions = domain.list_agreements("C-1001", active_only=False)
        msa_versions = [row for row in all_versions if row["id"] == agreement["id"] or row["id"] == saved["id"]]
        self.assertEqual(len(msa_versions), 2)

        # The saved version should be active
        active = [row for row in msa_versions if row["is_active"] == 1]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["id"], saved["id"])

        # The old version should be archived (inactive)
        archived = [row for row in msa_versions if row["is_active"] == 0]
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0]["status"], "archived")

    def test_save_version_unknown_agreement_returns_value_error(self):
        with self.assertRaisesRegex(ValueError, "Agreement not found"):
            domain.save_agreement_version("missing", {}, "comment", "structuring:lee")

    def test_invoice_history_setting_is_finance_owned_and_client_scoped(self):
        result = api.set_invoice_history("C-1001", api.InvoiceHistorySetting(enabled=True), Identity("finance.alex", "finance", "user"))
        self.assertTrue(result["include_history_on_invoice"])
        with self.assertRaises(HTTPException) as error:
            api.set_invoice_history("C-1001", api.InvoiceHistorySetting(enabled=False), Identity("structuring.lee", "structuring", "user"))
        self.assertEqual(error.exception.status_code, 403)
        with self.assertRaises(HTTPException) as error:
            api.set_invoice_history("missing", api.InvoiceHistorySetting(enabled=True), Identity("finance.alex", "finance", "user"))
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
