from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "china_intelligence_controls",
    ROOT / "china_intelligence_controls.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ChinaIntelligenceControlTests(unittest.TestCase):
    def test_all_controls_validate(self) -> None:
        receipt = MODULE.validate_all()
        self.assertEqual(receipt["status"], "CHINA_ENTERPRISE_SOCIAL_DAILY_CONTROLS_VALIDATED")
        self.assertEqual(receipt["enterprise_domain_count"], 20)
        self.assertEqual(receipt["social_platform_count"], 5)
        self.assertEqual(receipt["social_metric_count"], 70)
        self.assertEqual(receipt["daily_neuron_budget"], 9800)
        self.assertEqual(receipt["daily_browser_second_budget"], 570)
        self.assertFalse(receipt["raw_text_persisted"])
        self.assertTrue(receipt["numeric_huggingface_payload_only"])
        self.assertFalse(receipt["direct_center_connection_allowed"])
        self.assertEqual(receipt["model_calls"], 0)
        self.assertEqual(receipt["paid_calls"], 0)

    def test_platform_codes_match_access_policy(self) -> None:
        access = json.loads(MODULE.SOCIAL_ACCESS_PATH.read_text(encoding="utf-8"))
        codebook = json.loads(MODULE.SOCIAL_CODEBOOK_PATH.read_text(encoding="utf-8"))
        result = MODULE.validate_social_codebook(codebook, access)
        self.assertEqual(result["social_metric_count"], 70)
        self.assertEqual(result["social_event_count"], 12)
        self.assertEqual(result["social_relation_count"], 10)

    def test_social_policy_rejects_login_bypass(self) -> None:
        payload = json.loads(MODULE.SOCIAL_ACCESS_PATH.read_text(encoding="utf-8"))
        payload["global_policy"]["login_bypass_allowed"] = True
        with self.assertRaises(MODULE.ChinaIntelligenceControlError):
            MODULE.validate_social_access(payload)

    def test_daily_policy_rejects_paid_usage(self) -> None:
        payload = json.loads(MODULE.DAILY_POLICY_PATH.read_text(encoding="utf-8"))
        payload["daily_budget"]["paid_usage_allowed"] = True
        with self.assertRaises(MODULE.ChinaIntelligenceControlError):
            MODULE.validate_daily_policy(payload)

    def test_daily_policy_rejects_parallel_collection(self) -> None:
        payload = json.loads(MODULE.DAILY_POLICY_PATH.read_text(encoding="utf-8"))
        payload["daily_budget"]["maximum_concurrent_collection_tasks"] = 2
        with self.assertRaises(MODULE.ChinaIntelligenceControlError):
            MODULE.validate_daily_policy(payload)

    def test_cli_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            receipt = MODULE.validate_all()
            MODULE._write(output / "validation-receipt.json", receipt)
            loaded = json.loads((output / "validation-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded["control_sha256"], receipt["control_sha256"])


if __name__ == "__main__":
    unittest.main()
