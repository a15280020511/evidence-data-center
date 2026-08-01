from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "metno_geosatellite_task", HERE / "metno_geosatellite_task.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class MetnoGeosatelliteProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "metno-geosatellite")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 4)
        self.assertEqual(provider["limits"]["fixed_api_host"], "api.met.no")
        self.assertFalse(provider["limits"]["small_size_images_allowed"])
        self.assertFalse(provider["limits"]["unfiltered_availability_listing_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_static_image_request_is_fixed_and_bounded(self) -> None:
        url, query, extension = module.build_request(
            "get-static-image",
            {
                "area": "global",
                "spectrum": "infrared",
                "time": "2026-08-01T12:00:00Z",
            },
        )
        self.assertEqual(
            url, "https://api.met.no/weatherapi/geosatellite/1.4/"
        )
        self.assertEqual(
            query,
            {
                "area": "global",
                "type": "infrared",
                "time": "2026-08-01T12:00:00Z",
            },
        )
        self.assertEqual(extension, "png")

    def test_invalid_area_and_future_time_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("get-static-image", {"area": "../../etc"})
        with self.assertRaises(ValueError):
            module.build_request(
                "get-static-image",
                {"area": "europe", "time": "2999-01-01T00:00:00Z"},
            )

    def test_animation_is_europe_only_and_format_allowlisted(self) -> None:
        url, query, extension = module.build_request(
            "get-europe-animation", {"format": "webm"}
        )
        self.assertEqual(
            url, "https://api.met.no/weatherapi/geosatellite/1.4/europe.webm"
        )
        self.assertEqual(query, {})
        self.assertEqual(extension, "webm")
        with self.assertRaises(ValueError):
            module.build_request("get-europe-animation", {"format": "gif"})

    def test_availability_requires_area_filter(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("list-available", {})
        url, query, extension = module.build_request(
            "list-available", {"area": "africa", "spectrum": "visible"}
        )
        self.assertEqual(
            url,
            "https://api.met.no/weatherapi/geosatellite/1.4/available.json",
        )
        self.assertEqual(query, {"area": "africa", "type": "visible"})
        self.assertEqual(extension, "json")

    def test_content_contract_rejects_non_png(self) -> None:
        with self.assertRaises(RuntimeError):
            module._validate_content(
                "get-static-image", "text/html", b"<html>blocked</html>"
            )
        module._validate_content(
            "get-static-image", "image/png", b"\x89PNG\r\n\x1a\npayload"
        )


if __name__ == "__main__":
    unittest.main()
