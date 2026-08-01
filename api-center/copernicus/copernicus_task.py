#!/usr/bin/env python3
"""Bounded read-only Copernicus Data Space Ecosystem runtime."""
from __future__ import annotations

import json
import os
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
STAC_ORIGIN = "https://stac.dataspace.copernicus.eu"
SENTINEL_HUB_ORIGIN = "https://sh.dataspace.copernicus.eu"
IDENTITY_ORIGIN = "https://identity.dataspace.copernicus.eu"
OAUTH_ENDPOINT_PATH = "/auth/realms/CDSE/protocol/openid-connect/token"
CLIENT_ID_ENV = "COPERNICUS_CLIENT_ID"
CLIENT_SECRET_ENV = "COPERNICUS_CLIENT_SECRET"
USER_AGENT = "EvidenceDataCenter/1.0 github.com/a15280020511/evidence-data-center"
COLLECTIONS = {
    "sentinel-1-grd",
    "sentinel-2-l1c",
    "sentinel-2-l2a",
    "sentinel-2-global-mosaics",
}
RENDER_OPERATIONS = {
    "render-true-color-png",
    "render-false-color-png",
    "render-ndvi-png",
}
ITEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,255}$")
TIME_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

TRUE_COLOR_EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: ["B02", "B03", "B04", "dataMask"], output: {bands: 4}};
}
function evaluatePixel(s) {
  return [2.5*s.B04, 2.5*s.B03, 2.5*s.B02, s.dataMask];
}
"""

FALSE_COLOR_EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: ["B03", "B04", "B08", "dataMask"], output: {bands: 4}};
}
function evaluatePixel(s) {
  return [2.5*s.B08, 2.5*s.B04, 2.5*s.B03, s.dataMask];
}
"""

