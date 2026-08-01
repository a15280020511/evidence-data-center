from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("overture_maps_task", ROOT / "overture_maps_task.py")
assert SPEC and SPEC.loader
task = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task)


class OvertureMapsTests(unittest.TestCase):
    def ticket(self, operation="catalog-capabilities", parameters=None):
        return {
            "task_id": "overture-test-001",
            "provider": "overture-maps",
            "operation": operation,
            "objective": "test bounded read-only provider",
            "parameters": parameters or {},
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 30, "max_response_bytes": 1000000},
        }

    def test_catalog_and_schema_are_fixed(self):
        catalog = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "overture-maps")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 7)
        self.assertFalse(provider["limits"]["whole_world_download_allowed"])
        self.assertFalse(provider["limits"]["arbitrary_s3_paths_allowed"])
        task.validate_ticket(
            self.ticket(), schema_path=task.SCHEMA_PATH, catalog_path=task.CATALOG_PATH
        )

    def test_bbox_policy_rejects_unbounded_or_invalid_queries(self):
        self.assertEqual(task.validated_bbox([119.1, 26.0, 119.5, 26.3]), (119.1, 26.0, 119.5, 26.3))
        with self.assertRaises(ValueError):
            task.validated_bbox([-180, -90, 180, 90])
        with self.assertRaises(ValueError):
            task.validated_bbox([120, 26, 119, 27])

    def test_local_catalog_execution_needs_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket.write_text(json.dumps(self.ticket()), encoding="utf-8")
            self.assertEqual(task.execute(ticket, out), 0)
            diagnostics = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostics["status"], "API_OVERTURE_MAPS_COMPLETED")
            self.assertFalse(diagnostics["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
