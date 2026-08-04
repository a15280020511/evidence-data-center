#!/usr/bin/env python3
"""Bounded, fixed-host strategic intelligence open-data provider."""
from __future__ import annotations

import ipaddress
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

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
SOURCE_MATRIX_PATH = HERE / "source-access-matrix.json"

AS_RE = re.compile(r"^(?:AS)?[0-9]{1,10}$", re.IGNORECASE)
TIMESTAMP_RE = re.compile(r"^(?:[0-9]{10}|[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.+-]{5,30})$")
NAME_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,120}$")
INCIDENT_RE = re.compile(r"^[A-Za-z0-9 .,&()'/-]{2,80}$")
PEERING_OBJECTS = {"net", "ix", "fac", "org"}
OPENFEMA_DECLARATIONS_V2 = (
    "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
)


def required_text(parameters: Mapping[str, Any], name: str, maximum: int) -> str:
    value = str(parameters.get(name) or "").strip()
    if not value or len(value) > maximum or any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{name} is invalid")
    return value


def validated_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise ValueError("resource must be an IP address") from exc


def validated_ip_or_prefix(value: str) -> str:
    try:
        if "/" in value:
            return str(ipaddress.ip_network(value, strict=False))
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise ValueError("resource must be an IP address or prefix") from exc


def build_request(
    operation: str, parameters: Mapping[str, Any]
) -> tuple[str | None, list[tuple[str, str]], str]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, [], "catalog"
    if operation == "source-access-matrix":
        if parameters:
            raise ValueError("source-access-matrix accepts no parameters")
        return None, [], "source-matrix"
    if operation == "openfema-disaster-declarations":
        top = bounded_int(
            parameters.get("top"), default=100, minimum=1, maximum=1000, name="top"
        )
        skip = bounded_int(
            parameters.get("skip"), default=0, minimum=0, maximum=100000, name="skip"
        )
        query: list[tuple[str, str]] = [
            ("$top", str(top)),
            ("$skip", str(skip)),
            ("$orderby", "declarationDate desc"),
        ]
        terms: list[str] = []
        state = str(parameters.get("state") or "").strip().upper()
        if state:
            if not re.fullmatch(r"[A-Z]{2}", state):
                raise ValueError("state must be a two-letter code")
            terms.append(f"state eq '{state}'")
        incident = str(parameters.get("incident_type") or "").strip()
        if incident:
            if not INCIDENT_RE.fullmatch(incident):
                raise ValueError("incident_type is invalid")
            escaped = incident.replace("'", "''")
            terms.append(f"incidentType eq '{escaped}'")
        year_from = parameters.get("year_from")
        year_to = parameters.get("year_to")
        if year_from is not None:
            year_from = bounded_int(
                year_from,
                default=1953,
                minimum=1953,
                maximum=2100,
                name="year_from",
            )
            terms.append(f"fyDeclared ge {year_from}")
        if year_to is not None:
            year_to = bounded_int(
                year_to,
                default=2100,
                minimum=1953,
                maximum=2100,
                name="year_to",
            )
            terms.append(f"fyDeclared le {year_to}")
        if year_from is not None and year_to is not None and year_from > year_to:
            raise ValueError("year_from must not exceed year_to")
        if terms:
            query.append(("$filter", " and ".join(terms)))
        return OPENFEMA_DECLARATIONS_V2, query, "openfema"
    if operation == "ripestat-network-info":
        resource = validated_ip(required_text(parameters, "resource", 128))
        return (
            "https://stat.ripe.net/data/network-info/data.json",
            [("resource", resource)],
            "ripestat",
        )
    if operation == "ripestat-prefix-overview":
        resource = validated_ip_or_prefix(required_text(parameters, "resource", 128))
        return (
            "https://stat.ripe.net/data/prefix-overview/data.json",
            [("resource", resource)],
            "ripestat",
        )
    if operation == "ripestat-as-overview":
        resource = required_text(parameters, "resource", 16).upper()
        if not AS_RE.fullmatch(resource):
            raise ValueError("resource must be an ASN")
        if not resource.startswith("AS"):
            resource = "AS" + resource
        return (
            "https://stat.ripe.net/data/as-overview/data.json",
            [("resource", resource)],
            "ripestat",
        )
    if operation == "ripestat-bgp-state":
        raw_resource = required_text(parameters, "resource", 256)
        resource = (
            raw_resource.upper()
            if AS_RE.fullmatch(raw_resource)
            else validated_ip_or_prefix(raw_resource)
        )
        if AS_RE.fullmatch(resource) and not resource.startswith("AS"):
            resource = "AS" + resource
        query = [("resource", resource)]
        timestamp = str(parameters.get("timestamp") or "").strip()
        if timestamp:
            if not TIMESTAMP_RE.fullmatch(timestamp):
                raise ValueError("timestamp must be ISO8601 or a Unix timestamp")
            query.append(("timestamp", timestamp))
        return "https://stat.ripe.net/data/bgp-state/data.json", query, "ripestat"
    if operation == "peeringdb-search":
        object_type = required_text(parameters, "object_type", 8).lower()
        if object_type not in PEERING_OBJECTS:
            raise ValueError("object_type is not allowlisted")
        name = required_text(parameters, "name", 120)
        if not NAME_RE.fullmatch(name):
            raise ValueError("name is invalid")
        limit = bounded_int(
            parameters.get("limit"), default=25, minimum=1, maximum=100, name="limit"
        )
        query = [("name__contains", name), ("limit", str(limit))]
        country = str(parameters.get("country") or "").strip().upper()
        if country:
            if not re.fullmatch(r"[A-Z]{2}", country):
                raise ValueError("country must be a two-letter code")
            query.append(("country", country))
        return f"https://www.peeringdb.com/api/{object_type}", query, "peeringdb"
    if operation == "peeringdb-object":
        object_type = required_text(parameters, "object_type", 8).lower()
        if object_type not in PEERING_OBJECTS:
            raise ValueError("object_type is not allowlisted")
        object_id = bounded_int(
            parameters.get("object_id"),
            default=0,
            minimum=1,
            maximum=2147483647,
            name="object_id",
        )
        return f"https://www.peeringdb.com/api/{object_type}/{object_id}", [], "peeringdb"
    if operation == "mitre-attack-index":
        if parameters:
            raise ValueError("mitre-attack-index accepts no parameters")
        return (
            "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/index.json",
            [],
            "mitre-index",
        )
    raise ValueError(f"unsupported operation: {operation}")


