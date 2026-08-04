import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONNECTORS = ROOT / "connectors"
SCHEMA = json.loads(
    (ROOT / "connector.schema.json").read_text(encoding="utf-8")
)
NOAA_IDS = {
    "noaa-nws-points",
    "noaa-nws-forecast",
    "noaa-nws-forecast-hourly",
    "noaa-nws-gridpoint-stations",
    "noaa-nws-station-latest",
    "noaa-nws-alerts-active",
    "noaa-ncei-data-search",
}


class NoaaConnectorTests(unittest.TestCase):
    def load(self, connector_id):
        return json.loads(
            (CONNECTORS / f"{connector_id}.connector.json").read_text(
                encoding="utf-8"
            )
        )

    def test_all_noaa_connectors_validate(self):
        validator = Draft202012Validator(SCHEMA)
        for connector_id in NOAA_IDS:
            connector = self.load(connector_id)
            self.assertEqual(connector_id, connector["id"])
            self.assertTrue(connector["enabled"])
            self.assertEqual("GET", connector["method"])
            self.assertFalse(list(validator.iter_errors(connector)), connector_id)

    def test_only_official_fixed_hosts_and_no_secrets(self):
        expected_hosts = {
            "https://api.weather.gov",
            "https://www.ncei.noaa.gov",
        }
        for connector_id in NOAA_IDS:
            connector = self.load(connector_id)
            self.assertIn(connector["backend"]["host"], expected_hosts)
            self.assertTrue(connector["backend"]["url_pattern"].startswith("/"))
            self.assertNotIn("secret_header", connector)
            self.assertNotIn("secret_query", connector)

    def test_alerts_use_only_verified_parameters_and_bounded_filter(self):
        connector = self.load("noaa-nws-alerts-active")
        query_parameters = set(connector["input_query_strings"])
        self.assertFalse({"limit", "cursor", "start", "end"} & query_parameters)
        self.assertEqual(
            [["area", "point", "region", "zone", "event", "code"]],
            connector["parameter_rules"]["required_any_of"],
        )
        self.assertEqual(
            {"max_rate": 1, "every": "30s", "capacity": 1},
            connector["backend"]["resilience"]["rate_limit"],
        )

    def test_ncei_requires_bounds_and_uses_official_bbox_name(self):
        connector = self.load("noaa-ncei-data-search")
        self.assertEqual(
            [["dataset"], ["startDate"], ["endDate"]],
            connector["parameter_rules"]["required_any_of"],
        )
        self.assertIn("bbox", connector["input_query_strings"])
        self.assertIn("bbox", connector["parameter_rules"]["properties"])
        self.assertNotIn("boundingBox", connector["input_query_strings"])
        self.assertNotIn(
            "boundingBox", connector["parameter_rules"]["properties"]
        )


if __name__ == "__main__":
    unittest.main()
