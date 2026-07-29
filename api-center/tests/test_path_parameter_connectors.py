from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

API_CENTER = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


api_ticket = load_module("api_center_api_ticket_path_tests", API_CENTER / "api_ticket.py")
build_config = load_module("api_center_build_config_path_tests", API_CENTER / "build_config.py")


def packet(connector_id: str, parameters: dict):
    return {
        "task_id": f"path-test-{connector_id}",
        "objective": "validate controlled path parameter rendering",
        "data_policy": {"classification": "public", "contains_personal_data": False, "notes": "public test data only"},
        "requests": [{"request_id": "request-1", "connector_id": connector_id, "parameters": parameters, "allow_empty": False}],
        "acceptance": {"require_all": True, "minimum_successful_requests": 1, "timeout_seconds": 15, "max_attempts": 1, "max_response_bytes_per_request": 100000},
    }


class ControlledPathParameterTests(unittest.TestCase):
    def test_compiler_exposes_controlled_secretless_routes(self) -> None:
        config, rows, env_names = build_config.build()
        row_map = {row["id"]: row for row in rows}
        self.assertEqual(row_map["chinadata-live-dataset"]["path_parameter_names"], ["dataset_id"])
        self.assertEqual(row_map["dbnomics-series"]["path_parameter_names"], ["dataset_code", "provider_code", "series_code"])
        self.assertEqual(row_map["worldbank-indicator-jsonstat"]["path_parameter_names"], ["country_code", "indicator_code"])
        self.assertEqual(row_map["osm-commercial-around"]["path_parameter_names"], ["latitude", "longitude", "radius"])
        for connector_id in (
            "chinadata-live-dataset",
            "dbnomics-series",
            "worldbank-indicator-jsonstat",
            "osm-commercial-around",
        ):
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

    def test_chinadata_path_is_rendered_and_not_forwarded_as_query(self) -> None:
        plan = api_ticket._validate_and_plan(packet("chinadata-live-dataset", {"dataset_id": "china-gdp"}), root=API_CENTER)
        request = plan["requests"][0]
        self.assertEqual(request["endpoint"], "/data/chinadata/dataset/china-gdp")
        self.assertEqual(request["path_parameters"], {"dataset_id": "china-gdp"})
        self.assertEqual(request["parameters"], {})

    def test_dbnomics_path_and_observation_query_are_separated(self) -> None:
        plan = api_ticket._validate_and_plan(packet("dbnomics-series", {"provider_code": "NBS", "dataset_code": "A_A0201", "series_code": "A020106", "observations": 1}), root=API_CENTER)
        request = plan["requests"][0]
        self.assertEqual(request["endpoint"], "/data/dbnomics/series/NBS/A_A0201/A020106")
        self.assertEqual(request["parameters"], {"observations": 1})
        self.assertEqual(request["path_parameters"]["provider_code"], "NBS")

    def test_path_traversal_and_unexpected_parameters_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "forbidden character"):
            api_ticket._validate_and_plan(packet("chinadata-live-dataset", {"dataset_id": "../secret"}), root=API_CENTER)
        with self.assertRaisesRegex(ValueError, "non-allowlisted"):
            api_ticket._validate_and_plan(packet("chinadata-live-dataset", {"dataset_id": "china-gdp", "url": "https://example.com"}), root=API_CENTER)

    def test_missing_path_parameter_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required path parameter"):
            api_ticket._validate_and_plan(packet("chinadata-live-dataset", {}), root=API_CENTER)


if __name__ == "__main__":
    unittest.main()