def validate_response(kind: str, data: Any) -> int | None:
    if not isinstance(data, Mapping):
        raise RuntimeError("upstream response must be a JSON object")
    if kind == "ripestat":
        if data.get("status") != "ok" or not isinstance(data.get("data"), Mapping):
            raise RuntimeError("RIPEstat response contract failed")
        return None
    if kind == "peeringdb":
        rows = data.get("data")
        if not isinstance(rows, list):
            raise RuntimeError("PeeringDB response contract failed")
        return len(rows)
    if kind == "openfema":
        rows = data.get("DisasterDeclarationsSummaries")
        if not isinstance(rows, list):
            raise RuntimeError("OpenFEMA response contract failed")
        return len(rows)
    if kind == "mitre-index":
        if not isinstance(data.get("collections"), list):
            raise RuntimeError("MITRE ATT&CK index contract failed")
        return len(data["collections"])
    raise RuntimeError("unknown response contract")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45,
        minimum=5,
        maximum=90,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=10_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_STRATEGIC_SOURCE_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "credential_mode": "none",
        "secret_values_exposed": False,
        "automatic_pagination": False,
        "automatic_retry": False,
        "redirects_allowed": False,
    }
    try:
        url, query, kind = build_request(operation, parameters)
        if kind == "catalog":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif kind == "source-matrix":
            snapshot = {"source_access_matrix": load_json(SOURCE_MATRIX_PATH)}
        else:
            response = requests.get(
                str(url),
                params=query,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "evidence-data-center-strategic-intelligence/1",
                },
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            if not response.ok:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"upstream HTTP {response.status_code}: {text}")
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("upstream returned invalid JSON") from exc
            row_count = validate_response(kind, data)
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {"provider": kind, "operation": operation, "data": data}
            metadata.update(
                {
                    "upstream_called": True,
                    "api_origin": urlparse(str(url)).hostname,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "row_count": row_count,
                }
            )
        status = "INTEL_STRATEGIC_SOURCE_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="strategic-intelligence",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-strategic-source]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="strategic-intelligence-ticket-status-v1",
            display_name="战略情报固定开放数据",
        )
    )
