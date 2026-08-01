#!/usr/bin/env python3
"""Bounded read-only NASA Open APIs, Image Library and Earthdata GIBS runtime."""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import date
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
SECRET_ENV = "NASA_API_KEY"
NASA_ORIGIN = "https://api.nasa.gov"
IMAGES_ORIGIN = "https://images-api.nasa.gov"
GIBS_ORIGIN = "https://gibs.earthdata.nasa.gov"
LAYER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$")
NASA_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ASTEROID_RE = re.compile(r"^[0-9]{1,20}$")
KEY_REQUIRED = {
    "apod",
    "neo-feed",
    "neo-lookup",
    "neo-browse",
    "donki-cme",
    "donki-cme-analysis",
    "donki-gst",
    "donki-ips",
    "donki-flr",
    "donki-sep",
    "donki-mpc",
    "donki-rbe",
    "donki-hss",
    "donki-notifications",
    "epic-natural",
    "epic-enhanced",
}
DONKI_PATHS = {
    "donki-cme": "CME",
    "donki-cme-analysis": "CMEAnalysis",
    "donki-gst": "GST",
    "donki-ips": "IPS",
    "donki-flr": "FLR",
    "donki-sep": "SEP",
    "donki-mpc": "MPC",
    "donki-rbe": "RBE",
    "donki-hss": "HSS",
    "donki-notifications": "notifications",
}


def _date_value(parameters: Mapping[str, Any], name: str, *, required: bool = False) -> str | None:
    raw = parameters.get(name)
    if raw in (None, ""):
        if required:
            raise ValueError(f"{name} is required")
        return None
    value = str(raw)
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid YYYY-MM-DD date") from exc
    return value


def _date_window(
    parameters: Mapping[str, Any],
    *,
    max_days: int,
    require_start: bool = False,
) -> tuple[str | None, str | None]:
    start = _date_value(parameters, "start_date", required=require_start)
    end = _date_value(parameters, "end_date")
    if end and not start:
        raise ValueError("end_date requires start_date")
    if start and end:
        start_day = date.fromisoformat(start)
        end_day = date.fromisoformat(end)
        if start_day > end_day:
            raise ValueError("start_date must not be after end_date")
        if (end_day - start_day).days > max_days:
            raise ValueError(f"date range must not exceed {max_days} days")
    return start, end


def _bool_query(value: Any) -> str:
    return "true" if bool(value) else "false"


def _gibs_scope(parameters: Mapping[str, Any]) -> tuple[str, str]:
    projection = str(parameters.get("projection") or "epsg4326")
    catalog = str(parameters.get("catalog") or "best")
    if projection not in {"epsg4326", "epsg3857"}:
        raise ValueError("projection is invalid")
    if catalog not in {"best", "nrt", "std", "all"}:
        raise ValueError("catalog is invalid")
    return projection, catalog


def _safe_layer(parameters: Mapping[str, Any]) -> str:
    value = str(parameters.get("layer") or "")
    if not LAYER_RE.fullmatch(value):
        raise ValueError("layer is invalid")
    return value


def _safe_nasa_id(parameters: Mapping[str, Any]) -> str:
    value = str(parameters.get("nasa_id") or "")
    if not NASA_ID_RE.fullmatch(value):
        raise ValueError("nasa_id is invalid")
    return value


