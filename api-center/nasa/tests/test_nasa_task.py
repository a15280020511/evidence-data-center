from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nasa_task", HERE / "nasa_task.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class NasaProviderTests(unittest.TestCase):
    def test_catalog_contract_and_archive_boundary(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        ids = {row["operation_id"] for row in provider["operations"]}
        self.assertEqual(provider["provider_id"], "nasa")
        self.assertEqual(provider["ticket_prefix"], "[intel-nasa]")
        self.assertEqual(provider["required_secret_environment_variable"], "NASA_API_KEY")
        self.assertEqual(len(ids), 25)
        self.assertFalse(provider["limits"]["archived_earth_api_allowed"])
        self.assertFalse(provider["limits"]["archived_mars_rover_api_allowed"])
        self.assertFalse(provider["limits"]["bulk_download_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])
        self.assertNotIn("earth-imagery", ids)
        self.assertNotIn("mars-rover-photos", ids)

    def test_apod_modes_are_bounded_and_key_is_not_built(self) -> None:
        url, query, requires_key, preferred = module.build_request(
            "apod",
            {"start_date": "2026-07-01", "end_date": "2026-07-31", "thumbs": True},
        )
        self.assertEqual(url, "https://api.nasa.gov/planetary/apod")
        self.assertEqual(query["thumbs"], "true")
        self.assertTrue(requires_key)
        self.assertEqual(preferred, "json")
        self.assertNotIn("api_key", query)
        with self.assertRaises(ValueError):
            module.build_request(
                "apod",
                {"date": "2026-07-01", "count": 2},
            )
        with self.assertRaises(ValueError):
            module.build_request(
                "apod",
                {"start_date": "2026-01-01", "end_date": "2026-03-01"},
            )

    def test_neows_feed_is_limited_to_seven_days(self) -> None:
        url, query, requires_key, _ = module.build_request(
            "neo-feed",
            {"start_date": "2026-08-01", "end_date": "2026-08-08"},
        )
        self.assertEqual(url, "https://api.nasa.gov/neo/rest/v1/feed")
        self.assertEqual(query["start_date"], "2026-08-01")
        self.assertTrue(requires_key)
        with self.assertRaises(ValueError):
            module.build_request(
                "neo-feed",
                {"start_date": "2026-08-01", "end_date": "2026-08-09"},
            )

    def test_donki_query_names_are_fixed(self) -> None:
        url, query, requires_key, _ = module.build_request(
            "donki-cme-analysis",
            {
                "start_date": "2026-07-01",
                "end_date": "2026-07-31",
                "most_accurate_only": True,
                "complete_entry_only": False,
                "speed": 500,
                "half_angle": 30,
                "catalog": "ALL",
            },
        )
        self.assertEqual(url, "https://api.nasa.gov/DONKI/CMEAnalysis")
        self.assertEqual(query["mostAccurateOnly"], "true")
        self.assertEqual(query["completeEntryOnly"], "false")
        self.assertEqual(query["halfAngle"], "30")
        self.assertTrue(requires_key)
        self.assertNotIn("api_key", query)

    def test_image_library_is_keyless_and_fixed(self) -> None:
        url, query, requires_key, _ = module.build_request(
            "nasa-images-search",
            {"q": "Apollo 11", "media_type": "image", "year_start": 1969, "year_end": 1970, "page": 1},
        )
        self.assertEqual(url, "https://images-api.nasa.gov/search")
        self.assertEqual(query["q"], "Apollo 11")
        self.assertFalse(requires_key)
        with self.assertRaises(ValueError):
            module.build_request(
                "nasa-images-search",
                {"q": "Apollo", "year_start": 2020, "year_end": 2019},
            )
        with self.assertRaises(ValueError):
            module.build_request("nasa-images-asset", {"nasa_id": "../../passwd"})

    def test_gibs_replacement_paths_are_fixed(self) -> None:
        url, query, requires_key, preferred = module.build_request(
            "gibs-wmts-capabilities",
            {"projection": "epsg4326", "catalog": "best"},
        )
        self.assertEqual(
            url,
            "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml",
        )
        self.assertEqual(query, {})
        self.assertFalse(requires_key)
        self.assertEqual(preferred, "xml")

        tile_url, tile_query, requires_key, preferred = module.build_request(
            "gibs-tile",
            {
                "projection": "epsg4326",
                "catalog": "best",
                "layer": "MODIS_Terra_CorrectedReflectance_TrueColor",
                "date": "2026-08-01",
                "tile_matrix_set": "250m",
                "tile_matrix": 2,
                "tile_row": 1,
                "tile_col": 3,
                "format": "jpg",
            },
        )
        self.assertEqual(tile_query, {})
        self.assertFalse(requires_key)
        self.assertEqual(preferred, "jpg")
        self.assertEqual(
            tile_url,
            "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2026-08-01/250m/2/1/3.jpg",
        )
        with self.assertRaises(ValueError):
            module.build_request(
                "gibs-layer-metadata",
                {"layer": "../../etc/passwd"},
            )

    def test_archived_and_unknown_operations_are_rejected(self) -> None:
        for operation in (
            "earth-imagery",
            "earth-assets",
            "mars-rover-photos",
            "arbitrary-url",
        ):
            with self.assertRaises(ValueError):
                module.build_request(operation, {})


if __name__ == "__main__":
    unittest.main()
