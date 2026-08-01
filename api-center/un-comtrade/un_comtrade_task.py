#!/usr/bin/env python3
"""Bounded read-only UN Comtrade execution for Intelligence Center tickets."""
from __future__ import annotations

import json
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
ORIGIN = "https://comtradeapi.un.org"
SECRET_ENV = "UN_COMTRADE_API_KEY"
CLASSIFICATION_RE = re.compile(r"^[A-Z][A-Z0-9]{0,7}$")
COMMODITY_RE = re.compile(r"^(?:TOTAL|[A-Za-z0-9.]{1,20})$")
FLOW_RE = re.compile(r"^[A-Z][A-Z0-9]{0,5}$")
GENERIC_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
PERIOD_RE = re.compile(r"^(?:[0-9]{4}|[0-9]{6})$")
KEYLESS_OPERATIONS = {"catalog-capabilities", "preview-trade", "reporters-reference", "partners-reference"}


def _type_frequency_classification(parameters: Mapping[str, Any]) -> tuple[str, str, str]:
    type_code = str(parameters.get("type_code") or "").upper()
    frequency = str(parameters.get("frequency") or "").upper()
    classification = str(parameters.get("classification") or "").upper()
    if type_code not in {"C", "S"}:
        raise ValueError("type_code must be C or S")
    if frequency not in {"A", "M"}:
        raise ValueError("frequency must be A or M")
    if not CLASSIFICATION_RE.fullmatch(classification):
        raise ValueError("classification is invalid")
    return type_code, frequency, classification


def _integer_codes(
    parameters: Mapping[str, Any],
    key: str,
    *,
    required: bool,
    maximum: int,
    default: list[int] | None = None,
) -> list[str]:
    raw = parameters.get(key)
    if raw in (None, []):
        if default is not None:
            raw = default
        elif required:
            raise ValueError(f"{key} is required")
        else:
            return []
    if not isinstance(raw, list) or not raw or len(raw) > maximum:
        raise ValueError(f"{key} must contain 1 to {maximum} integer codes")
    values: list[str] = []
    for item in raw:
        if isinstance(item, bool):
            raise ValueError(f"{key} contains an invalid code")
        try:
            value = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} contains an invalid code") from exc
        if value < 0 or value > 9999:
            raise ValueError(f"{key} contains an out-of-range code")
        values.append(str(value))
    if len(values) != len(set(values)):
        raise ValueError(f"{key} codes must be unique")
    return values


def _string_codes(
    parameters: Mapping[str, Any],
    key: str,
    *,
    pattern: re.Pattern[str],
    required: bool,
    maximum: int,
) -> list[str]:
    raw = parameters.get(key)
    if raw in (None, []):
        if required:
            raise ValueError(f"{key} is required")
        return []
    if not isinstance(raw, list) or not raw or len(raw) > maximum:
        raise ValueError(f"{key} must contain 1 to {maximum} codes")
    values = [str(item).upper() for item in raw]
    if len(values) != len(set(values)) or any(not pattern.fullmatch(value) for value in values):
        raise ValueError(f"{key} contains an invalid or duplicate code")
    return values


def _periods(parameters: Mapping[str, Any], *, required: bool, maximum: int) -> list[str]:
    raw = parameters.get("periods")
    if raw in (None, []):
        if required:
            raise ValueError("periods is required")
        return []
    if not isinstance(raw, list) or not raw or len(raw) > maximum:
        raise ValueError(f"periods must contain 1 to {maximum} values")
    values = [str(item) for item in raw]
    if len(values) != len(set(values)) or any(not PERIOD_RE.fullmatch(value) for value in values):
        raise ValueError("periods contains an invalid or duplicate period")
    return values


def _append_boolean(query: list[tuple[str, str]], parameters: Mapping[str, Any], key: str, upstream: str) -> None:
    raw = parameters.get(key)
    if raw is None:
        return
    if not isinstance(raw, bool):
        raise ValueError(f"{key} must be boolean")
    query.append((upstream, "true" if raw else "false"))


def _trade_query(parameters: Mapping[str, Any], *, preview: bool, trade_balance: bool = False) -> list[tuple[str, str]]:
    periods = _periods(parameters, required=True, maximum=1 if preview else 12)
    reporters = _integer_codes(parameters, "reporter_codes", required=True, maximum=5)
    commodities = _string_codes(
        parameters,
        "commodity_codes",
        pattern=COMMODITY_RE,
        required=True,
        maximum=1 if preview else 20,
    )
    partners = _integer_codes(parameters, "partner_codes", required=False, maximum=10, default=[0])
    partner2 = _integer_codes(parameters, "partner2_codes", required=False, maximum=5, default=[0])
    flows = [] if trade_balance else _string_codes(
        parameters, "flow_codes", pattern=FLOW_RE, required=True, maximum=6
    )
    customs = _string_codes(
        parameters, "customs_codes", pattern=GENERIC_CODE_RE, required=False, maximum=10
    )
    modes = _string_codes(
        parameters, "mode_of_transport_codes", pattern=GENERIC_CODE_RE, required=False, maximum=10
    )
    max_records = bounded_int(
        parameters.get("max_records"),
        default=500 if preview else 5000,
        minimum=1,
        maximum=500 if preview else 5000,
        name="max_records",
    )
    query: list[tuple[str, str]] = [
        ("period", ",".join(periods)),
        ("reporterCode", ",".join(reporters)),
        ("cmdCode", ",".join(commodities)),
        ("partnerCode", ",".join(partners)),
        ("partner2Code", ",".join(partner2)),
        ("maxRecords", str(max_records)),
        ("format", "json"),
    ]
    if flows:
        query.append(("flowCode", ",".join(flows)))
    if customs:
        query.append(("customsCode", ",".join(customs)))
    if modes:
        query.append(("motCode", ",".join(modes)))
    breakdown = parameters.get("breakdown_mode")
    if breakdown not in (None, ""):
        value = str(breakdown).lower()
        if value not in {"classic", "plus"}:
            raise ValueError("breakdown_mode must be classic or plus")
        query.append(("breakdownMode", value))
    _append_boolean(query, parameters, "count_only", "countOnly")
    _append_boolean(query, parameters, "include_descriptions", "includeDesc")
    return query


