from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "prc_legal_risk_audit.py"
SPEC = importlib.util.spec_from_file_location("prc_legal_risk_audit", MODULE_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class PrcLegalRiskAuditTests(unittest.TestCase):
    def _run(self, workflow_id: str, ticket: dict) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            output_dir = root / "artifacts"
            github_output = root / "github-output.txt"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            with mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(github_output)}, clear=False):
                status = AUDIT._preflight(workflow_id, ticket_path, output_dir)
            receipt = json.loads((output_dir / "prc-legal-risk-audit.json").read_text(encoding="utf-8"))
            self.assertNotIn("dummy-secret-value", json.dumps(receipt, ensure_ascii=False))
            self.assertFalse(receipt["secret_or_real_name_values_recorded"])
            return status, receipt

    def test_registry_is_complete_and_valid(self) -> None:
        registry = AUDIT._load_json(AUDIT.REGISTRY_PATH)
        AUDIT._validate_registry(registry)
        self.assertGreaterEqual(len(registry["providers"]), 8)
        self.assertGreaterEqual(len(registry["workflows"]), 8)
        for provider in registry["providers"].values():
            self.assertTrue(provider["secret_environment_variables"])

    def test_fixed_attributable_provider_is_audited_and_allowed_with_controls(self) -> None:
        status, receipt = self._run(
            ".github/workflows/yuandian-api-ticket.yml",
            {
                "provider_id": "yuandian",
                "operation_id": "search-cases",
                "data_policy": {"contains_personal_data": False},
                "test_secret": "dummy-secret-value",
            },
        )
        self.assertEqual(status, 0)
        self.assertTrue(receipt["accepted"])
        self.assertEqual(receipt["decision"], "ALLOW_WITH_CONTROLS")
        self.assertEqual(receipt["identity_attribution_state"], "ATTRIBUTABLE")
        self.assertEqual(receipt["jurisdiction_profile"], "PRC_STRICT")
        self.assertTrue(receipt["trace_records"])
        self.assertTrue(receipt["required_controls"])

    def test_local_catalog_operation_does_not_inject_upstream_risk(self) -> None:
        status, receipt = self._run(
            ".github/workflows/qweather-api-ticket.yml",
            {"provider_id": "qweather", "operation_id": "catalog-capabilities"},
        )
        self.assertEqual(status, 0)
        self.assertEqual(receipt["decision"], "NOT_APPLICABLE")
        self.assertIn("LOCAL_OPERATION_NO_UPSTREAM_COLLECTION", receipt["reason_codes"])

    def test_personal_or_restricted_data_declaration_is_blocked(self) -> None:
        status, receipt = self._run(
            ".github/workflows/tushare-api-ticket.yml",
            {
                "provider_id": "tushare",
                "operation_id": "daily-market",
                "data_policy": {"contains_personal_data": True},
            },
        )
        self.assertEqual(status, 2)
        self.assertFalse(receipt["accepted"])
        self.assertEqual(receipt["decision"], "BLOCK")
        self.assertTrue(receipt["blocking_findings"])

    def test_company_workflow_is_fixed_to_tianyancha(self) -> None:
        status, receipt = self._run(
            ".github/workflows/company-intelligence-api-ticket.yml",
            {
                "provider": "tianyancha",
                "operation": "company-basic",
                "parameters": {"keyword": "example"},
            },
        )
        self.assertEqual(status, 0)
        self.assertEqual(receipt["provider_id"], "tianyancha")
        self.assertEqual(receipt["channel_tier"], "ORANGE_DEDICATED")

    def test_external_distribution_requires_review(self) -> None:
        status, receipt = self._run(
            ".github/workflows/aifin-api-ticket.yml",
            {
                "provider_id": "aifin-market",
                "operation_id": "stock-quote",
                "distribution_scope": "external",
            },
        )
        self.assertEqual(status, 2)
        self.assertEqual(receipt["decision"], "REVIEW_REQUIRED")
        self.assertTrue(receipt["review_findings"])

    def test_unregistered_workflow_fails_closed(self) -> None:
        status, receipt = self._run(
            ".github/workflows/unknown.yml",
            {"provider_id": "yuandian", "operation_id": "search-cases"},
        )
        self.assertEqual(status, 2)
        self.assertEqual(receipt["decision"], "REVIEW_REQUIRED")
        self.assertIn("WORKFLOW_NOT_REGISTERED", receipt["reason_codes"])


if __name__ == "__main__":
    unittest.main()
