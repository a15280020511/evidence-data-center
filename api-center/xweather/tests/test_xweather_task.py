from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("xweather_task", ROOT / "xweather_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class XweatherTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "xweather-test-001",
            "provider": "xweather",
            "operation": operation,
            "objective": "test bounded Xweather provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1000000,
                "max_rows": 100,
            },
        }

    def test_catalog_and_schema_are_fixed(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "xweather")
        self.assertEqual(provider["required_secret_environment_variable"], "XWEATHER_CLIENT_SECRET")
        self.assertEqual(provider["required_repository_variable"], "XWEATHER_CLIENT_ID")
        self.assertEqual(len(provider["operations"]), 10)
        self.assertEqual(provider["limits"]["fixed_api_host"], "data.api.xweather.com")
        self.assertFalse(provider["limits"]["arbitrary_query_parameters_allowed"])
        self.assertFalse(provider["limits"]["client_supplied_credentials_allowed"])
        task.validate_ticket(
            self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH
        )

    def test_request_builder_keeps_fixed_origin_and_redacts_credentials(self):
        url, query, metadata = task.build_request(
            "forecasts",
            {"location": "26.08,119.30", "filter": "1hr", "limit": 24},
        )
        self.assertEqual(url, "https://data.api.xweather.com/forecasts/26.08,119.30")
        self.assertEqual(query, {"filter": "1hr", "limit": "24"})
        self.assertNotIn("client_id", query)
        self.assertNotIn("client_secret", query)
        self.assertEqual(metadata["request_origin"], "data.api.xweather.com")
        with patch.dict(
            os.environ,
            {
                "XWEATHER_CLIENT_ID": "test-client-id",
                "XWEATHER_CLIENT_SECRET": "test-client-secret",
            },
            clear=False,
        ):
            self.assertEqual(task.credentials(), ("test-client-id", "test-client-secret"))

    def test_combined_dashboard_key_is_split_without_exposure(self):
        with patch.dict(
            os.environ,
            {
                "XWEATHER_CLIENT_ID": "test-client-id",
                "XWEATHER_CLIENT_SECRET": "test-client-id_test-client-secret",
            },
            clear=False,
        ):
            self.assertEqual(task.credentials(), ("test-client-id", "test-client-secret"))

    def test_history_summary_uses_plimit_for_daily_periods(self):
        url, query, _ = task.build_request(
            "observations-summary",
            {
                "location": "fuzhou,fujian,china",
                "from": "2026-07-25",
                "to": "2026-07-31",
                "plimit": 7,
            },
        )
        self.assertEqual(
            url,
            "https://data.api.xweather.com/observations/summary/fuzhou,fujian,china",
        )
        self.assertEqual(
            query,
            {"from": "2026-07-25", "to": "2026-07-31", "plimit": "7"},
        )

    def test_schema_rejects_path_escape(self):
        bad = self.ticket("forecasts", {"location": "https://example.com", "limit": 1})
        with self.assertRaises(ValueError):
            task.validate_ticket(bad, schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_local_catalog_execution_needs_no_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_XWEATHER_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
