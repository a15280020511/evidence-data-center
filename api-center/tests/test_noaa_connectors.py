from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONNECTORS = ROOT / "connectors"
SCHEMA = json.loads((ROOT / "connector.schema.json").read_text(encoding="utf-8"))


class NoaaChinaHistoricalConnectorTests(unittest.TestCase):
    def load(self, connector_id: str) -> dict:
        return json.loads(
            (CONNECTORS / f"{connector_id}.connector.json").read_text(
                encoding="utf-8"
            )
        )

    def test_only_four_china_historical_noaa_connectors_exist(self) -> None:
        paths = sorted(CONNECTORS.glob("noaa-*.connector.json"))
        self.assertEqual(
            [path.stem.removesuffix(".connector") for path in paths],
            [
                "noaa-ncei-china-daily",
                "noaa-ncei-china-monthly",
                "noaa-ncei-china-station-search",
                "noaa-ncei-china-yearly",
            ],
        )
        self.assertFalse(any("nws" in path.name for path in paths))

    def test_all_connectors_validate_and_use_only_ncei(self) -> None:
        validator = Draft202012Validator(SCHEMA)
        for path in CONNECTORS.glob("noaa-*.connector.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(list(validator.iter_errors(doc)), [])
            self.assertEqual(doc["method"], "GET")
            self.assertEqual(doc["backend"]["host"], "https://www.ncei.noaa.gov")
            self.assertNotIn("secret_header", doc)
            self.assertNotIn("secret_query", doc)

    def test_station_search_is_fixed_to_china_bbox(self) -> None:
        doc = self.load("noaa-ncei-china-station-search")
        rules = doc["parameter_rules"]["properties"]
        self.assertEqual(rules["bbox"]["enum"], ["53.56,73.50,18.10,134.77"])
        self.assertEqual(
            rules["dataset"]["enum"],
            [
                "daily-summaries",
                "global-summary-of-the-month",
                "global-summary-of-the-year",
            ],
        )
        self.assertEqual(
            doc["backend"]["url_pattern"],
            "/access/services/search/v1/data",
        )

    def test_data_connectors_require_china_stations_json_and_metric(self) -> None:
        expected = {
            "noaa-ncei-china-daily": "daily-summaries",
            "noaa-ncei-china-monthly": "global-summary-of-the-month",
            "noaa-ncei-china-yearly": "global-summary-of-the-year",
        }
        for connector_id, dataset in expected.items():
            doc = self.load(connector_id)
            rules = doc["parameter_rules"]["properties"]
            self.assertEqual(rules["dataset"]["enum"], [dataset])
            self.assertEqual(rules["format"]["enum"], ["json"])
            self.assertEqual(rules["units"]["enum"], ["metric"])
            self.assertIn("^CH", rules["stations"]["pattern"])
            self.assertEqual(
                doc["backend"]["url_pattern"],
                "/access/services/data/v1",
            )


if __name__ == "__main__":
    unittest.main()
