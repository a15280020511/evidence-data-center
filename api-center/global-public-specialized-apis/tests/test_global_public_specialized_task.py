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
    "global_public_specialized_task",
    HERE / "global_public_specialized_task.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GlobalPublicSpecializedTests(unittest.TestCase):
    def test_catalog_schema_parity_and_safety(self) -> None:
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
        self.assertEqual(matrix["active_source_count"], 2)

    def test_poland_fixed_contracts(self) -> None:
        url, method, headers, query, body, used, source = MODULE.build_request(
            "poland-isztar4-help",
            {"language": "EN"},
        )
        self.assertEqual(url, "https://ext-isztar4.mf.gov.pl/taryfa_celna/Help")
        self.assertEqual(method, "GET")
        self.assertIn(("lang", "EN"), query)
        self.assertIn("text/html", headers["Accept"])
        self.assertIsNone(body)
        self.assertEqual(used, [])
        self.assertEqual(source, "poland-isztar4")

        url, _, _, query, _, _, source = MODULE.build_request(
            "poland-isztar4-tariff-sections",
            {"language": "PL", "simulation_date": "20260805"},
        )
        self.assertEqual(
            url,
            "https://ext-isztar4.mf.gov.pl/taryfa_celna/PrelimInfoHC",
        )
        self.assertIn(("lang", "PL"), query)
        self.assertIn(("date", "20260805"), query)
        self.assertEqual(source, "poland-isztar4")

    def test_korea_key_is_backend_only(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"KOREA_DATA_GO_KR_SERVICE_KEY": "kr-secret"},
            clear=False,
        ):
            url, method, _, query, body, used, source = MODULE.build_request(
                "korea-krx-listed-companies",
                {
                    "page": 2,
                    "limit": 10,
                    "base_date": "20260805",
                    "company_name": "Samsung",
                },
            )
        self.assertEqual(
            url,
            "https://apis.data.go.kr/1160100/service/"
            "GetKrxListedInfoService/getItemInfo",
        )
        self.assertEqual(method, "GET")
        self.assertIn(("serviceKey", "kr-secret"), query)
        self.assertIn(("resultType", "json"), query)
        self.assertIn(("basDt", "20260805"), query)
        self.assertIn(("likeCorpNm", "Samsung"), query)
        self.assertIsNone(body)
        self.assertEqual(used, ["KOREA_DATA_GO_KR_SERVICE_KEY"])
        self.assertEqual(source, "korea-data-go-kr-krx-listed")

    def test_fail_closed_and_parameter_guards(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"KOREA_DATA_GO_KR_SERVICE_KEY": ""},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                MODULE.build_request("korea-krx-listed-companies", {})
        with self.assertRaises(ValueError):
            MODULE.build_request("poland-isztar4-help", {"language": "DE"})
        with self.assertRaises(ValueError):
            MODULE.build_request(
                "poland-isztar4-tariff-sections",
                {"simulation_date": "2026-08-05"},
            )
        with mock.patch.dict(
            os.environ,
            {"KOREA_DATA_GO_KR_SERVICE_KEY": "kr-secret"},
            clear=False,
        ):
            with self.assertRaises(ValueError):
                MODULE.build_request(
                    "korea-krx-listed-companies",
                    {"company_name": "\u0000bad"},
                )
            with self.assertRaises(ValueError):
                MODULE.build_request(
                    "korea-krx-listed-companies",
                    {"url": "https://example.com"},
                )


if __name__ == "__main__":
    unittest.main()
