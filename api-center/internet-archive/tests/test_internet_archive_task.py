from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "internet_archive_task", HERE / "internet_archive_task.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class InternetArchiveProviderTests(unittest.TestCase):
    def test_catalog_contract(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        provider = catalog["providers"][0]
        self.assertEqual(provider["provider_id"], "internet-archive")
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertEqual(len(provider["operations"]), 6)
        self.assertFalse(provider["limits"]["file_downloads_allowed"])
        self.assertFalse(provider["limits"]["write_operations_allowed"])

    def test_search_request_is_fixed_and_bounded(self) -> None:
        path, query = module.build_request(
            "search-items",
            {"query": "collection:opensource_movies", "rows": 25, "page": 2},
        )
        self.assertEqual(path, "/advancedsearch.php")
        self.assertEqual(query["output"], "json")
        self.assertEqual(query["rows"], "25")
        self.assertEqual(query["page"], "2")

    def test_identifier_does_not_allow_path_escape(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("get-item-metadata", {"identifier": "../secret"})

    def test_wayback_requires_absolute_http_url(self) -> None:
        with self.assertRaises(ValueError):
            module.build_request("wayback-availability", {"url": "file:///etc/passwd"})
        path, query = module.build_request(
            "wayback-availability", {"url": "https://example.com", "timestamp": "20200101"}
        )
        self.assertEqual(path, "/wayback/available")
        self.assertEqual(query["timestamp"], "20200101")

    def test_cdx_contract_is_fixed(self) -> None:
        path, query = module.build_request(
            "wayback-captures",
            {"url": "https://example.com", "limit": 20, "from_timestamp": "2020"},
        )
        self.assertEqual(path, "/cdx/search/cdx")
        self.assertEqual(query["filter"], "statuscode:200")
        self.assertEqual(query["collapse"], "digest")
        self.assertEqual(query["limit"], "20")


if __name__ == "__main__":
    unittest.main()
