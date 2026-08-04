from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "china_intelligence_quota_consistency",
    ROOT / "china_intelligence_quota_consistency.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ChinaIntelligenceQuotaConsistencyTests(unittest.TestCase):
    def test_quota_policies_are_consistent(self) -> None:
        receipt = MODULE.validate()
        self.assertEqual(receipt["status"], "CLOUDFLARE_DAILY_QUOTA_POLICIES_CONSISTENT")
        self.assertEqual(receipt["utilization_soft_stop"], 0.98)
        self.assertEqual(receipt["workers_ai_daily_budget"], 9800)
        self.assertEqual(receipt["browser_run_daily_budget_seconds"], 570)
        self.assertTrue(receipt["hard_stop_on_429"])
        self.assertTrue(receipt["next_day_resume"])
        self.assertFalse(receipt["external_model_enabled_by_default"])
        self.assertFalse(receipt["automatic_paid_fallback_allowed"])

    def test_paid_fallback_change_is_rejected(self) -> None:
        routing = json.loads(MODULE.ROUTING_PATH.read_text(encoding="utf-8"))
        original = routing["external_model_policy"]["automatic_paid_fallback_allowed"]
        self.assertFalse(original)

    def test_daily_schedule_matches_utc_reset(self) -> None:
        daily = json.loads(MODULE.DAILY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(daily["cloudflare_free_limits"]["reset_time_utc"], "00:00")
        self.assertEqual(daily["schedule"]["resume_cron_utc"], "15 0 * * *")
        self.assertEqual(daily["schedule"]["resume_time_china_standard_time"], "08:15")


if __name__ == "__main__":
    unittest.main()
