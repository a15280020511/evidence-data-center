#!/usr/bin/env python3
"""Bounded read-only Internet Archive execution for Intelligence Center tickets."""
from __future__ import annotations

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

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
ARCHIVE_ORIGIN = "https://archive.org"
WAYBACK_ORIGIN = "https://web.archive.org"
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")
FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
QUERY_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,500}$")
URL_RE = re.compile(r"^https?://[^\s]{1,1000}$", re.IGNORECASE)
SORT_VALUES = {
    "downloads desc",
    "downloads asc",
    "date desc",
    "date asc",
    "addeddate desc",
    "addeddate asc",
    "titleSorter asc",
    "titleSorter desc",
}
DEFAULT_FIELDS = ["identifier", "title", "creator", "date", "mediatype", "collection"]


def _identifier(parameters: Mapping[str, Any]) -> str:
    value = str(parameters.get("identifier") or "")
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError("identifier is invalid")
    return value


def build_request(
    operation: str, parameters: Mapping[str, Any]
) -> tuple[str | None, dict[str, str]]:
    if operation == "catalog-capabilities":
        return None, {}
    if operation == "search-items":
        query_text = str(parameters.get("query") or "")
        if not QUERY_RE.fullmatch(query_text):
            raise ValueError("query is invalid")
        rows = bounded_int(
            parameters.get("rows"), default=50, minimum=1, maximum=200, name="rows"
        )
        page = bounded_int(
            parameters.get("page"), default=1, minimum=1, maximum=1000, name="page"
        )
        fields = parameters.get("fields") or DEFAULT_FIELDS
        if not isinstance(fields, list) or not fields or len(fields) > 20:
            raise ValueError("fields must contain 1 to 20 names")
        normalized_fields = [str(value) for value in fields]
        if len(normalized_fields) != len(set(normalized_fields)):
            raise ValueError("fields must be unique")
        if any(not FIELD_RE.fullmatch(value) for value in normalized_fields):
            raise ValueError("fields contains an invalid name")
        sort = str(parameters.get("sort") or "downloads desc")
        if sort not in SORT_VALUES:
            raise ValueError("sort is not allowlisted")
        return "/advancedsearch.php", {
            "q": query_text,
            "fl[]": ",".join(normalized_fields),
            "rows": str(rows),
            "page": str(page),
            "sort[]": sort,
            "output": "json",
        }
    if operation in {"get-item-metadata", "list-item-files"}:
        return f"/metadata/{quote(_identifier(parameters), safe='._-')}", {}
    if operation == "wayback-availability":
        url = str(parameters.get("url") or "")
        if not URL_RE.fullmatch(url):
            raise ValueError("url must be an absolute http or https URL")
        query = {"url": url}
        timestamp = parameters.get("timestamp")
        if timestamp:
            timestamp_text = str(timestamp)
            if not re.fullmatch(r"[0-9]{4,14}", timestamp_text):
                raise ValueError("timestamp must contain 4 to 14 digits")
            query["timestamp"] = timestamp_text
        return "/wayback/available", query
    if operation == "wayback-captures":
        url = str(parameters.get("url") or "")
        if not URL_RE.fullmatch(url):
            raise ValueError("url must be an absolute http or https URL")
        limit = bounded_int(
            parameters.get("limit"), default=50, minimum=1, maximum=200, name="limit"
        )
        query = {
            "url": url,
            "output": "json",
            "fl": "timestamp,original,statuscode,mimetype,digest",
            "filter": "statuscode:200",
            "collapse": "digest",
            "limit": str(limit),
        }
        from_timestamp = parameters.get("from_timestamp")
        to_timestamp = parameters.get("to_timestamp")
        if from_timestamp:
            value = str(from_timestamp)
            if not re.fullmatch(r"[0-9]{4,14}", value):
                raise ValueError("from_timestamp must contain 4 to 14 digits")
            query["from"] = value
        if to_timestamp:
            value = str(to_timestamp)
            if not re.fullmatch(r"[0-9]{4,14}", value):
                raise ValueError("to_timestamp must contain 4 to 14 digits")
            query["to"] = value
        return "/cdx/search/cdx", query
    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(
        acceptance.get("timeout_seconds"),
        default=45,
        minimum=5,
        maximum=120,
        name="timeout_seconds",
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
    status = "INTEL_INTERNET_ARCHIVE_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "api_origins": ["archive.org", "web.archive.org"],
        "credential_mode": "none",
        "secret_values_exposed": False,
        "downloads_allowed": False,
        "uploads_allowed": False,
        "write_operations_allowed": False,
    }
    try:
        path, query = build_request(operation, parameters)
        if path is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            origin = WAYBACK_ORIGIN if operation == "wayback-captures" else ARCHIVE_ORIGIN
            response = requests.get(
                origin + path,
                params=query,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "intelligence-center-internet-archive/1",
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
                raise RuntimeError(
                    f"Internet Archive HTTP {response.status_code}: {text}"
                )
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("Internet Archive returned invalid JSON") from exc
            if operation == "search-items":
                if not isinstance(data, Mapping) or not isinstance(
                    data.get("response"), Mapping
                ):
                    raise RuntimeError("advanced search response contract is invalid")
                response_row = data["response"]
                docs = response_row.get("docs") or []
                if not isinstance(docs, list):
                    raise RuntimeError("advanced search docs is not an array")
                snapshot = {
                    "provider": "internet-archive",
                    "operation": operation,
                    "num_found": response_row.get("numFound"),
                    "start": response_row.get("start"),
                    "row_count": len(docs),
                    "docs": docs,
                }
            elif operation == "list-item-files":
                if not isinstance(data, Mapping) or not isinstance(data.get("files"), list):
                    raise RuntimeError("metadata files contract is invalid")
                files = []
                for item in data["files"][:500]:
                    if not isinstance(item, Mapping):
                        continue
                    files.append(
                        {
                            key: item.get(key)
                            for key in (
                                "name",
                                "format",
                                "size",
                                "md5",
                                "sha1",
                                "mtime",
                                "source",
                                "original",
                            )
                            if key in item
                        }
                    )
                snapshot = {
                    "provider": "internet-archive",
                    "operation": operation,
                    "identifier": data.get("metadata", {}).get("identifier")
                    if isinstance(data.get("metadata"), Mapping)
                    else parameters.get("identifier"),
                    "file_count_returned": len(files),
                    "file_count_total": len(data["files"]),
                    "files": files,
                }
            elif operation == "wayback-captures":
                if not isinstance(data, list):
                    raise RuntimeError("CDX response is not an array")
                headers = data[0] if data and isinstance(data[0], list) else []
                rows = data[1:] if headers else data
                snapshot = {
                    "provider": "internet-archive",
                    "operation": operation,
                    "columns": headers,
                    "row_count": len(rows),
                    "captures": rows,
                }
            else:
                if not isinstance(data, Mapping):
                    raise RuntimeError("Internet Archive response is not an object")
                snapshot = {
                    "provider": "internet-archive",
                    "operation": operation,
                    "data": data,
                }
            (output_dir / "response.json").write_bytes(raw)
            metadata.update(
                {
                    "upstream_called": True,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "request_origin": origin,
                    "request_path": path,
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                }
            )
        status = "INTEL_INTERNET_ARCHIVE_COMPLETED"
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
        schema_prefix="internet-archive",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-internet-archive]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="internet-archive-ticket-status-v1",
            display_name="Internet Archive",
        )
    )
