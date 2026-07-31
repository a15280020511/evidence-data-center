#!/usr/bin/env python3
"""Execute one validated API request plan through an approved API-center gateway."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import math
import json
import os
import platform
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SAFE_ENV_KEYS = (
    "GITHUB_REPOSITORY",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_SHA",
    "GITHUB_WORKFLOW",
    "GITHUB_JOB",
    "ISSUE_NUMBER",
)
ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def run_identity() -> dict[str, str | None]:
    return {key.lower(): os.getenv(key) for key in SAFE_ENV_KEYS}


def _path_get(value: Any, path: str) -> tuple[bool, Any]:
    """Read an allowlisted dotted path from mappings or JSON arrays.

    Numeric path tokens select sequence indexes, which is required for public
    APIs such as World Bank that return ``[metadata, rows]`` at the root.
    """
    current = value
    for token in path.split("."):
        if isinstance(current, Mapping) and token in current:
            current = current[token]
            continue
        if isinstance(current, (list, tuple)) and token.isdigit():
            index = int(token)
            if 0 <= index < len(current):
                current = current[index]
                continue
        return False, None
    return True, current


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, bytes, list, tuple, dict, set)):
        return len(value) > 0
    return True


def evaluate_response_contract(
    payload: Any,
    contract: Mapping[str, Any],
    *,
    allow_empty: bool,
) -> dict[str, Any]:
    if not isinstance(payload, (Mapping, list, tuple)):
        return {
            "success": False,
            "state": "invalid_payload",
            "message": "response payload is not a JSON object or array",
            "business_status": None,
            "business_code": None,
            "data_present": False,
        }
    status_path = contract.get("status_path")
    exists = False
    business_status = None
    if status_path:
        exists, business_status = _path_get(payload, str(status_path))
    success_values = list(contract.get("success_values") or [])
    code = None
    message = ""
    error_code_path = contract.get("error_code_path")
    if error_code_path:
        _, code = _path_get(payload, str(error_code_path))
    message_path = contract.get("message_path")
    if message_path:
        _, raw_message = _path_get(payload, str(message_path))
        message = str(raw_message or "")
    paths = [str(item) for item in contract.get("any_data_paths", [])]
    data_present = True if not paths else any(
        item_exists and _nonempty(item)
        for item_exists, item in (_path_get(payload, path) for path in paths)
    )
    if contract.get("success_when_data_present") is True:
        successful = data_present or allow_empty
        business_status = "data_present" if data_present else "data_absent_allowed"
    else:
        successful = exists and business_status in success_values
    if not successful:
        return {
            "success": False,
            "state": "business_error",
            "message": message or "upstream business status is not successful",
            "business_status": business_status,
            "business_code": code,
            "data_present": data_present,
        }
    if not data_present and not allow_empty:
        return {
            "success": False,
            "state": "empty",
            "message": "business request succeeded but no accepted data path is non-empty",
            "business_status": business_status,
            "business_code": code,
            "data_present": False,
        }
    return {
        "success": True,
        "state": "success" if data_present else "success_empty",
        "message": message,
        "business_status": business_status,
        "business_code": code,
        "data_present": data_present,
    }


def _haversine_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    radius = 6371.0088
    lat1, lat2 = math.radians(latitude_a), math.radians(latitude_b)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(longitude_b - longitude_a)
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(value)))


def _location_candidates(connector_id: str, payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    if connector_id == "osm-nominatim-search":
        for feature in payload.get("features") or []:
            if not isinstance(feature, Mapping):
                continue
            geometry = feature.get("geometry") if isinstance(feature.get("geometry"), Mapping) else {}
            coordinates = geometry.get("coordinates")
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                continue
            try:
                longitude = float(coordinates[0])
                latitude = float(coordinates[1])
            except (TypeError, ValueError):
                continue
            text = json.dumps(feature.get("properties") or {}, ensure_ascii=False)
            rows.append({"latitude": latitude, "longitude": longitude, "text": text})
    elif connector_id == "amap-geocode":
        for item in payload.get("geocodes") or []:
            if not isinstance(item, Mapping):
                continue
            parts = str(item.get("location") or "").split(",")
            if len(parts) != 2:
                continue
            try:
                longitude, latitude = float(parts[0]), float(parts[1])
            except ValueError:
                continue
            text = " ".join(
                str(item.get(key) or "")
                for key in ("formatted_address", "province", "city", "district", "adcode")
            )
            rows.append({"latitude": latitude, "longitude": longitude, "text": text})
    return rows


def evaluate_response_quality(payload: Any, request_row: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "possibly_truncated": False,
        "location_check_applied": False,
        "blocking_failure": False,
    }
    policy = request_row.get("response_quality")
    if isinstance(policy, Mapping):
        exists, collection = _path_get(payload, str(policy.get("collection_path") or ""))
        if exists and isinstance(collection, list):
            returned = len(collection)
            hard_limit = int(policy.get("hard_limit") or 0)
            result.update({
                "returned_count": returned,
                "hard_limit": hard_limit,
                "possibly_truncated": bool(hard_limit and returned >= hard_limit),
            })
            if result["possibly_truncated"]:
                result["recommended_action"] = str(policy.get("recommended_action") or "")
    checks = request_row.get("quality_checks")
    expected = checks.get("expected_location") if isinstance(checks, Mapping) else None
    if isinstance(expected, Mapping):
        result["location_check_applied"] = True
        candidates = _location_candidates(str(request_row.get("connector_id") or ""), payload)
        tokens = [str(item).casefold() for item in expected.get("admin_tokens") or []]
        scored = []
        for candidate in candidates:
            text = str(candidate.get("text") or "").casefold()
            admin_match = all(token in text for token in tokens)
            distance = _haversine_km(
                float(expected["latitude"]),
                float(expected["longitude"]),
                float(candidate["latitude"]),
                float(candidate["longitude"]),
            )
            scored.append({**candidate, "distance_km": distance, "admin_match": admin_match})
        eligible = [item for item in scored if item["admin_match"]]
        nearest = min(eligible or scored, key=lambda item: item["distance_km"], default=None)
        maximum = float(expected["max_distance_km"])
        matched = bool(nearest and nearest["admin_match"] and nearest["distance_km"] <= maximum)
        result.update({
            "candidate_count": len(scored),
            "nearest_distance_km": None if nearest is None else round(float(nearest["distance_km"]), 6),
            "max_distance_km": maximum,
            "admin_tokens": tokens,
            "location_match": matched,
            "blocking_failure": not matched,
            "failure_state": "quality_mismatch" if scored else "quality_unverifiable",
            "message": (
                "location candidates do not match the expected coordinates/administrative area"
                if scored
                else "response contains no supported location candidate"
            ),
        })
    return result


def _gateway_url(base_url: str, endpoint: str, parameters: Mapping[str, Any]) -> str:
    if (
        not endpoint.startswith("/data/")
        or "{" in endpoint
        or "}" in endpoint
        or "?" in endpoint
        or "#" in endpoint
        or "\\" in endpoint
    ):
        raise ValueError("gateway endpoint must be a concrete allowlisted /data route")
    base = base_url.rstrip("/")
    query_values: dict[str, str] = {}
    for key, value in parameters.items():
        if isinstance(value, bool):
            query_values[str(key)] = "true" if value else "false"
        else:
            query_values[str(key)] = str(value)
    query = urllib.parse.urlencode(query_values, doseq=False)
    return f"{base}{endpoint}" + (f"?{query}" if query else "")


def validate_gateway_base_url(base_url: str, mode: str) -> str:
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("gateway base URL must not contain credentials, query, or fragment")
    if not parsed.hostname:
        raise ValueError("gateway base URL has no hostname")
    host = parsed.hostname.casefold()
    if mode == "ephemeral":
        if parsed.scheme != "http" or host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("ephemeral gateway must use a loopback HTTP URL")
    elif mode == "remote":
        if parsed.scheme != "https":
            raise ValueError("remote gateway must use HTTPS")
        blocked_names = {"localhost", "metadata.google.internal", "metadata.azure.internal", "instance-data"}
        if host in blocked_names or host.endswith((".local", ".internal", ".localhost", ".svc", ".cluster.local")):
            raise ValueError("remote gateway hostname is internal or reserved")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address and (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_unspecified
            or address.is_multicast
        ):
            raise ValueError("remote gateway must not use a private or reserved literal IP")
    elif mode == "blocked":
        return base_url
    else:
        raise ValueError(f"unsupported gateway mode: {mode}")
    return base_url.rstrip("/")


def resolve_mode(plan: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    remote_url = str(os.getenv("API_GATEWAY_BASE_URL") or "").strip()
    remote_token = str(os.getenv("API_GATEWAY_AUTH_TOKEN") or "").strip()
    required = [str(item) for item in plan.get("required_secret_environment_variables", [])]
    result: dict[str, Any]
    if remote_url and remote_token:
        result = {
            "mode": "remote",
            "base_url": validate_gateway_base_url(remote_url, "remote"),
            "reason": "configured authenticated remote API gateway",
            "required_secret_count": len(required),
            "secret_source": "remote_gateway",
        }
    elif remote_url and not remote_token:
        result = {
            "mode": "blocked",
            "base_url": "",
            "reason": "remote API gateway is configured without API_GATEWAY_AUTH_TOKEN",
            "required_secret_count": len(required),
            "secret_source": "remote_gateway",
        }
    else:
        resolved: dict[str, str] = {}
        for name in required:
            if not ENV_NAME_RE.fullmatch(name):
                raise ValueError(f"invalid secret environment variable name: {name}")
            direct = os.getenv(name)
            if isinstance(direct, str) and direct:
                resolved[name] = direct
        missing = [name for name in required if name not in resolved]
        if missing:
            result = {
                "mode": "blocked",
                "base_url": "",
                "reason": "missing dedicated Repository Secret values",
                "missing_secret_environment_variables": missing,
                "required_secret_count": len(required),
                "secret_source": "dedicated_environment_variables",
            }
        else:
            temp_root = Path(os.getenv("RUNNER_TEMP") or "/tmp")
            temp_root.mkdir(parents=True, exist_ok=True)
            suffix = os.getenv("GITHUB_RUN_ID") or str(os.getpid())
            env_file = temp_root / f"api-center-runtime-{suffix}.env"
            lines: list[str] = []
            for name in required:
                value = resolved[name]
                if "\n" in value or "\r" in value or "\x00" in value:
                    raise ValueError(f"secret {name} contains a forbidden control character")
                lines.append(f"{name}={value}")
            env_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            env_file.chmod(0o600)
            result = {
                "mode": "ephemeral",
                "base_url": "http://127.0.0.1:18080",
                "reason": "ephemeral loopback gateway with dedicated Repository Secrets",
                "env_file": str(env_file),
                "required_secret_count": len(required),
                "secret_source": "dedicated_environment_variables",
            }
    public_result = {key: value for key, value in result.items() if key != "env_file"}
    write_json(output_dir / "gateway-mode.json", public_result)
    for name in ("mode", "base_url", "reason"):
        write_output(name, result.get(name, ""))
    write_output("env_file", result.get("env_file", ""))
    return result


def _fetch_one(
    *,
    base_url: str,
    auth_token: str,
    mode: str,
    request_row: Mapping[str, Any],
    timeout_seconds: int,
    max_attempts: int,
    max_bytes: int,
) -> dict[str, Any]:
    endpoint = str(request_row["endpoint"])
    parameters = dict(request_row.get("parameters") or {})
    url = _gateway_url(base_url, endpoint, parameters)
    attempts: list[dict[str, Any]] = []
    final_payload: Any = None
    final_headers: dict[str, str] = {}
    final_status: int | None = None
    error_type = ""
    error_message = ""

    for attempt in range(1, max_attempts + 1):
        started = time.perf_counter()
        headers = {
            "Accept": "application/json",
            "User-Agent": "independent-api-center-ticket/1",
        }
        if mode == "remote" and auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        outbound = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(outbound, timeout=timeout_seconds) as response:
                final_status = int(response.status)
                final_headers = {
                    "content-type": str(response.headers.get("Content-Type") or ""),
                    "date": str(response.headers.get("Date") or ""),
                    "cache-control": str(response.headers.get("Cache-Control") or ""),
                    "retry-after": str(response.headers.get("Retry-After") or ""),
                }
                raw = response.read(max_bytes + 1)
                if len(raw) > max_bytes:
                    raise ValueError(
                        f"response exceeds max_response_bytes_per_request={max_bytes}"
                    )
                final_payload = json.loads(raw.decode("utf-8"))
                attempts.append(
                    {
                        "attempt": attempt,
                        "http_status": final_status,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                        "outcome": "response",
                    }
                )
                break
        except urllib.error.HTTPError as exc:
            final_status = int(exc.code)
            final_headers = {
                "content-type": str(exc.headers.get("Content-Type") or "") if exc.headers else "",
                "date": str(exc.headers.get("Date") or "") if exc.headers else "",
                "retry-after": str(exc.headers.get("Retry-After") or "") if exc.headers else "",
            }
            body = exc.read(max_bytes + 1)
            if len(body) <= max_bytes and body:
                try:
                    final_payload = json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    final_payload = None
            error_type = type(exc).__name__
            error_message = str(exc)
            attempts.append(
                {
                    "attempt": attempt,
                    "http_status": final_status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                    "outcome": "http_error",
                }
            )
            if final_status not in TRANSIENT_HTTP or attempt >= max_attempts:
                break
        except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            error_type = type(exc).__name__
            error_message = str(exc)
            attempts.append(
                {
                    "attempt": attempt,
                    "http_status": final_status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                    "outcome": "network_or_payload_error",
                }
            )
            if attempt >= max_attempts:
                break
        if attempt < max_attempts:
            time.sleep(float(attempt))

    contract_result: dict[str, Any]
    if final_status is None:
        contract_result = {
            "success": False,
            "state": "network_error",
            "message": error_message or "no HTTP response",
            "business_status": None,
            "business_code": None,
            "data_present": False,
        }
    elif not 200 <= final_status < 300:
        contract_result = {
            "success": False,
            "state": "http_error",
            "message": error_message or f"HTTP {final_status}",
            "business_status": None,
            "business_code": None,
            "data_present": False,
        }
    elif final_payload is None:
        contract_result = {
            "success": False,
            "state": "invalid_json",
            "message": error_message or "response is not valid UTF-8 JSON",
            "business_status": None,
            "business_code": None,
            "data_present": False,
        }
    else:
        contract_result = evaluate_response_contract(
            final_payload,
            dict(request_row["response_contract"]),
            allow_empty=bool(request_row.get("allow_empty")),
        )
    quality = evaluate_response_quality(final_payload, request_row)
    if quality.get("blocking_failure") and contract_result.get("success"):
        contract_result = {
            "success": False,
            "state": str(quality.get("failure_state") or "quality_mismatch"),
            "message": str(quality.get("message") or "response quality check failed"),
            "business_status": contract_result.get("business_status"),
            "business_code": contract_result.get("business_code"),
            "data_present": contract_result.get("data_present", False),
        }
    return {
        "request_id": str(request_row["request_id"]),
        "connector_id": str(request_row["connector_id"]),
        "connector_sha256": str(request_row["connector_sha256"]),
        "endpoint": endpoint,
        "parameters": parameters,
        "observed_at": utc_now(),
        "http_status": final_status,
        "response_headers": final_headers,
        "attempts": attempts,
        "attempt_count": len(attempts),
        "state": contract_result["state"],
        "success": bool(contract_result["success"]),
        "business_status": contract_result["business_status"],
        "business_code": contract_result["business_code"],
        "message": contract_result["message"],
        "data_present": bool(contract_result["data_present"]),
        "quality": quality,
        "response": final_payload,
        "error_type": error_type or None,
    }


def _diagnostics(
    *,
    status: str,
    plan: Mapping[str, Any],
    gateway_mode: str,
    results: list[Mapping[str, Any]],
    primary_failure: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "api-ticket-diagnostics-v1",
        "created_at": utc_now(),
        "status": status,
        "task_id": str(plan.get("task_id") or ""),
        "ticket_sha256": str(plan.get("ticket_sha256") or ""),
        "gateway_mode": gateway_mode,
        "primary_failure": dict(primary_failure),
        "stage_status": {
            "validate_ticket": "PASS",
            "resolve_gateway": "PASS" if gateway_mode != "blocked" else "BLOCKED",
            "execute_requests": (
                "PASS"
                if status == "API_COMPLETED"
                else ("PARTIAL" if status == "API_PARTIAL" else "FAIL")
            ),
            "write_snapshot": "PASS",
            "write_manifest": "NOT_STARTED",
        },
        "request_state_counts": _counts(results),
        "run_identity": run_identity(),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "security": {
            "secret_values_included": False,
            "authorization_header_recorded": False,
            "arbitrary_urls_allowed": False,
            "ticket_requires_public_non_personal_data": True,
            "environment_allowlist": [key.lower() for key in SAFE_ENV_KEYS],
        },
    }


def _counts(results: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in results:
        key = str(item.get("state") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def execute(plan_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan = load_json(plan_path)
    if not isinstance(plan, Mapping):
        raise ValueError("request plan root must be an object")
    mode = str(os.getenv("API_GATEWAY_MODE") or "blocked")
    base_url = str(os.getenv("API_GATEWAY_BASE_URL") or "")
    auth_token = str(os.getenv("API_GATEWAY_AUTH_TOKEN") or "")
    started_at = utc_now()
    started = time.perf_counter()

    if mode == "blocked":
        results: list[dict[str, Any]] = []
        status = "API_BLOCKED"
        primary_failure = {
            "code": "API_GATEWAY_NOT_CONFIGURED",
            "stage": "resolve_gateway",
            "message": str(os.getenv("API_GATEWAY_BLOCK_REASON") or "no usable gateway mode"),
            "retryable": False,
        }
    else:
        base_url = validate_gateway_base_url(base_url, mode)
        acceptance = dict(plan["acceptance"])
        results = [
            _fetch_one(
                base_url=base_url,
                auth_token=auth_token,
                mode=mode,
                request_row=dict(row),
                timeout_seconds=int(acceptance["timeout_seconds"]),
                max_attempts=int(acceptance["max_attempts"]),
                max_bytes=int(acceptance["max_response_bytes_per_request"]),
            )
            for row in plan["requests"]
        ]
        successful = sum(bool(item["success"]) for item in results)
        required = int(acceptance["minimum_successful_requests"])
        if successful == len(results):
            status = "API_COMPLETED"
        elif successful >= required:
            status = "API_PARTIAL"
        else:
            status = "API_FAILED"
        failed = next((item for item in results if not item["success"]), None)
        primary_failure = (
            {
                "code": "NONE",
                "stage": "complete",
                "message": "",
                "retryable": False,
            }
            if status == "API_COMPLETED"
            else {
                "code": f"API_REQUEST_{str((failed or {}).get('state') or 'FAILED').upper()}",
                "stage": "execute_requests",
                "message": str((failed or {}).get("message") or "one or more API requests failed"),
                "request_id": (failed or {}).get("request_id"),
                "retryable": str((failed or {}).get("state")) in {"network_error", "http_error"},
            }
        )

    successful_count = sum(bool(item.get("success")) for item in results)
    snapshot = {
        "schema_version": "api-snapshot-v1",
        "created_at": utc_now(),
        "started_at": started_at,
        "status": status,
        "task_id": str(plan.get("task_id") or ""),
        "objective": str(plan.get("objective") or ""),
        "ticket_sha256": str(plan.get("ticket_sha256") or ""),
        "gateway_mode": mode,
        "data_policy": dict(plan.get("data_policy") or {}),
        "request_count": len(plan.get("requests") or []),
        "successful_request_count": successful_count,
        "failed_request_count": len(results) - successful_count,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "requests": results,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    write_json(output_dir / "api-snapshot.json", snapshot)

    audit = {
        "schema_version": "api-audit-v1",
        "created_at": utc_now(),
        "status": "PASS" if status in {"API_COMPLETED", "API_PARTIAL"} else status,
        "task_id": snapshot["task_id"],
        "ticket_sha256": snapshot["ticket_sha256"],
        "request_plan_sha256": canonical_sha(plan),
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "gateway_mode": mode,
        "request_count": snapshot["request_count"],
        "successful_request_count": successful_count,
        "external_data_fetch_attempts": sum(int(item.get("attempt_count") or 0) for item in results),
        "model_calls": 0,
        "arbitrary_urls_allowed": False,
        "connector_ids": [str(item.get("connector_id")) for item in results],
        "run_identity": run_identity(),
        "secret_values_included": False,
    }
    write_json(output_dir / "api-audit.json", audit)
    diagnostics = _diagnostics(
        status=status,
        plan=plan,
        gateway_mode=mode,
        results=results,
        primary_failure=primary_failure,
    )
    write_json(output_dir / "api-diagnostics.json", diagnostics)
    summary_lines = [
        f"# {status}",
        "",
        f"- Task ID: `{snapshot['task_id']}`",
        f"- Gateway mode: `{mode}`",
        f"- Requests: `{snapshot['request_count']}`",
        f"- Successful: `{successful_count}`",
        f"- Failed: `{snapshot['failed_request_count']}`",
        f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
        f"- Primary error: `{primary_failure.get('code')}`",
    ]
    (output_dir / "api-summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    for name, value in (
        ("status", status),
        ("successful_count", successful_count),
        ("request_count", snapshot["request_count"]),
        ("snapshot_sha256", snapshot["snapshot_sha256"]),
        ("error_code", primary_failure.get("code") or "NONE"),
    ):
        write_output(name, value)
    print(
        json.dumps(
            {
                "status": status,
                "task_id": snapshot["task_id"],
                "successful_request_count": successful_count,
                "request_count": snapshot["request_count"],
                "snapshot_sha256": snapshot["snapshot_sha256"],
                "primary_failure": primary_failure,
            },
            ensure_ascii=False,
        )
    )
    return 0 if status in {"API_COMPLETED", "API_PARTIAL"} else 3 if status == "API_BLOCKED" else 2


def finalize(output_dir: Path) -> int:
    diagnostics_path = output_dir / "api-diagnostics.json"
    if diagnostics_path.is_file():
        diagnostics = load_json(diagnostics_path)
        if isinstance(diagnostics, Mapping):
            diagnostics = dict(diagnostics)
            stage_status = dict(diagnostics.get("stage_status") or {})
            stage_status["write_manifest"] = "PASS"
            diagnostics["stage_status"] = stage_status
            write_json(diagnostics_path, diagnostics)
    rows: list[dict[str, Any]] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name in {
            "artifact-manifest.json",
            "api-center-runtime.env",
        }:
            continue
        rows.append(
            {
                "path": str(path.relative_to(output_dir)),
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "modified_at": datetime.fromtimestamp(
                    path.stat().st_mtime, timezone.utc
                ).isoformat(),
            }
        )
    manifest = {
        "schema_version": "artifact-manifest-v1",
        "created_at": utc_now(),
        "files": rows,
        "excluded_files": ["artifact-manifest.json", "api-center-runtime.env"],
        "secret_values_included": False,
    }
    write_json(output_dir / "artifact-manifest.json", manifest)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    mode_parser = sub.add_parser("resolve-mode")
    mode_parser.add_argument("--plan", required=True)
    mode_parser.add_argument("--output-dir", default="api-artifacts")
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--plan", required=True)
    execute_parser.add_argument("--output-dir", default="api-artifacts")
    finalize_parser = sub.add_parser("finalize")
    finalize_parser.add_argument("--output-dir", default="api-artifacts")
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "resolve-mode":
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            plan = load_json(Path(args.plan))
            resolve_mode(plan, output_dir)
        except Exception as exc:  # noqa: BLE001 - convert configuration errors to BLOCKED
            result = {
                "mode": "blocked",
                "base_url": "",
                "reason": f"{type(exc).__name__}: {exc}",
            }
            write_json(output_dir / "gateway-mode.json", result)
            for name in ("mode", "base_url", "reason"):
                write_output(name, result[name])
            write_output("env_file", "")
        return 0
    if args.command == "execute":
        return execute(Path(args.plan), Path(args.output_dir))
    if args.command == "finalize":
        return finalize(Path(args.output_dir))
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
