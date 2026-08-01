from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("alphafeed_task", ROOT / "alphafeed_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class _Klines:
    def get(self, symbol, **kwargs):
        return [{"symbol": symbol, "close": 1.0, "kwargs": kwargs}]
    def batch(self, symbols, **kwargs):
        return {symbol: [{"close": 1.0}] for symbol in symbols}
    def intraday(self, symbol, **kwargs):
        return [{"symbol": symbol, "close": 1.0}]
    def intraday_batch(self, symbols, **kwargs):
        return {symbol: [{"close": 1.0}] for symbol in symbols}
    def ex_factors(self, symbols, **kwargs):
        return [{"symbol": symbol, "ex_factor": 1.0} for symbol in symbols]


class _Quotes:
    def get(self, **kwargs):
        return [{"symbol": "600519.SH", "last_price": 1.0, "kwargs": kwargs}]


class _Depth:
    def get(self, symbol):
        return {"symbol": symbol, "bid_prices": [1.0], "ask_prices": [1.1]}


class _Instruments:
    def get(self, symbol):
        return {"symbol": symbol, "name": "test"}
    def batch(self, symbols):
        return [{"symbol": symbol, "name": "test"} for symbol in symbols]


class _AlphaFeed:
    def __init__(self, api_key):
        self.api_key = api_key
        self.klines = _Klines()
        self.quotes = _Quotes()
        self.depth = _Depth()
        self.instruments = _Instruments()


class AlphaFeedTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "alphafeed-test-001",
            "provider": "alphafeed",
            "operation": operation,
            "objective": "test bounded AlphaFeed provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_and_schema_are_fixed(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "alphafeed")
        self.assertEqual(provider["required_secret_environment_variable"], "ALPHAFEED_API_KEY")
        self.assertEqual(len(provider["operations"]), 10)
        self.assertFalse(provider["limits"]["arbitrary_sdk_methods_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])
        task.validate_ticket(
            self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH
        )

    def test_sdk_dispatch_is_allowlisted_and_backend_key_only(self):
        fake_module = types.ModuleType("alphafeed")
        fake_module.AlphaFeed = _AlphaFeed
        with patch.dict(sys.modules, {"alphafeed": fake_module}), patch.dict(
            os.environ, {"ALPHAFEED_API_KEY": "test-secret-key"}, clear=False
        ):
            result = task.execute_sdk(
                "klines",
                {"symbol": "600519.SH", "period": "1d", "count": 5, "adjust": "forward"},
            )
            with self.assertRaises(ValueError):
                task.execute_sdk("trade-order", {})
        self.assertEqual(result[0]["symbol"], "600519.SH")

    def test_local_catalog_execution_needs_no_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_ALPHAFEED_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
