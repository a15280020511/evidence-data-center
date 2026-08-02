#!/usr/bin/env python3
"""Bounded read-only OpenSky Network execution for Intelligence Center tickets."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

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
API_ORIGIN = "https://opensky-network.org"
AUTH_ENDPOINT = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
CLIENT_ID_ENV = "OPEN_SKY_CLIENT_ID"
CLIENT_SECRET_ENV = "OPEN_SKY_CLIENT_SECRET"

ICAO24_RE = re.compile(r"^[0-9a-f]{6}$")
AIRPORT_RE = re.compile(r"^[A-Z0-9]{4}$")
AUTH_REQUIRED = {
    "states-recent",
    "states-own",
    "flights-interval",
    "flights-aircraft",
    "airport-arrivals",
    "airport-departures",
    "track-aircraft",
}
FLIGHT_LIST_OPERATIONS = {
    "flights-interval",
    "flights-aircraft",
    "airport-arrivals",
    "airport-departures",
}


def _now_epoch() -> int:
    return int(time.time())


def _int_value(parameters: Mapping[str, Any], key: str, *, required: bool = False) -> int | None:
    raw = parameters.get(key)
    if raw in (None, ""):
        if required:
            raise ValueError(f"{key} is required")
        return None
    if isinstance(raw, bool):
        raise ValueError(f"{key} must be an integer")
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value


def _icao24_values(parameters: Mapping[str, Any], *, required: bool = False, maximum: int = 20) -> list[str]:
    raw = parameters.get("icao24")
    if raw in (None, []):
        if required:
            raise ValueError("icao24 is required")
        return []
    if not isinstance(raw, list) or not raw or len(raw) > maximum:
        raise ValueError(f"icao24 must contain 1 to {maximum} values")
    values = [str(item).lower() for item in raw]
    if len(values) != len(set(values)) or any(not ICAO24_RE.fullmatch(value) for value in values):
        raise ValueError("icao24 contains an invalid or duplicate address")
    return values


def _serial_values(parameters: Mapping[str, Any], *, required: bool = False, maximum: int = 10) -> list[int]:
    raw = parameters.get("serials")
    if raw in (None, []):
        if required:
            raise ValueError("serials is required")
        return []
    if not isinstance(raw, list) or not raw or len(raw) > maximum:
        raise ValueError(f"serials must contain 1 to {maximum} values")
    values: list[int] = []
    for item in raw:
        if isinstance(item, bool):
            raise ValueError("serials contains an invalid value")
        try:
            value = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError("serials contains an invalid value") from exc
        if value <= 0 or value > 2_147_483_647:
            raise ValueError("serials contains an out-of-range value")
        values.append(value)
    if len(values) != len(set(values)):
        raise ValueError("serials must be unique")
    return values


def _bbox(parameters: Mapping[str, Any]) -> list[tuple[str, str]]:
    keys = ("lamin", "lomin", "lamax", "lomax")
    present = [key for key in keys if parameters.get(key) is not None]
    if not present:
        return []
    if len(present) != 4:
        raise ValueError("lamin, lomin, lamax and lomax must be supplied together")
    try:
        lamin, lomin, lamax, lomax = (float(parameters[key]) for key in keys)
    except (TypeError, ValueError) as exc:
        raise ValueError("bounding box coordinates must be numbers") from exc
    if not (-90 <= lamin < lamax <= 90 and -180 <= lomin < lomax <= 180):
        raise ValueError("bounding box coordinates are invalid")
    area = (lamax - lamin) * (lomax - lomin)
    if area > 400:
        raise ValueError("bounding box area must not exceed 400 square degrees")
    return [(key, f"{value:.6f}".rstrip("0").rstrip(".")) for key, value in zip(keys, (lamin, lomin, lamax, lomax))]


def _extended(parameters: Mapping[str, Any]) -> list[tuple[str, str]]:
    raw = parameters.get("extended")
    if raw is None:
        return []
    if not isinstance(raw, bool):
        raise ValueError("extended must be boolean")
    return [("extended", "1" if raw else "0")]


def _interval(parameters: Mapping[str, Any], *, max_seconds: int, require_past_day: bool) -> tuple[int, int]:
    begin = _int_value(parameters, "begin", required=True)
    end = _int_value(parameters, "end", required=True)
    assert begin is not None and end is not None
    if begin >= end:
        raise ValueError("begin must be earlier than end")
    if end - begin > max_seconds:
        raise ValueError(f"time interval must not exceed {max_seconds} seconds")
    now = _now_epoch()
    if end > now + 60:
        raise ValueError("end must not be in the future")
    if require_past_day:
        day_start = int(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        if end > day_start:
            raise ValueError("this batch endpoint only exposes the previous UTC day or earlier")
    return begin, end


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, list[tuple[str, str]], bool]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, [], False

    if operation in {"states-current", "states-recent"}:
        query: list[tuple[str, str]] = []
        icaos = _icao24_values(parameters, maximum=20)
        bbox = _bbox(parameters)
        if not icaos and not bbox:
            raise ValueError("states queries require an ICAO24 filter or a bounded area")
        query.extend(("icao24", value) for value in icaos)
        query.extend(bbox)
        query.extend(_extended(parameters))
        if operation == "states-recent":
            requested = _int_value(parameters, "time", required=True)
            assert requested is not None
            now = _now_epoch()
            if requested < now - 3600 or requested > now + 60:
                raise ValueError("authenticated state time must be within the last hour")
            query.append(("time", str(requested)))
            return "/api/states/all", query, True
        if parameters.get("time") not in (None, 0, "0"):
            raise ValueError("states-current does not accept historical time")
        return "/api/states/all", query, False

    if operation == "states-own":
        icaos = _icao24_values(parameters, maximum=20)
        serials = _serial_values(parameters, maximum=10)
        if not icaos and not serials:
            raise ValueError("states-own requires an ICAO24 or receiver serial filter")
        query = [("icao24", value) for value in icaos]
        query.extend(("serials", str(value)) for value in serials)
        requested = _int_value(parameters, "time")
        if requested is not None:
            query.append(("time", str(requested)))
        return "/api/states/own", query, True

    if operation == "flights-interval":
        begin, end = _interval(parameters, max_seconds=7200, require_past_day=False)
        return "/api/flights/all", [("begin", str(begin)), ("end", str(end))], True

    if operation == "flights-aircraft":
        icao = _icao24_values(parameters, required=True, maximum=1)[0]
        begin, end = _interval(parameters, max_seconds=172800, require_past_day=True)
        return "/api/flights/aircraft", [("icao24", icao), ("begin", str(begin)), ("end", str(end))], True

    if operation in {"airport-arrivals", "airport-departures"}:
        airport = str(parameters.get("airport") or "").upper()
        if not AIRPORT_RE.fullmatch(airport):
            raise ValueError("airport must be a four-character ICAO airport identifier")
        begin, end = _interval(parameters, max_seconds=172800, require_past_day=True)
        suffix = "arrival" if operation == "airport-arrivals" else "departure"
        return f"/api/flights/{suffix}", [("airport", airport), ("begin", str(begin)), ("end", str(end))], True

    if operation == "track-aircraft":
        icao = _icao24_values(parameters, required=True, maximum=1)[0]
        requested = _int_value(parameters, "time", required=True)
        assert requested is not None
        now = _now_epoch()
        if requested != 0 and (requested < now - 30 * 86400 or requested > now + 60):
            raise ValueError("track time must be live (0) or within the last 30 days")
        return "/api/tracks/all", [("icao24", icao), ("time", str(requested))], True

    raise ValueError(f"unsupported operation: {operation}")


def _credentials() -> tuple[str, str]:
    client_id = str(os.environ.get(CLIENT_ID_ENV) or "").strip()
    client_secret = str(os.environ.get(CLIENT_SECRET_ENV) or "").strip()
    if bool(client_id) != bool(client_secret):
        raise RuntimeError(f"{CLIENT_ID_ENV} and {CLIENT_SECRET_ENV} must be configured together")
    return client_id, client_secret


def _token(client_id: str, client_secret: str, timeout: int) -> str:
    response = requests.post(
        AUTH_ENDPOINT,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "intelligence-center-opensky/1",
        },
        timeout=timeout,
        allow_redirects=False,
    )
    raw = bytes(response.content or b"")
    if len(raw) > 1_000_000:
        raise RuntimeError("OpenSky OAuth response exceeded 1 MB")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("OpenSky OAuth returned invalid JSON") from exc
    if not response.ok:
        raise RuntimeError(f"OpenSky OAuth HTTP {response.status_code}: {str(payload)[:800]}")
    token = str(payload.get("access_token") or "")
    if not token or len(token) > 10000:
        raise RuntimeError("OpenSky OAuth response did not contain a valid access token")
    return token


def _scrub(value: Any, secrets: list[str]) -> Any:
    if isinstance(value, str):
        clean = value
        for secret in secrets:
            if secret:
                clean = clean.replace(secret, "[REDACTED]")
        return clean
    if isinstance(value, list):
        return [_scrub(item, secrets) for item in value]
    if isinstance(value, Mapping):
        return {str(_scrub(key, secrets)): _scrub(item, secrets) for key, item in value.items()}
    return value


def _row_count(operation: str, payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        if operation.startswith("states-"):
            states = payload.get("states")
            return len(states) if isinstance(states, list) else 0
        if operation == "track-aircraft":
            path = payload.get("path")
            return len(path) if isinstance(path, list) else 0
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
        acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=60, name="timeout_seconds"
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
    status = "INTEL_OPENSKY_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    client_id = ""
    client_secret = ""
    access_token = ""
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "opensky-network.org",
        "api_version": "REST 1.4",
        "credential_mode": "oauth2_client_credentials_or_anonymous_current_states",
        "client_id_environment_variable": CLIENT_ID_ENV,
        "client_secret_environment_variable": CLIENT_SECRET_ENV,
        "secret_values_exposed": False,
        "business_requests_per_ticket": 1,
        "network_requests_per_ticket_max": 2,
        "automatic_retry": False,
        "automatic_pagination": False,
        "global_state_query_allowed": False,
        "trino_historical_access_enabled": False,
    }
    try:
        path, query, auth_required = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            client_id, client_secret = _credentials()
            use_auth = auth_required or bool(client_id)
            if auth_required and not client_id:
                raise RuntimeError(f"{CLIENT_ID_ENV} and {CLIENT_SECRET_ENV} are required for {operation}")
            headers = {"Accept": "application/json", "User-Agent": "intelligence-center-opensky/1"}
            if use_auth:
                access_token = _token(client_id, client_secret, timeout)
                headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(
                API_ORIGIN + path,
                params=query,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if response.status_code == 404 and operation in FLIGHT_LIST_OPERATIONS:
                payload: Any = []
            elif response.status_code == 404 and operation == "track-aircraft":
                payload = {}
            else:
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise RuntimeError("OpenSky returned invalid JSON") from exc
            clean = _scrub(payload, [client_secret, access_token])
            if not response.ok and response.status_code != 404:
                raise RuntimeError(f"OpenSky HTTP {response.status_code}: {str(clean)[:1200]}")
            sanitized = (json.dumps(clean, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
            if len(sanitized) > max_bytes:
                raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(sanitized)
            snapshot = {
                "provider": "opensky-network",
                "operation": operation,
                "row_count": _row_count(operation, clean),
                "data": clean,
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "oauth_token_request_used": use_auth,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_path": path,
                    "query_parameter_names": sorted({name for name, _ in query}),
                    "response_bytes": len(sanitized),
                    "response_sha256": bytes_sha(sanitized),
                    "row_count": _row_count(operation, clean),
                    "rate_limit_remaining": response.headers.get("X-Rate-Limit-Remaining", ""),
                    "rate_limit_retry_after_seconds": response.headers.get(
                        "X-Rate-Limit-Retry-After-Seconds", ""
                    ),
                }
            )
        status = "INTEL_OPENSKY_COMPLETED"
    except Exception as exc:
        message = str(exc)
        for secret in (client_secret, access_token):
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
        schema_prefix="opensky-network",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-opensky]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="opensky-network-ticket-status-v1",
            display_name="OpenSky Network",
        )
    )
