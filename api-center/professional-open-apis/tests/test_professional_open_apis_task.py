from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "professional_open_apis_task", HERE / "professional_open_apis_task.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProfessionalOpenApisTests(unittest.TestCase):
    def test_catalog_schema_and_operation_parity(self) -> None:
        catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        provider = catalog["providers"][0]
        catalog_ops = {row["operation_id"] for row in provider["operations"]}
        schema_ops = set(schema["properties"]["operation"]["enum"])
        self.assertEqual(catalog_ops, schema_ops)
        self.assertEqual(provider["limits"]["requests_per_ticket_max"], 1)
        self.assertIs(provider["limits"]["redirects_allowed"], False)
        self.assertIs(catalog["secret_values_exposed"], False)

    def test_data_gov_uk_request(self) -> None:
        url, method, params, body, kind, accept = MODULE.build_request(
            "data-gov-uk-search", {"query": "energy prices", "limit": 25}
        )
        self.assertEqual(url, "https://data.gov.uk/api/action/package_search")
        self.assertEqual(method, "GET")
        self.assertIsNone(body)
        self.assertEqual(kind, "ckan")
        self.assertEqual(dict(params)["rows"], "25")
        self.assertIn("json", accept)

    def test_pubchem_request_is_property_allowlisted(self) -> None:
        url, method, params, body, kind, _ = MODULE.build_request(
            "pubchem-compound-properties",
            {"name": "acetylsalicylic acid", "properties": ["MolecularFormula", "InChIKey"]},
        )
        self.assertEqual(method, "GET")
        self.assertEqual(params, [])
        self.assertIsNone(body)
        self.assertEqual(kind, "pubchem")
        self.assertIn("acetylsalicylic%20acid", url)
        self.assertIn("MolecularFormula,InChIKey", url)
        with self.assertRaises(ValueError):
            MODULE.build_request(
                "pubchem-compound-properties",
                {"name": "aspirin", "properties": ["NotAProperty"]},
            )

    def test_usgs_water_request_is_bounded(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request(
            "usgs-water-instantaneous",
            {"site": "01646500", "parameter_codes": ["00060", "00065"], "period": "PT6H"},
        )
        values = dict(params)
        self.assertEqual(url, "https://waterservices.usgs.gov/nwis/iv/")
        self.assertEqual(kind, "usgs-water")
        self.assertEqual(values["sites"], "01646500")
        self.assertEqual(values["parameterCd"], "00060,00065")
        self.assertEqual(values["period"], "PT6H")
        with self.assertRaises(ValueError):
            MODULE.build_request("usgs-water-instantaneous", {"site": "../bad"})

    def test_worms_request_is_fixed(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request(
            "worms-taxon-search", {"name": "Delphinus", "like": True, "marine_only": True}
        )
        self.assertEqual(
            url,
            "https://www.marinespecies.org/rest/AphiaRecordsByName/Delphinus",
        )
        self.assertEqual(kind, "worms")
        values = dict(params)
        self.assertEqual(values["like"], "true")
        self.assertEqual(values["marine_only"], "true")
        self.assertEqual(values["offset"], "1")
        self.assertNotIn("limit", values)

    def test_idref_and_sudoc_requests(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request(
            "idref-authority-search", {"query": "Fuzhou University", "index": "corpname_t", "limit": 10}
        )
        self.assertEqual(url, "https://www.idref.fr/Sru/Solr")
        self.assertEqual(kind, "idref")
        values = dict(params)
        self.assertEqual(values["q"], "corpname_t:Fuzhou University")
        self.assertEqual(values["rows"], "10")

        url, _, params, _, kind, _ = MODULE.build_request(
            "sudoc-isbn-lookup", {"isbn": "978-0-306-40615-7"}
        )
        self.assertEqual(url, "https://www.sudoc.fr/services/isbn2ppn/9780306406157")
        self.assertEqual(params, [])
        self.assertEqual(kind, "sudoc-xml")

    def test_ons_and_agris_requests(self) -> None:
        url, _, params, _, kind, _ = MODULE.build_request("ons-datasets", {"limit": 15})
        self.assertEqual(url, "https://api.beta.ons.gov.uk/v1/datasets")
        self.assertEqual(dict(params)["limit"], "15")
        self.assertEqual(kind, "ons")
        url, _, params, _, kind, accept = MODULE.build_request("agris-ods-index", {})
        self.assertEqual(url, "https://agris.fao.org/agris_ods")
        self.assertEqual(params, [])
        self.assertEqual(kind, "agris-html")
        self.assertIn("html", accept)

    def test_response_contracts(self) -> None:
        self.assertEqual(
            MODULE.validate_json_response("ckan", {"success": True, "result": {"results": [{}]}})[0],
            1,
        )
        self.assertEqual(
            MODULE.validate_json_response(
                "pubchem", {"PropertyTable": {"Properties": [{"CID": 2244}]}}
            )[0],
            1,
        )
        self.assertEqual(
            MODULE.validate_json_response("usgs-water", {"value": {"timeSeries": []}})[0],
            0,
        )
        self.assertEqual(MODULE.validate_json_response("worms", [{"AphiaID": 137094}])[0], 1)
        self.assertEqual(
            MODULE.validate_json_response("idref", {"response": {"docs": []}})[0],
            0,
        )
        self.assertEqual(MODULE.validate_json_response("ons", {"items": []})[0], 0)
        xml = b"<isbn2ppn><ppn>123456789</ppn></isbn2ppn>"
        self.assertEqual(MODULE.parse_xml_response("sudoc-xml", xml)[0], 1)
        html = b"<html><title>AGRIS</title><a href='sample.rdf.zip'>file</a></html>"
        count, data = MODULE.parse_agris_index(html)
        self.assertEqual(count, 1)
        self.assertTrue(data["index_available"])

    def test_query_sanitization_and_local_operations(self) -> None:
        self.assertEqual(MODULE.safe_plain_query("energy AND price:*"), "energy price")
        self.assertEqual(
            MODULE.build_request("catalog-capabilities", {}),
            (None, "LOCAL", [], None, "catalog", "application/json"),
        )
        self.assertEqual(
            MODULE.build_request("source-access-matrix", {}),
            (None, "LOCAL", [], None, "matrix", "application/json"),
        )
        with self.assertRaises(ValueError):
            MODULE.build_request("agris-ods-index", {"query": "x"})

    def test_matrix_exposes_live_status_and_candidates(self) -> None:
        matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
        production = {row["source_id"] for row in matrix["production_sources"]}
        self.assertTrue(
            {"pubchem-pug-rest", "usgs-water-services", "worms", "ons-api"}.issubset(production)
        )
        endpoint_fix = {row["source_id"] for row in matrix["endpoint_fix_pending_live_acceptance"]}
        self.assertTrue({"data-gov-uk", "fao-agris-ods"}.issubset(endpoint_fix))
        blocked = {row["source_id"] for row in matrix["implemented_external_connectivity_blocked"]}
        self.assertTrue({"idref", "sudoc"}.issubset(blocked))
        self.assertFalse(matrix["current_service_status"]["data_commons"]["new_key_required"])
        self.assertEqual(matrix["current_service_status"]["data_commons"]["current_live_issue"], 1015)
        self.assertIn("not-production", matrix["current_service_status"]["faostat"]["legacy_fenix_rest"])
        candidates = {row["source_id"] for row in matrix["free_key_or_registration_candidates"]}
        self.assertTrue({"nara-catalog", "usda-fooddata-central", "materials-project"}.issubset(candidates))
        future = {row["source_id"] for row in matrix["verified_future_no_key"]}
        self.assertTrue({"nhm-data-portal", "optimade-federation", "nioccs"}.issubset(future))
        self.assertIs(matrix["governance"]["write_operations_allowed"], False)


if __name__ == "__main__":
    unittest.main()
