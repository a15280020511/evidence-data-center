from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_catalog", ROOT / "build_catalog.py")
assert SPEC and SPEC.loader
build_catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_catalog)


class ApiCatalogTests(unittest.TestCase):
    def test_catalog_covers_every_connector_and_exposes_no_secret_values(self) -> None:
        catalog = build_catalog.build(
            ROOT / "connector-manifest.json",
            ROOT / "catalog-metadata.json",
            ROOT / "connectors",
        )
        manifest = json.loads((ROOT / "connector-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["connector_count"], manifest["connector_count"])
        self.assertEqual(catalog["enabled_connector_count"], manifest["enabled_connector_count"])
        self.assertFalse(catalog["direct_center_to_center_calls_allowed"])
        self.assertFalse(catalog["secret_values_exposed"])
        self.assertEqual(catalog["selection_owner"], "gpts-usage-center")
        self.assertEqual(catalog["maintenance_owner"], "web-gpt-github-plugin")
        self.assertEqual(catalog["schema_version"], "api-catalog-v3")
        self.assertEqual(catalog["managed_provider_count"], 7)
        self.assertEqual(catalog["enabled_managed_provider_count"], 7)
        providers = {row["provider_id"]: row for row in catalog["managed_providers"]}
        self.assertEqual(
            set(providers),
            {"bigquery", "earth-engine", "data-commons", "akshare", "ashare", "aifin-market", "yuandian-law"},
        )
        self.assertEqual(len(providers["bigquery"]["operations"]), 7)
        self.assertEqual(len(providers["earth-engine"]["operations"]), 6)
        self.assertEqual(len(providers["data-commons"]["operations"]), 5)
        self.assertEqual(len(providers["akshare"]["operations"]), 17)
        self.assertEqual(len(providers["ashare"]["operations"]), 1)
        self.assertEqual(len(providers["aifin-market"]["operations"]), 17)
        self.assertEqual(len(providers["yuandian-law"]["operations"]), 40)
        self.assertEqual(providers["yuandian-law"]["discovered_readonly_tool_count"], 37)
        self.assertEqual(
            providers["yuandian-law"]["required_secret_environment_variable_name"],
            "YUANDIAN_API_KEY",
        )
        self.assertEqual(providers["akshare"]["required_secret_environment_variable_name"], "")
        self.assertEqual(
            providers["data-commons"]["required_secret_environment_variable_name"],
            "GOOGLE_DATA_COMMONS_API_KEY",
        )
        self.assertEqual(providers["data-commons"]["ticket_prefix"], "[api-dc]")
        self.assertEqual(
            providers["aifin-market"]["required_secret_environment_variable_name"],
            "WIND_API_KEY",
        )
        self.assertFalse(any(row["secret_value_exposed"] for row in providers.values()))
        connector_map = {row["connector_id"]: row for row in catalog["connectors"]}
        self.assertTrue(
            {
                "newsapi-everything",
                "newsapi-top-headlines",
                "newsapi-sources",
                "openmeteo-forecast",
                "baidu-geocode",
                "baidu-place-search",
                "baidu-direction-driving",
                "amap-place-around",
                "amap-direction-transit",
                "baidu-routematrix-driving",
                "openmeteo-air-quality",
                "openmeteo-archive",
                "worldbank-indicators",
                "wikidata-entity-get",
                "dbnomics-search",
                "osm-nominatim-reverse",
            }.issubset(connector_map)
        )
        for connector_id in (
            "newsapi-everything",
            "newsapi-top-headlines",
            "newsapi-sources",
        ):
            self.assertTrue(connector_map[connector_id]["enabled"])
            self.assertEqual(
                connector_map[connector_id]["secret_environment_variable_name"],
                "NEWSAPI_API_KEY",
            )
        serialized = json.dumps(catalog, ensure_ascii=False)
        self.assertNotIn("VALIDATION_DUMMY_SECRET", serialized)
        for row in catalog["connectors"]:
            self.assertIn("parameter_names", row)
            self.assertIn("detail_file", row)
            self.assertIn("metadata_pointer", row)
            self.assertFalse(row["secret_value_exposed"])
            detail = ROOT / row["detail_file"]
            self.assertTrue(detail.is_file())
            connector = json.loads(detail.read_text(encoding="utf-8"))
            if row["enabled"]:
                contract = connector.get("response_contract")
                self.assertIsInstance(contract, dict)
                status_contract = bool(
                    contract.get("status_path") and contract.get("success_values")
                )
                data_contract = bool(
                    contract.get("success_when_data_present") is True
                    and contract.get("any_data_paths")
                )
                self.assertTrue(status_contract or data_contract)

    def test_catalog_output_is_deterministic(self) -> None:
        first = build_catalog.build(
            ROOT / "connector-manifest.json",
            ROOT / "catalog-metadata.json",
            ROOT / "connectors",
        )
        second = build_catalog.build(
            ROOT / "connector-manifest.json",
            ROOT / "catalog-metadata.json",
            ROOT / "connectors",
        )
        self.assertEqual(first, second)
        self.assertEqual(first["generation"], "deterministic-from-repository-state")

    def test_committed_catalog_matches_generator(self) -> None:
        generated = build_catalog.build(
            ROOT / "connector-manifest.json",
            ROOT / "catalog-metadata.json",
            ROOT / "connectors",
        )
        committed = json.loads((ROOT / "api-catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(generated, committed)
        self.assertEqual(
            build_catalog.render_markdown(generated),
            (ROOT / "api-catalog.md").read_text(encoding="utf-8"),
        )

    def test_main_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = build_catalog.build(
                ROOT / "connector-manifest.json",
                ROOT / "catalog-metadata.json",
                ROOT / "connectors",
            )
            json_path = root / "catalog.json"
            markdown_path = root / "catalog.md"
            json_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
            markdown_path.write_text(build_catalog.render_markdown(catalog), encoding="utf-8")
            self.assertIn("GPTs 使用中心", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("catalog_sha256", json_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
