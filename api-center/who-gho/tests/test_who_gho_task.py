from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("who_gho_task", ROOT / "who_gho_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class FakeResponse:
    ok = True
    status_code = 200
    headers = {"Content-Type": "application/json"}
    content = b'{"@odata.context":"x","value":[{"IndicatorCode":"WHOSIS_000001","SpatialDim":"CHN","TimeDim":2021,"NumericValue":78.2}]}'
    def json(self):
        return json.loads(self.content)


class WhoGhoTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "who-gho-test-001",
            "provider": "who-gho-odata",
            "operation": operation,
            "objective": "test bounded WHO GHO provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_and_schema_are_fixed_and_keyless(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "who-gho-odata")
        self.assertEqual(provider["ticket_prefix"], "[intel-who-gho]")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 8)
        self.assertEqual(provider["limits"]["fixed_api_host"], "ghoapi.azureedge.net")
        self.assertFalse(provider["limits"]["arbitrary_odata_filters_allowed"])
        self.assertTrue(provider["limits"]["legacy_endpoint_migration_watch_required"])
        task.validate_ticket(self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH)

    def test_request_builder_only_constructs_fixed_odata(self):
        path, query = task.build_request("get-indicator-data", {
            "indicator_code": "WHOSIS_000001",
            "country": "CHN",
            "year_from": 2015,
            "year_to": 2022,
            "sex": "BTSX",
            "top": 25,
        })
        self.assertEqual(path, "/WHOSIS_000001")
        self.assertEqual(query["$top"], "25")
        self.assertIn("SpatialDim eq 'CHN'", query["$filter"])
        self.assertIn("TimeDim ge 2015", query["$filter"])
        self.assertIn("Dim1 eq 'BTSX'", query["$filter"])
        self.assertEqual(query["$orderby"], "TimeDim desc")
        with self.assertRaises(ValueError):
            task.build_request("get-indicator-data", {"indicator_code": "https://evil.test"})
        with self.assertRaises(ValueError):
            task.build_request("search-indicators", {"query": "x' or 1 eq 1"})
        with self.assertRaises(ValueError):
            task.build_request("get-indicator-data", {"indicator_code": "WHOSIS_000001", "country": "CHN", "region": "WPR"})

    def test_local_catalog_execution_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_WHO_GHO_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])

    def test_mocked_upstream_execution_is_single_keyless_get(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(task.requests, "get", return_value=FakeResponse()) as get:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket("get-indicator-data", {"indicator_code": "WHOSIS_000001", "country": "CHN", "top": 1})), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            self.assertEqual(get.call_count, 1)
            kwargs = get.call_args.kwargs
            self.assertFalse(kwargs["allow_redirects"])
            self.assertNotIn("Authorization", kwargs["headers"])
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_WHO_GHO_COMPLETED")
            self.assertEqual(diagnostics["metadata"]["row_count"], 1)


if __name__ == "__main__":
    unittest.main()
