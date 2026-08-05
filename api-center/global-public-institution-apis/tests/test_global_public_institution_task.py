from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "global_public_institution_task",
    HERE / "global_public_institution_task.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GlobalPublicInstitutionTests(unittest.TestCase):
    def test_catalog_schema_operation_parity(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        provider = catalog["providers"][0]
        self.assertEqual(
            {row["operation_id"] for row in provider["operations"]},
            set(schema["properties"]["operation"]["enum"]),
        )
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertIs(provider["limits"]["redirects_allowed"], False)
        self.assertIs(provider["limits"]["arbitrary_urls_allowed"], False)
        self.assertIs(provider["limits"]["client_supplied_credentials_allowed"], False)
        self.assertIs(matrix["governance"]["write_operations_allowed"], False)
        self.assertIs(matrix["governance"]["personal_data_queries_allowed"], False)
        self.assertIs(catalog["secret_values_exposed"], False)

    def test_existing_no_key_request_contracts(self) -> None:
        url, method, headers, query, body, used, source = MODULE.build_request(
            "singapore-collections", {"page": 2}
        )
        self.assertEqual(url, "https://api-production.data.gov.sg/v2/public/api/collections")
        self.assertEqual(method, "GET")
        self.assertIn(("page", "2"), query)
        self.assertNotIn("x-api-key", headers)
        self.assertEqual(used, [])
        self.assertEqual(source, "singapore-data-gov")
        self.assertIsNone(body)

        url, method, _, query, _, used, source = MODULE.build_request("abs-dataflows", {})
        self.assertEqual(url, "https://data.api.abs.gov.au/rest/dataflow/ABS/all/latest")
        self.assertEqual(method, "GET")
        self.assertIn(("detail", "allstubs"), query)
        self.assertEqual(used, [])
        self.assertEqual(source, "australia-abs-data-api")

        url, _, _, query, _, _, _ = MODULE.build_request(
            "cnra-dataset-search", {"query": "groundwater", "limit": 10}
        )
        self.assertEqual(url, "https://data.cnra.ca.gov/api/3/action/package_search")
        self.assertIn(("rows", "10"), query)

        url, _, _, query, _, _, source = MODULE.build_request(
            "asu-dataverse-search", {"query": "climate", "limit": 5}
        )
        self.assertEqual(url, "https://dataverse.asu.edu/api/search")
        self.assertIn(("type", "dataset"), query)
        self.assertEqual(source, "asu-dataverse")

    def test_uk_api_catalogue_fixed_contract(self) -> None:
        url, method, headers, query, body, used, source = MODULE.build_request(
            "uk-api-catalogue-csv", {}
        )
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv",
        )
        self.assertEqual(method, "GET")
        self.assertEqual(query, [])
        self.assertIsNone(body)
        self.assertEqual(used, [])
        self.assertEqual(source, "uk-api-catalogue")
        self.assertIn("text/csv", headers["Accept"])

    def test_nipo_bounded_search_and_record_contracts(self) -> None:
        url, method, _, query, body, used, source = MODULE.build_request(
            "nipo-open-data-search",
            {
                "obj_type": 4,
                "obj_state": 1,
                "app_date_from": "01.06.2020",
                "app_date_to": "20.06.2020",
            },
        )
        self.assertEqual(url, "https://sis.nipo.gov.ua/api/v1/open-data/")
        self.assertEqual(method, "GET")
        self.assertIn(("obj_type", "4"), query)
        self.assertIn(("obj_state", "1"), query)
        self.assertIn(("app_date_from", "01.06.2020"), query)
        self.assertIn(("app_date_to", "20.06.2020"), query)
        self.assertIsNone(body)
        self.assertEqual(used, [])
        self.assertEqual(source, "ukraine-nipo")

        url, _, _, query, _, _, source = MODULE.build_request(
            "nipo-open-data-record", {"object_id": "m202011127", "obj_type": 4}
        )
        self.assertEqual(url, "https://sis.nipo.gov.ua/api/v1/open-data/m202011127/")
        self.assertEqual(query, [("obj_type", "4")])
        self.assertEqual(source, "ukraine-nipo")

    def test_nipo_query_guards(self) -> None:
        invalid_requests = [
            ("nipo-open-data-search", {"obj_type": 4}),
            (
                "nipo-open-data-search",
                {
                    "obj_type": 4,
                    "app_date_from": "01.01.2026",
                    "app_date_to": "15.02.2026",
                },
            ),
            (
                "nipo-open-data-search",
                {"obj_type": 4, "app_date_from": "01.01.2026"},
            ),
            (
                "nipo-open-data-search",
                {
                    "app_date_from": "01.01.2026",
                    "app_date_to": "02.01.2026",
                },
            ),
            ("nipo-open-data-record", {"object_id": "../../etc/passwd"}),
            (
                "nipo-open-data-search",
                {"obj_type": 99, "app_number": "m202011127"},
            ),
        ]
        for operation, parameters in invalid_requests:
            with self.subTest(operation=operation, parameters=parameters):
                with self.assertRaises(ValueError):
                    MODULE.build_request(operation, parameters)

    def test_required_keys_are_backend_only(self) -> None:
        cases = [
            (
                "BPS_API_KEY",
                "secret-bps",
                "bps-domain-list",
                {"domain_type": "all"},
                ("key", "secret-bps"),
            ),
            (
                "ESTAT_APP_ID",
                "estat-app",
                "estat-stats-list",
                {"query": "population", "limit": 10},
                ("appId", "estat-app"),
            ),
            (
                "INDIA_DATA_GOV_API_KEY",
                "india-key",
                "india-resource-get",
                {
                    "resource_id": "12345678-1234-1234-1234-123456789abc",
                    "limit": 10,
                },
                ("api-key", "india-key"),
            ),
        ]
        for env_name, value, operation, parameters, expected_query in cases:
            with self.subTest(operation=operation):
                with mock.patch.dict(os.environ, {env_name: value}, clear=False):
                    _, _, _, query, _, used, _ = MODULE.build_request(operation, parameters)
                    self.assertIn(expected_query, query)
                    self.assertEqual(used, [env_name])

        with mock.patch.dict(
            os.environ, {"MATERIALS_PROJECT_API_KEY": "mp-key"}, clear=False
        ):
            _, _, headers, query, _, used, _ = MODULE.build_request(
                "materials-summary-search", {"chemical_system": "Si-O", "limit": 5}
            )
            self.assertEqual(headers["X-API-KEY"], "mp-key")
            self.assertIn(("_limit", "5"), query)
            self.assertEqual(used, ["MATERIALS_PROJECT_API_KEY"])

    def test_missing_required_keys_fail_closed(self) -> None:
        names = [
            "BPS_API_KEY",
            "ESTAT_APP_ID",
            "MATERIALS_PROJECT_API_KEY",
            "INDIA_DATA_GOV_API_KEY",
            "BRAZIL_DADOS_GOV_TOKEN",
        ]
        cleaned = {name: "" for name in names}
        cases = [
            ("bps-domain-list", {"domain_type": "all"}),
            ("estat-stats-list", {"query": "population"}),
            ("materials-summary-search", {"chemical_system": "Si-O"}),
            (
                "india-resource-get",
                {"resource_id": "12345678-1234-1234-1234-123456789abc"},
            ),
            ("brazil-dataset-list", {"page": 1}),
        ]
        with mock.patch.dict(os.environ, cleaned, clear=False):
            for operation, parameters in cases:
                with self.subTest(operation=operation):
                    with self.assertRaises(RuntimeError):
                        MODULE.build_request(operation, parameters)

    def test_identifier_and_parameter_guards(self) -> None:
        cases = [
            ("singapore-collections", {"url": "https://example.com"}),
            ("abs-data", {"dataflow": "../../etc", "data_key": "all"}),
            ("materials-summary-search", {"chemical_system": "Si/O"}),
            ("asu-dataverse-search", {"query": "\u0000bad"}),
            ("india-resource-get", {"resource_id": "not-a-uuid"}),
        ]
        for operation, parameters in cases:
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    MODULE.build_request(operation, parameters)

    def test_source_status_counts_and_exclusions(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        sources = {row["source_id"]: row for row in matrix["sources"]}
        self.assertEqual(matrix["active_source_count"], len(sources))
        self.assertEqual(matrix["production_live_count"], 6)
        self.assertEqual(matrix["pending_free_credential_count"], 5)
        self.assertEqual(matrix["pending_live_acceptance_count"], 0)
        self.assertEqual(
            sources["uk-api-catalogue"]["implementation_status"], "production-live"
        )
        self.assertEqual(
            sources["ukraine-nipo"]["implementation_status"], "production-live"
        )
        self.assertEqual(sources["uk-api-catalogue"]["live_acceptance"]["issue"], 1102)
        self.assertEqual(sources["ukraine-nipo"]["live_acceptance"]["issue"], 1103)
        self.assertEqual(
            sources["uk-api-catalogue"]["live_acceptance"]["artifact_id"],
            8920690933,
        )
        self.assertEqual(
            sources["ukraine-nipo"]["live_acceptance"]["artifact_id"],
            8920823064,
        )
        excluded = {row["source_id"] for row in matrix["not_enabled"]}
        self.assertIn("issuelab-oai", excluded)
        self.assertIn("poland-isztar4", excluded)
        self.assertNotIn("ukraine-nipo", excluded)


if __name__ == "__main__":
    unittest.main()
