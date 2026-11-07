"""Unit and service-layer integration coverage for pricing and approval."""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from services.pricing_service import api, domain
from services.auth import Identity
from services.test_support import setup_demo


class JsonResponse:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self):
        return json.dumps(self.value).encode()


class PricingWorkflowTests(unittest.TestCase):
    def setUp(self):
        setup_demo(self)
        self.agreement = next(a for a in domain_agreements() if a["client_id"] == "C-1001" and a["agreement_type"] == "MSA")
        self.component = {
            "agreement_id": self.agreement["id"], "billing_stream": "SERVICE", "service_code": "FUEL",
            "service_name": "Fuel", "component_code": "monthly_per_vehicle",
            "component_name": "Monthly per vehicle", "charge_type": "recurring", "amount": 4.5,
            "currency": "USD", "rate_unit": "vehicle_month", "quantity": 500,
            "billing_frequency": "monthly", "billing_day": "1", "effective_from": "2026-04-01",
            "terms": {"pricing_basis": "USD"},
        }

    def contract_api_responses(self, client=None, agreements=None):
        return [JsonResponse(client or {"id": "C-1001", "name": "Northstar Fleet Services"}),
                JsonResponse(agreements if agreements is not None else domain_agreements())]

    def test_health_and_list_pricing_include_version_and_components(self):
        self.assertEqual(api.health()["status"], "ready")
        result = api.client_pricing("C-1001", Identity("finance.alex", "finance", "user"))
        self.assertTrue(result["requests"])
        self.assertTrue(any(row["status"] == "active" for row in result["components"]))
        self.assertEqual(api.client_pricing("missing", Identity("finance.alex", "finance", "user")), {"requests": [], "components": []})

    def test_empty_agreements_or_components_rejected_before_api_call(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            domain.submit_pricing("C-1001", [], [self.component], "finance.alex")
        with self.assertRaisesRegex(ValueError, "at least one"):
            domain.submit_pricing("C-1001", [self.agreement["id"]], [], "finance.alex")

    def test_unknown_client_and_unreachable_contract_service_report_actionable_errors(self):
        with patch.object(domain, "open_service_url", side_effect=[JsonResponse(None), JsonResponse([])]):
            with self.assertRaisesRegex(ValueError, "Client not found"):
                domain.submit_pricing("missing", [self.agreement["id"]], [self.component], "finance.alex")
        with patch.object(domain, "open_service_url", side_effect=OSError("offline")):
            with self.assertRaisesRegex(ValueError, "could not reach the Contract API"):
                domain.submit_pricing("C-1001", [self.agreement["id"]], [self.component], "finance.alex")

    def test_agreement_must_belong_to_client_and_be_in_selected_set(self):
        responses = self.contract_api_responses(agreements=[])
        with patch.object(domain, "open_service_url", side_effect=responses):
            with self.assertRaisesRegex(ValueError, "reference an agreement"):
                domain.submit_pricing("C-1001", [self.agreement["id"]], [self.component], "finance.alex")

    def test_duplicate_agreement_ids_are_deduplicated_for_reference_validation(self):
        responses = self.contract_api_responses()
        with patch.object(domain, "open_service_url", side_effect=responses):
            result = domain.submit_pricing("C-1001", [self.agreement["id"], self.agreement["id"]], [self.component], "finance.alex")
        self.assertEqual(result["status"], "pending_approval")

    def test_negative_amount_or_quantity_is_rejected_and_submission_rolls_back(self):
        for field in ("amount", "quantity"):
            invalid = {**self.component, field: -1}
            with patch.object(domain, "open_service_url", side_effect=self.contract_api_responses()):
                with self.assertRaisesRegex(ValueError, "cannot be negative"):
                    domain.submit_pricing("C-1001", [self.agreement["id"]], [invalid], "finance.alex")
            self.assertEqual(sql_scalar("SELECT COUNT(*) FROM pricing_approval_requests WHERE status='pending_approval'"), 0)

    def test_component_missing_required_identity_rolls_back_request(self):
        invalid = {key: value for key, value in self.component.items() if key != "service_code"}
        with patch.object(domain, "open_service_url", side_effect=self.contract_api_responses()):
            with self.assertRaises(KeyError):
                domain.submit_pricing("C-1001", [self.agreement["id"]], [invalid], "finance.alex")
        self.assertEqual(sql_scalar("SELECT COUNT(*) FROM pricing_approval_requests WHERE status='pending_approval'"), 0)

    def test_submit_pricing_persists_pending_version_and_flexible_terms(self):
        with patch.object(domain, "open_service_url", side_effect=self.contract_api_responses()):
            request = api.request_pricing_approval(
                api.PricingSubmission(client_id="C-1001", agreement_ids=[self.agreement["id"]], components=[api.PricingComponent(**self.component)]),
                Identity("finance.alex", "finance", "user"),
            )
        self.assertEqual(request["version"], 2)
        self.assertEqual(request["status"], "pending_approval")
        saved = domain.list_client_pricing("C-1001")
        pending = next(item for item in saved["components"] if item["approval_request_id"] == request["id"])
        self.assertEqual(json.loads(pending["terms_json"]), {"pricing_basis": "USD"})

    def test_pricing_api_is_finance_owned_and_requires_a_human_finance_user(self):
        payload = api.PricingSubmission(client_id="C-1001", agreement_ids=[self.agreement["id"]], components=[api.PricingComponent(**self.component)])
        with self.assertRaises(HTTPException) as error:
            api.request_pricing_approval(payload, Identity("structuring.lee", "structuring", "user"))
        self.assertEqual(error.exception.status_code, 403)
        with self.assertRaises(HTTPException) as error:
            api.request_pricing_approval(payload, Identity("unknown", None, "service"))
        self.assertEqual(error.exception.status_code, 403)

    def test_pydantic_rejects_negative_component_amount_and_quantity(self):
        for field in ("amount", "quantity"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                api.PricingComponent(**{**self.component, field: -0.01})

    def test_approval_rejects_missing_request_self_approval_and_repeat(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            domain.approve_pricing("missing", "finance.jordan")
        request = self.create_pending_request()
        with self.assertRaisesRegex(ValueError, "cannot approve their own"):
            api.approve_pricing_request(request, Identity("finance.alex", "finance", "user"))
        result = api.approve_pricing_request(request, Identity("finance.jordan", "finance", "user"))
        self.assertEqual(result["status"], "active")
        with self.assertRaisesRegex(ValueError, "no longer awaiting"):
            domain.approve_pricing(request, "finance.kim")

    def test_second_approver_activates_and_supersedes_prior_version(self):
        request = self.create_pending_request()
        result = domain.approve_pricing(request, "finance.jordan")
        self.assertEqual(result["approved_by"], "finance.jordan")
        self.assertEqual(sql_scalar("SELECT COUNT(*) FROM pricing_components WHERE client_id='C-1001' AND status='active'"), 1)
        self.assertEqual(sql_scalar("SELECT COUNT(*) FROM pricing_components WHERE client_id='C-1001' AND status='superseded'"), 11)
        self.assertEqual(sql_scalar("SELECT status FROM agreements WHERE id=?", (self.agreement["id"],)), "active")

    def test_non_finance_cannot_approve_through_api(self):
        request = self.create_pending_request()
        with self.assertRaises(HTTPException) as error:
            api.approve_pricing_request(request, Identity("structuring.lee", "structuring", "user"))
        self.assertEqual(error.exception.status_code, 403)

    def create_pending_request(self):
        with patch.object(domain, "open_service_url", side_effect=self.contract_api_responses()):
            return domain.submit_pricing("C-1001", [self.agreement["id"]], [self.component], "finance.alex")["id"]


def domain_agreements():
    from services.contract_service.domain import list_agreements
    return list_agreements()


def sql_scalar(query, params=()):
    from apollo_wheels_mvp.storage import DATABASE_PATH
    with closing(sqlite3.connect(DATABASE_PATH)) as db:
        return db.execute(query, params).fetchone()[0]


if __name__ == "__main__":
    unittest.main()

