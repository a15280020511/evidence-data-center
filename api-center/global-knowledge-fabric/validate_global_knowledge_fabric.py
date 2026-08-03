#!/usr/bin/env python3
"""Validate the third-wave global knowledge fabric and bounded live access."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from global_knowledge_fabric_task import CATALOG_PATH, MATRIX_PATH, build, execute, load_json

DUMMY_SECRETS = {
    "ROR_CLIENT_ID": "fixture-ror-client",
    "ORCID_PUBLIC_API_TOKEN": "fixture-orcid-token",
    "REGULATIONS_GOV_API_KEY": "fixture-regulations-key",
    "DATA_GOV_API_KEY": "fixture-data-gov-key",
}

SEARCH_PARAMS = {
    "entity-search": {"query": "Oxford", "limit": 2},
    "scholarly-search": {"query": "10.1038/s41586-020-2649-2", "limit": 2},
    "dataset-search": {"query": "climate", "limit": 2},
    "government-search": {"query": "climate", "limit": 2},
    "science-search": {"query": "kinase", "limit": 2},
    "standards-search": {"query": "http", "limit": 2},
}
RECORD_IDS = {
    "ror": "03yrm5c26",
    "orcid": "0000-0002-1825-0097",
    "harvard-dataverse": "1",
    "openml": "61",
    "grants-gov": "289999",
    "regulations-gov": "FDA-2009-N-0501-0012",
    "data-gov": "6f011de5-22bf-4c88-a4aa-e61fc29a4a67",
    "rcsb-pdb": "4HHB",
    "uniprot": "P69905",
    "chembl": "CHEMBL25",
}


def parameters_for(operation: str, source_id: str) -> dict:
    if operation == "record-get":
        return {"source_id": source_id, "record_id": RECORD_IDS[source_id]}
    row = dict(SEARCH_PARAMS[operation])
    row["source_id"] = source_id
    if operation == "scholarly-search":
        row["query"] = "graph neural networks"
    return row


def validate_registry() -> dict:
    for key, value in DUMMY_SECRETS.items():
        os.environ[key] = value
    matrix = load_json(MATRIX_PATH)
    catalog = load_json(CATALOG_PATH)
    provider = catalog["providers"][0]
    operations = {row["operation_id"]: row for row in provider["operations"]}
    sources = matrix["sources"]
    assert provider["provider_id"] == "global-knowledge-fabric"
    assert provider["ticket_prefix"] == "[intel-knowledge-fabric]"
    assert len(sources) == matrix["active_source_count"] == provider["limits"]["source_count"] == 15
    assert len(operations) == 9
    assert provider["limits"]["requests_per_ticket_max"] == 1
    assert provider["limits"]["max_response_bytes"] == 5000000
    assert provider["limits"]["arbitrary_urls_allowed"] is False
    assert provider["limits"]["arbitrary_sparql_allowed"] is False
    assert provider["limits"]["write_operations_allowed"] is False
    assert provider["limits"]["personal_profiling_allowed"] is False

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
            assert not any(name.lower() in {"url", "host", "path", "headers", "api_key", "token", "sparql"} for name in params)
            if "Authorization" in headers:
                assert source_id == "orcid"
            checked.append({
                "source_id": source_id, "operation": operation, "method": method,
                "origin": f"{parsed.scheme}://{parsed.netloc}",
                "credential_names": credential_names, "body_present": body is not None,
                "query_names": [name for name, _ in query],
            })
    return {
        "status": "PASS", "source_count": len(sources), "operation_count": len(operations),
        "builder_cases": len(checked), "rows": checked, "network_used": False,
        "model_calls": 0, "secret_values_exposed": False,
    }


LIVE_CASES = {
    "ror": ("entity-search", {"source_id": "ror", "query": "University of Oxford", "limit": 2}),
    "dblp-publication": ("scholarly-search", {"source_id": "dblp-publication", "query": "graph neural networks", "limit": 2}),
    "dblp-author": ("entity-search", {"source_id": "dblp-author", "query": "Barbara Liskov", "limit": 2}),
    "dblp-venue": ("scholarly-search", {"source_id": "dblp-venue", "query": "SIGIR", "limit": 2}),
    "harvard-dataverse": ("dataset-search", {"source_id": "harvard-dataverse", "query": "climate", "limit": 2}),
    "openml": ("dataset-search", {"source_id": "openml", "query": "iris", "limit": 2}),
    "grants-gov": ("government-search", {"source_id": "grants-gov", "query": "health", "limit": 2}),
    "data-gov": ("government-search", {"source_id": "data-gov", "query": "climate", "limit": 2}),
    "eu-cellar": ("government-search", {"source_id": "eu-cellar", "query": "climate", "limit": 2}),
    "rcsb-pdb": ("science-search", {"source_id": "rcsb-pdb", "query": "thymidine kinase", "limit": 2}),
    "uniprot": ("science-search", {"source_id": "uniprot", "query": "kinase", "limit": 2}),
    "chembl": ("science-search", {"source_id": "chembl", "query": "aspirin", "limit": 2}),
    "ietf-datatracker": ("standards-search", {"source_id": "ietf-datatracker", "query": "http", "limit": 2}),
}
KEY_CASES = {
    "data-gov": ("DATA_GOV_API_KEY", "government-search", {"source_id": "data-gov", "query": "climate", "limit": 2}),
    "orcid": ("ORCID_PUBLIC_API_TOKEN", "entity-search", {"source_id": "orcid", "query": "family-name:Smith", "limit": 2}),
    "regulations-gov": ("REGULATIONS_GOV_API_KEY", "government-search", {"source_id": "regulations-gov", "query": "artificial intelligence", "limit": 2}),
}


def execute_case(source_id: str, operation: str, parameters: dict, output: Path) -> dict:
    ticket = {
        "task_id": f"fabric-live-{source_id.replace('_', '-')}",
        "provider": "global-knowledge-fabric",
        "operation": operation,
        "objective": f"Bounded live acceptance for {source_id}",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 45, "max_response_bytes": 5000000},
    }
    output.mkdir(parents=True, exist_ok=True)
    ticket_path = output / "ticket.json"
    ticket_path.write_text(json.dumps(ticket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.environ.pop("GLOBAL_KNOWLEDGE_FABRIC_FIXTURE_MODE", None)
    code = execute(ticket_path, output)
    diagnostics = json.loads((output / "diagnostics.json").read_text(encoding="utf-8"))
    if code != 0 or diagnostics["status"] != "INTEL_KNOWLEDGE_FABRIC_COMPLETED":
        raise RuntimeError(json.dumps(diagnostics, ensure_ascii=False))
    return {
        "status": "PASS", "source_id": source_id, "operation": operation,
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
                "status": "SKIP_NOT_CONFIGURED", "source_id": args.live_key_source,
                "required_secret": secret_name, "network_used": False, "request_count": 0,
                "model_calls": 0, "secret_values_exposed": False,
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