def build_request(
    operation: str,
    parameters: Mapping[str, Any],
) -> tuple[str | None, dict[str, str], bool, str]:
    """Return fixed URL, safe query, whether a NASA key is required, and file type."""
    if operation == "catalog-capabilities":
        return None, {}, False, "json"

    if operation == "apod":
        single_date = _date_value(parameters, "date")
        start, end = _date_window(parameters, max_days=31)
        count = parameters.get("count")
        active_modes = sum(bool(value) for value in (single_date, start, count not in (None, "")))
        if active_modes > 1:
            raise ValueError("apod date, date range and count modes are mutually exclusive")
        query: dict[str, str] = {}
        if single_date:
            query["date"] = single_date
        if start:
            query["start_date"] = start
        if end:
            query["end_date"] = end
        if count not in (None, ""):
            query["count"] = str(
                bounded_int(count, default=1, minimum=1, maximum=10, name="count")
            )
        if "thumbs" in parameters:
            query["thumbs"] = _bool_query(parameters["thumbs"])
        return NASA_ORIGIN + "/planetary/apod", query, True, "json"

    if operation == "neo-feed":
        start, end = _date_window(parameters, max_days=7, require_start=True)
        query = {"start_date": str(start)}
        if end:
            query["end_date"] = end
        return NASA_ORIGIN + "/neo/rest/v1/feed", query, True, "json"

    if operation == "neo-lookup":
        asteroid_id = str(parameters.get("asteroid_id") or "")
        if not ASTEROID_RE.fullmatch(asteroid_id):
            raise ValueError("asteroid_id is invalid")
        return (
            NASA_ORIGIN + "/neo/rest/v1/neo/" + quote(asteroid_id, safe=""),
            {},
            True,
            "json",
        )

    if operation == "neo-browse":
        query = {
            "page": str(
                bounded_int(parameters.get("page"), default=0, minimum=0, maximum=10000, name="page")
            ),
            "size": str(
                bounded_int(parameters.get("size"), default=20, minimum=1, maximum=100, name="size")
            ),
        }
        return NASA_ORIGIN + "/neo/rest/v1/neo/browse", query, True, "json"

    if operation in DONKI_PATHS:
        start, end = _date_window(parameters, max_days=31)
        query = {}
        if start:
            query["startDate"] = start
        if end:
            query["endDate"] = end
        if operation == "donki-cme-analysis":
            if "most_accurate_only" in parameters:
                query["mostAccurateOnly"] = _bool_query(parameters["most_accurate_only"])
            if "complete_entry_only" in parameters:
                query["completeEntryOnly"] = _bool_query(parameters["complete_entry_only"])
            if "speed" in parameters:
                query["speed"] = str(
                    bounded_int(parameters["speed"], default=0, minimum=0, maximum=5000, name="speed")
                )
            if "half_angle" in parameters:
                query["halfAngle"] = str(
                    bounded_int(parameters["half_angle"], default=0, minimum=0, maximum=180, name="half_angle")
                )
            if "catalog" in parameters:
                query["catalog"] = str(parameters["catalog"])
        if operation == "donki-ips":
            if "location" in parameters:
                query["location"] = str(parameters["location"])
            if "catalog" in parameters:
                query["catalog"] = str(parameters["catalog"])
        if operation == "donki-notifications" and "type" in parameters:
            query["type"] = str(parameters["type"])
        return NASA_ORIGIN + "/DONKI/" + DONKI_PATHS[operation], query, True, "json"

    if operation in {"epic-natural", "epic-enhanced"}:
        mode = "natural" if operation == "epic-natural" else "enhanced"
        selected_date = _date_value(parameters, "date")
        path = f"/EPIC/api/{mode}"
        if selected_date:
            path += "/date/" + quote(selected_date, safe="-")
        return NASA_ORIGIN + path, {}, True, "json"

    if operation == "nasa-images-search":
        query_text = str(parameters.get("q") or "").strip()
        if not query_text or len(query_text) > 200 or any(ord(ch) < 32 for ch in query_text):
            raise ValueError("q is invalid")
        query = {"q": query_text}
        if "media_type" in parameters:
            query["media_type"] = str(parameters["media_type"])
        year_start = parameters.get("year_start")
        year_end = parameters.get("year_end")
        if year_start not in (None, ""):
            query["year_start"] = str(
                bounded_int(year_start, default=1900, minimum=1900, maximum=2100, name="year_start")
            )
        if year_end not in (None, ""):
            query["year_end"] = str(
                bounded_int(year_end, default=2100, minimum=1900, maximum=2100, name="year_end")
            )
        if year_start not in (None, "") and year_end not in (None, ""):
            if int(str(year_start)) > int(str(year_end)):
                raise ValueError("year_start must not be after year_end")
        query["page"] = str(
            bounded_int(parameters.get("page"), default=1, minimum=1, maximum=100, name="page")
        )
        return IMAGES_ORIGIN + "/search", query, False, "json"

    if operation in {
        "nasa-images-asset",
        "nasa-images-metadata",
        "nasa-images-captions",
    }:
        route = {
            "nasa-images-asset": "asset",
            "nasa-images-metadata": "metadata",
            "nasa-images-captions": "captions",
        }[operation]
        nasa_id = _safe_nasa_id(parameters)
        preferred = "json" if operation != "nasa-images-captions" else "txt"
        return IMAGES_ORIGIN + f"/{route}/" + quote(nasa_id, safe="._-"), {}, False, preferred

    if operation == "gibs-wmts-capabilities":
        projection, catalog = _gibs_scope(parameters)
        return (
            GIBS_ORIGIN + f"/wmts/{projection}/{catalog}/1.0.0/WMTSCapabilities.xml",
            {},
            False,
            "xml",
        )

    if operation == "gibs-wms-capabilities":
        projection, catalog = _gibs_scope(parameters)
        query = {"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.3.0"}
        return GIBS_ORIGIN + f"/wms/{projection}/{catalog}/wms.cgi", query, False, "xml"

    if operation == "gibs-layer-metadata":
        layer = _safe_layer(parameters)
        return (
            GIBS_ORIGIN + "/layer-metadata/v1.0/" + quote(layer, safe="._-") + ".json",
            {},
            False,
            "json",
        )

    if operation == "gibs-tile":
        projection, catalog = _gibs_scope(parameters)
        layer = _safe_layer(parameters)
        selected_date = _date_value(parameters, "date", required=True)
        matrix_set = str(parameters.get("tile_matrix_set") or "")
        allowed_matrix_sets = {"31.25m", "62.5m", "125m", "250m", "500m", "1km", "2km", "4km", "8km", "16km"}
        if matrix_set not in allowed_matrix_sets:
            raise ValueError("tile_matrix_set is invalid")
        matrix = bounded_int(parameters.get("tile_matrix"), default=0, minimum=0, maximum=30, name="tile_matrix")
        row = bounded_int(parameters.get("tile_row"), default=0, minimum=0, maximum=100000, name="tile_row")
        col = bounded_int(parameters.get("tile_col"), default=0, minimum=0, maximum=100000, name="tile_col")
        image_format = str(parameters.get("format") or "")
        if image_format not in {"jpg", "png"}:
            raise ValueError("format is invalid")
        path = (
            f"/wmts/{projection}/{catalog}/{quote(layer, safe='._-')}/default/"
            f"{quote(str(selected_date), safe='-')}/{quote(matrix_set, safe='.')}/"
            f"{matrix}/{row}/{col}.{image_format}"
        )
        return GIBS_ORIGIN + path, {}, False, image_format

    raise ValueError(f"unsupported operation: {operation}")


