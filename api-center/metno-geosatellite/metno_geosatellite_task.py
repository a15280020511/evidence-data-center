#!/usr/bin/env python3
"""Bounded read-only MET Norway Geosatellite 1.4 runtime."""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime, timezone
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
ORIGIN = "https://api.met.no"
BASE_PATH = "/weatherapi/geosatellite/1.4"
USER_AGENT = "EvidenceDataCenter/1.0 github.com/a15280020511/evidence-data-center"
AREAS = {"africa", "atlantic_ocean", "europe", "global", "mediterranean"}
SPECTRA = {"infrared", "visible"}
VIDEO_FORMATS = {"mp4", "webm"}
TIME_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:00Z$")


def _area(parameters: Mapping[str, Any], *, required: bool = True) -> str:
    value = str(parameters.get("area") or "")
    if not value and not required:
        return ""
    if value not in AREAS:
        raise ValueError("area is invalid")
    return value


def _spectrum(parameters: Mapping[str, Any], *, required: bool = False) -> str:
    value = str(parameters.get("spectrum") or "")
    if not value and not required:
        return ""
    if value not in SPECTRA:
        raise ValueError("spectrum is invalid")
    return value


def _capture_time(parameters: Mapping[str, Any]) -> str:
    value = str(parameters.get("time") or "")
    if not value:
        return ""
    if not TIME_RE.fullmatch(value):
        raise ValueError("time must match YYYY-MM-DDThh:mm:00Z")
    parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:00Z").replace(tzinfo=timezone.utc)
    if parsed > datetime.now(timezone.utc):
        raise ValueError("time must not be in the future")
    return value


def build_request(
    operation: str, parameters: Mapping[str, Any]
) -> tuple[str | None, dict[str, str], str]:
    """Return fixed URL, allowlisted query and expected output extension."""
    if operation == "catalog-capabilities":
        return None, {}, "json"

    if operation == "get-static-image":
        query = {
            "area": _area(parameters),
            "type": _spectrum(parameters) or "infrared",
        }
        capture_time = _capture_time(parameters)
        if capture_time:
            query["time"] = capture_time
        return ORIGIN + BASE_PATH + "/", query, "png"

    if operation == "get-europe-animation":
        video_format = str(parameters.get("format") or "mp4")
        if video_format not in VIDEO_FORMATS:
            raise ValueError("format is invalid")
        return ORIGIN + BASE_PATH + "/europe." + quote(video_format, safe=""), {}, video_format

    if operation == "list-available":
        query = {"area": _area(parameters)}
        spectrum = _spectrum(parameters)
        if spectrum:
            query["type"] = spectrum
        return ORIGIN + BASE_PATH + "/available.json", query, "json"

    raise ValueError(f"unsupported operation: {operation}")


def _validate_content(operation: str, content_type: str, raw: bytes) -> None:
    lowered = content_type.lower()
    if operation == "get-static-image":
        if "image/png" not in lowered or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("MET Norway returned a non-PNG static image")
    elif operation == "get-europe-animation":
        if not (
            "video/mp4" in lowered
            or "video/webm" in lowered
            or "application/octet-stream" in lowered
        ):
            raise RuntimeError("MET Norway returned an unexpected animation content type")
    elif operation == "list-available":
        if "json" not in lowered:
            raise RuntimeError("MET Norway returned a non-JSON availability response")


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
        maximum=90,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=20_000_000,
        minimum=1024,
        maximum=30_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_METNO_GEOSATELLITE_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "provider": "metno-geosatellite",
        "api_version": "1.4",
        "credential_mode": "none",
        "user_agent_identified": True,
        "user_agent": USER_AGENT,
        "requests_per_ticket": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "cache_headers_observed": False,
        "write_operations_allowed": False,
        "secret_values_exposed": False,
        "attribution": "Norwegian Meteorological Institute (MET Norway), CC BY 4.0",
    }
    try:
        url, query, extension = build_request(operation, parameters)
        if url is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            accept = {
                "png": "image/png",
                "mp4": "video/mp4",
                "webm": "video/webm",
                "json": "application/json",
            }[extension]
            response = requests.get(
                url,
                params=query,
                headers={"Accept": accept, "User-Agent": USER_AGENT},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            if not response.ok:
                detail = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"MET Norway Geosatellite HTTP {response.status_code}: {detail}"
                )
            content_type = response.headers.get("Content-Type", "")
            _validate_content(operation, content_type, raw)
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "host": "api.met.no",
                    "request_path": url.removeprefix(ORIGIN),
                    "query_parameter_names": sorted(query),
                    "content_type": content_type,
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "last_modified": response.headers.get("Last-Modified"),
                    "expires": response.headers.get("Expires"),
                    "etag": response.headers.get("ETag"),
                    "cache_headers_observed": any(
                        response.headers.get(name)
                        for name in ("Last-Modified", "Expires", "ETag")
                    ),
                    "deprecated_version_warning": response.status_code == 203,
                }
            )
            if extension == "json":
                try:
                    data = response.json()
                except ValueError as exc:
                    raise RuntimeError(
                        "MET Norway returned invalid availability JSON"
                    ) from exc
                row_count = len(data) if isinstance(data, list) else (
                    len(data.get("files", []))
                    if isinstance(data, Mapping) and isinstance(data.get("files"), list)
                    else 1
                )
                snapshot = {
                    "provider": "metno-geosatellite",
                    "operation": operation,
                    "area": parameters.get("area"),
                    "spectrum": parameters.get("spectrum"),
                    "row_count": row_count,
                    "data": data,
                }
                (output_dir / "response.json").write_bytes(raw)
                metadata["row_count"] = row_count
            else:
                filename = f"response.{extension}"
                (output_dir / filename).write_bytes(raw)
                snapshot = {
                    "provider": "metno-geosatellite",
                    "operation": operation,
                    "area": parameters.get("area", "europe"),
                    "spectrum": parameters.get("spectrum", "infrared"),
                    "capture_time": parameters.get("time", "latest"),
                    "response_file": filename,
                    "response_bytes": len(raw),
                    "content_type": content_type,
                    "attribution": metadata["attribution"],
                }
        status = "INTEL_METNO_GEOSATELLITE_COMPLETED"
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
        schema_prefix="metno-geosatellite",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-metno-geosatellite]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="metno-geosatellite-ticket-status-v1",
            display_name="MET Norway Geosatellite",
        )
    )
