#!/usr/bin/env python3
"""Bounded read-only HexDB aviation metadata execution."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote

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
ORIGIN = "https://hexdb.io"
ICAO24_RE = re.compile(r"^[0-9A-Fa-f]{6}$")
CALLSIGN_RE = re.compile(r"^[A-Za-z0-9]{2,12}$")
ICAO_AIRPORT_RE = re.compile(r"^[A-Za-z0-9]{4}$")
IATA_AIRPORT_RE = re.compile(r"^[A-Za-z0-9]{3}$")


def _value(parameters: Mapping[str, Any], key: str, pattern: re.Pattern[str]) -> str:
    value = str(parameters.get(key) or "").strip()
    if not pattern.fullmatch(value):
        raise ValueError(f"{key} is invalid")
    return value.upper()


def build_request(operation: str, parameters: Mapping[str, Any]) -> str | None:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities does not accept parameters")
        return None
    if operation == "aircraft-by-icao24":
        return "/api/v1/aircraft/" + quote(_value(parameters, "icao24", ICAO24_RE), safe="")
    if operation == "route-by-icao-callsign":
        return "/api/v1/route/icao/" + quote(_value(parameters, "callsign", CALLSIGN_RE), safe="")
    if operation == "route-by-iata-callsign":
        return "/api/v1/route/iata/" + quote(_value(parameters, "callsign", CALLSIGN_RE), safe="")
    if operation == "airport-by-icao":
        return "/api/v1/airport/icao/" + quote(_value(parameters, "airport", ICAO_AIRPORT_RE), safe="")
    if operation == "airport-by-iata":
        return "/api/v1/airport/iata/" + quote(_value(parameters, "airport", IATA_AIRPORT_RE), safe="")
    raise ValueError(f"unsupported operation: {operation}")


def _is_not_found(status_code: int, payload: Any) -> bool:
    if status_code == 404:
        return True
    if isinstance(payload, Mapping):
        return str(payload.get("status") or "") == "404"
    return False


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=20, minimum=5, maximum=30, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=500_000, minimum=1024, maximum=2_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_HEXDB_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "hexdb.io",
        "credential_mode": "none",
        "secret_values_exposed": False,
        "requests_per_ticket": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "bulk_lookup": False,
        "data_quality": "crowdsourced_best_effort",
    }
    try:
        path = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                ORIGIN + path,
                headers={"Accept": "application/json", "User-Agent": "intelligence-center-hexdb/1"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError("HexDB returned invalid JSON") from exc
            if _is_not_found(response.status_code, payload):
                clean = payload if isinstance(payload, Mapping) else {"status": "404", "error": "not found"}
                snapshot = {"provider": "hexdb-aviation", "operation": operation, "found": False, "record": clean}
            else:
                if not response.ok:
                    raise RuntimeError(f"HexDB HTTP {response.status_code}: {str(payload)[:1000]}")
                if not isinstance(payload, Mapping):
                    raise RuntimeError("HexDB response contract is not an object")
                snapshot = {"provider": "hexdb-aviation", "operation": operation, "found": True, "record": dict(payload)}
            sanitized = (json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
            if len(sanitized) > max_bytes:
                raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(sanitized)
            metadata.update({
                "upstream_called": True,
                "http_status": response.status_code,
                "request_path": path,
                "response_bytes": len(sanitized),
                "response_sha256": bytes_sha(sanitized),
                "found": bool(snapshot.get("found")),
            })
        status = "INTEL_HEXDB_COMPLETED"
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
        schema_prefix="hexdb-aviation",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-hexdb]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="hexdb-aviation-ticket-status-v1",
            display_name="HexDB Aviation",
        )
    )