def _row_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if not isinstance(value, Mapping):
        return 0
    for key in ("near_earth_objects", "collection", "data"):
        nested = value.get(key)
        if isinstance(nested, list):
            return len(nested)
        if isinstance(nested, Mapping):
            if key == "collection" and isinstance(nested.get("items"), list):
                return len(nested["items"])
            return len(nested)
    return 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds"
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
    status = "INTEL_NASA_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    secret = str(os.environ.get(SECRET_ENV) or "").strip()
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "requests_per_ticket": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "credential_environment_variable": SECRET_ENV,
        "secret_values_exposed": False,
        "archived_earth_api_used": False,
        "archived_mars_rover_api_used": False,
    }
    try:
        url, query, requires_key, preferred_type = build_request(operation, parameters)
        if url is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            if requires_key and not secret:
                raise RuntimeError(f"{SECRET_ENV} is not configured")
            safe_query_names = sorted(query)
            upstream_query = dict(query)
            if requires_key:
                upstream_query["api_key"] = secret
            response = requests.get(
                url,
                params=upstream_query,
                headers={
                    "Accept": "application/json, application/xml, text/xml, text/plain, image/png, image/jpeg",
                    "User-Agent": "intelligence-center-nasa/1",
                },
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if secret and secret.encode("utf-8") in raw:
                raise RuntimeError("NASA response unexpectedly contained the API key")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok:
                detail = response.text[:1000]
                if secret:
                    detail = detail.replace(secret, "[REDACTED]")
                raise RuntimeError(f"NASA HTTP {response.status_code}: {detail}")

            content_type = response.headers.get("Content-Type", "")
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "host": url.split("/", 3)[2],
                    "request_path": "/" + url.split("/", 3)[3] if len(url.split("/", 3)) > 3 else "/",
                    "query_parameter_names": safe_query_names,
                    "content_type": content_type,
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "rate_limit_limit": response.headers.get("X-RateLimit-Limit"),
                    "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
                }
            )

            is_json = "json" in content_type.lower() or preferred_type == "json"
            if is_json:
                try:
                    data = response.json()
                except ValueError as exc:
                    raise RuntimeError("NASA returned invalid JSON") from exc
                snapshot = {
                    "provider": "nasa",
                    "operation": operation,
                    "row_count": _row_count(data),
                    "data": data,
                }
                (output_dir / "response.json").write_bytes(raw)
                metadata["row_count"] = _row_count(data)
            else:
                extension = preferred_type if preferred_type in {"xml", "txt", "jpg", "png"} else "bin"
                (output_dir / f"response.{extension}").write_bytes(raw)
                snapshot = {
                    "provider": "nasa",
                    "operation": operation,
                    "response_file": f"response.{extension}",
                    "response_bytes": len(raw),
                    "content_type": content_type,
                }
        status = "INTEL_NASA_COMPLETED"
    except Exception as exc:
        message = str(exc)
        if secret:
            message = message.replace(secret, "[REDACTED]")
        failure = {"type": type(exc).__name__, "message": message[:2000]}
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="nasa",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-nasa]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="nasa-ticket-status-v1",
            display_name="NASA",
        )
    )
