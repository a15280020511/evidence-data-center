#!/usr/bin/env python3
"""Bounded read-only runtime for WTO and IMF statistics providers."""
from __future__ import annotations

import argparse
import json
import os
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

CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,79}$")
PERIOD_RE = re.compile(r"^[0-9]{4}(?:-(?:M[0-9]{2}|Q[1-4]))?$")
PROVIDERS = {
    "wto": {
        "origin": "https://api.wto.org/timeseries/v1",
        "prefix": "[intel-wto]",
        "status": "INTEL_WTO",
        "secret": "WTO_API_KEY",
        "secret_header": "Ocp-Apim-Subscription-Key",
        "max_requests": 1,
    },
    "imf": {
        "origin": "https://api.imf.org/external/sdmx/3.0",
        "prefix": "[intel-imf]",
        "status": "INTEL_IMF",
        "secret": "IMF_API_KEY",
        "secret_header": "Ocp-Apim-Subscription-Key",
        "max_requests": 1,
    },}


def _catalog(provider: str) -> Path:
    return HERE.parent / provider / "provider-catalog.json"


def _schema(provider: str) -> Path:
    return HERE.parent / provider / "ticket.schema.json"


def _codes(value: Any, name: str, maximum: int) -> list[str]:
    if value in (None, []):
        return []
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} codes")
    values = [str(x) for x in value]
    if len(values) != len(set(values)) or any(not CODE_RE.fullmatch(x) for x in values):
        raise ValueError(f"{name} contains an invalid or duplicate code")
    return values


def _periods(value: Any, maximum: int) -> list[str]:
    if value in (None, []):
        return []
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError(f"periods must contain 1 to {maximum} values")
    values = [str(x) for x in value]
    if len(values) != len(set(values)) or any(not PERIOD_RE.fullmatch(x) for x in values):
        raise ValueError("periods contains an invalid or duplicate period")
    return values


def build_request(provider: str, operation: str, p: Mapping[str, Any]) -> tuple[str | None, list[tuple[str, str]]]:
    if operation == "catalog-capabilities":
        return None, []

    if provider == "wto":
        fixed = {
            "indicator-categories": "/indicator_categories",
            "indicators": "/indicators",
            "reporters": "/reporter",
            "partners": "/partner",
        }
        if operation in fixed:
            return fixed[operation], [("lang", str(bounded_int(p.get("lang"), default=1, minimum=1, maximum=3, name="lang")))]
        if operation not in {"data-count", "data"}:
            raise ValueError(f"unsupported WTO operation: {operation}")
        indicators = _codes(p.get("indicator_codes"), "indicator_codes", 10)
        if not indicators:
            raise ValueError("indicator_codes is required")
        query = [
            ("i", ",".join(indicators)),
            ("r", ",".join(_codes(p.get("reporter_codes"), "reporter_codes", 20)) or "all"),
            ("p", ",".join(_codes(p.get("partner_codes"), "partner_codes", 20)) or "all"),
            ("ps", ",".join(_periods(p.get("periods"), 24)) or "default"),
            ("pc", ",".join(_codes(p.get("product_codes"), "product_codes", 20)) or "default"),
            ("spc", "true" if p.get("product_subsector", False) else "false"),
            ("fmt", "json"),
            ("mode", str(p.get("mode") or "full")),
            ("dec", str(p.get("decimals") if p.get("decimals") is not None else "default")),
            ("off", str(bounded_int(p.get("offset"), default=0, minimum=0, maximum=100000, name="offset"))),
            ("max", str(bounded_int(p.get("max_records"), default=100, minimum=1, maximum=500, name="max_records"))),
            ("head", str(p.get("heading_style") or "H")),
            ("lang", str(bounded_int(p.get("lang"), default=1, minimum=1, maximum=3, name="lang"))),
            ("meta", "true" if p.get("include_metadata", False) else "false"),
        ]
        return "/data_count" if operation == "data-count" else "/data", query

    if provider == "imf":
        structure_ops = {
            "get-dataflow": ("dataflow", "flow"),
            "get-datastructure": ("datastructure", "structure_id"),
            "get-codelist": ("codelist", "codelist_id"),
            "get-conceptscheme": ("conceptscheme", "conceptscheme_id"),
        }
        if operation in structure_ops:
            resource_type, parameter_name = structure_ops[operation]
            agency = str(p.get("agency") or "")
            resource_id = str(p.get(parameter_name) or "")
            version = str(p.get("version") or "+")
            if not CODE_RE.fullmatch(agency) or not CODE_RE.fullmatch(resource_id):
                raise ValueError(f"agency and {parameter_name} are required")
            if not re.fullmatch(r"^(?:\+|latest|[0-9]+(?:\.[0-9]+){0,3})$", version):
                raise ValueError("version is invalid")
            path = "/structure/" + "/".join(
                quote(value, safe="._@+-")
                for value in (resource_type, agency, resource_id, version)
            )
            return path, []
        if operation != "get-data":
            raise ValueError(f"unsupported IMF operation: {operation}")
        agency = str(p.get("agency") or "")
        flow = str(p.get("flow") or "")
        version = str(p.get("version") or "+")
        key = str(p.get("key") or "")
        if not CODE_RE.fullmatch(agency) or not CODE_RE.fullmatch(flow):
            raise ValueError("agency and flow are required")
        if not re.fullmatch(r"^(?:\+|latest|[0-9]+(?:\.[0-9]+){0,3})$", version):
            raise ValueError("version is invalid")
        if not re.fullmatch(r"^[A-Za-z0-9*+._@-]{1,500}$", key):
            raise ValueError("key is invalid")
        path = "/data/dataflow/" + "/".join(
            quote(value, safe="*+._@-") for value in (agency, flow, version, key)
        )
        query: list[tuple[str, str]] = []
        start_period = p.get("start_period")
        end_period = p.get("end_period")
        if start_period not in (None, ""):
            if not PERIOD_RE.fullmatch(str(start_period)):
                raise ValueError("start_period is invalid")
            query.append(("startPeriod", str(start_period)))
        if end_period not in (None, ""):
            if not PERIOD_RE.fullmatch(str(end_period)):
                raise ValueError("end_period is invalid")
            query.append(("endPeriod", str(end_period)))
        dimension = p.get("dimension_at_observation")
        if dimension not in (None, ""):
            if dimension not in {"AllDimensions", "TimeDimension", "MeasureDimension"}:
                raise ValueError("dimension_at_observation is invalid")
            query.append(("dimensionAtObservation", str(dimension)))
        return path, query

    raise ValueError(f"unsupported provider: {provider}")


