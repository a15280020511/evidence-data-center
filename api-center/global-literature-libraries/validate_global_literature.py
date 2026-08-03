#!/usr/bin/env python3
"""Validate the fixed global literature provider without escaping its registry."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from global_literature_task import (
    CATALOG_PATH,
    MATRIX_PATH,
    build,
    execute,
    load_json,
)

DUMMY_SECRETS = {
    "CORE_API_KEY": "fixture-core-key",
    "SEMANTIC_SCHOLAR_API_KEY": "fixture-semantic-key",
    "NASA_ADS_API_TOKEN": "fixture-ads-token",
    "EUROPEANA_API_KEY": "fixture-europeana-key",
    "DPLA_API_KEY": "fixture-dpla-key",
    "CINII_APP_ID": "fixture-cinii-app",
    "DOAJ_API_KEY": "fixture-doaj-key",
}


def parameters_for(operation: str, source_id: str) -> dict:
    if operation == "literature-search":
        return {"source_id": source_id, "query": "climate policy", "limit": 3}
    if operation == "literature-record":
        identifiers = {
            "core": "1",
            "openaire": "doi_dedup___::a55b42c0d32a4a24cf99e621623d110e",
            "semantic-scholar": "CorpusID:1",
            "europe-pmc": "12345678",
            "zenodo": "1234",
            "osf": "abc12",
            "figshare": "1234",
            "econbiz": "10003864941",
            "osti": "1234",
            "nasa-ads": "2020ApJ...000..001A",
            "library-of-congress": "2021667269",
            "open-library": "OL45883W",
            "europeana": "/2020601/https___1914_1918_europeana_eu_contributions_1",
            "dpla": "12345678-abcd-1234-abcd-1234567890ab",
        }
        return {"source_id": source_id, "record_id": identifiers[source_id]}
    if operation == "preprint-feed":
        return {
            "source_id": source_id,
            "from_date": "2026-01-01",
            "until_date": "2026-01-02",
            "cursor": 0,
        }
    if operation == "oai-identify":
        return {"source_id": source_id}
    if operation == "oai-list-records":
        return {
            "source_id": source_id,
            "metadata_prefix": "oai_dc",
            "from_date": "2026-01-01",
            "until_date": "2026-01-02",
        }
    if operation == "oai-get-record":
        return {
            "source_id": source_id,
            "identifier": "oai:fixture:1",
            "metadata_prefix": "oai_dc",
        }
    if operation == "sru-search":
        return {
            "source_id": source_id,
            "query": "climate",
            "limit": 3,
            "record_schema": "dc",
        }
    if operation == "patent-publication-get":
        return {
            "source_id": source_id,
            "publication_number": "EP1004359NWB1",
            "format": "formats",
        }
    raise ValueError(operation)


def validate_registry() -> dict:
    for key, value in DUMMY_SECRETS.items():
        os.environ[key] = value
    matrix = load_json(MATRIX_PATH)
    catalog = load_json(CATALOG_PATH)
    provider = catalog["providers"][0]
    operations = {row["operation_id"]: row for row in provider["operations"]}
    sources = matrix["sources"]
    assert provider["provider_id"] == "global-literature-libraries"
    assert provider["ticket_prefix"] == "[intel-literature]"
    assert (
        len(sources)
        == matrix["active_source_count"]
        == provider["limits"]["source_count"]
        == 26
    )
    assert len(operations) == 10
    assert matrix["governance"]["fixed_sources_only"] is True
    assert matrix["governance"]["arbitrary_urls_allowed"] is False
    assert matrix["governance"]["automatic_pagination_allowed"] is False
    assert matrix["governance"]["paywall_bypass_allowed"] is False
    assert provider["limits"]["requests_per_ticket_max"] == 1
    assert provider["limits"]["write_operations_allowed"] is False
    assert provider["limits"]["unauthorized_full_text_copying_allowed"] is False
    base_source = next(row for row in sources if row["source_id"] == "base")
    assert base_source["credential_mode"] == "none"
    assert base_source["credential_env"] == ""
    assert base_source["access_control"] == "ip_allowlist_required"

    checked = []
    for source in sources:
        source_id = source["source_id"]
        for operation in source["operations"]:
            params = parameters_for(operation, source_id)
            row, request = build(operation, params)
            method, url, headers, query, body, credential_names = request
            parsed = urlsplit(url)
            assert row["source_id"] == source_id
            assert parsed.scheme == "https" and parsed.netloc
            assert method in {"GET", "POST"}
            assert len(credential_names) <= 1
            assert not any(
                name.lower() in {"url", "host", "path", "headers", "api_key", "token"}
                for name in params
            )
            assert "Authorization" not in headers or credential_names
            checked.append(
                {
                    "source_id": source_id,
                    "operation": operation,
                    "method": method,
                    "origin": f"{parsed.scheme}://{parsed.netloc}",
                    "credential_names": credential_names,
                    "body_present": body is not None,
                    "query_names": [name for name, _ in query],
                }
            )
    return {
        "status": "PASS",
        "source_count": len(sources),
        "operation_count": len(operations),
        "builder_cases": len(checked),
        "rows": checked,
        "network_used": False,
        "model_calls": 0,
        "secret_values_exposed": False,
    }


LIVE_CASES = {
    "openaire": (
        "literature-search",
        {"source_id": "openaire", "query": "climate policy", "limit": 2},
    ),
    "europe-pmc": (
        "literature-search",
        {"source_id": "europe-pmc", "query": "malaria", "limit": 2},
    ),
    "econbiz": (
        "literature-search",
        {"source_id": "econbiz", "query": "industrial policy", "limit": 2},
    ),
    "osti": (
        "literature-search",
        {"source_id": "osti", "query": "energy storage", "limit": 2},
    ),
    "library-of-congress": (
        "literature-search",
        {"source_id": "library-of-congress", "query": "economic history", "limit": 2},
    ),
    "econstor-oai": ("oai-identify", {"source_id": "econstor-oai"}),
    "ndl-sru": (
        "sru-search",
        {"source_id": "ndl-sru", "query": "economics", "limit": 2, "record_schema": "dc"},
    ),
    "epo-publication-server": (
        "patent-publication-get",
        {
            "source_id": "epo-publication-server",
            "publication_number": "EP1004359NWB1",
            "format": "formats",
        },
    ),
}


def execute_case(source_id: str, output: Path) -> dict:
    operation, parameters = LIVE_CASES[source_id]
    ticket = {
        "task_id": f"literature-live-{source_id.replace('_', '-')}",
        "provider": "global-literature-libraries",
        "operation": operation,
        "objective": f"Bounded live acceptance for {source_id}",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 60, "max_response_bytes": 5000000},
    }
    output.mkdir(parents=True, exist_ok=True)
    ticket_path = output / "ticket.json"
    ticket_path.write_text(
        json.dumps(ticket, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.environ.pop("GLOBAL_LITERATURE_FIXTURE_MODE", None)
    code = execute(ticket_path, output)
    diagnostics = json.loads(
        (output / "diagnostics.json").read_text(encoding="utf-8")
    )
    if code != 0 or diagnostics["status"] != "INTEL_LITERATURE_COMPLETED":
        raise RuntimeError(json.dumps(diagnostics, ensure_ascii=False))
    return {
        "status": "PASS",
        "source_id": source_id,
        "operation": operation,
        "http_status": diagnostics["metadata"]["http_status"],
        "response_bytes": diagnostics["metadata"]["response_bytes"],
        "response_sha256": diagnostics["metadata"]["response_sha256"],
        "network_used": diagnostics["metadata"]["network_used"],
        "request_count": diagnostics["metadata"]["request_count"],
        "model_calls": diagnostics["model_calls"],
        "secret_values_exposed": diagnostics["secret_values_exposed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--live-source", choices=sorted(LIVE_CASES))
    args = parser.parse_args()
    output = Path(args.output)
    if args.live_source:
        receipt = execute_case(args.live_source, output.parent / f"live-{args.live_source}")
    else:
        receipt = validate_registry()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
