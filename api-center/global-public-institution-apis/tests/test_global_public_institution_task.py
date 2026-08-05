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
    "global_public_institution_task", HERE / "global_public_institution_task.py"
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

    def test_no_key_request_contracts(self) -> None:
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

    def test_new_official_catalog_and_publication_contracts(self) -> None:
        url, method, headers, query, body, used, source = MODULE.build_request(
            "uk-api-catalogue-index", {}
        )
        self.assertEqual(url, "https://www.api.gov.uk/index/")
        self.assertEqual(method, "GET")
        self.assertIn("text/html", headers["Accept"])
        self.assertEqual(query, [])
        self.assertIsNone(body)
        self.assertEqual(used, [])
        self.assertEqual(source, "uk-api-catalogue")

        url, method, _, query, _, used, source = MODULE.build_request(
            "poland-isztar4-service-info", {}
        )
        self.assertTrue(url.startswith("https://puesc.gov.pl/"))
        self.assertEqual(method, "GET")
        self.assertEqual(query, [])
        self.assertEqual(used, [])
        self.assertEqual(source, "poland-isztar4")

        url, method, _, query, _, used, source = MODULE.build_request(
            "ukraine-nipo-statistics", {}
        )
        self.assertEqual(url, "https://nipo.gov.ua/en/statistics-reports/")
        self.assertEqual(method, "GET")
        self.assertEqual(query, [])
        self.assertEqual(used, [])
        self.assertEqual(source, "ukraine-nipo")

    def test_required_keys_are_backend_only(self) -> None:
        with mock.patch.dict(os.environ, {"BPS_API_KEY": "secret-bps"}, clear=False):
            _, _, _, query, _, used, _ = MODULE.build_request("bps-domain-list", {"domain_type": "all"})
            self.assertIn(("key", "secret-bps"), query)
            self.assertEqual(used, ["BPS_API_KEY"])
        with mock.patch.dict(os.environ, {"ESTAT_APP_ID": "estat-app"}, clear=False):
            _, _, _, query, _, used, _ = MODULE.build_request(
                "estat-stats-list", {"query": "population", "limit": 10}
            )
            self.assertIn(("appId", "estat-app"), query)
            self.assertEqual(used, ["ESTAT_APP_ID"])
        with mock.patch.dict(os.environ, {"MATERIALS_PROJECT_API_KEY": "mp-key"}, clear=False):
            _, _, headers, query, _, used, _ = MODULE.build_request(
                "materials-summary-search", {"chemical_system": "Si-O", "limit": 5}
            )
            self.assertEqual(headers["X-API-KEY"], "mp-key")
            self.assertIn(("_limit", "5"), query)
            self.assertEqual(used, ["MATERIALS_PROJECT_API_KEY"])
        with mock.patch.dict(os.environ, {"INDIA_DATA_GOV_API_KEY": "india-key"}, clear=False):
            url, _, _, query, _, used, _ = MODULE.build_request(
                "india-resource-get",
                {"resource_id": "12345678-1234-1234-1234-123456789abc", "limit": 10},
            )
            self.assertEqual(url, "https://api.data.gov.in/resource/12345678-1234-1234-1234-123456789abc")
            self.assertIn(("api-key", "india-key"), query)
            self.assertEqual(used, ["INDIA_DATA_GOV_API_KEY"])
        with mock.patch.dict(os.environ, {"KOREA_DATA_GO_KR_SERVICE_KEY": "kr-key"}, clear=False):
            url, _, _, query, _, used, source = MODULE.build_request(
                "korea-krx-listed-companies",
                {"page": 2, "limit": 10, "base_date": "20260805", "company_name": "Samsung"},
            )
            self.assertEqual(url, "https://apis.data.go.kr/1160100/service/GetKrxListedInfoService/getItemInfo")
            self.assertIn(("serviceKey", "kr-key"), query)
            self.assertIn(("resultType", "json"), query)
            self.assertIn(("basDt", "20260805"), query)
            self.assertIn(("likeCorpNm", "Samsung"), query)
            self.assertEqual(used, ["KOREA_DATA_GO_KR_SERVICE_KEY"])
            self.assertEqual(source, "korea-data-go-kr-krx-listed")

    def test_missing_required_keys_fail_closed(self) -> None:
        names = [
            "BPS_API_KEY",
            "ESTAT_APP_ID",
            "MATERIALS_PROJECT_API_KEY",
            "INDIA_DATA_GOV_API_KEY",
            "BRAZIL_DADOS_GOV_TOKEN",
            "KOREA_DATA_GO_KR_SERVICE_KEY",
        ]
        cleaned = {name: "" for name in names}
        with mock.patch.dict(os.environ, cleaned, clear=False):
            with self.assertRaises(RuntimeError):
                MODULE.build_request("bps-domain-list", {"domain_type": "all"})
            with self.assertRaises(RuntimeError):
                MODULE.build_request("estat-stats-list", {"query": "population"})
            with self.assertRaises(RuntimeError):
                MODULE.build_request("materials-summary-search", {"chemical_system": "Si-O"})
            with self.assertRaises(RuntimeError):
                MODULE.build_request(
                    "india-resource-get", {"resource_id": "12345678-1234-1234-1234-123456789abc"}
                )
            with self.assertRaises(RuntimeError):
                MODULE.build_request("brazil-dataset-list", {"page": 1})
            with self.assertRaises(RuntimeError):
                MODULE.build_request("korea-krx-listed-companies", {})

    def test_identifier_and_parameter_guards(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.build_request("singapore-collections", {"url": "https://example.com"})
        with self.assertRaises(ValueError):
            MODULE.build_request("abs-data", {"dataflow": "../../etc", "data_key": "all"})
        with self.assertRaises(ValueError):
            MODULE.build_request("materials-summary-search", {"chemical_system": "Si/O"})
        with self.assertRaises(ValueError):
            MODULE.build_request("asu-dataverse-search", {"query": "\u0000bad"})
        with self.assertRaises(ValueError):
            MODULE.build_request("india-resource-get", {"resource_id": "not-a-uuid"})
        with mock.patch.dict(os.environ, {"KOREA_DATA_GO_KR_SERVICE_KEY": "kr-key"}, clear=False):
            with self.assertRaises(ValueError):
                MODULE.build_request("korea-krx-listed-companies", {"base_date": "2026-08-05"})
            with self.assertRaises(ValueError):
                MODULE.build_request("korea-krx-listed-companies", {"company_name": "\u0000bad"})


if __name__ == "__main__":
    unittest.main()
