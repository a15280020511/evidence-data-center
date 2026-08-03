#!/usr/bin/env python3
"""Validate all fixed software/security builders and bounded live sources."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from open_software_security_task import CATALOG_PATH, MATRIX_PATH, build, execute, load_json

DUMMY_SECRETS = {
    "SWH_API_TOKEN": "fixture-swh-token",
    "NVD_API_KEY": "fixture-nvd-key",
}


def parameters_for(operation: str, source_id: str) -> dict:
    if operation == "software-object-get":
        return {
            "source_id": source_id,
            "object_type": "directory",
            "object_id": "3ee1366c6dd0b7f4ba9536e9bcc300236ac8f200",
            "hash_algorithm": "sha1",
        }
    if operation == "package-search":
        return {"source_id": source_id, "query": "requests", "limit": 3}
    if operation == "package-get":
        names = {
            "deps-dev": "react",
            "pypi": "requests",
            "npm": "react",
            "crates-io": "serde",
            "rubygems": "rails",
            "packagist": "symfony/console",
            "pub-dev": "http",
        }
        row = {"source_id": source_id, "package": names[source_id]}
        if source_id == "deps-dev":
            row["system"] = "NPM"
        return row
    if operation == "package-version-get":
        values = {
            "deps-dev": ("react", "18.2.0", "NPM"),
            "pypi": ("requests", "2.32.3", None),
            "npm": ("react", "18.2.0", None),
            "crates-io": ("serde", "1.0.203", None),
        }
        package, version, system = values[source_id]
        row = {"source_id": source_id, "package": package, "version": version}
        if system:
            row["system"] = system
        return row
    if operation == "dependency-graph-get":
        return {"source_id": source_id, "package": "react", "version": "18.2.0", "system": "NPM"}
    if operation == "license-definition-get":
        return {
            "source_id": source_id,
            "component_type": "npm",
            "provider": "npmjs",
            "namespace": "-",
            "package": "lodash",
            "version": "4.17.21",
        }
    if operation == "vulnerability-record-get":
        record = "GHSA-c3g4-w6cv-6v7h" if source_id == "osv" else "CVE-2021-44228"
        return {"source_id": source_id, "vulnerability_id": record}
    if operation == "package-vulnerability-query":
        return {"source_id": source_id, "ecosystem": "PyPI", "package": "jinja2", "version": "2.4.1"}
    if operation == "security-standard-record-get":
        if source_id == "cisa-kev":
            return {"source_id": source_id}
        if source_id == "openssf-scorecard":
            return {"source_id": source_id, "platform": "github.com", "owner": "kubernetes", "repository": "kubernetes"}
        if source_id == "spdx-license-list":
            return {"source_id": source_id, "record_id": "MIT"}
        if source_id == "rfc-editor":
            return {"source_id": source_id, "record_id": "9000"}
        if source_id == "iana-registries":
            return {"source_id": source_id, "registry": "protocol-numbers"}
    raise ValueError((operation, source_id))


def validate_registry() -> dict:
    for key, value in DUMMY_SECRETS.items():
        os.environ[key] = value
    matrix = load_json(MATRIX_PATH)
    catalog = load_json(CATALOG_PATH)
    provider = catalog["providers"][0]
    operations = {row["operation_id"]: row for row in provider["operations"]}
    sources = matrix["sources"]
    assert provider["provider_id"] == "open-software-security-knowledge"
    assert provider["ticket_prefix"] == "[intel-software-security]"
    assert len(sources) == matrix["active_source_count"] == provider["limits"]["source_count"] == 18
    assert len(operations) == 11
    assert matrix["governance"]["fixed_sources_only"] is True
    assert matrix["governance"]["arbitrary_urls_allowed"] is False
    assert matrix["governance"]["automatic_pagination_allowed"] is False
    assert matrix["governance"]["package_download_allowed"] is False
    assert matrix["governance"]["source_code_execution_allowed"] is False
    assert matrix["governance"]["exploit_code_retrieval_allowed"] is False
    assert provider["limits"]["requests_per_ticket_max"] == 1
    assert provider["limits"]["write_operations_allowed"] is False

    rows = []
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
            assert "Authorization" not in headers or credential_names == ["SWH_API_TOKEN"]
            assert "apiKey" not in headers or credential_names == ["NVD_API_KEY"]
            rows.append({
                "source_id": source_id,
                "operation": operation,
                "method": method,
                "origin": f"{parsed.scheme}://{parsed.netloc}",
                "query_names": [name for name, _ in query],
                "body_present": body is not None,
                "credential_names": credential_names,
            })
    return {
        "status": "PASS",
        "source_count": len(sources),
        "operation_count": len(operations),
        "builder_cases": len(rows),
        "rows": rows,
        "network_used": False,
        "model_calls": 0,
        "secret_values_exposed": False,
    }


LIVE_CASES = {
    "software-heritage": ("software-object-get", parameters_for("software-object-get", "software-heritage")),
    "deps-dev": ("package-get", parameters_for("package-get", "deps-dev")),
    "clearlydefined": ("package-search", parameters_for("package-search", "clearlydefined")),
    "pypi": ("package-get", parameters_for("package-get", "pypi")),
    "npm": ("package-get", parameters_for("package-get", "npm")),
    "crates-io": ("package-get", parameters_for("package-get", "crates-io")),
    "rubygems": ("package-get", parameters_for("package-get", "rubygems")),
    "packagist": ("package-get", parameters_for("package-get", "packagist")),
    "pub-dev": ("package-get", parameters_for("package-get", "pub-dev")),
    "osv": ("vulnerability-record-get", parameters_for("vulnerability-record-get", "osv")),
    "nvd": ("vulnerability-record-get", parameters_for("vulnerability-record-get", "nvd")),
    "cisa-kev": ("security-standard-record-get", parameters_for("security-standard-record-get", "cisa-kev")),
    "first-epss": ("vulnerability-record-get", parameters_for("vulnerability-record-get", "first-epss")),
    "openssf-scorecard": ("security-standard-record-get", parameters_for("security-standard-record-get", "openssf-scorecard")),
    "mitre-cve": ("vulnerability-record-get", parameters_for("vulnerability-record-get", "mitre-cve")),
    "spdx-license-list": ("security-standard-record-get", parameters_for("security-standard-record-get", "spdx-license-list")),
    "rfc-editor": ("security-standard-record-get", parameters_for("security-standard-record-get", "rfc-editor")),
    "iana-registries": ("security-standard-record-get", parameters_for("security-standard-record-get", "iana-registries")),
}


def execute_live(source_id: str, output_root: Path) -> dict:
    operation, parameters = LIVE_CASES[source_id]
    ticket = {
        "task_id": f"software-security-live-{source_id}",
        "provider": "open-software-security-knowledge",
        "operation": operation,
        "objective": f"Bounded live acceptance for {source_id}",
        "parameters": parameters,
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {"timeout_seconds": 60, "max_response_bytes": 10000000},
    }
    output = output_root / f"live-{source_id}"
    output.mkdir(parents=True, exist_ok=True)
    ticket_path = output / "ticket.json"
    ticket_path.write_text(json.dumps(ticket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.environ.pop("OPEN_SOFTWARE_SECURITY_FIXTURE_MODE", None)
    code = execute(ticket_path, output)
    diagnostics = json.loads((output / "diagnostics.json").read_text(encoding="utf-8"))
    if code != 0 or diagnostics["status"] != "INTEL_SOFTWARE_SECURITY_COMPLETED":
        raise RuntimeError(json.dumps(diagnostics, ensure_ascii=False))
    metadata = diagnostics["metadata"]
    return {
        "status": "PASS",
        "source_id": source_id,
        "operation": operation,
        "http_status": metadata["http_status"],
        "response_bytes": metadata["response_bytes"],
        "response_sha256": metadata["response_sha256"],
        "network_used": metadata["network_used"],
        "request_count": metadata["request_count"],
        "credential_names": metadata["credential_names"],
        "package_downloaded": metadata["package_downloaded"],
        "package_installed": metadata["package_installed"],
        "source_code_executed": metadata["source_code_executed"],
        "exploit_code_retrieved": metadata["exploit_code_retrieved"],
        "model_calls": diagnostics["model_calls"],
        "secret_values_exposed": diagnostics["secret_values_exposed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--live-source", choices=sorted(LIVE_CASES))
    args = parser.parse_args()
    output = Path(args.output)
    receipt = execute_live(args.live_source, output.parent) if args.live_source else validate_registry()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
