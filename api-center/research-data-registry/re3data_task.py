#!/usr/bin/env python3
"""Bounded, keyless re3data v40 registry provider."""
from __future__ import annotations

import re
import sys
import time
import xml.etree.ElementTree as ET
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
REPOSITORY_ID_RE = re.compile(r"^r3d[0-9]{9,15}$")


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, str]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, "catalog"
    if operation == "re3data-repositories":
        if parameters:
            raise ValueError("re3data-repositories accepts no parameters")
        return "https://www.re3data.org/api/v40/repositories", "index"
    if operation == "re3data-repository":
        repository_id = str(parameters.get("repository_id") or "").strip().lower()
        if not REPOSITORY_ID_RE.fullmatch(repository_id):
            raise ValueError("repository_id must match the official r3d identifier format")
        return f"https://www.re3data.org/api/v40/repository/{repository_id}", "record"
    raise ValueError(f"unsupported operation: {operation}")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def validate_xml(kind: str, raw: bytes) -> tuple[str, int]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise RuntimeError("re3data returned invalid XML") from exc
    names = [local_name(element.tag) for element in root.iter()]
    if kind == "index":
        count = sum(name in {"repository", "repositoryentry"} for name in names)
        if count == 0:
            count = sum(name in {"id", "repositoryid"} for name in names)
        if count == 0:
            raise RuntimeError("re3data index XML contains no repository entries")
    elif kind == "record":
        signals = {"repository", "repositoryname", "repositoryurl", "repositoryid"}
        if not signals.intersection(names):
            raise RuntimeError("re3data record XML does not match the repository schema")
        count = 1
    else:
        raise RuntimeError("unknown re3data response kind")
    return local_name(root.tag), count


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=60,
        minimum=5,
        maximum=90,
        name="timeout_seconds",
    )
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=15_000_000,
        minimum=1024,
        maximum=15_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_RE3DATA_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "credential_mode": "none",
        "secret_values_exposed": False,
        "automatic_pagination": False,
        "automatic_retry": False,
        "redirects_allowed": False,
    }
    try:
        url, kind = build_request(operation, parameters)
        if kind == "catalog":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                str(url),
                headers={
                    "Accept": "application/xml, text/xml;q=0.9",
                    "User-Agent": "evidence-data-center-re3data/1",
                },
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(
                    f"response exceeds acceptance.max_response_bytes={max_bytes}"
                )
            if not response.ok:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"upstream HTTP {response.status_code}: {text}")
            root_name, record_count = validate_xml(kind, raw)
            (output_dir / "response.xml").write_bytes(raw)
            snapshot = {
                "provider": "re3data",
                "operation": operation,
                "response_file": "response.xml",
                "xml_root": root_name,
                "record_count": record_count,
            }
            metadata.update(
                {
                    "upstream_called": True,
                    "api_origin": urlparse(str(url)).hostname,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "record_count": record_count,
                }
            )
        status = "INTEL_RE3DATA_COMPLETED"
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
        schema_prefix="re3data",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-re3data]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="re3data-ticket-status-v1",
            display_name="re3data全球科研数据仓库目录",
        )
    )
