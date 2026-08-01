from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gapup_mcp_task", ROOT / "gapup_mcp_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)

BLOCKED = ['adversarial_input_stress_tester', 'affiliate_fraud_clickstream_detector', 'ai_governance_full_report_async', 'ai_governance_full_report_result', 'anti_demissions_hr', 'attack_surface_monitor', 'bias_amplification_tracker', 'candidate_screening_ranking', 'clinical_evidence_briefer', 'clinical_pharma_intel', 'comp_benchmark_geo_delta', 'comp_plan_architect', 'competitive_deep_dive_async', 'competitive_deep_dive_result', 'contract_risk_scanner', 'crm_connector', 'crypto_wallet_intel', 'diversity_inclusion_metrics', 'dpdp_consent_artifact_generator', 'email_domain_health_check', 'enps_auto', 'executive_comp_peer_benchmark', 'fraud_detector', 'global_salary_inflation_adjuster', 'hallucination_confidence_meter', 'hr_benefits_esg_aligner', 'incident_response_evidence_collector', 'ip_contract_clause_extractor', 'ip_employee_invention_tracker', 'jailbreak_attempt_detector', 'job_result', 'kyc_screener', 'kyc_screener_batch', 'kyc_screener_batch_result', 'ld_architect', 'legal_clause_extractor', 'lgpd_data_subject_rights_automator', 'model_behavior_drift_monitor', 'model_safety_certification_checker', 'onboarding_salaries', 'patent_landscape_async', 'patent_landscape_result', 'pentest_scope_estimator', 'realtime_data_streams', 'recruiting_architect', 'sabbatical_policy_comparator', 'safety_guardrail_breach_analyzer', 'safety_violation_incident_logger', 'sanctions_screener_multi', 'social_influencer_fake_follower_detector', 'talent_contract_risk_mapper', 'talent_intelligence', 'talent_legal_dashboard', 'talent_litigation_exposure', 'talent_poaching_risk', 'tool_recommend', 'ugc_moderation_classifier', 'usdc_x402_payments_intel', 'webhooks_manage', 'workflow_orchestrator', 'x402_liquidity_monitor', 'x402_payment_flow_analyzer', 'x402_payment_fraud_detector']


class FakeRaw:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
    def read(self, size: int, decode_content: bool = True) -> bytes:
        return self.payload[:size]


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200, content_type: str = "application/json") -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.raw = FakeRaw(raw)
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.is_redirect = False


class GapupMcpTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "gapup-test-001",
            "provider": "gapup-mcp",
            "operation": operation,
            "objective": "test bounded Gapup intelligence provider",
            "parameters": parameters or {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
                "contains_confidential_data": False,
            },
            "payment_policy": {"automatic_x402_payment_authorized": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1_000_000},
        }

    def test_catalog_is_fixed_and_excludes_blocked_tools(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        ids = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(provider["provider_id"], "gapup-mcp")
        self.assertEqual(provider["required_secret_environment_variable"], "GAPUP_API_KEY")
        self.assertEqual(len(ids), 209)
        self.assertEqual(provider["limits"]["fixed_mcp_tool_count"], 208)
        self.assertEqual(provider["limits"]["official_tool_count"], 271)
        self.assertFalse(set(BLOCKED) & ids)
        self.assertIn("china_market_data", ids)
        self.assertIn("competitive_deep_dive", ids)
        self.assertIn("research_paper_qa", ids)
        self.assertFalse(provider["limits"]["automatic_x402_payment_allowed"])
        self.assertFalse(provider["limits"]["async_jobs_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_ticket_schema_rejects_every_blocked_operation(self):
        for operation in BLOCKED:
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    task.validate_ticket(self.ticket(operation, {}), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_key_is_backend_only_and_prefixed(self):
        with patch.dict(os.environ, {"GAPUP_API_KEY": "gpk_test_key_12345"}, clear=False):
            self.assertEqual(task.api_key(), "gpk_test_key_12345")
        with patch.dict(os.environ, {"GAPUP_API_KEY": "wrong"}, clear=False):
            with self.assertRaises(task.GapupMcpError):
                task.api_key()

    def test_parameter_guard_blocks_private_urls_personal_data_and_control_fields(self):
        for payload in (
            {"url": "http://example.com"},
            {"url": "https://127.0.0.1/a"},
            {"url": "https://169.254.169.254/latest"},
            {"contact": "analyst@example.com"},
            {"api_key": "gpk_secret_123456"},
            {"async": True},
            {"callback_url": "https://example.com/callback"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    task.validate_public_parameters(payload)
        task.validate_public_parameters({"url": "https://example.com/public", "company": "Yonghui Superstores"})

    def test_local_catalog_needs_no_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_GAPUP_MCP_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_mocked_tool_call_succeeds_and_never_persists_key(self):
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": json.dumps({"classification": "Retail Trade"})}]},
        }
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"GAPUP_API_KEY": "gpk_test_key_12345"}, clear=False
        ), patch.object(task.requests, "post", return_value=FakeResponse(response)):
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(
                json.dumps(self.ticket("industry_classifier_naics_sic", {"company_description": "Publicly listed supermarket and omnichannel retail operator serving consumers through physical stores, supply-chain services, and digital commerce.", "company_name": "Yonghui Superstores"})),
                encoding="utf-8",
            )
            self.assertEqual(task.execute(ticket_path, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_GAPUP_MCP_COMPLETED")
            self.assertTrue(diagnostics["metadata"]["upstream_called"])
            for path in out.iterdir():
                if path.is_file():
                    self.assertNotIn(b"gpk_test_key_12345", path.read_bytes())

    def test_x402_payment_is_fail_closed(self):
        with patch.dict(os.environ, {"GAPUP_API_KEY": "gpk_test_key_12345"}, clear=False), patch.object(
            task.requests, "post", return_value=FakeResponse({"error": "payment_required"}, status_code=402)
        ):
            with self.assertRaises(task.GapupMcpError) as caught:
                task.query_gapup("industry_classifier_naics_sic", {"company_description": "retailer"}, timeout=30, max_bytes=100000)
            self.assertEqual(caught.exception.code, "GAPUP_MCP_PAYMENT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
