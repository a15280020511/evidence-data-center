from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "global_sensor_backbone_task",
    HERE / "global_sensor_backbone_task.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class GlobalSensorBackboneTests(unittest.TestCase):
    def test_glofas_uses_fixed_official_endpoint(self) -> None:
        url, query, _ = module.build_request("glofas-collection", {})
        self.assertEqual(
            url,
            "https://ewds.climate.copernicus.eu/api/catalogue/v1/collections/cems-glofas-forecast",
        )
        self.assertEqual(query, {})

    def test_ripe_result_path_is_bounded(self) -> None:
        url, query, _ = module.build_request(
            "ripe-atlas-results",
            {"measurement_id": 123, "start": 100, "stop": 200},
        )
        self.assertEqual(
            url,
            "https://atlas.ripe.net/api/v2/measurements/123/results/",
        )
        self.assertEqual(query, {"start": 100, "stop": 200})

    def test_portwatch_rejects_path_injection(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid collection_id"):
            module.build_request(
                "portwatch-items", {"collection_id": "../private"}
            )

    def test_secret_operations_fail_when_unconfigured(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GIE_API_KEY"):
                module.build_request("gie-storage", {})
            with self.assertRaisesRegex(RuntimeError, "GLOBAL_FISHING_WATCH"):
                module.build_request("gfw-events", {})
            with self.assertRaisesRegex(RuntimeError, "KOREA_DATA"):
                module.build_request("kpx-current-supply", {})

    def test_nasa_power_rejects_unknown_temporal_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "temporal"):
            module.build_request(
                "nasa-power-point",
                {
                    "temporal": "second",
                    "parameters": ["T2M"],
                    "latitude": 1,
                    "longitude": 2,
                },
            )

    def test_wis2_topic_is_namespace_limited(self) -> None:
        with self.assertRaisesRegex(ValueError, "namespace"):
            module._wis2({"topic": "#"}, 5)


if __name__ == "__main__":
    unittest.main()
