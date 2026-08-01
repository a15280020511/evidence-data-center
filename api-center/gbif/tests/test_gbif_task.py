from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gbif_task", HERE / "gbif_task.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class GbifProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "gbif")
        self.assertEqual(provider["ticket_prefix"], "[intel-gbif]")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 10)
        self.assertEqual(provider["limits"]["fixed_api_host"], "api.gbif.org")
        self.assertFalse(provider["limits"]["bulk_download_allowed"])
        self.assertFalse(provider["limits"]["automatic_pagination_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_species_match_is_fixed(self) -> None:
        path, query = module.build_request(
            "species-match",
            {"name": "Panda ailuropoda", "kingdom": "Animalia", "strict": True},
        )
        self.assertEqual(path, "/v1/species/match")
        self.assertEqual(query["name"], "Panda ailuropoda")
        self.assertEqual(query["strict"], "true")

    def test_occurrence_spatial_search_is_bounded(self) -> None:
        path, query = module.build_request(
            "occurrence-search",
            {
                "geo_distance": "26.064655,119.286946,5km",
                "country": "CN",
                "limit": 100,
                "offset": 20,
            },
        )
        self.assertEqual(path, "/v1/occurrence/search")
        self.assertEqual(query["geoDistance"], "26.064655,119.286946,5km")
        self.assertEqual(query["country"], "CN")
        self.assertEqual(query["limit"], "100")
        self.assertEqual(query["offset"], "20")

    def test_occurrence_offset_hard_limit(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request(
                "occurrence-search", {"q": "bird", "limit": 300, "offset": 99900}
            )

    def test_invalid_geo_distance_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request(
                "occurrence-count", {"geo_distance": "../../etc/passwd"}
            )

    def test_dataset_uuid_is_validated(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("dataset-get", {"dataset_key": "not-a-uuid"})
        path, query = module.build_request(
            "dataset-get",
            {"dataset_key": "7ddf754f-d193-4cc9-b351-99906754a03b"},
        )
        self.assertEqual(
            path, "/v1/dataset/7ddf754f-d193-4cc9-b351-99906754a03b"
        )
        self.assertEqual(query, {})


if __name__ == "__main__":
    unittest.main()
