
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


api_ticket = load("api_quality_ticket", ROOT / "api_ticket.py")
api_task = load("api_quality_task", ROOT / "api_task.py")


def packet(connector_id, parameters, quality_checks=None):
    row = {"request_id": "request-1", "connector_id": connector_id, "parameters": parameters}
    if quality_checks:
        row["quality_checks"] = quality_checks
    return {
        "task_id": "quality-test-0001",
        "objective": "validate parameter and response quality controls",
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "requests": [row],
        "acceptance": {"require_all": True, "minimum_successful_requests": 1},
    }


class ApiQualityTests(unittest.TestCase):
    def test_newsapi_rules_reject_invalid_combinations_and_limits(self):
        with self.assertRaisesRegex(ValueError, "requires at least one"):
            api_ticket._validate_and_plan(packet("newsapi-everything", {}), ROOT)
        with self.assertRaisesRegex(ValueError, "above maximum"):
            api_ticket._validate_and_plan(
                packet("newsapi-everything", {"q": "Fuzhou", "pageSize": 101}), ROOT
            )
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            api_ticket._validate_and_plan(
                packet("newsapi-top-headlines", {"sources": "bbc-news", "country": "us"}), ROOT
            )

    def test_osm_limit_is_annotated(self):
        quality = api_task.evaluate_response_quality(
            {"elements": [{"id": index} for index in range(300)]},
            {
                "connector_id": "osm-commercial-around",
                "response_quality": {
                    "collection_path": "elements",
                    "hard_limit": 300,
                    "recommended_action": "tile",
                },
            },
        )
        self.assertTrue(quality["possibly_truncated"])
        self.assertEqual(quality["returned_count"], 300)

    def test_location_mismatch_is_blocking(self):
        quality = api_task.evaluate_response_quality(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "geometry": {"coordinates": [117.2, 31.8]},
                        "properties": {"display_name": "合肥市"},
                    }
                ],
            },
            {
                "connector_id": "osm-nominatim-search",
                "quality_checks": {
                    "expected_location": {
                        "latitude": 26.06,
                        "longitude": 119.29,
                        "max_distance_km": 5,
                        "admin_tokens": ["福州"],
                    }
                },
            },
        )
        self.assertTrue(quality["blocking_failure"])
        self.assertFalse(quality["location_match"])


if __name__ == "__main__":
    unittest.main()
