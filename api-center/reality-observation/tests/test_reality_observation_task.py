from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reality_observation_task", HERE / "reality_observation_task.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class RealityObservationProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "reality-observation")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 25)
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertFalse(provider["limits"]["device_control_allowed"])
        self.assertFalse(provider["limits"]["individual_tracking_allowed"])
        self.assertEqual(
            set(provider["limits"]["optional_secret_environment_variables"]),
            {"FIRMS_MAP_KEY", "FINGRID_API_KEY", "ENTSOE_API_TOKEN"},
        )

    def test_stac_search_is_fixed_and_bounded(self) -> None:
        spec = module.build_request(
            "planetary-stac-search",
            {
                "collections": ["naip"],
                "bbox": [-84.5, 33.5, -84.4, 33.6],
                "limit": 10,
            },
            environ={},
        )
        self.assertEqual(spec["method"], "POST")
        self.assertEqual(
            spec["url"], "https://planetarycomputer.microsoft.com/api/stac/v1/search"
        )
        self.assertEqual(spec["json"]["collections"], ["naip"])
        self.assertEqual(spec["json"]["limit"], 10)

    def test_bbox_rejects_unbounded_span(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request(
                "planetary-stac-search",
                {
                    "collections": ["naip"],
                    "bbox": [-170, -80, 170, 80],
                },
                environ={},
            )

    def test_kartaview_is_public_read_only(self) -> None:
        spec = module.build_request(
            "kartaview-nearby-photos",
            {"latitude": 40.7580, "longitude": -73.9855, "radius_m": 500},
            environ={},
        )
        self.assertEqual(spec["method"], "GET")
        self.assertEqual(spec["url"], "https://api.openstreetcam.org/2.0/photo/")
        self.assertNotIn("access_token", spec["params"])

    def test_melbourne_latest_is_fixed(self) -> None:
        spec = module.build_request(
            "melbourne-pedestrian-latest",
            {"location_id": 3, "limit": 20},
            environ={},
        )
        self.assertIn(
            "pedestrian-counting-system-past-hour-counts-per-minute",
            spec["url"],
        )
        self.assertEqual(spec["params"]["limit"], "20")
        self.assertEqual(spec["params"]["where"], "location_id=3")

    def test_power_endpoints_are_fixed(self) -> None:
        generation = module.build_request(
            "elexon-generation-summary",
            {
                "start_time": "2026-08-01T00:00:00Z",
                "end_time": "2026-08-01T01:00:00Z",
            },
            environ={},
        )
        self.assertEqual(
            generation["url"],
            "https://data.elexon.co.uk/bmrs/api/v1/generation/outturn/summary",
        )
        neso = module.build_request("neso-generation-mix", {}, environ={})
        self.assertEqual(neso["url"], "https://api.carbonintensity.org.uk/generation")

    def test_backend_secret_is_required_and_not_in_safe_path(self) -> None:
        with self.assertRaises(RuntimeError):
            module.build_request(
                "nasa-firms-area",
                {
                    "source": "VIIRS_SNPP_NRT",
                    "bbox": [119, 25, 120, 26],
                    "day_range": 1,
                },
                environ={},
            )
        spec = module.build_request(
            "nasa-firms-area",
            {
                "source": "VIIRS_SNPP_NRT",
                "bbox": [119, 25, 120, 26],
                "day_range": 1,
            },
            environ={"FIRMS_MAP_KEY": "secret-value"},
        )
        self.assertIn("secret-value", spec["url"])
        self.assertNotIn("secret-value", spec["safe_path"])

    def test_entsoe_token_is_backend_only(self) -> None:
        spec = module.build_request(
            "entsoe-document",
            {
                "document_type": "A65",
                "period_start": "202608010000",
                "period_end": "202608020000",
            },
            environ={"ENTSOE_API_TOKEN": "secret-token"},
        )
        self.assertEqual(spec["params"]["securityToken"], "secret-token")
        self.assertNotIn("secret-token", spec["safe_path"])

    def test_melbourne_summary_aggregates_counts(self) -> None:
        result = module._summarize_melbourne(
            {
                "total_count": 2,
                "results": [
                    {
                        "location_id": 3,
                        "sensing_datetime": "2026-08-01T00:00:00Z",
                        "total_of_directions": 10,
                    },
                    {
                        "location_id": 4,
                        "sensing_datetime": "2026-08-01T00:01:00Z",
                        "total_of_directions": 20,
                    },
                ],
            }
        )
        self.assertEqual(result["sensor_count"], 2)
        self.assertEqual(result["sum_total_of_directions"], 30)


if __name__ == "__main__":
    unittest.main()
