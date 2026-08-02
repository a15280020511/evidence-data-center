#!/usr/bin/env python3
"""Bounded read-only Asian Development Bank KIDB SDMX execution."""
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
ORIGIN = "https://kidb.adb.org"
COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,79}$")
VERSION_RE = re.compile(r"^(?:\+|latest|[0-9]+(?:\.[0-9]+){0,3})$")
CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,39}$")


def component(value: Any, name: str) -> str:
    text = str(value or "")
    if not COMPONENT_RE.fullmatch(text):
        raise ValueError(f"{name} is not a valid SDMX component")
    return quote(text, safe="._@-")


def version(value: Any) -> str:
    text = str(value or "+")
    if not VERSION_RE.fullmatch(text):
        raise ValueError("version is invalid")
    return text


def codes(value: Any, name: str, maximum: int) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} codes")
    result = [str(item) for item in value]
    if len(set(result)) != len(result) or any(not CODE_RE.fullmatch(item) for item in result):
        raise ValueError(f"{name} contains an invalid or duplicate code")
    return result


def bounded_year(value: Any, name: str) -> int | None:
    if value in (None, ""):
        return None
    return bounded_int(value, default=2000, minimum=2000, maximum=2024, name=name)


def build_request(
    operation: str, parameters: Mapping[str, Any]
) -> tuple[str | None, list[tuple[str, str]], str]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, [], "json"

    if operation == "list-dataflows":
        return "/api/v4/sdmx/structure/dataflow/all/all/+", [("format", "sdmx-json")], "json"

    structure_map = {
        "get-dataflow": ("dataflow", "flow"),
        "get-datastructure": ("datastructure", "structure_id"),
        "get-codelist": ("codelist", "codelist_id"),
        "get-conceptscheme": ("conceptscheme", "conceptscheme_id"),
    }
    if operation in structure_map:
        resource, identifier_name = structure_map[operation]
        agency = component(parameters.get("agency") or "ADB", "agency")
        identifier = component(parameters.get(identifier_name), identifier_name)
        path = f"/api/v4/sdmx/structure/{resource}/{agency}/{identifier}/{version(parameters.get('version'))}"
        references = str(parameters.get("references") or "none")
        if references not in {"none", "parents", "ancestors", "children", "descendants", "all"}:
            raise ValueError("references is invalid")
        return path, [("format", "sdmx-json"), ("references", references)], "json"

    if operation == "list-indicators":
        dataflow = component(parameters.get("dataflow"), "dataflow")
        return f"/api/dataflow/indicators/{dataflow}", [], "json"

    if operation == "get-data":
        dataflow = component(parameters.get("dataflow"), "dataflow")
        indicators = codes(parameters.get("indicators"), "indicators", 20)
        economies = codes(parameters.get("economies"), "economies", 20)
        start = bounded_year(parameters.get("start_period"), "start_period")
        end = bounded_year(parameters.get("end_period"), "end_period")
        if start is not None and end is not None:
            if start > end:
                raise ValueError("start_period must not exceed end_period")
            if end - start > 24:
                raise ValueError("period span must not exceed 25 years")
        fmt = str(parameters.get("format") or "json")
        if fmt not in {"json", "csv"}:
            raise ValueError("format must be json or csv")
        sdmx_version = str(parameters.get("sdmx_version") or "3.0")
        if sdmx_version not in {"3.0", "2.1"}:
            raise ValueError("sdmx_version must be 3.0 or 2.1")
        grouping = str(parameters.get("grouping") or "indicator")
        if grouping not in {"indicator", "economy"}:
            raise ValueError("grouping must be indicator or economy")
        path = (
            f"/api/v4/sdmx/data/ADB,{dataflow}/"
            f"A.{'+'.join(indicators)}.{'+'.join(economies)}"
        )
        query: list[tuple[str, str]] = [
            ("version", sdmx_version),
            ("format", "sdmx-json" if fmt == "json" else "sdmx-csv"),
            ("grouping", grouping),
        ]
        if start is not None:
            query.append(("startPeriod", str(start)))
        if end is not None:
            query.append(("endPeriod", str(end)))
        return path, query, fmt

    raise ValueError(f"unsupported operation: {operation}")


def row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        for key in ("data", "results", "values", "series", "dataflows"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
            if isinstance(value, Mapping):
                return len(value)
        return 1
    return 0


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000,
        minimum=1024,
        maximum=20_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_ADB_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "kidb.adb.org",
        "credential_mode": "none",
        "requests_per_ticket_max": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "secret_values_exposed": False,
    }

    try:
        path, query, fmt = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                ORIGIN + path,
                params=query,
                headers={
                    "Accept": "application/json" if fmt == "json" else "text/csv",
                    "User-Agent": "intelligence-center-adb/1",
                },
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_path": path,
                    "query_parameter_names": sorted({key for key, _ in query}),
                    "response_bytes_raw": len(raw),
                }
            )
            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            if not response.ok:
                text = raw[:1200].decode("utf-8", errors="replace")
                raise RuntimeError(f"ADB HTTP {response.status_code}: {text}")

            if fmt == "json":
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise RuntimeError("ADB returned invalid JSON") from exc
                sanitized = (
                    json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
                ).encode("utf-8")
                if len(sanitized) > max_bytes:
                    raise RuntimeError("sanitized response exceeds max_response_bytes")
                data_path = output_dir / "response.json"
                data_path.write_bytes(sanitized)
                count = row_count(payload)
                snapshot = {
                    "provider": "adb",
                    "operation": operation,
                    "request_path": path,
                    "row_count": count,
                    "data": payload,
                }
                stored = sanitized
            else:
                data_path = output_dir / "response.csv"
                data_path.write_bytes(raw)
                count = max(0, len(raw.splitlines()) - 1)
                snapshot = {
                    "provider": "adb",
                    "operation": operation,
                    "request_path": path,
                    "row_count": count,
                    "artifact_file": data_path.name,
                    "artifact_bytes": len(raw),
                }
                stored = raw
            metadata.update(
                {
                    "response_bytes": len(stored),
                    "response_sha256": bytes_sha(stored),
                    "row_count": count,
                }
            )
        status = "INTEL_ADB_COMPLETED"
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
        schema_prefix="adb",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-adb]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="adb-ticket-status-v1",
            display_name="ADB KIDB",
        )
    )
