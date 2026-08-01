from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("baostock_quota", ROOT / "baostock_quota.py")
assert SPEC and SPEC.loader
quota = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quota)
POLICY = json.loads((ROOT / "quota-policy.json").read_text(encoding="utf-8"))


class BaoStockQuotaTests(unittest.TestCase):
    def state(self, *, date="2026-08-01", count=0, blacklisted=False):
        value = quota.default_state(date, POLICY)
        value["request_count"] = count
        value["blacklisted"] = blacklisted
        return value

    def test_policy_is_hard_capped_and_serial(self):
        self.assertEqual(POLICY["daily_request_limit"], 50000)
        self.assertEqual(POLICY["max_parallel_connections"], 1)
        self.assertEqual(POLICY["timezone"], "Asia/Shanghai")
        self.assertEqual(POLICY["concurrency_group"], "api-baostock-global-single-connection")
        self.assertTrue(POLICY["ledger_fail_closed"])
        self.assertFalse(POLICY["catalog_operations_consume_quota"])

    def test_reservation_increments_exactly_once(self):
        updated, receipt = quota.reserve_state(
            self.state(count=12),
            today="2026-08-01",
            reserved_at="2026-08-01T11:00:00+08:00",
            run_id=100,
            issue_number=200,
            policy=POLICY,
        )
        self.assertTrue(receipt["allowed"])
        self.assertEqual(updated["request_count"], 13)
        self.assertEqual(receipt["request_count"], 13)
        self.assertEqual(receipt["remaining_requests"], 49987)
        self.assertFalse(receipt["blacklisted"])

    def test_fifty_thousandth_request_is_allowed_then_blacklisted(self):
        updated, receipt = quota.reserve_state(
            self.state(count=49999),
            today="2026-08-01",
            reserved_at="2026-08-01T11:00:00+08:00",
            run_id=100,
            issue_number=200,
            policy=POLICY,
        )
        self.assertTrue(receipt["allowed"])
        self.assertEqual(receipt["request_count"], 50000)
        self.assertEqual(receipt["remaining_requests"], 0)
        self.assertTrue(updated["blacklisted"])
        self.assertTrue(receipt["blacklisted"])

    def test_request_after_limit_is_rejected_without_increment(self):
        updated, receipt = quota.reserve_state(
            self.state(count=50000, blacklisted=True),
            today="2026-08-01",
            reserved_at="2026-08-01T11:00:00+08:00",
            run_id=101,
            issue_number=201,
            policy=POLICY,
        )
        self.assertFalse(receipt["allowed"])
        self.assertEqual(receipt["status"], "BAOSTOCK_DAILY_BLACKLISTED")
        self.assertEqual(updated["request_count"], 50000)
        self.assertEqual(receipt["request_count"], 50000)
        self.assertTrue(receipt["blacklisted"])

    def test_new_shanghai_day_resets_counter_and_blacklist(self):
        updated, receipt = quota.reserve_state(
            self.state(date="2026-08-01", count=50000, blacklisted=True),
            today="2026-08-02",
            reserved_at="2026-08-02T00:00:01+08:00",
            run_id=102,
            issue_number=202,
            policy=POLICY,
        )
        self.assertTrue(receipt["allowed"])
        self.assertEqual(updated["date"], "2026-08-02")
        self.assertEqual(updated["request_count"], 1)
        self.assertFalse(updated["blacklisted"])

    def test_catalog_operation_needs_no_ledger_or_github_token(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            ticket = root / "ticket.json"
            ticket.write_text(json.dumps({"operation": "catalog-capabilities"}), encoding="utf-8")
            self.assertEqual(quota.reserve(ticket, root), 0)
            receipt = json.loads((root / "baostock-quota-receipt.json").read_text(encoding="utf-8"))
            self.assertTrue(receipt["allowed"])
            self.assertFalse(receipt["reservation_required"])
            self.assertEqual(receipt["status"], "BAOSTOCK_QUOTA_NOT_REQUIRED")

    def test_ledger_failure_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "GITHUB_TOKEN": "token",
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_RUN_ID": "100",
                "ISSUE_NUMBER": "200",
            },
            clear=True,
        ):
            root = Path(tmp)
            ticket = root / "ticket.json"
            ticket.write_text(json.dumps({"operation": "trade-dates"}), encoding="utf-8")
            with patch.object(
                quota,
                "github_json",
                side_effect=quota.QuotaError("BAOSTOCK_QUOTA_LEDGER_UNAVAILABLE", "unavailable"),
            ):
                self.assertEqual(quota.reserve(ticket, root), 1)
            receipt = json.loads((root / "baostock-quota-receipt.json").read_text(encoding="utf-8"))
            self.assertFalse(receipt["allowed"])
            self.assertTrue(receipt["blacklisted"])
            self.assertEqual(receipt["error"]["code"], "BAOSTOCK_QUOTA_LEDGER_UNAVAILABLE")

    def test_fenced_ledger_round_trip(self):
        state = self.state(count=23)
        parsed = quota.parse_ledger_body(quota.fenced_json(state))
        self.assertEqual(parsed["request_count"], 23)
        self.assertEqual(parsed["daily_limit"], 50000)


if __name__ == "__main__":
    unittest.main()
