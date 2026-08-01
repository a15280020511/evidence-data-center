from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("copernicus_task", HERE / "copernicus_task.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class CopernicusProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "copernicus-cdse")
        self.assertEqual(provider["required_secret_environment_variable"], "COPERNICUS_CLIENT_SECRET")
        self.assertEqual(provider["required_repository_variable"], "COPERNICUS_CLIENT_ID")
        self.assertEqual(len(provider["operations"]), 7)
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 2)
        self.assertFalse(provider["limits"]["bulk_download_allowed"])
        self.assertFalse(provider["limits"]["arbitrary_evalscripts_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_search_payload_is_bounded_and_latest_first(self) -> None:
        payload = module._search_payload({
            "collection": "sentinel-2-l2a",
            "bbox": [119.285, 26.055, 119.298, 26.069],
            "start_time": "2026-07-01T00:00:00Z",
            "end_time": "2026-08-01T00:00:00Z",
            "cloud_cover_max": 30,
            "limit": 5,
        })
        self.assertEqual(payload["collections"], ["sentinel-2-l2a"])
        self.assertEqual(payload["limit"], 5)
        self.assertEqual(payload["sortby"][0]["direction"], "desc")
        self.assertEqual(payload["query"]["eo:cloud_cover"]["lte"], 30)

    def test_bbox_and_time_limits_are_enforced(self) -> None:
        with self.assertRaises(ValueError):
            module._bbox({"bbox": [118, 25, 120, 27]})
        with self.assertRaises(ValueError):
            module._time_range({
                "start_time": "2025-01-01T00:00:00Z",
                "end_time": "2026-08-01T00:00:00Z",
            }, max_days=366)

    def test_process_payload_uses_fixed_evalscript(self) -> None:
        payload = module._process_payload("render-true-color-png", {
            "bbox": [119.285, 26.055, 119.298, 26.069],
            "start_time": "2026-07-01T00:00:00Z",
            "end_time": "2026-08-01T00:00:00Z",
            "cloud_cover_max": 50,
            "width": 1024,
            "height": 1024,
        })
        self.assertEqual(payload["input"]["data"][0]["type"], "sentinel-2-l2a")
        self.assertEqual(payload["output"]["responses"][0]["format"]["type"], "image/png")
        self.assertIn("B04", payload["evalscript"])
        self.assertNotIn("evalscript", {"bbox", "start_time", "end_time", "cloud_cover_max", "width", "height"})

    def test_item_id_and_collection_are_allowlisted(self) -> None:
        self.assertEqual(module._collection({"collection": "sentinel-1-grd"}), "sentinel-1-grd")
        with self.assertRaises(ValueError):
            module._collection({"collection": "private-data"})
        self.assertIsNotNone(module.ITEM_RE.fullmatch("S2C_MSIL2A_20260731T024559_N0512_R132_T50RKV"))
        self.assertIsNone(module.ITEM_RE.fullmatch("../../secret"))


if __name__ == "__main__":
    unittest.main()
