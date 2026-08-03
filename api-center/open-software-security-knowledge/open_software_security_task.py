#!/usr/bin/env python3
"""Bounded read-only runtime for open software, security and standards metadata."""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlsplit

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    bytes_sha,
    finish_execution,
    load_json,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
MATRIX_PATH = HERE / "source-access-matrix.json"
USER_AGENT = "evidence-data-center-open-software-security/1.0"

PACKAGE_SYSTEMS = {"GO", "RUBYGEMS", "NPM", "CARGO", "MAVEN", "PYPI", "NUGET"}
DEPENDENCY_SYSTEMS = {"NPM", "CARGO", "MAVEN", "PYPI"}
OSV_ECOSYSTEMS = {"PyPI", "npm", "Go", "Maven", "NuGet", "RubyGems", "crates.io", "Packagist", "Pub"}
IANA_REGISTRIES = {
    "protocol-numbers",
    "service-names-port-numbers",
    "media-types",
    "tls-parameters",
    "http-fields",
    "well-known-uris",
}


def safe_text(value: Any, name: str, maximum: int, pattern: str | None = None) -> str:
    rendered = str(value or "").strip()
    if not rendered or len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    if pattern is not None and re.fullmatch(pattern, rendered) is None:
        raise ValueError(f"{name} is invalid")
    return rendered


def optional_text(value: Any, name: str, maximum: int, pattern: str) -> str:
    rendered = str(value or "").strip()
    if len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    if rendered and re.fullmatch(pattern, rendered) is None:
        raise ValueError(f"{name} is invalid")
    return rendered


def backend_credential(name: str) -> str:
    value = str(os.getenv(name) or "").strip()
    if len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise RuntimeError(f"invalid backend credential: {name}")
    return value


def source_map() -> dict[str, Mapping[str, Any]]:
    rows = load_json(MATRIX_PATH).get("sources")
    if not isinstance(rows, list):
        raise RuntimeError("source matrix is invalid")
    return {str(row["source_id"]): row for row in rows if isinstance(row, Mapping)}


def source_for(source_id: Any, operation: str) -> Mapping[str, Any]:
    source_id = safe_text(source_id, "source_id", 80, r"^[a-z0-9-]+$")
    row = source_map().get(source_id)
    if row is None:
        raise ValueError("source_id is not enabled")
    if operation not in (row.get("operations") or []):
        raise ValueError(f"{source_id} does not support {operation}")
    parsed = urlsplit(str(row.get("base_url") or ""))
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("source registry contains a non-HTTPS endpoint")
    return row