def _scrub(value: Any, secrets: list[str]) -> Any:
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [_scrub(x, secrets) for x in value]
    if isinstance(value, Mapping):
        return {str(_scrub(k, secrets)): _scrub(v, secrets) for k, v in value.items()}
    return value


def _row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        for key in ("values", "data", "results", "Dataset"):
            if isinstance(payload.get(key), list):
                return len(payload[key])
        for key in ("count", "total", "TotalRecords"):
            if isinstance(payload.get(key), int):
                return int(payload[key])
        return 1
    return 0


def execute_for(provider: str, ticket_path: Path, output_dir: Path) -> int:
    cfg = PROVIDERS[provider]
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=_schema(provider), catalog_path=_catalog(provider))
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=30, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=10_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at, started_perf = utc_now(), time.perf_counter()
    status, failure, snapshot = f"{cfg['status']}_FAILED", None, None
    password = str(os.getenv(cfg.get("secret", "")) or "").strip() if cfg.get("secret") else ""
    secrets = [password]
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origin": cfg["origin"].split("/")[2],
        "requests_per_ticket_max": cfg["max_requests"],
        "automatic_retry": False,
        "automatic_pagination": False,
        "secret_values_exposed": False,
    }
    try:
        path, query = build_request(provider, operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(_catalog(provider))}
        else:
            headers = {"Accept": "application/json", "User-Agent": f"intelligence-center-{provider}/1"}
            if provider in {"wto", "imf"}:
                if not password:
                    raise RuntimeError(f"{cfg['secret']} is not configured")
                headers[cfg["secret_header"]] = password
                if provider == "imf":
                    headers["Accept"] = (
                        "application/json, application/vnd.sdmx.data+json, "
                        "application/vnd.sdmx.structure+json, */*;q=0.8"
                    )
            response = requests.get(cfg["origin"] + path, params=query, headers=headers, timeout=timeout, allow_redirects=False)
            raw = bytes(response.content or b"")
            metadata.update({
                "upstream_called": True,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "request_path": path,
                "query_parameter_names": sorted({k for k, _ in query}),
            })
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok:
                try:
                    error_payload = _scrub(response.json(), secrets)
                    detail = str(error_payload)[:1200]
                except ValueError:
                    detail = _scrub(raw[:1200].decode("utf-8", errors="replace"), secrets)
                raise RuntimeError(f"{provider.upper()} HTTP {response.status_code}: {detail}")
            try:
                payload = response.json()
            except ValueError as exc:
                content_type = response.headers.get("Content-Type", "")
                raise RuntimeError(
                    f"{provider.upper()} HTTP {response.status_code} returned non-JSON "
                    f"content-type {content_type or 'unknown'}"
                ) from exc
            clean = _scrub(payload, secrets)
            sanitized = (json.dumps(clean, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
            if len(sanitized) > max_bytes:
                raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(sanitized)
            snapshot = {"provider": provider, "operation": operation, "row_count": _row_count(clean), "data": clean}
            metadata.update({
                "response_bytes": len(sanitized),
                "response_sha256": bytes_sha(sanitized),
                "row_count": _row_count(clean),
                "credential_used": provider in {"wto", "imf"},
                "ephemeral_token_persisted": False,
            })
        status = f"{cfg['status']}_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(_scrub(str(exc), secrets))[:2000]}
    return finish_execution(
        ticket=ticket, output_dir=output_dir, status=status, snapshot=snapshot,
        metadata=metadata, failure=failure, started_at=started_at,
        started_perf=started_perf, schema_prefix=provider,
    )


def main(provider: str) -> int:
    cfg = PROVIDERS[provider]
    return run_cli(
        execute=lambda ticket, output: execute_for(provider, ticket, output),
        ticket_prefix=cfg["prefix"],
        schema_path=_schema(provider),
        catalog_path=_catalog(provider),
        status_schema=f"{provider}-ticket-status-v1",
        display_name=provider.upper(),
    )
