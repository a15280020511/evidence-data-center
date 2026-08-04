from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "strategic_intelligence_task", HERE / "strategic_intelligence_task.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_catalog_and_schema_are_valid() -> None:
    catalog = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
    schema = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert catalog["secret_values_exposed"] is False
    provider = catalog["providers"][0]
    operation_ids = {item["operation_id"] for item in provider["operations"]}
    assert operation_ids == set(schema["properties"]["operation"]["enum"])
    assert provider["limits"]["requests_per_ticket_max"] == 1
    assert provider["limits"]["redirects_allowed"] is False


def test_openfema_request_is_fixed_and_bounded() -> None:
    url, query, kind = MODULE.build_request(
        "openfema-disaster-declarations",
        {"state": "CA", "year_from": 2020, "year_to": 2026, "top": 25},
    )
    assert url == "https://www.fema.gov/api/open/v1/DisasterDeclarationsSummaries"
    assert kind == "openfema"
    values = dict(query)
    assert values["$top"] == "25"
    assert "state eq 'CA'" in values["$filter"]


def test_ripestat_resources_are_structurally_validated() -> None:
    url, query, kind = MODULE.build_request(
        "ripestat-network-info", {"resource": "8.8.8.8"}
    )
    assert url == "https://stat.ripe.net/data/network-info/data.json"
    assert query == [("resource", "8.8.8.8")]
    assert kind == "ripestat"
    with pytest.raises(ValueError):
        MODULE.build_request("ripestat-network-info", {"resource": "example.com"})
    with pytest.raises(ValueError):
        MODULE.build_request("ripestat-prefix-overview", {"resource": "8.8.8.8;rm"})


def test_peeringdb_rejects_arbitrary_object_types() -> None:
    url, query, kind = MODULE.build_request(
        "peeringdb-search", {"object_type": "net", "name": "Google", "limit": 10}
    )
    assert url == "https://www.peeringdb.com/api/net"
    assert dict(query)["limit"] == "10"
    assert kind == "peeringdb"
    with pytest.raises(ValueError):
        MODULE.build_request(
            "peeringdb-search", {"object_type": "../../admin", "name": "x"}
        )


def test_local_operations_make_no_upstream_request() -> None:
    assert MODULE.build_request("catalog-capabilities", {}) == (None, [], "catalog")
    assert MODULE.build_request("source-access-matrix", {}) == (
        None,
        [],
        "source-matrix",
    )


def test_response_contracts() -> None:
    assert MODULE.validate_response(
        "ripestat", {"status": "ok", "data": {"asns": [15169]}}
    ) is None
    assert MODULE.validate_response("peeringdb", {"data": [{"id": 1}]}) == 1
    assert MODULE.validate_response(
        "openfema", {"DisasterDeclarationsSummaries": []}
    ) == 0
    assert MODULE.validate_response("mitre-index", {"collections": [{"id": "x"}]}) == 1
    with pytest.raises(RuntimeError):
        MODULE.validate_response("peeringdb", {"data": {}})


def test_source_matrix_does_not_hide_conditions() -> None:
    matrix = json.loads((HERE / "source-access-matrix.json").read_text(encoding="utf-8"))
    conditions = {item["source_id"]: item["condition"] for item in matrix["conditional_sources"]}
    assert conditions["ucdp"] == "free_token_required"
    assert conditions["global-fishing-watch"] == "token_required_and_noncommercial_only"
    assert conditions["opensanctions"] == "noncommercial_or_separate_license"
    assert matrix["governance"]["write_operations_allowed"] is False
