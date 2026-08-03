#!/usr/bin/env python3
"""Validate second-wave global knowledge sources and bounded live access."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from global_knowledge_archives_task import (
    CATALOG_PATH,
    MATRIX_PATH,
    build,
    execute,
    load_json,
)

DUMMY_SECRETS = {
    "GOOGLE_API_KEY": "fixture-google-key",
    "BHL_API_KEY": "fixture-bhl-key",
}


def parameters_for(operation: str, source_id: str) -> dict:
    if operation == "knowledge-search":
        queries = {
            "dnb-sru": "tit=climate",
        }
        return {"source_id": source_id, "query": queries.get(source_id, "climate policy"), "limit": 3}
    if operation == "knowledge-record":
        record_ids = {
            "ukri-gtr": "07D6E9EA-F096-44BF-BAF6-01F2D3DE4489",
            "clinicaltrials-gov": "NCT05905666",
            "federal-register": "2026-06105",
            "met-museum": "437133",
            "art-institute-chicago": "129884",
            "digitalnz": "38022714",
            "google-books": "zyTCAlFPjgYC",
            "bhl": "125582",
        }
        return {"source_id": source_id, "record_id": record_ids[source_id]}
    if operation == "oai-identify":
        return {"source_id": source_id}
    if operation == "oai-list-records":
        return {"source_id": source_id, "metadata_prefix": "oai_dc"}
    if operation == "oai-get-record":
        return {"source_id": source_id, "identifier": "oai:fixture:1", "metadata_prefix": "oai_dc"}
    if operation == "sru-search":
        return {"source_id": source_id, "query": "tit=climate", "limit": 3, "record_schema": "MARC21-xml"}
    if operation == "metadata-file-get":
        return {"source_id": source_id, "dataset": "reference"}
    raise ValueError(operation)


def validate_registry() -> dict:
    for key, value in DUMMY_SECRETS.items():
        os.environ[key] = value
    matrix = load_json(MATRIX_PATH)
    catalog = load_json(CATALOG_PATH)
    provider = catalog["providers"][0]
    operations = {row["operation_id"]: row for row in provider["operations"]}
    sources = matrix["sources"]
    assert provider["provider_id"] == "global-knowledge-archives"
    assert provider["ticket_prefix"] == "[intel-knowledge]"
    assert len(sources) == matrix["active_source_count"] == provider["limits"]["source_count"] == 16
    assert len(operations) == 9
    assert matrix["governance"]["fixed_sources_only"] is True
    assert matrix["governance"]["arbitrary_urls_allowed"] is False
    assert matrix["governance"]["automatic_pagination_allowed"] is False
    assert matrix["governance"]["paywall_bypass_allowed"] is False
    assert matrix["governance"]["patient_level_data_allowed"] is False
    assert provider["limits"]["requests_per_ticket_max"] == 1
    assert provider["limits"]["write_operations_allowed"] is False
    assert provider["limits"]["unauthorized_full_text_copying_allowed"] is False
    keyed_sources = {row["source_id"] for row in sources if row["credential_mode"] == "required_free_key"}
    assert keyed_sources == {"google-books", "bhl"}
    assert provider["optional_secret_environment_variables"] == ["GOOGLE_API_KEY", "BHL_API_KEY"]
    assert not ({"trove", "nara", "smithsonian", "govinfo"} & {row["source_id"] for row in sources})

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
            assert not any(name.lower() in {"url", "host", "path", "headers", "api_key", "token"} for name in params)
            assert "Authorization" not in headers
            checked.append({
                "source_id": source_id,
                "operation": operation,
                "method": method,
                "origin": f"{parsed.scheme}://{parsed.netloc}",
                "credential_names": credential_names,
                "body_present": body is not None,
                "query_names": [name for name, _ in query],
            })
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
    "eric": ("knowledge-search", {"source_id": "eric", "query": "climate education", "limit": 20}),
    "ukri-gtr": ("knowledge-search", {"source_id": "ukri-gtr", "query": "energy resilience", "limit": 25}),
    "nih-reporter": ("knowledge-search", {"source_id": "nih-reporter", "query": "malaria vaccine", "limit": 2}),
    "clinicaltrials-gov": ("knowledge-search", {"source_id": "clinicaltrials-gov", "query": "malaria", "limit": 2}),
    "usgs-publications": ("knowledge-search", {"source_id": "usgs-publications", "query": "earthquake", "limit": 2}),
    "federal-register": ("knowledge-search", {"source_id": "federal-register", "query": "artificial intelligence", "limit": 2}),
    "met-museum": ("knowledge-search", {"source_id": "met-museum", "query": "sunflowers", "limit": 2}),
    "art-institute-chicago": ("knowledge-search", {"source_id": "art-institute-chicago", "query": "monet", "limit": 2}),
    "digitalnz": ("knowledge-search", {"source_id": "digitalnz", "query": "social welfare", "limit": 2}),
    "dnb-sru": ("sru-search", {"source_id": "dnb-sru", "query": "tit=climate", "limit": 2, "record_schema": "MARC21-xml"}),
    "hal-oai": ("oai-identify", {"source_id": "hal-oai"}),
    "doab-oai": ("oai-identify", {"source_id": "doab-oai"}),
    "rijksmuseum-oai": ("oai-identify", {"source_id": "rijksmuseum-oai"}),
    "nber-metadata": ("metadata-file-get", {"source_id": "nber-metadata", "dataset": "reference"}),
}

KEY_CASES = {
    "google-books": ("GOOGLE_API_KEY", "knowledge-search", {"source_id": "google-books", "query": "economic history", "limit": 2}),
    "bhl": ("BHL_API_KEY", "knowledge-search", {"source_id": "bhl", "query": "orchids", "limit": 2}),
}


def execute_case(source_id: str, operation: str, parameters: dict, output: Path) -> dict:
    ticket = {
        "task_id": f"knowledge-live-{source_id.replace('_', '-')}",
        "provider": "global-knowledge-archives",
        "operation": operation,
        "objective": f"Bounded live acceptance for {source_id}",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 60, "max_response_bytes": 15000000},
    }
    output.mkdir(parents=True, exist_ok=True)
    ticket_path = output / "ticket.json"
    ticket_path.write_text(json.dumps(ticket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.environ.pop("GLOBAL_KNOWLEDGE_FIXTURE_MODE", None)
    code = execute(ticket_path, output)
    diagnostics = json.loads((output / "diagnostics.json").read_text(encoding="utf-8"))
    if code != 0 or diagnostics["status"] != "INTEL_KNOWLEDGE_COMPLETED":
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
        "credential_names": diagnostics["metadata"]["credential_names"],
        "model_calls": diagnostics["model_calls"],
        "secret_values_exposed": diagnostics["secret_values_exposed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--live-source", choices=sorted(LIVE_CASES))
    parser.add_argument("--live-key-source", choices=sorted(KEY_CASES))
    args = parser.parse_args()
    output = Path(args.output)
    if args.live_source:
        operation, parameters = LIVE_CASES[args.live_source]
        receipt = execute_case(args.live_source, operation, parameters, output.parent / f"live-{args.live_source}")
    elif args.live_key_source:
        secret_name, operation, parameters = KEY_CASES[args.live_key_source]
        if not str(os.getenv(secret_name) or "").strip():
            receipt = {
                "status": "SKIP_NOT_CONFIGURED",
                "source_id": args.live_key_source,
                "required_secret": secret_name,
                "network_used": False,
                "request_count": 0,
                "model_calls": 0,
                "secret_values_exposed": False,
            }
        else:
            receipt = execute_case(args.live_key_source, operation, parameters, output.parent / f"live-{args.live_key_source}")
    else:
        receipt = validate_registry()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
