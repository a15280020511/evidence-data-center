import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import api_ticket
from api_task import evaluate_response_contract


class WorldBankConnectorTests(unittest.TestCase):
    def setUp(self):
        self.connector = json.loads(
            (ROOT / "connectors/worldbank-indicator-jsonstat.connector.json").read_text(encoding="utf-8")
        )

    def test_jsonstat_contract_accepts_nonempty_dataset(self):
        result = evaluate_response_contract(
            {"class": "dataset", "value": [65.5, 66.2], "id": ["country", "indicator", "time"]},
            self.connector["response_contract"],
            allow_empty=False,
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["data_present"])

    def test_jsonstat_contract_rejects_empty_values(self):
        result = evaluate_response_contract(
            {"class": "dataset", "value": []},
            self.connector["response_contract"],
            allow_empty=False,
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["state"], "empty")

    def test_ticket_renders_path_and_keeps_query_separate(self):
        packet = {
            "task_id": "worldbank-test-20260728",
            "objective": "test",
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "requests": [{
                "request_id": "urban-share",
                "connector_id": "worldbank-indicator-jsonstat",
                "parameters": {
                    "country_code": "CHN",
                    "indicator_code": "SP.URB.TOTL.IN.ZS",
                    "format": "jsonstat",
                    "date": "2015:2025",
                },
                "allow_empty": False,
            }],
            "acceptance": {"require_all": True, "minimum_successful_requests": 1},
        }
        plan = api_ticket._validate_and_plan(packet, ROOT)
        row = plan["requests"][0]
        self.assertEqual(row["endpoint"], "/data/worldbank/indicator/CHN/SP.URB.TOTL.IN.ZS")
        self.assertEqual(
            row["parameters"],
            {"format": "jsonstat", "date": "2015:2025"},
        )
        self.assertEqual(row["path_parameters"]["country_code"], "CHN")

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            api_ticket._render_path_parameters(
                self.connector,
                "bad",
                {"country_code": "../CHN", "indicator_code": "SP.URB.TOTL"},
            )

    def test_connector_allows_explicit_jsonstat_format(self):
        self.assertNotIn("?", self.connector["backend"]["url_pattern"])
        self.assertIn("format", self.connector.get("input_query_strings", []))

    def test_connector_uses_fixed_official_host_without_secret(self):
        self.assertEqual(self.connector["backend"]["host"], "https://api.worldbank.org")
        self.assertNotIn("secret_header", self.connector)
        self.assertNotIn("secret_query", self.connector)

    def test_connector_forwards_only_fixed_execution_user_agent(self):
        self.assertEqual(self.connector.get("input_headers"), ["User-Agent"])
        self.assertNotIn("Authorization", self.connector.get("input_headers", []))


if __name__ == "__main__":
    unittest.main()
