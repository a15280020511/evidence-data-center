from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_catalog",
    ROOT / "build_catalog_market_search.py",
)
assert SPEC and SPEC.loader
build_catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_catalog)

EXPECTED_OPERATION_COUNTS = {
    "bigquery": 7,
    "earth-engine": 6,
    "akshare": 17,
    "ashare": 1,
    "aifin-market": 17,
    "yuandian-law": 40,
    "tianyancha": 3,
    "miaoxiang": 4,
    "jina-reader": 2,
    "exa": 3,
    "tavily": 5,
    "firecrawl": 4,
    "tickflow": 5,
    "serpapi": 4,
    "tushare": 20,
    "wolfram-alpha": 4,
    "llamaparse": 3,
}


class ApiCatalogTests(unittest.TestCase):
    def build(self) -> dict:
        return build_catalog.build(
            ROOT / "connector-manifest.json",
            ROOT / "catalog-metadata.json",
            ROOT / "connectors",
        )

    def test_catalog_covers_every_connector_and_exposes_no_secret_values(self) -> None:
        catalog = self.build()
        manifest = json.loads(
            (ROOT / "connector-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog["connector_count"], manifest["connector_count"])
        self.assertEqual(
            catalog["enabled_connector_count"],
            manifest["enabled_connector_count"],
        )
        self.assertEqual(catalog["connector_count"], 68)
        self.assertEqual(catalog["managed_provider_count"], 17)
        self.assertEqual(catalog["enabled_managed_provider_count"], 17)
        self.assertEqual(catalog["managed_operation_count"], 145)
        self.assertGreaterEqual(catalog["exposed_parameter_count"], 850)
        self.assertFalse(catalog["direct_center_to_center_calls_allowed"])
        self.assertFalse(catalog["secret_values_exposed"])
        self.assertEqual(catalog["selection_owner"], "gpts-usage-center")
        self.assertEqual(catalog["maintenance_owner"], "web-gpt-github-plugin")
        self.assertEqual(catalog["schema_version"], "api-catalog-v3")

        providers = {
            row["provider_id"]: row for row in catalog["managed_providers"]
        }
        self.assertEqual(set(providers), set(EXPECTED_OPERATION_COUNTS))
        self.assertNotIn("tianditu", providers)
        self.assertNotIn("qichacha", providers)
        for provider_id, expected in EXPECTED_OPERATION_COUNTS.items():
            self.assertEqual(len(providers[provider_id]["operations"]), expected)
            self.assertFalse(providers[provider_id]["secret_value_exposed"])

        expected_secret_names = {
            "bigquery": "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",
            "earth-engine": "GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON",
            "aifin-market": "WIND_API_KEY",
            "yuandian-law": "YUANDIAN_API_KEY",
            "tianyancha": "TIANYANCHA_API_TOKEN",
            "miaoxiang": "MX_APIKEY",
            "exa": "EXA_API_KEY",
            "tavily": "TAVILY_API_KEY",
            "firecrawl": "FIRECRAWL_API_KEY",
            "tickflow": "TICKFLOW_API_KEY",
            "serpapi": "SERPAPI_API_KEY",
            "tushare": "TUSHARE_API_TOKEN",
            "wolfram-alpha": "WOLFRAM_ALPHA_APP_ID",
            "llamaparse": "LLAMA_CLOUD_API_KEY",
        }
        for provider_id, secret_name in expected_secret_names.items():
            self.assertEqual(
                providers[provider_id][
                    "required_secret_environment_variable_name"
                ],
                secret_name,
            )

        self.assertEqual(
            providers["tushare"]["ticket_prefix"],
            "[api-tushare]",
        )
        self.assertEqual(
            {row["operation_id"] for row in providers["tushare"]["operations"]},
            {
                "catalog-capabilities",
                "trade-calendar",
                "stock-basic",
                "daily-quotes",
                "weekly-quotes",
                "monthly-quotes",
                "adjust-factor",
                "daily-basic",
                "money-flow",
                "margin-summary",
                "top-list",
                "income-statement",
                "balance-sheet",
                "cash-flow-statement",
                "financial-indicator",
                "index-basic",
                "index-daily",
                "fund-basic",
                "fund-nav",
                "hk-hold",
            },
        )
        tushare_limits = providers["tushare"]["limits"]
        self.assertFalse(tushare_limits["arbitrary_api_names_allowed"])
        self.assertFalse(tushare_limits["arbitrary_urls_allowed"])
        self.assertFalse(tushare_limits["write_operations_allowed"])
        self.assertFalse(tushare_limits["trading_or_order_execution_allowed"])

        wolfram = providers["wolfram-alpha"]
        self.assertEqual(wolfram["ticket_prefix"], "[api-wolfram]")
        self.assertEqual(
            {row["operation_id"] for row in wolfram["operations"]},
            {
                "catalog-capabilities",
                "full-results",
                "short-answer",
                "llm-result",
            },
        )
        self.assertFalse(wolfram["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(wolfram["limits"]["write_operations_allowed"])

        llamaparse = providers["llamaparse"]
        self.assertEqual(llamaparse["ticket_prefix"], "[api-llamaparse]")
        self.assertEqual(
            {row["operation_id"] for row in llamaparse["operations"]},
            {
                "catalog-capabilities",
                "parse-public-document",
                "get-job",
            },
        )
        self.assertFalse(llamaparse["limits"]["arbitrary_urls_allowed"])
        self.assertFalse(llamaparse["limits"]["webhooks_allowed"])
        self.assertFalse(llamaparse["limits"]["presigned_urls_exposed"])

        for catalog_file in (
            "tushare/provider-catalog.json",
            "knowledge-tools/provider-catalog.json",
        ):
            self.assertIn(catalog_file, catalog["managed_provider_catalog_files"])
            self.assertIn(catalog_file, catalog["detail_reading_order"])
        self.assertNotIn(
            "tianditu/provider-catalog.json",
            catalog["managed_provider_catalog_files"],
        )

        self.assertEqual(
            providers["yuandian-law"]["discovered_readonly_tool_count"],
            37,
        )
        self.assertEqual(
            providers["jina-reader"][
                "required_secret_environment_variable_name"
            ],
            "",
        )
        self.assertEqual(
            providers["jina-reader"][
                "optional_secret_environment_variable_name"
            ],
            "JINA_API_KEY",
        )
        self.assertEqual(
            providers["akshare"]["required_secret_environment_variable_name"],
            "",
        )

        connector_map = {
            row["connector_id"]: row for row in catalog["connectors"]
        }
        self.assertTrue(
            {
                "newsapi-everything",
                "newsapi-top-headlines",
                "newsapi-sources",
                "openmeteo-forecast",
                "baidu-geocode",
                "baidu-place-search",
                "worldbank-indicators",
                "wikidata-entity-get",
                "dbnomics-search",
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
        self.assertNotIn("TIANDITU_API_KEY", serialized)
        self.assertNotIn("TIANDITU_EXPECTED_EGRESS_IP", serialized)
        self.assertNotIn("QICHACHA_CREDENTIALS_JSON", serialized)
        self.assertNotIn("Bearer llx-", serialized)
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
                    contract.get("status_path")
                    and contract.get("success_values")
                )
                data_contract = bool(
                    contract.get("success_when_data_present") is True
                    and contract.get("any_data_paths")
                )
                self.assertTrue(status_contract or data_contract)

    def test_catalog_output_is_deterministic(self) -> None:
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(
            first["generation"],
            "deterministic-from-repository-state",
        )

    def test_committed_catalog_matches_generator(self) -> None:
        generated = self.build()
        committed = json.loads(
            (ROOT / "api-catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(generated, committed)
        self.assertEqual(
            build_catalog.render_markdown(generated),
            (ROOT / "api-catalog.md").read_text(encoding="utf-8"),
        )

    def test_main_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = self.build()
            json_path = root / "catalog.json"
            markdown_path = root / "catalog.md"
            json_path.write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            markdown_path.write_text(
                build_catalog.render_markdown(catalog),
                encoding="utf-8",
            )
            self.assertIn(
                "GPTs 使用中心",
                markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "catalog_sha256",
                json_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
