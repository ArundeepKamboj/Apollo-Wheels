"""Provider-boundary, evidence, and malformed-output tests for agreement extraction."""

from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from apollo_wheels_mvp.documents import extract_pdf_pages
from apollo_wheels_mvp.extraction import extract_agreement_terms, extract_with_ollama, validate_terms
from services.test_support import PROJECT_ROOT


class JsonResponse:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self):
        return json.dumps(self.value).encode()


class ExtractionProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = PROJECT_ROOT / "samples/contracts/Northstar_Fleet_Services/northstar_msa_v1.pdf"
        cls.pages = extract_pdf_pages(path)
        cls.source_page, cls.source_row = next(
            (index, line) for index, page in enumerate(cls.pages, start=1)
            for line in page.splitlines() if line.startswith("SERVICE|FUEL|")
        )

    def service_item(self, **changes):
        value = {
            "service_code": "FUEL", "service_name": "Fuel", "subscribed": True,
            "billing_stream": "SERVICE", "component_name": "monthly_per_vehicle",
            "contract_amount": 4.5, "rate_unit": "vehicle_month", "charge_type": "recurring",
            "pricing_basis": "USD", "billing_frequency": "monthly", "billing_day": "1",
            "vehicle_count": 500, "driver_count": None, "source_text": self.source_row,
            "evidence_page": self.source_page,
        }
        return {**value, **changes}

    def model_response(self, item=None, content=None):
        terms = {"services": [item or self.service_item()], "components": [], "lease": None}
        response_text = content if content is not None else json.dumps(terms)
        return JsonResponse({"message": {"content": response_text}})

    def test_synthetic_provider_extracts_msa_and_mla_with_page_evidence(self):
        mla = extract_pdf_pages(PROJECT_ROOT / "samples/contracts/Northstar_Fleet_Services/northstar_mla_v1.pdf")
        with patch.dict(os.environ, {"LLM_PROVIDER": "synthetic"}):
            msa_terms = extract_agreement_terms(self.pages, "MSA")
            mla_terms = extract_agreement_terms(mla, "MLA")
        self.assertEqual(len(msa_terms["services"]), 13)
        self.assertEqual(msa_terms["extraction_provider"], "synthetic")
        self.assertGreaterEqual(mla_terms["lease"]["evidence_page"], 2)
        self.assertEqual(msa_terms["services"][0]["evidence_page"], self.source_page)
        self.assertIn("LEASE|", mla_terms["lease"]["source_text"])

    def test_unknown_provider_is_rejected(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "unsupported"}):
            with self.assertRaisesRegex(ValueError, "Unknown LLM_PROVIDER"):
                extract_agreement_terms(self.pages, "MSA")

    def test_valid_ollama_response_is_validated_and_marked_uncalibrated(self):
        with patch("apollo_wheels_mvp.extraction.urlopen", self._urlopen(self.model_response())):
            with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "test-model"}):
                result = extract_with_ollama(self.pages, "MSA")
        self.assertEqual(result["extraction_provider"], "ollama")
        self.assertEqual(result["extraction_model"], "test-model")
        self.assertEqual(result["services"][0]["field_confidence"], {})
        self.assertIn("not calibrated", result["services"][0]["confidence_method"])

    def test_ollama_timeout_and_malformed_json_return_actionable_errors(self):
        with patch("apollo_wheels_mvp.extraction.urlopen", side_effect=TimeoutError("timeout")):
            with self.assertRaisesRegex(ValueError, "Could not get extraction"):
                extract_with_ollama(self.pages, "MSA")
        with patch("apollo_wheels_mvp.extraction.urlopen", self._urlopen(self.model_response(content="not json"))):
            with self.assertRaisesRegex(ValueError, "invalid agreement extraction"):
                extract_with_ollama(self.pages, "MSA")

    def test_ollama_rejects_wrong_stream_missing_fields_bad_page_and_unverifiable_quote(self):
        cases = (
            (self.service_item(billing_stream="LEASE"), "stream must be SERVICE"),
            ({"service_code": "FUEL"}, "missing required fields"),
            (self.service_item(evidence_page=0), "invalid evidence page"),
            (self.service_item(source_text="not in source"), "does not match the source"),
            (self.service_item(contract_amount=-1), "non-negative number"),
        )
        for item, message in cases:
            with self.subTest(message=message), patch("apollo_wheels_mvp.extraction.urlopen", self._urlopen(self.model_response(item))):
                with self.assertRaisesRegex(ValueError, message):
                    extract_with_ollama(self.pages, "MSA")

    def test_ollama_normalizes_unknown_service_code_but_rejects_wrong_agreement_shape(self):
        with patch("apollo_wheels_mvp.extraction.urlopen", self._urlopen(self.model_response(self.service_item(service_code="made-up")))):
            result = extract_with_ollama(self.pages, "MSA")
        self.assertEqual(result["services"][0]["service_code"], "UNKNOWN")
        wrong_shape = {"services": [self.service_item()], "components": [], "lease": {}}
        with self.assertRaisesRegex(ValueError, "cannot include a lease"):
            validate_terms(wrong_shape, self.pages, "MSA")

    @staticmethod
    def _urlopen(response):
        return lambda *_args, **_kwargs: response


if __name__ == "__main__":
    unittest.main()
