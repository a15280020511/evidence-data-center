from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


api_ticket = load_module("api_ticket_osm_worldbank_tests", ROOT / "api_ticket.py")
api_task = load_module("api_task_osm_worldbank_tests", ROOT / "api_task.py")
build_config = load_module("build_config_osm_worldbank_tests", ROOT / "build_config.py")


def packet(connector_id: str, parameters: dict):
    return {
        "task_id": f"connector-test-{connector_id}",
        "objective": "validate safe public data connector",
        "data_policy": {
            "classification": "public",
            "contains_personal_data": False,
            "notes": "public test only",
        },
        "requests": [
            {
                "request_id": "request-1",
                "connector_id": connector_id,
                "parameters": parameters,
                "allow_empty": False,
            }
        ],
        "acceptance": {
            "require_all": True,
            "minimum_successful_requests": 1,
            "timeout_seconds": 20,
            "max_attempts": 1,
            "max_response_bytes_per_request": 100000,
        },
    }


class OsmWorldBankConnectorTests(unittest.TestCase):
    def connector(self, name: str):
        return json.loads(
            (ROOT / "connectors" / f"{name}.connector.json").read_text(
                encoding="utf-8"
            )
        )

    def test_compiler_exposes_three_secretless_public_routes(self):
        config, rows, env_names = build_config.build()
        row_map = {row["id"]: row for row in rows}
        for connector_id in (
            "worldbank-indicator-jsonstat",
            "osm-nominatim-search",
            "osm-commercial-around",
        ):
            self.assertTrue(row_map[connector_id]["enabled"])
            self.assertIsNone(row_map[connector_id]["secret_environment_variable"])
        self.assertEqual(
            len(config["endpoints"]),
            sum(bool(row["enabled"]) for row in rows),
        )
        expected_env_names = sorted({
            str(row["secret_environment_variable"])
            for row in rows
            if row.get("enabled") and row.get("secret_environment_variable")
        })
        self.assertEqual(env_names, expected_env_names)

    def test_worldbank_format_and_date_are_forwarded_as_query(self):
        plan = api_ticket._validate_and_plan(
            packet(
                "worldbank-indicator-jsonstat",
                {
                    "country_code": "CHN",
                    "indicator_code": "SP.URB.TOTL.IN.ZS",
                    "format": "jsonstat",
                    "date": "2015:2025",
                },
            ),
            ROOT,
        )
        row = plan["requests"][0]
        self.assertEqual(
            row["endpoint"],
            "/data/worldbank/indicator/CHN/SP.URB.TOTL.IN.ZS",
        )
        self.assertEqual(
            row["parameters"], {"format": "jsonstat", "date": "2015:2025"}
        )
        connector = self.connector("worldbank-indicator-jsonstat")
        self.assertNotIn("?", connector["backend"]["url_pattern"])
        self.assertEqual(connector["backend"]["host"], "https://api.worldbank.org")

    def test_nominatim_requires_explicit_safe_format_and_query(self):
        plan = api_ticket._validate_and_plan(
            packet(
                "osm-nominatim-search",
                {
                    "q": "福州宝龙城市广场,福州,中国",
                    "format": "geocodejson",
                    "limit": 5,
                    "countrycodes": "cn",
                },
            ),
            ROOT,
        )
        row = plan["requests"][0]
        self.assertEqual(row["endpoint"], "/data/osm/nominatim/search")
        self.assertEqual(row["parameters"]["format"], "geocodejson")
        connector = self.connector("osm-nominatim-search")
        self.assertEqual(
            connector["backend"]["host"], "https://nominatim.openstreetmap.org"
        )
        self.assertNotIn("secret_header", connector)
        self.assertNotIn("secret_query", connector)

    def test_overpass_route_is_bounded_and_path_only(self):
        plan = api_ticket._validate_and_plan(
            packet(
                "osm-commercial-around",
                {"latitude": "26.0620", "longitude": "119.2920", "radius": "2000"},
            ),
            ROOT,
        )
        row = plan["requests"][0]
        self.assertEqual(
            row["endpoint"],
            "/data/osm/commercial/around/26.0620/119.2920/2000",
        )
        self.assertEqual(row["parameters"], {})
        connector = self.connector("osm-commercial-around")
        self.assertIn("out%20center%20tags%20qt%20300", connector["backend"]["url_pattern"])
        self.assertEqual(connector["backend"]["host"], "https://overpass-api.de")

    def test_overpass_path_traversal_and_oversized_radius_are_rejected(self):
        with self.assertRaises(ValueError):
            api_ticket._validate_and_plan(
                packet(
                    "osm-commercial-around",
                    {"latitude": "../26", "longitude": "119.2", "radius": "2000"},
                ),
                ROOT,
            )
        with self.assertRaises(ValueError):
            api_ticket._validate_and_plan(
                packet(
                    "osm-commercial-around",
                    {"latitude": "26.06", "longitude": "119.2", "radius": "25000"},
                ),
                ROOT,
            )

    def test_response_contracts_accept_expected_nonempty_shapes(self):
        nominatim = self.connector("osm-nominatim-search")
        overpass = self.connector("osm-commercial-around")
        worldbank = self.connector("worldbank-indicator-jsonstat")
        self.assertTrue(
            api_task.evaluate_response_contract(
                {"type": "FeatureCollection", "features": [{"type": "Feature"}]},
                nominatim["response_contract"],
                allow_empty=False,
            )["success"]
        )
        self.assertTrue(
            api_task.evaluate_response_contract(
                {"version": 0.6, "elements": [{"type": "node", "id": 1}]},
                overpass["response_contract"],
                allow_empty=False,
            )["success"]
        )
        self.assertTrue(
            api_task.evaluate_response_contract(
                {"class": "dataset", "value": [1.0]},
                worldbank["response_contract"],
                allow_empty=False,
            )["success"]
        )


if __name__ == "__main__":
    unittest.main()
