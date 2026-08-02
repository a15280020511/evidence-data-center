#!/usr/bin/env python3
"""Bounded Cloudflare intelligence provider: Browser Rendering, Radar, and URL Scanner reads."""
from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlsplit, urlunsplit

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import (  # noqa: E402
    bounded_int,
    bytes_sha,
    finish_execution,
    provider_row,
    run_cli,
    utc_now,
    validate_ticket,
)

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
API_BASE = "https://api.cloudflare.com/client/v4"
TOKEN_ENV = "CLOUDFLARE_API_TOKEN"
ACCOUNT_ENV = "CLOUDFLARE_ACCOUNT_ID"
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.azure.internal",
    "kubernetes.default",
    "kubernetes.default.svc",
    "instance-data",
}
BLOCKED_SUFFIXES = (".local", ".internal", ".localhost", ".svc", ".cluster.local")
HTTP_SUMMARY_DIMENSIONS = {
    "ADM1",
    "API_TRAFFIC",
    "AS",
    "BOT_CLASS",
    "BROWSER_FAMILY",
    "DEVICE_TYPE",
    "HTTP_PROTOCOL",
    "HTTP_VERSION",
    "IP_VERSION",
    "OS",
    "TLS_VERSION",
}
LAYER7_DIMENSIONS = {
    "HTTP_METHOD",
    "HTTP_VERSION",
    "IP_VERSION",
    "MANAGED_RULES",
    "MITIGATION_PRODUCT",
    "INDUSTRY",
    "VERTICAL",
}
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$")
DATE_RANGE_RE = re.compile(r"^(?:[1-9]|[1-9][0-9]|[1-2][0-9]{2}|3[0-5][0-9]|36[0-4])d(?:control)?$|^(?:[1-9]|[1-4][0-9]|5[0-2])w(?:control)?$")


class Spec:
    def __init__(
        self,
        method: str,
        url: str,
        *,
        params: list[tuple[str, str]] | None = None,
        json_body: Mapping[str, Any] | None = None,
        response_kind: str = "json",
        credential_mode: str = "bearer-token",
    ) -> None:
        self.method = method
        self.url = url
        self.params = params
        self.json_body = json_body
        self.response_kind = response_kind
        self.credential_mode = credential_mode


def text(parameters: Mapping[str, Any], name: str, maximum: int, required: bool = False) -> str:
    value = str(parameters.get(name) or "").strip()
    if required and not value:
        raise ValueError(f"{name} is required")
    if len(value) > maximum or any(ord(char) < 32 for char in value):
        raise ValueError(f"{name} is invalid")
    return value


def secret(name: str) -> str:
    value = str(os.environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"missing required backend secret or variable: {name}")
    return value


def account_id() -> str:
    value = secret(ACCOUNT_ENV)
    if not re.fullmatch(r"^[0-9a-fA-F]{32}$", value):
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID must be a 32-character hexadecimal account ID")
    return value


def validate_public_https_url(value: Any) -> str:
    url = str(value or "").strip()
    if not 8 <= len(url) <= 2048:
        raise ValueError("url must contain 8 to 2048 characters")
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("url must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("url credentials and custom ports are forbidden")
    hostname = parsed.hostname.casefold().rstrip(".")
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(BLOCKED_SUFFIXES):
        raise ValueError("url targets a blocked hostname")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise ValueError("url targets a non-public IP address")
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError("url hostname could not be resolved") from exc
    addresses = {str(row[4][0]).split("%", 1)[0] for row in records if row and len(row) >= 5 and row[4]}
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("url hostname does not resolve exclusively to public IPs")
    return urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, ""))


