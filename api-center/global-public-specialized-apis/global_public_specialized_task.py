#!/usr/bin/env python3
"""Bounded runtime for service-specific public institution sources."""
from __future__ import annotations

import json
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
MATRIX_PATH = HERE / "source-access-matrix.json"
USER_AGENT = "evidence-data-center-public-specialized/1.0"
DATE8_RE = re.compile(r"^[0-9]{8}$")
PLAIN_TEXT_RE = re.compile(r"[^0-9A-Za-z\u00C0-\u024F\u3400-\u9FFF _.,:+*/()-]+")


def operation_parameters(parameters: Mapping[str, Any], allowed: set[str]) -> None:
    unsupported = set(parameters) - allowed
    if unsupported:
        raise ValueError(f"unsupported parameters: {sorted(unsupported)}")


def safe_text(value: Any, name: str, maximum: int, *, required: bool = True) -> str:
    rendered = str(value or "").strip()
    if not rendered and not required:
        return ""
    if not rendered or len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    return rendered


def safe_query(value: Any, name: str, maximum: int, *, required: bool = False) -> str:
    rendered = safe_text(value, name, maximum, required=required)
    if not rendered:
        return ""
    rendered = PLAIN_TEXT_RE.sub(" ", rendered)
    rendered = " ".join(rendered.split())
    if required and not rendered:
        raise ValueError(f"{name} contains no searchable text")
    return rendered


def credential(name: str) -> str:
    value = str(os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"required backend credential is not configured: {name}")
    if len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise RuntimeError(f"invalid backend credential: {name}")
    return value


def build_request(operation: str, parameters: Mapping[str, Any]):
    headers = {
        "Accept": "application/json, text/html;q=0.8, text/plain;q=0.7",
        "User-Agent": USER_AGENT,
    }
    query: list[tuple[str, str]] = []
    credentials_used: list[str] = []

    if operation == "catalog-capabilities":
        operation_parameters(parameters, set())
        return None, "LOCAL", headers, query, None, credentials_used, "catalog"
    if operation == "source-access-matrix":
        operation_parameters(parameters, set())
        return None, "LOCAL", headers, query, None, credentials_used, "matrix"

    if operation == "poland-isztar4-help":
        operation_parameters(parameters, {"language"})
        language = str(parameters.get("language") or "EN").strip().upper()
        if language not in {"EN", "PL"}:
            raise ValueError("language must be EN or PL")
        headers["Accept"] = "text/html, application/xhtml+xml;q=0.9"
        query.append(("lang", language))
        return (
            "https://ext-isztar4.mf.gov.pl/taryfa_celna/Help",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            "poland-isztar4",
        )

    if operation == "poland-isztar4-tariff-sections":
        operation_parameters(parameters, {"language", "simulation_date"})
        language = str(parameters.get("language") or "EN").strip().upper()
        if language not in {"EN", "PL"}:
            raise ValueError("language must be EN or PL")
        simulation_date = safe_text(
            parameters.get("simulation_date"),
            "simulation_date",
            8,
            required=False,
        )
        if simulation_date and not DATE8_RE.fullmatch(simulation_date):
            raise ValueError("simulation_date must use YYYYMMDD")
        headers["Accept"] = "text/html, application/xhtml+xml;q=0.9"
        query.append(("lang", language))
        if simulation_date:
            query.append(("date", simulation_date))
        return (
            "https://ext-isztar4.mf.gov.pl/taryfa_celna/PrelimInfoHC",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            "poland-isztar4",
        )

    if operation == "korea-krx-listed-companies":
        operation_parameters(
            parameters,
            {"page", "limit", "base_date", "company_name"},
        )
        page = bounded_int(
            parameters.get("page"),
            default=1,
            minimum=1,
            maximum=1000,
            name="page",
        )
        limit = bounded_int(
            parameters.get("limit"),
            default=20,
            minimum=1,
            maximum=100,
            name="limit",
        )
        base_date = safe_text(
            parameters.get("base_date"),
            "base_date",
            8,
            required=False,
        )
        if base_date and not DATE8_RE.fullmatch(base_date):
            raise ValueError("base_date must use YYYYMMDD")
        company_name = safe_query(
            parameters.get("company_name"),
            "company_name",
            80,
            required=False,
        )
        key = credential("KOREA_DATA_GO_KR_SERVICE_KEY")
        credentials_used.append("KOREA_DATA_GO_KR_SERVICE_KEY")
        query.extend(
            [
                ("serviceKey", key),
                ("resultType", "json"),
                ("pageNo", str(page)),
                ("numOfRows", str(limit)),
            ]
        )
        if base_date:
            query.append(("basDt", base_date))
        if company_name:
            query.append(("likeCorpNm", company_name))
        return (
            "https://apis.data.go.kr/1160100/service/"
            "GetKrxListedInfoService/getItemInfo",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            "korea-data-go-kr-krx-listed",
        )

    raise ValueError(f"unsupported operation: {operation}")


def parse_response(raw: bytes, content_type: str) -> Any:
    lowered = content_type.lower()
    if "json" in lowered:
        return json.loads(raw.decode("utf-8"))
    text = raw.decode("utf-8", errors="replace")
    return {
        "content_type": content_type,
        "text": text[:2_000_000],
        "truncated": len(text) > 2_000_000,
    }


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45,
        minimum=5,
        maximum=90,
        name="timeout_seconds",
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
    status = "INTEL_PUBLIC_SPECIALIZED_APIS_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "request_count": 0,
        "automatic_pagination": False,
        "automatic_retry": False,
        "redirects_allowed": False,
        "write_operations_allowed": False,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    try:
        url, method, headers, query, body, credentials_used, source_id = build_request(
            operation,
            parameters,
        )
        if method == "LOCAL":
            if source_id == "catalog":
                snapshot = {"provider": provider_row(CATALOG_PATH)}
            else:
                snapshot = {"source_access_matrix": load_json(MATRIX_PATH)}
        else:
            response = requests.request(
                method,
                str(url),
                params=query,
                json=body,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            if not 200 <= response.status_code < 300:
                error_text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"upstream HTTP {response.status_code}: {error_text}"
                )
            content_type = response.headers.get("Content-Type", "")
            data = parse_response(raw, content_type)
            suffix = "json" if "json" in content_type.lower() else "txt"
            (output_dir / f"upstream-response.{suffix}").write_bytes(raw)
            snapshot = {
                "source_id": source_id,
                "operation": operation,
                "data": data,
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "request_count": 1,
                    "api_origin": urlparse(str(url)).hostname,
                    "http_method": method,
                    "http_status": response.status_code,
                    "content_type": content_type,
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "credential_mode": "backend" if credentials_used else "none",
                    "credential_environment_variables_used": credentials_used,
                }
            )
        status = "INTEL_PUBLIC_SPECIALIZED_APIS_COMPLETED"
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
        schema_prefix="global-public-specialized",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-public-specialized]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="global-public-specialized-ticket-status-v1",
            display_name="全球公共机构专项API",
        )
    )
