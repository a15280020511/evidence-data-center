#!/usr/bin/env python3
"""Bounded read-only runtime for WTO, IMF DataMapper and FAOSTAT."""
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
DATASET_RE = re.compile(r"^[A-Z0-9_]{1,16}$")
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
        "origin": "https://www.imf.org/external/datamapper/api/v2",
        "prefix": "[intel-imf]",
        "status": "INTEL_IMF",
        "secret": "",
        "max_requests": 1,
    },
    "faostat": {
        "origin": "https://faostatservices.fao.org/api/v1",
        "prefix": "[intel-faostat]",
        "status": "INTEL_FAOSTAT",
        "secret": "FAOSTAT_PASSWORD",
        "username": "FAOSTAT_USERNAME",
        "auth_origin": "https://faostatservices.fao.org/api/v1/auth/login",
        "max_requests": 2,
    },
}


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
            "indicators": "/indicator",
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
        fixed = {
            "list-indicators": "/indicators",
            "list-countries": "/countries",
            "list-regions": "/regions",
            "list-groups": "/groups",
        }
        if operation in fixed:
            if p:
                raise ValueError(f"{operation} accepts no parameters")
            return fixed[operation], []
        if operation != "get-series":
            raise ValueError(f"unsupported IMF operation: {operation}")
        indicator = str(p.get("indicator") or "")
        locations = _codes(p.get("locations"), "locations", 20)
        if not CODE_RE.fullmatch(indicator) or not locations:
            raise ValueError("indicator and at least one location are required")
        path = "/" + "/".join([quote(indicator, safe=""), *[quote(x, safe="") for x in locations]])
        periods = _periods(p.get("periods"), 50)
        return path, ([("periods", ",".join(periods))] if periods else [])

    if provider == "faostat":
        lang = str(p.get("lang") or "en")
        if lang not in {"en", "es", "fr"}:
            raise ValueError("lang must be en, es or fr")
        if operation == "list-groups":
            return f"/{lang}/groups", []
        if operation == "list-datasets":
            return f"/{lang}/definitions/domaincodes", []
        dataset = str(p.get("dataset") or "").upper()
        if not DATASET_RE.fullmatch(dataset):
            raise ValueError("dataset is invalid")
        if operation == "list-parameters":
            return f"/{lang}/dimensions/{quote(dataset, safe='')}", []
        if operation == "get-parameter-codes":
            parameter = str(p.get("parameter") or "")
            if not CODE_RE.fullmatch(parameter):
                raise ValueError("parameter is invalid")
            return f"/{lang}/codes/{quote(parameter, safe='')}/{quote(dataset, safe='')}", []
        if operation not in {"get-data-size", "get-data"}:
            raise ValueError(f"unsupported FAOSTAT operation: {operation}")
        filters = p.get("filters")
        if not isinstance(filters, Mapping) or not filters:
            raise ValueError("filters must contain at least one bounded dimension filter")
        query: list[tuple[str, str]] = []
        for key, raw in filters.items():
            if not CODE_RE.fullmatch(str(key)):
                raise ValueError("filter name is invalid")
            values = _codes(raw, f"filters.{key}", 20)
            if not values:
                raise ValueError(f"filters.{key} is empty")
            query.append((str(key), ",".join(values)))
        query.extend([
            ("page_number", str(bounded_int(p.get("page_number"), default=1, minimum=1, maximum=100000, name="page_number"))),
            ("page_size", str(bounded_int(p.get("page_size"), default=100, minimum=1, maximum=500, name="page_size"))),
            ("output_type", "objects"),
        ])
        path = f"/{lang}/data/{quote(dataset, safe='')}"
        if operation == "get-data-size":
            query.append(("show_codes", "true"))
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
    username = str(os.getenv(cfg.get("username", "")) or "").strip() if cfg.get("username") else ""
    token = ""
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
            if provider == "wto":
                if not password:
                    raise RuntimeError("WTO_API_KEY is not configured")
                headers[cfg["secret_header"]] = password
            elif provider == "faostat":
                if not username or not password:
                    raise RuntimeError("FAOSTAT_USERNAME and FAOSTAT_PASSWORD must both be configured")
                auth = requests.post(cfg["auth_origin"], data={"username": username, "password": password}, headers={"Accept": "application/json"}, timeout=timeout, allow_redirects=False)
                try:
                    auth_payload = auth.json()
                except ValueError as exc:
                    raise RuntimeError("FAOSTAT authentication returned invalid JSON") from exc
                if not auth.ok:
                    raise RuntimeError(f"FAOSTAT authentication HTTP {auth.status_code}")
                token = str((auth_payload.get("AuthenticationResult") or {}).get("AccessToken") or auth_payload.get("access_token") or "")
                if not token:
                    raise RuntimeError("FAOSTAT authentication returned no access token")
                secrets.append(token)
                headers["Authorization"] = f"Bearer {token}"
                metadata["authentication_http_status"] = auth.status_code
            response = requests.get(cfg["origin"] + path, params=query, headers=headers, timeout=timeout, allow_redirects=False)
            raw = bytes(response.content or b"")
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError(f"{provider.upper()} returned invalid JSON") from exc
            clean = _scrub(payload, secrets)
            if not response.ok:
                raise RuntimeError(f"{provider.upper()} HTTP {response.status_code}: {str(clean)[:1200]}")
            sanitized = (json.dumps(clean, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
            if len(sanitized) > max_bytes:
                raise RuntimeError("sanitized response exceeds max_response_bytes")
            (output_dir / "response.json").write_bytes(sanitized)
            snapshot = {"provider": provider, "operation": operation, "row_count": _row_count(clean), "data": clean}
            metadata.update({
                "upstream_called": True,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "request_path": path,
                "query_parameter_names": sorted({k for k, _ in query}),
                "response_bytes": len(sanitized),
                "response_sha256": bytes_sha(sanitized),
                "row_count": _row_count(clean),
                "credential_used": provider in {"wto", "faostat"},
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
