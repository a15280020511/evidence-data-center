from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aifin_task", ROOT / "aifin_task.py")
assert SPEC and SPEC.loader
aifin_task = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = aifin_task
SPEC.loader.exec_module(aifin_task)


class AIFinAdapterTests(unittest.TestCase):
    def test_provider_catalog_is_fixed_read_only_and_secret_safe(self) -> None:
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        self.assertFalse(catalog["secret_values_exposed"])
        self.assertEqual(catalog["required_secret_environment_variable"], "WIND_API_KEY")
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "aifin-market")
        self.assertTrue(provider["enabled"])
        operations = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(
            operations,
            {
                "catalog-capabilities",
                "catalog-tools",
                "stock-quote",
                "stock-price-indicators",
                "financial-news",
                "economic-data",
                "analytics-query",
            },
        )
        self.assertFalse(provider["limits"]["arbitrary_tool_names_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])

    def test_runtime_map_exposes_only_fixed_servers_and_tools(self) -> None:
        self.assertEqual(
            set(aifin_task.SERVER_ENDPOINTS),
            {"stock_data", "financial_docs", "economic_data", "analytics_data"},
        )
        for operation, row in aifin_task.OPERATION_MAP.items():
            server_type, tool_name, parameters = row
            self.assertIn(server_type, aifin_task.SERVER_ENDPOINTS)
            self.assertTrue(tool_name)
            self.assertIsInstance(parameters, tuple)
            self.assertNotIn("url", parameters)
            self.assertNotIn("api_key", parameters)
            self.assertNotIn("authorization", parameters)

    def test_parameter_sanitizer_rejects_unknown_fields(self) -> None:
        with self.assertRaises(ValueError):
            aifin_task.sanitize_parameters(
                "stock-quote",
                {"windcode": "600519.SH", "tool_name": "arbitrary"},
            )
        cleaned = aifin_task.sanitize_parameters(
            "stock-price-indicators",
            {"windcode": "600519.SH", "indexes": "中文简称,最新成交价"},
        )
        self.assertEqual(set(cleaned), {"windcode", "indexes"})


if __name__ == "__main__":
    unittest.main()
