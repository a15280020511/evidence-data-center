#!/usr/bin/env python3
"""Bounded read-only OECD SDMX execution for API-center tickets."""
from __future__ import annotations

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
BASE_URL = "https://sdmx.oecd.org/public/rest/v1"
COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$")
VERSION_RE = re.compile(r"^(?:latest|[0-9]+(?:\.[0-9]+){0,3})$")
KEY_RE = re.compile(r"^[A-Za-z0-9+._@-]{1,500}$")


def component(value: Any, name: str) -> str:
    text = str(value or "")
    if not COMPONENT_RE.fullmatch(text):
        raise ValueError(f"{name} is not a valid SDMX component")
    return quote(text, safe="._@-")


def version(value: Any) -> str:
    text = str(value or "latest")
    if not VERSION_RE.fullmatch(text):
        raise ValueError("version is invalid")
    return text


def build_request(
    operation: str, parameters: Mapping[str, Any]
) -> tuple[str | None, dict[str, str], str]:
    fmt = str(parameters.get("format") or "json")
    if fmt not in {"json", "csv"}:
        raise ValueError("format must be json or csv")
    if operation == "catalog-capabilities":
        return None, {}, fmt
    if operation == "list-dataflows":
        return "/dataflow/all/all/latest", {}, fmt
    if operation == "get-dataflow":
        return (
            f"/dataflow/{component(parameters['agency'], 'agency')}/"
            f"{component(parameters['flow'], 'flow')}/{version(parameters.get('version'))}",
            {},
            fmt,
        )
    if operation == "get-datastructure":
        return (
            f"/datastructure/{component(parameters['agency'], 'agency')}/"
            f"{component(parameters['structure_id'], 'structure_id')}/"
            f"{version(parameters.get('version'))}",
            {},
            fmt,
        )
    if operation == "get-codelist":
        return (
            f"/codelist/{component(parameters['agency'], 'agency')}/"
            f"{component(parameters['codelist_id'], 'codelist_id')}/"
            f"{version(parameters.get('version'))}",
            {},
            fmt,
        )
    if operation == "get-data":
        key = str(parameters["key"])
        if not KEY_RE.fullmatch(key):
            raise ValueError("key is not a valid bounded SDMX key")
        path = (
            f"/data/{component(parameters['agency'], 'agency')},"
            f"{component(parameters['flow'], 'flow')},"
            f"{version(parameters.get('version'))}/{quote(key, safe='+._@-')}"
        )
        query: dict[str, str] = {}
        mapping = {
            "start_period": "startPeriod",
            "end_period": "endPeriod",
            "dimension_at_observation": "dimension_at_observation",
        }
        for source, target in mapping.items():
            value = parameters.get(source)
            if value not in (None, ""):
                query[target] = str(value)
        return path, query, fmt
    raise ValueError(f"unsupported operation: {operation}")


def accept_header(operation: str, fmt: str) -> str:
    data = operation == "get-data"
    if fmt == "csv":
        return (
            "application/vnd.sdmx.data+csv;version=2.0.0"
            if data
            else "application/vnd.sdmx.structure+csv;version=2.0.0"
        )
    return (
        "application/vnd.sdmx.data+json;version=2.0.0"
        if data
        else "application/vnd.sdmx.structure+json;version=2.0.0"
    )


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45, minimum=5, maximum=120, name="timeout_seconds"
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000, minimum=1024, maximum=20_000_000,
        name="max_response_bytes"
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "API_OECD_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "sdmx.oecd.org",
        "credential_mode": "none",
        "secret_values_exposed": False,
    }

    try:
        path, query, fmt = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                BASE_URL + path,
                params=query,
                headers={
                    "Accept": accept_header(operation, fmt),
                    "User-Agent": "gpts-oecd-api-center/1",
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
                raise RuntimeError(f"OECD HTTP {response.status_code}: {text}")
            suffix = "json" if fmt == "json" else "csv"
            data_path = output_dir / f"response.{suffix}"
            data_path.write_bytes(raw)
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_path": path,
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                }
            )
            if fmt == "json":
                try:
                    data = response.json()
                except ValueError as exc:
                    raise RuntimeError("OECD returned invalid JSON") from exc
                snapshot = {
                    "provider": "oecd",
                    "operation": operation,
                    "request_path": path,
                    "data": data,
                }
            else:
                snapshot = {
                    "provider": "oecd",
                    "operation": operation,
                    "request_path": path,
                    "artifact_file": data_path.name,
                    "artifact_bytes": len(raw),
                }
        status = "API_OECD_COMPLETED"
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
        schema_prefix="oecd",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[api-oecd]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="oecd-ticket-status-v1",
            display_name="OECD",
        )
    )