NDVI_EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: ["B04", "B08", "dataMask"], output: {bands: 4}};
}
function evaluatePixel(s) {
  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
  let rgb = colorBlend(ndvi,
    [-0.2, 0.0, 0.2, 0.4, 0.6, 0.8],
    [[0.05,0.05,0.05], [0.5,0.5,0.5], [0.8,0.7,0.4], [0.6,0.8,0.3], [0.2,0.6,0.2], [0.0,0.3,0.0]]);
  return [rgb[0], rgb[1], rgb[2], s.dataMask];
}
"""


class CopernicusError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def _collection(parameters: Mapping[str, Any]) -> str:
    value = str(parameters.get("collection") or "")
    if value not in COLLECTIONS:
        raise ValueError("collection is invalid")
    return value


def _bbox(parameters: Mapping[str, Any]) -> list[float]:
    raw = parameters.get("bbox")
    if not isinstance(raw, list) or len(raw) != 4:
        raise ValueError("bbox must contain four numbers")
    try:
        bbox = [float(value) for value in raw]
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox must contain four numbers") from exc
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("bbox is outside WGS84 bounds or has invalid ordering")
    if east - west > 1.0 or north - south > 1.0:
        raise ValueError("bbox span must not exceed one degree per axis")
    return bbox


def _timestamp(value: Any, name: str) -> datetime:
    text = str(value or "")
    if not TIME_RE.fullmatch(text):
        raise ValueError(f"{name} must match YYYY-MM-DDThh:mm:ssZ")
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _time_range(parameters: Mapping[str, Any], *, max_days: int) -> tuple[str, str]:
    start_text = str(parameters.get("start_time") or "")
    end_text = str(parameters.get("end_time") or "")
    start = _timestamp(start_text, "start_time")
    end = _timestamp(end_text, "end_time")
    if start >= end:
        raise ValueError("start_time must be earlier than end_time")
    if (end - start).total_seconds() > max_days * 86400:
        raise ValueError(f"time range must not exceed {max_days} days")
    if end > datetime.now(timezone.utc).replace(microsecond=0):
        raise ValueError("end_time must not be in the future")
    return start_text, end_text


def _limit(parameters: Mapping[str, Any]) -> int:
    value = int(parameters.get("limit") or 5)
    if not 1 <= value <= 20:
        raise ValueError("limit must be between 1 and 20")
    return value


def _cloud_cover(parameters: Mapping[str, Any]) -> float | None:
    value = parameters.get("cloud_cover_max")
    if value is None:
        return None
    number = float(value)
    if not 0 <= number <= 100:
        raise ValueError("cloud_cover_max must be between 0 and 100")
    return number


def _validate_credential(name: str, value: str, maximum: int) -> None:
    if not 8 <= len(value) <= maximum:
        raise CopernicusError("COPERNICUS_CREDENTIAL_INVALID", f"invalid {name} length")
    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in value):
        raise CopernicusError("COPERNICUS_CREDENTIAL_INVALID", f"invalid {name} characters")


def credentials() -> tuple[str, str]:
    client_id = str(os.getenv(CLIENT_ID_ENV) or "").strip()
    client_secret = str(os.getenv(CLIENT_SECRET_ENV) or "").strip()
    if not client_id:
        raise CopernicusError(
            "COPERNICUS_CLIENT_ID_MISSING",
            f"missing repository Variable {CLIENT_ID_ENV}",
        )
    if not client_secret:
        raise CopernicusError(
            "COPERNICUS_CLIENT_SECRET_MISSING",
            f"missing repository Secret {CLIENT_SECRET_ENV}",
        )
    _validate_credential(CLIENT_ID_ENV, client_id, 512)
    _validate_credential(CLIENT_SECRET_ENV, client_secret, 2048)
    return client_id, client_secret


def _bounded_response(response: requests.Response, max_bytes: int) -> bytes:
    raw = response.raw.read(max_bytes + 1, decode_content=True)
    if len(raw) > max_bytes:
        raise CopernicusError(
            "COPERNICUS_RESPONSE_TOO_LARGE",
            f"response exceeds acceptance.max_response_bytes={max_bytes}",
        )
    if response.is_redirect:
        raise CopernicusError(
            "COPERNICUS_REDIRECT_REJECTED",
            f"upstream attempted HTTP {response.status_code} redirect",
        )
    return raw


def _request_json(
    method: str,
    url: str,
    *,
    timeout: int,
    max_bytes: int,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any] | None = None,
) -> tuple[Any, requests.Response, bytes]:
    response = requests.request(
        method,
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT, **dict(headers or {})},
        params=params,
        json=payload,
        timeout=timeout,
        allow_redirects=False,
        stream=True,
    )
    raw = _bounded_response(response, max_bytes)
    if not 200 <= response.status_code < 300:
        detail = raw[:1000].decode("utf-8", errors="replace")
        retryable = response.status_code == 429 or 500 <= response.status_code <= 599
        raise CopernicusError(
            "COPERNICUS_HTTP_ERROR",
            f"upstream HTTP {response.status_code}: {detail}",
            retryable=retryable,
        )
    try:
        data = json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CopernicusError("COPERNICUS_INVALID_JSON", "upstream returned invalid JSON") from exc
    return data, response, raw


def _oauth_token(timeout: int) -> str:
    client_id, client_secret = credentials()
    response = requests.post(
        IDENTITY_ORIGIN + OAUTH_ENDPOINT_PATH,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=timeout,
        allow_redirects=False,
    )
    raw = response.content
    if len(raw) > 1_000_000:
        raise CopernicusError("COPERNICUS_TOKEN_RESPONSE_TOO_LARGE", "token response too large")
    if response.is_redirect or not 200 <= response.status_code < 300:
        raise CopernicusError(
            "COPERNICUS_AUTH_FAILED",
            f"OAuth token endpoint HTTP {response.status_code}",
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise CopernicusError("COPERNICUS_AUTH_INVALID_JSON", "token endpoint returned invalid JSON") from exc
    token = str(payload.get("access_token") or "") if isinstance(payload, Mapping) else ""
    if not 32 <= len(token) <= 8192:
        raise CopernicusError("COPERNICUS_AUTH_TOKEN_INVALID", "token endpoint returned invalid access token")
    return token


def _search_payload(parameters: Mapping[str, Any]) -> dict[str, Any]:
    collection = _collection(parameters)
    bbox = _bbox(parameters)
    start, end = _time_range(parameters, max_days=366)
    payload: dict[str, Any] = {
        "collections": [collection],
        "bbox": bbox,
        "datetime": f"{start}/{end}",
        "limit": _limit(parameters),
        "sortby": [{"field": "datetime", "direction": "desc"}],
        "fields": {
            "include": [
                "properties.datetime",
                "properties.eo:cloud_cover",
                "properties.gsd",
                "properties.platform",
                "properties.constellation",
            ],
            "exclude": ["geometry"],
        },
    }
    cloud_cover = _cloud_cover(parameters)
    if cloud_cover is not None and collection.startswith("sentinel-2"):
        payload["query"] = {"eo:cloud_cover": {"lte": cloud_cover}}
    return payload


def _process_payload(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    bbox = _bbox(parameters)
    start, end = _time_range(parameters, max_days=90)
    width = int(parameters.get("width") or 1024)
    height = int(parameters.get("height") or 1024)
    if not 64 <= width <= 2048 or not 64 <= height <= 2048:
        raise ValueError("width and height must be between 64 and 2048")
    if width * height > 4_194_304:
        raise ValueError("output pixel count must not exceed 4194304")
    mosaicking_order = str(parameters.get("mosaicking_order") or "leastCC")
    if mosaicking_order not in {"leastCC", "mostRecent", "leastRecent"}:
        raise ValueError("mosaicking_order is invalid")
    evalscript = {
        "render-true-color-png": TRUE_COLOR_EVALSCRIPT,
        "render-false-color-png": FALSE_COLOR_EVALSCRIPT,
        "render-ndvi-png": NDVI_EVALSCRIPT,
    }[operation]
    return {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [
                {
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {"from": start, "to": end},
                        "mosaickingOrder": mosaicking_order,
                        "maxCloudCoverage": int(_cloud_cover(parameters) or 100),
                    },
                }
            ],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{"identifier": "default", "format": {"type": "image/png"}}],
        },
        "evalscript": evalscript,
    }


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=60,
        minimum=5,
        maximum=180,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=10_000_000,
        minimum=1024,
        maximum=30_000_000,
        name="max_response_bytes",
    )
    max_rows = bounded_int(
        acceptance.get("max_rows"),
        default=20,
        minimum=1,
        maximum=100,
        name="max_rows",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_COPERNICUS_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "provider": "copernicus-cdse",
        "requests_per_ticket_max": 2,
        "automatic_retry": False,
        "automatic_pagination": False,
        "write_operations_allowed": False,
        "secret_values_exposed": False,
        "user_agent": USER_AGENT,
        "attribution": "European Union, Copernicus Sentinel data",
    }
    token = ""
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
            metadata["credential_mode"] = "none"
        elif operation == "stac-list-collections":
            data, response, raw = _request_json(
                "GET",
                STAC_ORIGIN + "/v1/collections",
                timeout=timeout,
                max_bytes=max_bytes,
            )
            collections = data.get("collections", []) if isinstance(data, Mapping) else []
            if not isinstance(collections, list) or len(collections) > max_rows:
                raise CopernicusError(
                    "COPERNICUS_RESULT_TOO_MANY_ROWS",
                    f"collection result exceeds max_rows={max_rows}",
                )
            metadata.update({
                "upstream_called": True,
                "credential_mode": "none",
                "host": "stac.dataspace.copernicus.eu",
                "request_path": "/v1/collections",
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "result_rows": len(collections),
                "requests_used": 1,
            })
            snapshot = {"provider": "copernicus-cdse", "operation": operation, "data": data}
            (output_dir / "response.json").write_bytes(raw)
        elif operation == "stac-search-items":
            payload = _search_payload(parameters)
            data, response, raw = _request_json(
                "POST",
                STAC_ORIGIN + "/v1/search",
                timeout=timeout,
                max_bytes=max_bytes,
                headers={"Content-Type": "application/json"},
                payload=payload,
            )
            features = data.get("features", []) if isinstance(data, Mapping) else []
            if not isinstance(features, list) or len(features) > max_rows:
                raise CopernicusError(
                    "COPERNICUS_RESULT_TOO_MANY_ROWS",
                    f"search result exceeds max_rows={max_rows}",
                )
            metadata.update({
                "upstream_called": True,
                "credential_mode": "none",
                "host": "stac.dataspace.copernicus.eu",
                "request_path": "/v1/search",
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "result_rows": len(features),
                "requests_used": 1,
            })
            snapshot = {"provider": "copernicus-cdse", "operation": operation, "data": data}
            (output_dir / "response.json").write_bytes(raw)
        elif operation == "stac-get-item":
            collection = _collection(parameters)
            item_id = str(parameters.get("item_id") or "")
            if not ITEM_RE.fullmatch(item_id):
                raise ValueError("item_id is invalid")
            path = f"/v1/collections/{quote(collection, safe='-')}/items/{quote(item_id, safe='._-')}"
            data, response, raw = _request_json(
                "GET",
                STAC_ORIGIN + path,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            metadata.update({
                "upstream_called": True,
                "credential_mode": "none",
                "host": "stac.dataspace.copernicus.eu",
                "request_path": path,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "result_rows": 1,
                "requests_used": 1,
            })
            snapshot = {"provider": "copernicus-cdse", "operation": operation, "data": data}
            (output_dir / "response.json").write_bytes(raw)
        elif operation in RENDER_OPERATIONS:
            payload = _process_payload(operation, parameters)
            token = _oauth_token(timeout)
            response = requests.post(
                SENTINEL_HUB_ORIGIN + "/process/v1",
                headers={
                    "Accept": "image/png",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                    "User-Agent": USER_AGENT,
                },
                json=payload,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
            )
            raw = _bounded_response(response, max_bytes)
            if not 200 <= response.status_code < 300:
                detail = raw[:1000].decode("utf-8", errors="replace")
                raise CopernicusError(
                    "COPERNICUS_PROCESS_FAILED",
                    f"Processing API HTTP {response.status_code}: {detail}",
                    retryable=response.status_code == 429 or 500 <= response.status_code <= 599,
                )
            content_type = response.headers.get("Content-Type", "")
            if "image/png" not in content_type.lower() or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                raise CopernicusError("COPERNICUS_INVALID_PNG", "Processing API returned non-PNG content")
            (output_dir / "response.png").write_bytes(raw)
            metadata.update({
                "upstream_called": True,
                "credential_mode": "oauth-client-id-variable-plus-client-secret-backend-only",
                "host": "sh.dataspace.copernicus.eu",
                "request_path": "/process/v1",
                "http_status": response.status_code,
                "content_type": content_type,
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "requests_used": 2,
                "oauth_token_persisted": False,
            })
            snapshot = {
                "provider": "copernicus-cdse",
                "operation": operation,
                "collection": "sentinel-2-l2a",
                "bbox": parameters.get("bbox"),
                "start_time": parameters.get("start_time"),
                "end_time": parameters.get("end_time"),
                "response_file": "response.png",
                "response_bytes": len(raw),
                "attribution": metadata["attribution"],
            }
        else:
            raise ValueError(f"unsupported operation: {operation}")
        status = "INTEL_COPERNICUS_COMPLETED"
    except Exception as exc:
        message = str(exc)
        for value in (
            str(os.getenv(CLIENT_ID_ENV) or ""),
            str(os.getenv(CLIENT_SECRET_ENV) or ""),
            token,
        ):
            if value:
                message = message.replace(value, "[REDACTED]")
        failure = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "COPERNICUS_EXECUTION_ERROR"),
            "retryable": bool(getattr(exc, "retryable", False)),
            "message": message[:2000],
        }
    return finish_execution(
        ticket=ticket,
        output_dir=output_dir,
        status=status,
        snapshot=snapshot,
        metadata=metadata,
        failure=failure,
        started_at=started_at,
        started_perf=started_perf,
        schema_prefix="copernicus",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-copernicus]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="copernicus-ticket-status-v1",
            display_name="Copernicus Data Space",
        )
    )
