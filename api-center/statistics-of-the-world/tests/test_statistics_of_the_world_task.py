from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("statistics_of_the_world_task", HERE / "statistics_of_the_world_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class StatisticsOfTheWorldTests(unittest.TestCase):
    def test_catalog_has_fixed_safe_surface(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "statistics-of-the-world")
        self.assertEqual(provider["optional_secret_environment_variable"], "SOTW_API_KEY")
        self.assertEqual(len(provider["operations"]), 11)
        limits = provider["limits"]
        self.assertEqual(limits["requests_per_ticket_max"], 1)
        self.assertEqual(limits["provider_concurrency_max"], 1)
        self.assertFalse(limits["arbitrary_urls_allowed"])
        self.assertFalse(limits["arbitrary_paths_allowed"])
        self.assertFalse(limits["arbitrary_headers_allowed"])
        self.assertFalse(limits["client_supplied_credentials_allowed"])
        self.assertFalse(limits["automatic_pagination_allowed"])
        self.assertFalse(limits["bulk_download_allowed"])
        self.assertFalse(limits["natural_language_chat_allowed"])
        self.assertFalse(limits["write_operations_allowed"])
        self.assertFalse(limits["secret_values_exposed"])

    def test_fixed_paths_and_queries(self) -> None:
        url, query, meta = module.build_request("list-countries", {})
        self.assertEqual(url, "https://statisticsoftheworld.com/api/v1/countries")
        self.assertEqual(query, {})
        self.assertFalse(meta["secret_value_exposed"])

        url, query, _ = module.build_request("get-history", {"indicator": "NY.GDP.MKTP.CD", "country": "CHN"})
        self.assertEqual(url, "https://statisticsoftheworld.com/api/v2/history")
        self.assertEqual(query, {"indicator": "NY.GDP.MKTP.CD", "country": "CHN"})

        url, query, _ = module.build_request("compare-countries", {"countries": ["CHN", "USA", "JPN"]})
        self.assertEqual(url, "https://statisticsoftheworld.com/api/v1/compare")
        self.assertEqual(query["countries"], "CHN,USA,JPN")

        url, query, _ = module.build_request("get-series", {"series": "IMF.CPI.YOY.M", "geo": "CHN", "from": "2020-01-01", "latest": True})
        self.assertEqual(url, "https://statisticsoftheworld.com/api/v1/series/IMF.CPI.YOY.M")
        self.assertEqual(query, {"geo": "CHN", "from": "2020-01-01", "latest": "1"})

    def test_rejects_escape_hatches(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("get-country", {"country": "../../etc/passwd"})
        with self.assertRaises(ValueError):
            module.build_request("get-indicator", {"indicator": "https://example.com"})
        with self.assertRaises(ValueError):
            module.build_request("compare-countries", {"countries": ["CHN"]})
        with self.assertRaises(ValueError):
            module.build_request("compare-countries", {"countries": ["CHN", "CHN"]})
        with self.assertRaises(ValueError):
            module.build_request("search-indicators", {"query": "gdp\nX-API-Key: leak"})
        with self.assertRaises(ValueError):
            module.build_request("get-series", {"series": "SERIES", "from": "2020/01/01"})
        with self.assertRaises(ValueError):
            module.build_request("series-bulk", {})

    def test_optional_key_is_backend_only(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(module.optional_api_key(), "")
        with patch.dict(os.environ, {"SOTW_API_KEY": "sotw_test_value"}, clear=True):
            self.assertEqual(module.optional_api_key(), "sotw_test_value")
            _, _, meta = module.build_request("list-countries", {})
            self.assertNotIn("sotw_test_value", json.dumps(meta))

    def test_row_count_contract(self) -> None:
        self.assertEqual(module._row_count({"count": 218, "data": [{}, {}]}), 2)
        self.assertEqual(module._row_count({"indicators": [{}, {}, {}]}), 3)
        self.assertEqual(module._row_count({"count": 51}), 51)
        self.assertEqual(module._row_count({"country": {}}), 1)


if __name__ == "__main__":
    unittest.main()
