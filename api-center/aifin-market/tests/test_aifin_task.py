from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aifin_task", ROOT / "aifin_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class AIFinAdapterTests(unittest.TestCase):
    def test_provider_catalog_exposes_all_discovered_read_only_tools(self) -> None:
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        operations = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(len(module.OPERATION_MAP), 15)
        self.assertEqual(operations, {"catalog-capabilities", "catalog-tools", *module.OPERATION_MAP.keys()})
        self.assertFalse(provider["limits"]["arbitrary_tool_names_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])
        self.assertEqual(provider["limits"]["upstream_tools_exposed"], 15)

    def test_runtime_map_uses_only_fixed_servers_and_known_tools(self) -> None:
        self.assertEqual(set(module.SERVER_ENDPOINTS), {"stock_data", "financial_docs", "economic_data", "analytics_data"})
        self.assertEqual(len({tool for _, tool, _ in module.OPERATION_MAP.values()}), 15)
        for server_type, tool_name, parameters in module.OPERATION_MAP.values():
            self.assertIn(server_type, module.SERVER_ENDPOINTS)
            self.assertTrue(tool_name)
            self.assertNotIn("url", parameters)
            self.assertNotIn("api_key", parameters)

    def test_parameter_sanitizer_enforces_kline_and_document_limits(self) -> None:
        cleaned = module.sanitize_parameters("stock-kline", {"windcode":"600519.SH", "begin_date":"2026-01-01", "end_date":"2026-07-31", "period":"10", "count":100})
        self.assertEqual(cleaned["count"], 100)
        with self.assertRaises(ValueError):
            module.sanitize_parameters("stock-kline", {"windcode":"600519.SH", "begin_date":"20260101", "end_date":"2026-07-31"})
        with self.assertRaises(ValueError):
            module.sanitize_parameters("financial-news", {"query":"贵州茅台", "top_k":21})

    def test_economic_aliases_and_time_rules(self) -> None:
        cleaned = module.sanitize_parameters("economic-data", {"executionMode":"search", "question":"中国GDP"})
        self.assertEqual(cleaned["executionMode"], "仅搜索")
        with self.assertRaises(ValueError):
            module.sanitize_parameters("economic-data", {"executionMode":"fetch", "question":"G0000069"})
        cleaned = module.sanitize_parameters("economic-data", {"executionMode":"fetch", "question":"G0000069", "observation":"10"})
        self.assertEqual(cleaned["executionMode"], "仅提数")

    def test_execute_calls_fixed_tool_and_never_exposes_key(self) -> None:
        ticket = {"task_id":"aifin-test-0001", "objective":"test", "operation":"stock-basicinfo", "parameters":{"question":"贵州茅台基本档案"}, "data_policy":{"classification":"public", "contains_personal_data":False}}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"WIND_API_KEY":"secret-value"}), mock.patch.object(module, "initialize"), mock.patch.object(module, "mcp_request", return_value={"content":[{"text":"ok"}]}) as request:
            root=Path(tmp); ticket_path=root/'ticket.json'; ticket_path.write_text(json.dumps(ticket),encoding='utf-8')
            self.assertEqual(module.execute(ticket_path, root/'out'),0)
            snap=json.loads((root/'out/aifin-snapshot.json').read_text())
            self.assertEqual(snap['tool_name'],'get_stock_basicinfo')
            self.assertNotIn('secret-value', json.dumps(snap))
            request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
