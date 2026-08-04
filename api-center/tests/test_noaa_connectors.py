import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONNECTORS = ROOT / "connectors"
SCHEMA = json.loads((ROOT / "connector.schema.json").read_text(encoding="utf-8"))
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
        return json.loads((CONNECTORS / f"{connector_id}.connector.json").read_text(encoding="utf-8"))

    def test_all_noaa_connectors_validate(self):
        validator = Draft202012Validator(SCHEMA)
        for connector_id in NOAA_IDS:
            connector = self.load(connector_id)
            self.assertEqual(connector_id, connector["id"])
            self.assertTrue(connector["enabled"])
            self.assertEqual("GET", connector["method"])
            self.assertFalse(list(validator.iter_errors(connector)), connector_id)

    def test_only_official_fixed_hosts_and_no_secrets(self):
        expected = {"https://api.weather.gov", "https://www.ncei.noaa.gov"}
        for connector_id in NOAA_IDS:
            connector = self.load(connector_id)
            self.assertIn(connector["backend"]["host"], expected)
            self.assertNotIn("secret_header", connector)
            self.assertNotIn("secret_query", connector)
            self.assertIn("qos", "qos")

    def test_alerts_require_a_bounded_filter(self):
        connector = self.load("noaa-nws-alerts-active")
        self.assertEqual([["area", "point", "region", "zone", "event", "code"]], connector["parameter_rules"]["required_any_of"])

    def test_ncei_requires_dataset_and_date_bounds(self):
        connector = self.load("noaa-ncei-data-search")
        self.assertEqual([["dataset"], ["startDate"], ["endDate"]], connector["parameter_rules"]["required_any_of"])

if __name__ == "__main__":
    unittest.main()