def common_radar_params(parameters: Mapping[str, Any], *, allow_limit: bool = False) -> list[tuple[str, str]]:
    query: list[tuple[str, str]] = [("format", "json")]
    if parameters.get("date_range"):
        value = text(parameters, "date_range", 16, True)
        if not DATE_RANGE_RE.fullmatch(value):
            raise ValueError("date_range must be 1d..364d or 1w..52w, optionally suffixed by control")
        query.append(("dateRange", value))
    if parameters.get("location"):
        value = text(parameters, "location", 2, True).upper()
        if not re.fullmatch(r"^[A-Z]{2}$", value):
            raise ValueError("location must be an ISO alpha-2 code")
        query.append(("location", value))
    if parameters.get("asn") not in (None, ""):
        query.append(("asn", str(bounded_int(parameters.get("asn"), default=0, minimum=1, maximum=4294967295, name="asn"))))
    if allow_limit:
        query.append(("limit", str(bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit"))))
    return query


def scan_id(parameters: Mapping[str, Any]) -> str:
    value = text(parameters, "scan_id", 36, True)
    if not UUID_RE.fullmatch(value):
        raise ValueError("scan_id must be a UUID")
    return value.lower()


def build(operation: str, parameters: Mapping[str, Any]) -> Spec | dict[str, Any]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return {"provider": provider_row(CATALOG_PATH)}

    browser_map = {
        "browser-content": ("content", "text"),
        "browser-markdown": ("markdown", "text"),
        "browser-links": ("links", "json"),
        "browser-screenshot": ("screenshot", "binary"),
        "browser-pdf": ("pdf", "binary"),
        "browser-snapshot": ("snapshot", "json"),
        "browser-accessibility-tree": ("accessibilityTree", "json"),
    }
    if operation in browser_map:
        endpoint, response_kind = browser_map[operation]
        body = {"url": validate_public_https_url(parameters.get("url"))}
        return Spec(
            "POST",
            f"{API_BASE}/accounts/{account_id()}/browser-rendering/{endpoint}",
            json_body=body,
            response_kind=response_kind,
        )

    if operation == "radar-global-search":
        query = [("query", text(parameters, "query", 200, True)), ("limit", str(bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit"))), ("format", "json")]
        return Spec("GET", f"{API_BASE}/radar/search/global", params=query)
    if operation == "radar-outages":
        query = common_radar_params(parameters, allow_limit=True)
        if parameters.get("offset") not in (None, ""):
            query.append(("offset", str(bounded_int(parameters.get("offset"), default=0, minimum=0, maximum=10000, name="offset"))))
        return Spec("GET", f"{API_BASE}/radar/annotations/outages", params=query)
    if operation == "radar-outage-locations":
        return Spec("GET", f"{API_BASE}/radar/annotations/outages/locations", params=common_radar_params(parameters))
    if operation == "radar-http-summary":
        dimension = text(parameters, "dimension", 32, True).upper()
        if dimension not in HTTP_SUMMARY_DIMENSIONS:
            raise ValueError("dimension is not allowlisted")
        return Spec("GET", f"{API_BASE}/radar/http/summary/{quote(dimension)}", params=common_radar_params(parameters))
    if operation == "radar-http-timeseries":
        query = common_radar_params(parameters)
        if parameters.get("aggregation_interval"):
            interval = text(parameters, "aggregation_interval", 3, True)
            if interval not in {"15m", "1h", "1d", "1w"}:
                raise ValueError("aggregation_interval is not allowlisted")
            query.append(("aggInterval", interval))
        return Spec("GET", f"{API_BASE}/radar/http/timeseries", params=query)
    if operation == "radar-ranking-top":
        query = common_radar_params(parameters, allow_limit=True)
        ranking_type = str(parameters.get("ranking_type") or "POPULAR").upper()
        if ranking_type not in {"POPULAR", "TRENDING_RISE", "TRENDING_STEADY"}:
            raise ValueError("ranking_type is not allowlisted")
        query.append(("rankingType", ranking_type))
        return Spec("GET", f"{API_BASE}/radar/ranking/top", params=query)
    if operation == "radar-ranking-domain":
        domain = text(parameters, "domain", 253, True).lower().rstrip(".")
        if not DOMAIN_RE.fullmatch(domain):
            raise ValueError("domain is invalid")
        query = [("format", "json")]
        if parameters.get("location"):
            location = text(parameters, "location", 2, True).upper()
            if not re.fullmatch(r"^[A-Z]{2}$", location):
                raise ValueError("location must be an ISO alpha-2 code")
            query.append(("location", location))
        return Spec("GET", f"{API_BASE}/radar/ranking/domain/{quote(domain)}", params=query)
    if operation == "radar-layer7-summary":
        dimension = text(parameters, "dimension", 32, True).upper()
        if dimension not in LAYER7_DIMENSIONS:
            raise ValueError("dimension is not allowlisted")
        return Spec("GET", f"{API_BASE}/radar/attacks/layer7/summary/{quote(dimension)}", params=common_radar_params(parameters))
    if operation == "radar-layer7-top-attacks":
        return Spec("GET", f"{API_BASE}/radar/attacks/layer7/top/attacks", params=common_radar_params(parameters))

    scanner_base = f"{API_BASE}/accounts/{account_id()}/urlscanner/v2"
    if operation == "urlscanner-search":
        query = [("q", text(parameters, "query", 500, True)), ("size", str(bounded_int(parameters.get("size"), default=20, minimum=1, maximum=100, name="size")))]
        return Spec("GET", f"{scanner_base}/search", params=query)
    if operation == "urlscanner-result":
        return Spec("GET", f"{scanner_base}/result/{scan_id(parameters)}")
    if operation == "urlscanner-har":
        return Spec("GET", f"{scanner_base}/har/{scan_id(parameters)}")
    if operation == "urlscanner-dom":
        return Spec("GET", f"{scanner_base}/dom/{scan_id(parameters)}", response_kind="text")
    if operation == "urlscanner-screenshot":
        return Spec("GET", f"{scanner_base}/screenshots/{scan_id(parameters)}.png", response_kind="binary")
    raise ValueError(f"unsupported operation: {operation}")


def sanitize(value: Any) -> Any:
    forbidden = {"authorization", "cookie", "set-cookie", "token", "secret", "api_key", "apikey"}
    if isinstance(value, Mapping):
        return {str(key): sanitize(item) for key, item in value.items() if str(key).casefold() not in forbidden}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at, started_perf = utc_now(), time.perf_counter()
    status = "INTEL_CLOUDFLARE_FAILED"
    failure: dict[str, Any] | None = None
    snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "requests_per_ticket_max": 1,
        "automatic_retry": False,
        "automatic_pagination": False,
        "secret_values_exposed": False,
        "operation": operation,
    }
    try:
        spec = build(operation, parameters)
        if isinstance(spec, dict):
            snapshot = {"provider": "cloudflare", "operation": operation, "data": spec}
        else:
            headers = {
                "Accept": "application/json, text/plain;q=0.9, text/html;q=0.8, image/*;q=0.7, application/pdf;q=0.7",
                "Authorization": f"Bearer {secret(TOKEN_ENV)}",
                "Content-Type": "application/json",
                "User-Agent": "gpts-intelligence-center-cloudflare/1",
            }
            response = requests.request(
                spec.method,
                spec.url,
                params=spec.params,
                json=spec.json_body,
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
            )
            raw = bytes(response.content or b"")
            content_type = str(response.headers.get("Content-Type") or "")
            metadata.update({
                "upstream_called": True,
                "api_host": "api.cloudflare.com",
                "request_path": urlsplit(spec.url).path,
                "http_status": int(response.status_code),
                "content_type": content_type,
                "response_bytes_raw": len(raw),
                "credential_mode": spec.credential_mode,
            })
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok:
                message = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"upstream HTTP {response.status_code}: {message}")

            payload: Any = None
            is_json = "json" in content_type.casefold()
            if is_json:
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise RuntimeError("Cloudflare returned invalid JSON") from exc
                if isinstance(payload, Mapping) and payload.get("success") is False:
                    raise RuntimeError(f"Cloudflare business failure: {payload.get('errors') or payload.get('messages')}")

            if spec.response_kind == "binary" and not is_json:
                suffix = ".pdf" if "pdf" in content_type.casefold() or operation == "browser-pdf" else ".png"
                filename = f"response{suffix}"
                (output_dir / filename).write_bytes(raw)
                snapshot = {
                    "provider": "cloudflare",
                    "operation": operation,
                    "artifact_file": filename,
                    "content_type": content_type,
                    "bytes": len(raw),
                    "sha256": bytes_sha(raw),
                }
            elif spec.response_kind == "text" and not is_json:
                value = raw.decode("utf-8", errors="replace")
                (output_dir / "response.txt").write_text(value, encoding="utf-8")
                snapshot = {"provider": "cloudflare", "operation": operation, "text": value[:200000], "truncated_for_snapshot": len(value) > 200000}
            else:
                if payload is None:
                    value = raw.decode("utf-8", errors="replace")
                    payload = {"text": value[:200000], "truncated_for_snapshot": len(value) > 200000}
                snapshot = {"provider": "cloudflare", "operation": operation, "data": sanitize(payload)}
            metadata["response_sha256"] = bytes_sha(raw)
            status = "INTEL_CLOUDFLARE_COMPLETED"
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
        schema_prefix="cloudflare-intelligence",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-cloudflare]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="cloudflare-intelligence-ticket-status-v1",
            display_name="Cloudflare Intelligence",
        )
    )
