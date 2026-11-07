"""Fast Python checks that keep the frontend page and behavior hooks intact."""

from pathlib import Path
import re
import unittest


FRONTEND_ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (FRONTEND_ROOT / "index.html").read_text(encoding="utf-8")
        cls.js = (FRONTEND_ROOT / "app.js").read_text(encoding="utf-8")
        cls.css = (FRONTEND_ROOT / "styles.css").read_text(encoding="utf-8")

    def test_entry_page_loads_styles_config_and_application(self):
        for asset in ("/styles.css", "/runtime-config.js", "/app.js"):
            with self.subTest(asset=asset):
                self.assertIn(asset, self.html)
                self.assertTrue((FRONTEND_ROOT / asset.lstrip("/")).is_file())

    def test_page_has_login_workspace_and_accessible_toast(self):
        for selector in ('id="user-label"', 'id="logout"', 'id="main"', 'id="toast"',
                         'data-page="overview"', 'data-page="contracts"',
                         'data-page="pricing"', 'data-page="billing"'):
            with self.subTest(selector=selector):
                self.assertIn(selector, self.html)
        self.assertRegex(self.html, r'id="toast"[^>]*role="status"')

    def test_client_request_auth_and_upload_ui_hooks_are_present(self):
        hooks = (
            "async function login(event)", "function clientPicker(allowEmpty=false)", "function serviceUrl(path)",
            "async function uploadAgreement(e)", "async function saveTerms()",
            "async function loadAgreementPdf(agreementId)", "async function downloadAgreementPdf(agreement)",
            "className='pdf-page'", "aria-label=\"Scrollable source PDF\"",
            "async function uploadBilling(e)", "async function filterReport(kind)",
            "Authorization:`Bearer ${state.token}`", "#agreement-upload", "#billing-upload",
        )
        for hook in hooks:
            with self.subTest(hook=hook):
                self.assertIn(hook, self.js)
        self.assertIn("Type selection is optional and checked against the document.", self.js)
        self.assertIn('name="agreement_type"', self.js)
        self.assertIn('id="existing-client-picker"', self.js)
        self.assertIn('id="upload-client-picker"', self.js)
        self.assertIn("state.contractExistingClientId=null", self.js)
        self.assertIn("state.contractUploadClientId", self.js)
        self.assertIn("viewer.dataset.state='ready'", self.js)
        self.assertIn("Could not display this PDF.", self.js)
        self.assertIn("new pdfjs.TextLayer", self.js)
        self.assertIn("function bindEvidenceHighlights()", self.js)
        self.assertIn("pdf-text-highlight", self.css)
        self.assertIn("function renderAgreementFacts(agreement)", self.js)
        self.assertIn("class=\"agreement-facts\"", self.js)

    def test_role_specific_edit_and_approval_controls_are_encoded(self):
        self.assertGreaterEqual(self.js.count("state.role !== 'structuring'"), 1)
        self.assertGreaterEqual(self.js.count("state.role!=='finance'"), 3)
        self.assertIn("r.initiated_by===state.userId", self.js)
        self.assertIn("approve-btn", self.js)

    def test_display_rate_formats_usd_percent_and_basis_points(self):
        for basis in ("USD", "PERCENTAGE", "BASIS_POINTS"):
            with self.subTest(basis=basis):
                self.assertIn(basis, self.js)

    def test_rendered_page_functions_and_error_recovery_exist(self):
        for name in ("renderOverview", "renderContracts", "renderPricing", "renderBilling", "renderTermsEditor"):
            with self.subTest(name=name):
                self.assertRegex(self.js, rf"function {name}\(")
        self.assertIn("Could not load the workspace", self.js)
        self.assertIn("Something went wrong", self.js)
        self.assertRegex(self.css, r"\.toast")


if __name__ == "__main__":
    unittest.main()
