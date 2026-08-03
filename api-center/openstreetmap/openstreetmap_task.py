#!/usr/bin/env python3
"""Bounded read-only OpenStreetMap, Nominatim and Overpass execution."""
from __future__ import annotations

import html
import os
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
USER_AGENT = "a15280020511-evidence-data-center/1.0 (https://github.com/a15280020511/evidence-data-center)"
ALLOWED_HOSTS = {
    "api.openstreetmap.org",
    "nominatim.openstreetmap.org",
    "overpass-api.de",
}
TAG_KEY_RE = re.compile(r"^[A-Za-z0-9_:.-]{1,64}$")
TAG_VALUE_RE = re.compile(r"^[A-Za-z0-9_ :./()&+,'-]{1,100}$")
ELEMENT_TYPES = {"node", "way", "relation", "all"}


def _fixed_url(host: str, path: str) -> str:
    if host not in ALLOWED_HOSTS or not path.startswith("/") or "://" in path:
        raise ValueError("request target is not allowlisted")
    url = f"https://{host}{path}"
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != host:
        raise ValueError("request target failed fixed-host validation")
    return url


def _float(value: Any, *, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} is outside the allowed range")
    return number


def _tag_filter(parameters: Mapping[str, Any]) -> str:
    key = str(parameters.get("tag_key") or "")
    if not TAG_KEY_RE.fullmatch(key):
        raise ValueError("tag_key is invalid")
    value = parameters.get("tag_value")
    if value is None:
        return f'["{key}"]'
    value_text = str(value)
    if not TAG_VALUE_RE.fullmatch(value_text):
        raise ValueError("tag_value is invalid")
    return f'["{key}"="{value_text}"]'


def _elements(element_type: str, selector: str) -> str:
    if element_type not in ELEMENT_TYPES:
        raise ValueError("element_type is invalid")
    types = ("node", "way", "relation") if element_type == "all" else (element_type,)
    return "".join(f"{kind}{selector};" for kind in types)


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, str, dict[str, Any] | str]:
    if operation == "catalog-capabilities":
        return None, "LOCAL", {}
    if operation == "osm-object":
        object_type = str(parameters.get("object_type") or "")
        if object_type not in {"node", "way", "relation"}:
            raise ValueError("object_type is invalid")
        object_id = bounded_int(parameters.get("object_id"), default=0, minimum=1, maximum=999_999_999_999, name="object_id")
        return _fixed_url("api.openstreetmap.org", f"/api/0.6/{object_type}/{object_id}.json"), "GET", {}
    if operation == "nominatim-search":
        query = str(parameters.get("query") or "").strip()
        if len(query) < 2:
            raise ValueError("query is required")
        params: dict[str, Any] = {
            "format": "jsonv2",
            "q": query,
            "limit": bounded_int(parameters.get("limit"), default=5, minimum=1, maximum=10, name="limit"),
            "addressdetails": 1 if parameters.get("addressdetails", True) else 0,
            "extratags": 1 if parameters.get("extratags", False) else 0,
            "namedetails": 1 if parameters.get("namedetails", False) else 0,
        }
        for name in ("countrycodes", "language"):
            if parameters.get(name) is not None:
                target = "accept-language" if name == "language" else name
                params[target] = str(parameters[name])
        email = os.getenv("NOMINATIM_EMAIL", "").strip()
        if email:
            params["email"] = email
        return _fixed_url("nominatim.openstreetmap.org", "/search"), "GET", params
    if operation == "nominatim-reverse":
        params = {
            "format": "jsonv2",
            "lat": _float(parameters.get("lat"), name="lat", minimum=-90, maximum=90),
            "lon": _float(parameters.get("lon"), name="lon", minimum=-180, maximum=180),
            "zoom": bounded_int(parameters.get("zoom"), default=18, minimum=3, maximum=18, name="zoom"),
            "addressdetails": 1 if parameters.get("addressdetails", True) else 0,
            "extratags": 1 if parameters.get("extratags", False) else 0,
            "namedetails": 1 if parameters.get("namedetails", False) else 0,
        }
        if parameters.get("language") is not None:
            params["accept-language"] = str(parameters["language"])
        email = os.getenv("NOMINATIM_EMAIL", "").strip()
        if email:
            params["email"] = email
        return _fixed_url("nominatim.openstreetmap.org", "/reverse"), "GET", params
    if operation in {"overpass-nearby", "overpass-bbox"}:
        tag_filter = _tag_filter(parameters)
        element_type = str(parameters.get("element_type") or "all")
        limit = bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=200, name="limit")
        if operation == "overpass-nearby":
            lat = _float(parameters.get("lat"), name="lat", minimum=-90, maximum=90)
            lon = _float(parameters.get("lon"), name="lon", minimum=-180, maximum=180)
            radius = bounded_int(parameters.get("radius_m"), default=500, minimum=1, maximum=5000, name="radius_m")
            selector = f'(around:{radius},{lat:.7f},{lon:.7f}){tag_filter}'
        else:
            south = _float(parameters.get("south"), name="south", minimum=-90, maximum=90)
            west = _float(parameters.get("west"), name="west", minimum=-180, maximum=180)
            north = _float(parameters.get("north"), name="north", minimum=-90, maximum=90)
            east = _float(parameters.get("east"), name="east", minimum=-180, maximum=180)
            if south >= north or west >= east:
                raise ValueError("bbox coordinates must satisfy south<north and west<east")
            if north - south > 2.0 or east - west > 2.0:
                raise ValueError("bbox span exceeds 2 degrees")
            selector = f'({south:.7f},{west:.7f},{north:.7f},{east:.7f}){tag_filter}'
        body = f"[out:json][timeout:25];({_elements(element_type, selector)});out body {limit};"
        if len(body) > 2000:
            raise ValueError("generated Overpass query is too long")
        return _fixed_url("overpass-api.de", "/api/interpreter"), "POST", body
    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_OPENSTREETMAP_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "credential_mode": "none",
        "secret_values_exposed": False,
        "automatic_pagination": False,
        "requests_per_ticket": 0,
        "raw_overpass_ql_accepted": False,
        "nominatim_bulk_mode": False,
    }
    try:
        url, method, payload = build_request(operation, parameters)
        if url is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
            kwargs: dict[str, Any] = {
                "headers": headers,
                "timeout": timeout,
                "allow_redirects": False,
            }
            if method == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                kwargs["data"] = {"data": payload}
                response = requests.post(url, **kwargs)
            else:
                kwargs["params"] = payload
                response = requests.get(url, **kwargs)
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"OSM upstream HTTP {response.status_code}: {text}")
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("OSM upstream returned invalid JSON") from exc
            if operation.startswith("overpass-"):
                if not isinstance(data, Mapping) or not isinstance(data.get("elements"), list):
                    raise RuntimeError("Overpass response does not match elements contract")
                row_count = len(data["elements"])
            elif operation == "nominatim-search":
                if not isinstance(data, list):
                    raise RuntimeError("Nominatim search response must be a list")
                row_count = len(data)
            else:
                row_count = 1
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {"provider": "openstreetmap", "operation": operation, "data": data}
            metadata.update({
                "upstream_called": True,
                "requests_per_ticket": 1,
                "api_host": urlparse(url).hostname,
                "request_path": urlparse(url).path,
                "http_method": method,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "row_count": row_count,
            })
        status = "INTEL_OPENSTREETMAP_COMPLETED"
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
        schema_prefix="openstreetmap",
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(
        execute=execute,
        ticket_prefix="[intel-osm]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="openstreetmap-ticket-status-v1",
        display_name="OpenStreetMap",
    ))
