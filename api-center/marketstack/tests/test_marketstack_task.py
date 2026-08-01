from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("marketstack_task", HERE / "marketstack_task.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class MarketstackProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "marketstack")
        self.assertEqual(provider["ticket_prefix"], "[intel-marketstack]")
        self.assertEqual(
            provider["required_secret_environment_variable"],
            "MARKETSTACK_ACCESS_KEY",
        )
        self.assertEqual(len(provider["operations"]), 11)
        self.assertEqual(provider["limits"]["free_plan_requests_per_month"], 100)
        self.assertEqual(provider["limits"]["historical_span_days_max"], 366)
        self.assertFalse(provider["limits"]["automatic_pagination_allowed"])
        self.assertFalse(provider["limits"]["intraday_or_realtime_operations_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])

    def test_latest_request_is_fixed_and_has_no_key(self) -> None:
        path, query = module.build_request(
            "eod-latest",
            {"symbols": ["AAPL", "MSFT"], "limit": 2, "offset": 0},
        )
        self.assertEqual(path, "/v2/eod/latest")
        self.assertEqual(query["symbols"], "AAPL,MSFT")
        self.assertEqual(query["limit"], "2")
        self.assertNotIn("access_key", query)

    def test_history_is_limited_to_one_year(self) -> None:
        path, query = module.build_request(
            "eod-history",
            {
                "symbols": ["AAPL"],
                "date_from": "2025-08-01",
                "date_to": "2026-08-01",
                "sort": "asc",
            },
        )
        self.assertEqual(path, "/v2/eod")
        self.assertEqual(query["sort"], "ASC")
        with self.assertRaises(ValueError):
            module.build_request(
                "eod-history",
                {
                    "symbols": ["AAPL"],
                    "date_from": "2024-01-01",
                    "date_to": "2026-01-03",
                },
            )

    def test_reversed_or_invalid_dates_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request(
                "dividends",
                {
                    "symbols": ["AAPL"],
                    "date_from": "2026-08-02",
                    "date_to": "2026-08-01",
                },
            )
        with self.assertRaises(ValueError):
            module.build_request(
                "eod-by-date",
                {"symbols": ["AAPL"], "date": "2026-02-31"},
            )

    def test_symbol_quota_and_validation(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request(
                "eod-latest",
                {"symbols": ["A", "B", "C", "D", "E", "F"]},
            )
        with self.assertRaises(ValueError):
            module.build_request("eod-latest", {"symbols": ["AAPL", "AAPL"]})
        with self.assertRaises(ValueError):
            module.build_request("ticker-info", {"symbol": "../../etc/passwd"})

    def test_directory_paths_and_query_allowlist(self) -> None:
        path, query = module.build_request(
            "tickers-list",
            {"search": "Apple", "exchange": "XNAS", "limit": 10},
        )
        self.assertEqual(path, "/v2/tickerslist")
        self.assertEqual(query["search"], "Apple")
        self.assertEqual(query["exchange"], "XNAS")
        self.assertNotIn("access_key", query)
        self.assertEqual(module.build_request("exchanges-list", {})[0], "/v2/exchanges")
        self.assertEqual(module.build_request("currencies-list", {})[0], "/v2/currencies")
        self.assertEqual(module.build_request("timezones-list", {})[0], "/v2/timezones")

    def test_paid_or_unknown_operations_are_not_exposed(self) -> None:
        for operation in ("intraday", "realtime", "bonds", "commodities", "edgar"):
            with self.assertRaises(ValueError):
                module.build_request(operation, {})


if __name__ == "__main__":
    unittest.main()