def _date_value(parameters: Mapping[str, Any], key: str) -> str | None:
    raw = parameters.get(key)
    if raw in (None, ""):
        return None
    value = str(raw)
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be YYYY-MM-DD") from exc
    return value


def _availability_query(parameters: Mapping[str, Any]) -> list[tuple[str, str]]:
    query: list[tuple[str, str]] = [("format", "json")]
    periods = _periods(parameters, required=False, maximum=12)
    reporters = _integer_codes(parameters, "reporter_codes", required=False, maximum=10)
    if periods:
        query.append(("period", ",".join(periods)))
    if reporters:
        query.append(("reporterCode", ",".join(reporters)))
    start = _date_value(parameters, "published_date_from")
    end = _date_value(parameters, "published_date_to")
    if start and end and start > end:
        raise ValueError("published_date_from must not be after published_date_to")
    if start:
        query.append(("publishedDateFrom", start))
    if end:
        query.append(("publishedDateTo", end))
    return query


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, list[tuple[str, str]], bool]:
    if operation == "catalog-capabilities":
        return None, [], False
    if operation == "reporters-reference":
        return "/files/v1/app/reference/Reporters.json", [], False
    if operation == "partners-reference":
        return "/files/v1/app/reference/partnerAreas.json", [], False
    if operation == "live-updates":
        if parameters:
            raise ValueError("live-updates accepts no parameters")
        return "/data/v1/getLiveUpdate", [], True

    type_code, frequency, classification = _type_frequency_classification(parameters)
    suffix = "/".join(quote(value, safe="") for value in (type_code, frequency, classification))
    if operation == "preview-trade":
        return f"/public/v1/preview/{suffix}", _trade_query(parameters, preview=True), False
    if operation == "final-trade":
        return f"/data/v1/get/{suffix}", _trade_query(parameters, preview=False), True
    if operation == "tariffline-trade":
        if type_code != "C":
            raise ValueError("tariffline-trade supports commodity type C only")
        return f"/data/v1/getTariffline/{suffix}", _trade_query(parameters, preview=False), True
    if operation == "data-availability":
        return f"/data/v1/getDa/{suffix}", _availability_query(parameters), True
    if operation == "metadata":
        periods = _periods(parameters, required=True, maximum=12)
        reporters = _integer_codes(parameters, "reporter_codes", required=True, maximum=5)
        return (
            f"/data/v1/getMetadata/{suffix}",
            [("period", ",".join(periods)), ("reporterCode", ",".join(reporters)), ("format", "json")],
            True,
        )
    if operation == "trade-balance":
        if type_code != "C":
            raise ValueError("trade-balance supports commodity type C only")
        return f"/tools/v1/getTradeBalance/{suffix}", _trade_query(parameters, preview=False, trade_balance=True), True
    raise ValueError(f"unsupported operation: {operation}")


def _scrub(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [_scrub(item, secret) for item in value]
    if isinstance(value, Mapping):
        return {str(_scrub(key, secret)): _scrub(item, secret) for key, item in value.items()}
    return value


def _row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        for key in ("data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
        if isinstance(payload.get("count"), int):
            return int(payload["count"])
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
    status = "INTEL_UN_COMTRADE_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    secret = str(os.environ.get(SECRET_ENV) or "").strip()
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": "comtradeapi.un.org",
        "api_version": "v1",
        "credential_mode": "subscription_key_query_backend_only_or_keyless_preview",
        "secret_environment_variable": SECRET_ENV,
        "secret_values_exposed": False,
        "requests_per_ticket": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "bulk_api_enabled": False,
        "async_api_enabled": False,
    }
    try:
        path, query, requires_key = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            if requires_key and not secret:
                raise RuntimeError(f"{SECRET_ENV} is not configured")
            safe_query_names = sorted({name for name, _ in query})
            upstream_query = list(query)
            if requires_key:
                upstream_query.append(("subscription-key", secret))
            response = requests.get(
                ORIGIN + path,
                params=upstream_query,
                headers={"Accept": "application/json", "User-Agent": "intelligence-center-un-comtrade/1"},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError("UN Comtrade returned invalid JSON") from exc
            clean = _scrub(payload, secret)
            if not response.ok:
                raise RuntimeError(f"UN Comtrade HTTP {response.status_code}: {str(clean)[:1200]}")
            if isinstance(clean, Mapping) and clean.get("error"):
                raise RuntimeError(f"UN Comtrade business error: {str(clean.get('error'))[:1200]}")
            sanitized = (json.dumps(clean, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
            if len(sanitized) > max_bytes:
                raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(sanitized)
            snapshot = {
                "provider": "un-comtrade",
                "operation": operation,
                "row_count": _row_count(clean),
                "data": clean,
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_path": path,
                    "query_parameter_names": safe_query_names,
                    "response_bytes": len(sanitized),
                    "response_sha256": bytes_sha(sanitized),
                    "row_count": _row_count(clean),
                    "credential_used": requires_key,
                }
            )
        status = "INTEL_UN_COMTRADE_COMPLETED"
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
        schema_prefix="un-comtrade",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-un-comtrade]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="un-comtrade-ticket-status-v1",
            display_name="UN Comtrade",
        )
    )
