from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "country_industry_atlas_task", HERE / "country_industry_atlas_task.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CountryIndustryAtlasTests(unittest.TestCase):
    def test_catalog_schema_and_operation_parity(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        provider = catalog["providers"][0]
        self.assertEqual(
            {row["operation_id"] for row in provider["operations"]},
            set(schema["properties"]["operation"]["enum"]),
        )
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertIs(provider["limits"]["redirects_allowed"], False)
        self.assertIs(provider["limits"]["arbitrary_urls_allowed"], False)
        self.assertIs(provider["limits"]["discovery_results_are_production_authorities"], False)
        self.assertIs(catalog["secret_values_exposed"], False)

    def test_fixed_request_contracts(self) -> None:
        self.assertEqual(
            MODULE.build_request("catalog-capabilities", {}),
            (None, "LOCAL", [], None, "catalog"),
        )
        self.assertEqual(
            MODULE.build_request("country-industry-atlas", {}),
            (None, "LOCAL", [], None, "atlas"),
        )
        self.assertEqual(
            MODULE.build_request("atlas-search", {"industry": "procurement", "limit": 10}),
            (None, "LOCAL", [], None, "atlas-search"),
        )
        url, method, params, body, kind = MODULE.build_request(
            "portal-registry-search",
            {"country": "AU", "status": "active", "api_only": True, "limit": 10},
        )
        self.assertEqual(url, "https://dataportals.org/api/data.json")
        self.assertEqual(method, "GET")
        self.assertEqual(params, [])
        self.assertIsNone(body)
        self.assertEqual(kind, "portal-registry")
        with self.assertRaises(ValueError):
            MODULE.build_request("portal-registry-search", {"url": "https://example.com"})
        with self.assertRaises(ValueError):
            MODULE.build_request("country-industry-atlas", {"query": "x"})

    def test_portal_registry_filters_are_bounded(self) -> None:
        sample = {
            "au-government": {
                "title": "Australian Government Data",
                "url": "https://data.gov.au",
                "publisher": "Australian Government",
                "publisher_classification": "Government",
                "country": "AU",
                "place": "Australia",
                "status": "active",
                "generator": "CKAN",
                "api_endpoint": "https://data.gov.au/data/api/3",
                "api_type": "CKAN",
                "license_id": "cc-by",
                "tags": ["government", "level.national"],
            },
            "au-community": {
                "title": "Community Portal",
                "url": "https://community.example",
                "publisher": "Community",
                "publisher_classification": "Community",
                "country": "AU",
                "status": "active",
                "generator": "CKAN",
                "api_endpoint": "https://community.example/api",
                "api_type": "CKAN",
                "tags": ["community"],
            },
            "au-old": {
                "title": "Old Government Portal",
                "url": "https://old.example",
                "publisher": "Government",
                "publisher_classification": "Government",
                "country": "AU",
                "status": "inactive",
                "tags": ["government"],
            },
            "ca-government": {
                "title": "Canada Government Portal",
                "url": "https://open.canada.ca",
                "publisher": "Government of Canada",
                "publisher_classification": "Government",
                "country": "CA",
                "status": "active",
                "generator": "CKAN",
                "api_endpoint": "https://open.canada.ca/data/api",
                "api_type": "CKAN",
                "tags": ["government"],
            },
        }
        result = MODULE.filter_portal_registry(
            sample,
            {
                "country": "AU",
                "status": "active",
                "api_only": True,
                "government_only": True,
                "limit": 10,
            },
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["portal_id"], "au-government")
        self.assertIs(result["discovery_only"], True)
        self.assertIs(result["verification_required_before_production"], True)
        self.assertEqual(result["registry_license"], "Public Domain")

    def test_local_atlas_country_and_industry_search(self) -> None:
        atlas = json.loads((HERE / "source-atlas.json").read_text(encoding="utf-8"))
        china = MODULE.filter_atlas(atlas, {"country": "CN", "limit": 20})
        self.assertGreaterEqual(china["count"], 1)
        self.assertTrue(any(row["source_id"] == "asia-country-gateway" for row in china["results"]))
        procurement = MODULE.filter_atlas(atlas, {"industry": "procurement", "limit": 100})
        self.assertGreaterEqual(procurement["count"], 3)
        self.assertTrue(
            any(row["source_id"] == "open-contracting-data-registry" for row in procurement["results"])
        )
        direct = MODULE.filter_atlas(atlas, {"access_tier": "direct-no-key-pending-live", "limit": 100})
        self.assertGreaterEqual(direct["count"], 5)

    def test_atlas_governance_and_coverage(self) -> None:
        atlas = json.loads((HERE / "source-atlas.json").read_text(encoding="utf-8"))
        self.assertIn("All countries", atlas["coverage_target"])
        self.assertEqual(len(atlas["regional_country_gateways"]), 6)
        self.assertGreaterEqual(len(atlas["industry_discovery_directories"]), 20)
        source_ids = {
            row["source_id"]
            for section in (
                "official_discovery_layers",
                "regional_country_gateways",
                "industry_discovery_directories",
                "direct_api_candidates",
                "registration_or_application_candidates",
                "catalog_only_sources",
            )
            for row in atlas[section]
        }
        self.assertTrue(
            {
                "dataportals-public-registry",
                "data-europa-catalogue-network",
                "afdb-country-open-data-platforms",
                "eclac-cepalstat-nso-directory",
                "open-contracting-data-registry",
                "wipo-ip-api-catalog",
            }.issubset(source_ids)
        )
        governance = atlas["governance"]
        self.assertIs(governance["registry_results_are_discovery_only"], True)
        self.assertIs(governance["redirects_allowed"], False)
        self.assertIs(governance["personal_data_queries_allowed"], False)
        self.assertIs(
            governance["promotion_requires_official_identity_license_contract_and_live_acceptance"],
            True,
        )


if __name__ == "__main__":
    unittest.main()
