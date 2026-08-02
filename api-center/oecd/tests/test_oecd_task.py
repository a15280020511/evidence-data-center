from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("oecd_task", ROOT / "oecd_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class OECDTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "oecd-test-001",
            "provider": "oecd",
            "operation": operation,
            "objective": "test bounded OECD SDMX provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_and_schema_are_fixed(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "oecd")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 6)
        self.assertEqual(provider["limits"]["fixed_api_host"], "sdmx.oecd.org")
        self.assertFalse(provider["limits"]["arbitrary_sdmx_resource_types_allowed"])
        task.validate_ticket(
            self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH
        )

    def test_request_builder_keeps_fixed_sdmx_prefix(self):
        path, query, fmt = task.build_request(
            "get-data",
            {
                "agency": "OECD.SDD.STES",
                "flow": "DSD_STES",
                "version": "latest",
                "key": "M.CPALTT01.IXOB",
                "start_period": "2020-01",
                "format": "json",
            },
        )
        self.assertTrue(path.startswith("/data/OECD.SDD.STES,DSD_STES,latest/"))
        self.assertEqual(query["startPeriod"], "2020-01")
        self.assertEqual(fmt, "json")
        self.assertEqual(
            task.accept_header("list-dataflows", "json"),
            "application/vnd.sdmx.structure+json;version=1.0",
        )
        with self.assertRaises(ValueError):
            task.accept_header("list-dataflows", "csv")
        with self.assertRaises(ValueError):
            task.build_request(
                "get-data",
                {"agency": "OECD", "flow": "FLOW", "key": "https://example.com"},
            )

    def test_local_catalog_execution_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_OECD_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
