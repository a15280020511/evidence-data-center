from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("adb_task", ROOT / "adb_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class ADBTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "adb-test-001",
            "provider": "adb",
            "operation": operation,
            "objective": "test bounded ADB KIDB provider",
            "parameters": parameters or {},
            "data_policy": {
                "classification": "public",
                "contains_personal_data": False,
            },
            "acceptance": {
                "timeout_seconds": 30,
                "max_response_bytes": 1_000_000,
            },
        }

    def test_catalog_contract_is_fixed_and_keyless(self):
        row = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))["providers"][0]
        self.assertEqual(row["provider_id"], "adb")
        self.assertEqual(row["required_secret_environment_variable"], "")
        self.assertEqual(len(row["operations"]), 8)
        self.assertEqual(row["limits"]["fixed_api_host"], "kidb.adb.org")
        self.assertEqual(row["limits"]["official_rate_limit_queries_per_minute"], 20)
        self.assertEqual(row["limits"]["requests_per_ticket_max"], 1)
        self.assertFalse(row["limits"]["empty_dimension_bulk_queries_allowed"])
        self.assertFalse(row["limits"]["write_operations_allowed"])
        task.validate_ticket(
            self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH
        )

    def test_request_builder_uses_fixed_hosts_and_bounded_dimensions(self):
        path, query, fmt = task.build_request(
            "get-data",
            {
                "dataflow": "EO_NA",
                "indicators": ["NGDP_XDC", "NGDPVA_XDC"],
                "economies": ["PHI", "SIN"],
                "start_period": 2020,
                "end_period": 2024,
                "format": "json",
            },
        )
        self.assertEqual(
            path,
            "/api/v4/sdmx/data/ADB,EO_NA/A.NGDP_XDC+NGDPVA_XDC.PHI+SIN",
        )
        self.assertIn(("format", "sdmx-json"), query)
        self.assertIn(("startPeriod", "2020"), query)
        self.assertEqual(fmt, "json")

        path, query, _ = task.build_request(
            "get-codelist",
            {"agency": "ADB", "codelist_id": "CL_ECONOMY_CODES"},
        )
        self.assertEqual(
            path,
            "/api/v4/sdmx/structure/codelist/ADB/CL_ECONOMY_CODES/+",
        )
        self.assertIn(("format", "sdmx-json"), query)

    def test_bulk_and_unbounded_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            task.build_request(
                "get-data",
                {"dataflow": "EO_NA", "indicators": [], "economies": ["CHN"]},
            )
        with self.assertRaises(ValueError):
            task.build_request(
                "get-data",
                {
                    "dataflow": "EO_NA",
                    "indicators": ["NGDP_XDC"],
                    "economies": ["CHN"],
                    "start_period": 2024,
                    "end_period": 2020,
                },
            )
        with self.assertRaises(ValueError):
            task.build_request("list-indicators", {"dataflow": "https://example.com"})

    def test_local_catalog_execution_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "INTEL_ADB_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