def credentials_for(row: Mapping[str, Any]) -> tuple[dict[str, str], list[str]]:
    source_id = str(row["source_id"])
    headers: dict[str, str] = {}
    used: list[str] = []
    if source_id == "software-heritage":
        token = backend_credential("SWH_API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
            used.append("SWH_API_TOKEN")
    elif source_id == "nvd":
        key = backend_credential("NVD_API_KEY")
        if key:
            headers["apiKey"] = key
            used.append("NVD_API_KEY")
    return headers, used


def common_headers(accept: str = "application/json, application/xml;q=0.8, text/xml;q=0.8") -> dict[str, str]:
    return {"Accept": accept, "User-Agent": USER_AGENT}


def package_name(value: Any) -> str:
    return safe_text(value, "package", 220, r"^[A-Za-z0-9@._/+:-]+$")


def package_version(value: Any) -> str:
    return safe_text(value, "version", 120, r"^[A-Za-z0-9._+:-]+$")


def package_system(value: Any, *, dependency: bool = False) -> str:
    system = safe_text(value, "system", 20, r"^[A-Z]+$")
    allowed = DEPENDENCY_SYSTEMS if dependency else PACKAGE_SYSTEMS
    if system not in allowed:
        raise ValueError("system is not allowlisted")
    return system


def build_software_object(row: Mapping[str, Any], p: Mapping[str, Any]):
    object_type = safe_text(p.get("object_type"), "object_type", 20, r"^[a-z]+$")
    if object_type not in {"content", "directory", "revision", "release", "snapshot"}:
        raise ValueError("object_type is not allowlisted")
    object_id = safe_text(p.get("object_id"), "object_id", 64, r"^[A-Fa-f0-9]{40,64}$").lower()
    algorithm = str(p.get("hash_algorithm") or "sha1")
    if algorithm not in {"sha1", "sha1_git", "sha256", "blake2s256"}:
        raise ValueError("hash_algorithm is not allowlisted")
    if object_type == "content":
        expected = 64 if algorithm in {"sha256", "blake2s256"} else 40
        if len(object_id) != expected:
            raise ValueError("content hash length does not match hash_algorithm")
        url = f"https://archive.softwareheritage.org/api/1/content/{algorithm}:{object_id}/"
    else:
        if len(object_id) != 40:
            raise ValueError("Software Heritage object identifiers must be 40 hex characters")
        url = f"https://archive.softwareheritage.org/api/1/{object_type}/{object_id}/"
    headers, credentials = credentials_for(row)
    headers.update(common_headers("application/json"))
    return "GET", url, headers, [], None, credentials


def build_package_search(row: Mapping[str, Any], p: Mapping[str, Any]):
    source_id = str(row["source_id"])
    term = safe_text(p.get("query"), "query", 300)
    limit = bounded_int(p.get("limit"), default=20, minimum=1, maximum=50, name="limit")
    headers = common_headers("application/json")
    if source_id == "clearlydefined":
        return "GET", "https://api.clearlydefined.io/definitions", headers, [("pattern", term)], None, []
    if source_id == "npm":
        return "GET", "https://registry.npmjs.org/-/v1/search", headers, [("text", term), ("size", str(limit)), ("from", "0")], None, []
    if source_id == "crates-io":
        return "GET", "https://crates.io/api/v1/crates", headers, [("q", term), ("per_page", str(limit)), ("page", "1")], None, []
    if source_id == "rubygems":
        return "GET", "https://rubygems.org/api/v1/search.json", headers, [("query", term)], None, []
    if source_id == "packagist":
        return "GET", "https://packagist.org/search.json", headers, [("q", term), ("per_page", str(limit))], None, []
    if source_id == "pub-dev":
        return "GET", "https://pub.dev/api/search", headers, [("q", term), ("page", "1")], None, []
    raise ValueError("unsupported package-search source")


def build_package_get(row: Mapping[str, Any], p: Mapping[str, Any]):
    source_id = str(row["source_id"])
    name = package_name(p.get("package"))
    encoded = quote(name, safe="")
    headers = common_headers("application/json")
    if source_id == "deps-dev":
        system = package_system(p.get("system"))
        return "GET", f"https://api.deps.dev/v3/systems/{system}/packages/{encoded}", headers, [], None, []
    if source_id == "pypi":
        return "GET", f"https://pypi.org/pypi/{encoded}/json", headers, [], None, []
    if source_id == "npm":
        return "GET", f"https://registry.npmjs.org/{encoded}", headers, [], None, []
    if source_id == "crates-io":
        return "GET", f"https://crates.io/api/v1/crates/{encoded}", headers, [], None, []
    if source_id == "rubygems":
        return "GET", f"https://rubygems.org/api/v1/gems/{encoded}.json", headers, [], None, []
    if source_id == "packagist":
        if name.count("/") != 1:
            raise ValueError("Packagist package must be vendor/name")
        vendor, package = name.split("/", 1)
        return "GET", f"https://repo.packagist.org/p2/{quote(vendor, safe='')}/{quote(package, safe='')}.json", headers, [], None, []
    if source_id == "pub-dev":
        return "GET", f"https://pub.dev/api/packages/{encoded}", headers, [], None, []
    raise ValueError("unsupported package-get source")


def build_package_version(row: Mapping[str, Any], p: Mapping[str, Any]):
    source_id = str(row["source_id"])
    name = package_name(p.get("package"))
    version = package_version(p.get("version"))
    encoded_name = quote(name, safe="")
    encoded_version = quote(version, safe="")
    headers = common_headers("application/json")
    if source_id == "deps-dev":
        system = package_system(p.get("system"))
        url = f"https://api.deps.dev/v3/systems/{system}/packages/{encoded_name}/versions/{encoded_version}"
    elif source_id == "pypi":
        url = f"https://pypi.org/pypi/{encoded_name}/{encoded_version}/json"
    elif source_id == "npm":
        url = f"https://registry.npmjs.org/{encoded_name}/{encoded_version}"
    elif source_id == "crates-io":
        url = f"https://crates.io/api/v1/crates/{encoded_name}/{encoded_version}"
    else:
        raise ValueError("unsupported package-version source")
    return "GET", url, headers, [], None, []


def build_dependency_graph(row: Mapping[str, Any], p: Mapping[str, Any]):
    system = package_system(p.get("system"), dependency=True)
    name = quote(package_name(p.get("package")), safe="")
    version = quote(package_version(p.get("version")), safe="")
    url = f"https://api.deps.dev/v3/systems/{system}/packages/{name}/versions/{version}:dependencies"
    return "GET", url, common_headers("application/json"), [], None, []


def build_license_definition(row: Mapping[str, Any], p: Mapping[str, Any]):
    component_type = safe_text(p.get("component_type"), "component_type", 20, r"^[a-z]+$")
    provider = safe_text(p.get("provider"), "provider", 30, r"^[a-z]+$")
    allowed = {
        "npm": "npmjs", "pypi": "pypi", "maven": "mavencentral", "nuget": "nuget",
        "gem": "rubygems", "crate": "cratesio", "go": "golang", "composer": "packagist",
    }
    if allowed.get(component_type) != provider:
        raise ValueError("component_type/provider combination is not allowlisted")
    namespace = optional_text(p.get("namespace"), "namespace", 160, r"^[A-Za-z0-9@._/+:-]*$") or "-"
    name = package_name(p.get("package"))
    version = package_version(p.get("version"))
    parts = [component_type, provider, namespace, name, version]
    encoded = "/".join(quote(part, safe="") for part in parts)
    return "GET", f"https://api.clearlydefined.io/definitions/{encoded}", common_headers("application/json"), [], None, []


def cve_id(value: Any) -> str:
    return safe_text(value, "vulnerability_id", 30, r"^CVE-[0-9]{4}-[0-9]{4,7}$").upper()


def build_vulnerability_record(row: Mapping[str, Any], p: Mapping[str, Any]):
    source_id = str(row["source_id"])
    raw = safe_text(p.get("vulnerability_id"), "vulnerability_id", 100, r"^[A-Za-z0-9._:-]+$")
    headers, credentials = credentials_for(row)
    headers.update(common_headers("application/json"))
    query: list[tuple[str, str]] = []
    if source_id == "osv":
        url = f"https://api.osv.dev/v1/vulns/{quote(raw, safe='._:-')}"
    elif source_id == "nvd":
        value = cve_id(raw)
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        query.append(("cveId", value))
    elif source_id == "mitre-cve":
        value = cve_id(raw)
        url = f"https://cveawg.mitre.org/api/cve/{value}"
    elif source_id == "first-epss":
        value = cve_id(raw)
        url = "https://api.first.org/data/v1/epss"
        query.append(("cve", value))
    else:
        raise ValueError("unsupported vulnerability source")
    return "GET", url, headers, query, None, credentials


def build_package_vulnerability(row: Mapping[str, Any], p: Mapping[str, Any]):
    ecosystem = safe_text(p.get("ecosystem"), "ecosystem", 30)
    if ecosystem not in OSV_ECOSYSTEMS:
        raise ValueError("ecosystem is not allowlisted")
    body = {
        "version": package_version(p.get("version")),
        "package": {"name": package_name(p.get("package")), "ecosystem": ecosystem},
    }
    return "POST", "https://api.osv.dev/v1/query", common_headers("application/json"), [], body, []


def build_security_standard(row: Mapping[str, Any], p: Mapping[str, Any]):
    source_id = str(row["source_id"])
    headers = common_headers()
    if source_id == "cisa-kev":
        return "GET", "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", common_headers("application/json"), [], None, []
    if source_id == "openssf-scorecard":
        platform = safe_text(p.get("platform"), "platform", 20)
        if platform not in {"github.com", "gitlab.com"}:
            raise ValueError("platform is not allowlisted")
        owner = safe_text(p.get("owner"), "owner", 100, r"^[A-Za-z0-9._-]+$")
        repository = safe_text(p.get("repository"), "repository", 100, r"^[A-Za-z0-9._-]+$")
        url = f"https://api.securityscorecards.dev/projects/{platform}/{quote(owner, safe='')}/{quote(repository, safe='')}"
        return "GET", url, common_headers("application/json"), [], None, []
    if source_id == "spdx-license-list":
        license_id = safe_text(p.get("record_id"), "record_id", 100, r"^[A-Za-z0-9.-]+$")
        return "GET", f"https://spdx.org/licenses/{quote(license_id, safe='.-')}.json", common_headers("application/json"), [], None, []
    if source_id == "rfc-editor":
        number = safe_text(p.get("record_id"), "record_id", 5, r"^[0-9]{1,5}$")
        if int(number) < 1:
            raise ValueError("RFC number is invalid")
        return "GET", f"https://www.rfc-editor.org/rfc/rfc{int(number)}.json", common_headers("application/json"), [], None, []
    if source_id == "iana-registries":
        registry = safe_text(p.get("registry"), "registry", 80, r"^[a-z0-9-]+$")
        if registry not in IANA_REGISTRIES:
            raise ValueError("registry is not allowlisted")
        url = f"https://www.iana.org/assignments/{registry}/{registry}.xml"
        return "GET", url, common_headers("application/xml, text/xml;q=0.9"), [], None, []
    raise ValueError("unsupported security-standard source")


def build(operation: str, parameters: Mapping[str, Any]):
    row = source_for(parameters.get("source_id"), operation)
    if operation == "software-object-get":
        request = build_software_object(row, parameters)
    elif operation == "package-search":
        request = build_package_search(row, parameters)
    elif operation == "package-get":
        request = build_package_get(row, parameters)
    elif operation == "package-version-get":
        request = build_package_version(row, parameters)
    elif operation == "dependency-graph-get":
        request = build_dependency_graph(row, parameters)
    elif operation == "license-definition-get":
        request = build_license_definition(row, parameters)
    elif operation == "vulnerability-record-get":
        request = build_vulnerability_record(row, parameters)
    elif operation == "package-vulnerability-query":
        request = build_package_vulnerability(row, parameters)
    elif operation == "security-standard-record-get":
        request = build_security_standard(row, parameters)
    else:
        raise ValueError(f"unsupported operation: {operation}")
    return row, request


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    started_at = utc_now()
    started_perf = time.perf_counter()
    fixture = os.getenv("OPEN_SOFTWARE_SECURITY_FIXTURE_MODE") == "1"
    snapshot = None
    failure = None
    status = "INTEL_SOFTWARE_SECURITY_FAILED"
    metadata: dict[str, Any] = {
        "fixture_mode": fixture,
        "network_used": False,
        "upstream_called": False,
        "request_count": 0,
        "credential_names": [],
        "automatic_pagination_used": False,
        "automatic_retry_used": False,
        "redirect_followed": False,
        "package_downloaded": False,
        "package_installed": False,
        "source_code_executed": False,
        "exploit_code_retrieved": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        if operation == "catalog-capabilities":
            snapshot = provider_row(CATALOG_PATH)
        elif operation == "source-access-matrix":
            snapshot = load_json(MATRIX_PATH)
        else:
            row, request = build(operation, ticket.get("parameters") or {})
            method, url, headers, query, body, credentials = request
            parsed = urlsplit(url)
            if fixture:
                snapshot = {
                    "fixture": True,
                    "operation": operation,
                    "source_id": row["source_id"],
                    "method": method,
                    "origin": f"{parsed.scheme}://{parsed.netloc}",
                    "path_template_verified": True,
                    "query_names": [name for name, _ in query],
                    "body_present": body is not None,
                    "credential_names": credentials,
                }
            else:
                acceptance = ticket.get("acceptance") or {}
                timeout = bounded_int(acceptance.get("timeout_seconds"), default=60, minimum=5, maximum=90, name="timeout_seconds")
                max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5000000, minimum=1024, maximum=15000000, name="max_response_bytes")
                response = requests.request(method, url, headers=headers, params=query, json=body, timeout=timeout, allow_redirects=False)
                raw = response.content
                metadata.update({
                    "network_used": True,
                    "upstream_called": True,
                    "request_count": 1,
                    "source_id": row["source_id"],
                    "source_name": row["name"],
                    "source_category": row["category"],
                    "credential_names": credentials,
                    "http_status": response.status_code,
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "request_origin": f"{parsed.scheme}://{parsed.netloc}",
                    "license_policy": row["license_policy"],
                    "cost": row["cost"],
                })
                if 300 <= response.status_code < 400:
                    raise RuntimeError("redirects are forbidden")
                response.raise_for_status()
                if len(raw) > max_bytes:
                    raise RuntimeError("response exceeds max_response_bytes")
                content_type = response.headers.get("content-type", "").lower()
                if "json" in content_type:
                    data: Any = response.json()
                else:
                    data = {"content_type": content_type, "text": response.text}
                snapshot = {
                    "provider": "open-software-security-knowledge",
                    "operation": operation,
                    "source_id": row["source_id"],
                    "source_name": row["name"],
                    "license_policy": row["license_policy"],
                    "data": data,
                }
        status = "INTEL_SOFTWARE_SECURITY_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:1500]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="intel-software-security",
    )


def main() -> int:
    return run_cli(
        execute=execute,
        ticket_prefix="[intel-software-security]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="intel-software-security-ticket-status-v1",
        display_name="全球开源软件、安全与开放标准知识层",
    )


if __name__ == "__main__":
    raise SystemExit(main())
