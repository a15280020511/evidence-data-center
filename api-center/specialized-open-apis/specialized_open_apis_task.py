#!/usr/bin/env python3
"""Bounded runtime for specialized natural-history, materials, policy and heritage APIs."""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlparse

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
USER_AGENT = "evidence-data-center-specialized-open-apis/1"
RESERVED_QUERY_RE = re.compile(r"[+\-!(){}\[\]^\"~*?:\\/]|\b(?:AND|OR|NOT)\b", re.IGNORECASE)
ELEMENT_RE = re.compile(r"^[A-Z][a-z]?$", re.ASCII)
OPTIMADE_PROVIDERS = {
    "mc3d-pbe-v1": "https://optimade.materialscloud.org/main/mc3d-pbe-v1/v1/structures",
    "mc3d-pbesol-v1": "https://optimade.materialscloud.org/main/mc3d-pbesol-v1/v1/structures",
    "mc2d": "https://optimade.materialscloud.org/main/mc2d/v1/structures",
    "pyrene-mofs": "https://optimade.materialscloud.org/main/pyrene-mofs/v1/structures",
}
RIJKSMUSEUM_FIELDS = {
    "title",
    "creator",
    "type",
    "material",
    "description",
    "aboutActor",
    "technique",
    "objectNumber",
    "creationDate",
}


def safe_text(value: Any, name: str, maximum: int, minimum: int = 1) -> str:
    text = str(value or "").strip()
    if len(text) < minimum or len(text) > maximum or any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{name} is invalid")
    return text


def safe_plain_query(value: Any, name: str = "query", maximum: int = 200) -> str:
    text = safe_text(value, name, maximum, 1)
    text = RESERVED_QUERY_RE.sub(" ", text)
    text = " ".join(text.split())
    if not text:
        raise ValueError(f"{name} contains no searchable text")
    return text


def safe_elements(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not 1 <= len(value) <= 5:
        raise ValueError("elements must contain 1 to 5 chemical symbols")
    rows = [safe_text(item, "element", 2) for item in value]
    if len(rows) != len(set(rows)) or any(not ELEMENT_RE.fullmatch(row) for row in rows):
        raise ValueError("elements contains an invalid or duplicate chemical symbol")
    return rows


def build_request(
    operation: str,
    parameters: Mapping[str, Any],
) -> tuple[str | None, str, list[tuple[str, str]], Mapping[str, Any] | None, str, str]:
    if operation == "catalog-capabilities":
        if parameters:
            raise ValueError("catalog-capabilities accepts no parameters")
        return None, "LOCAL", [], None, "catalog", "application/json"
    if operation == "source-access-matrix":
        if parameters:
            raise ValueError("source-access-matrix accepts no parameters")
        return None, "LOCAL", [], None, "matrix", "application/json"
    if operation == "nhm-dataset-search":
        query = safe_plain_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        return (
            "https://data.nhm.ac.uk/api/3/action/package_search",
            "GET",
            [("q", query), ("rows", str(limit)), ("start", "0")],
            None,
            "nhm-ckan",
            "application/json",
        )
    if operation == "optimade-structures":
        provider = safe_text(parameters.get("provider") or "mc3d-pbe-v1", "provider", 32)
        if provider not in OPTIMADE_PROVIDERS:
            raise ValueError("provider is not allowlisted")
        limit = bounded_int(parameters.get("limit"), default=5, minimum=1, maximum=20, name="limit")
        params: list[tuple[str, str]] = [
            ("page_limit", str(limit)),
            ("response_fields", "chemical_formula_reduced,elements,nelements,lattice_vectors,cartesian_site_positions,species_at_sites"),
        ]
        elements = safe_elements(parameters.get("elements"))
        if elements:
            quoted = ",".join(f'"{item}"' for item in elements)
            params.append(("filter", f"elements HAS ALL {quoted}"))
        return OPTIMADE_PROVIDERS[provider], "GET", params, None, "optimade", "application/vnd.api+json,application/json"
    if operation == "gov-uk-search":
        query = safe_plain_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        order = str(parameters.get("order") or "-public_timestamp")
        if order not in {"-public_timestamp", "public_timestamp", "relevance"}:
            raise ValueError("order is not allowlisted")
        return (
            "https://www.gov.uk/api/search.json",
            "GET",
            [("q", query), ("count", str(limit)), ("start", "0"), ("order", order)],
            None,
            "gov-uk-search",
            "application/json",
        )
    if operation == "rijksmuseum-collection-search":
        field = safe_text(parameters.get("field") or "title", "field", 32)
        if field not in RIJKSMUSEUM_FIELDS:
            raise ValueError("field is not allowlisted")
        query = safe_plain_query(parameters.get("query"), maximum=160)
        params = [(field, query)]
        if parameters.get("image_available") is not None:
            params.append(("imageAvailable", str(bool(parameters["image_available"])).lower()))
        return (
            "https://data.rijksmuseum.nl/search/collection",
            "GET",
            params,
            None,
            "rijksmuseum",
            "application/json",
        )
    if operation == "bgs-collections":
        if parameters:
            raise ValueError("bgs-collections accepts no parameters")
        return (
            "https://ogcapi.bgs.ac.uk/collections",
            "GET",
            [("f", "json")],
            None,
            "bgs-collections",
            "application/json",
        )
    raise ValueError(f"unsupported operation: {operation}")


def validate_response(kind: str, data: Any) -> int | None:
    if not isinstance(data, Mapping):
        raise RuntimeError("upstream response must be a JSON object")
    if kind == "nhm-ckan":
        result = data.get("result")
        rows = result.get("results") if isinstance(result, Mapping) else None
        if data.get("success") is not True or not isinstance(rows, list):
            raise RuntimeError("Natural History Museum CKAN response contract failed")
        return len(rows)
    if kind == "optimade":
        rows = data.get("data")
        meta = data.get("meta")
        if not isinstance(rows, list) or not isinstance(meta, Mapping):
            raise RuntimeError("OPTIMADE response contract failed")
        return len(rows)
    if kind == "gov-uk-search":
        rows = data.get("results")
        if not isinstance(rows, list):
            raise RuntimeError("GOV.UK Search response contract failed")
        return len(rows)
    if kind == "rijksmuseum":
        rows = data.get("orderedItems")
        collection = data.get("partOf")
        if not isinstance(rows, list) or not isinstance(collection, Mapping):
            raise RuntimeError("Rijksmuseum Search response contract failed")
        return len(rows)
    if kind == "bgs-collections":
        rows = data.get("collections")
        if not isinstance(rows, list):
            raise RuntimeError("BGS OGC API collections response contract failed")
        return len(rows)
    raise RuntimeError("unknown response contract")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=90, name="timeout_seconds")
    max_bytes = bounded_int(
        acceptance.get("max_response_bytes"),
        default=5_000_000,
        minimum=1024,
        maximum=10_000_000,
        name="max_response_bytes",
    )
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_SPECIALIZED_OPEN_FAILED"
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
        url, method, query, body, kind, accept = build_request(operation, parameters)
        if kind == "catalog":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        elif kind == "matrix":
            snapshot = {"source_access_matrix": load_json(MATRIX_PATH)}
        else:
            response = requests.request(
                method,
                str(url),
                params=query,
                json=dict(body) if body is not None else None,
                headers={"Accept": accept, "User-Agent": USER_AGENT},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not 200 <= response.status_code < 300:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"upstream HTTP {response.status_code}: {text}")
            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("upstream returned invalid JSON") from exc
            row_count = validate_response(kind, data)
            (output_dir / "response.json").write_bytes(raw)
            snapshot = {"provider": kind, "operation": operation, "data": data}
            metadata.update(
                {
                    "upstream_called": True,
                    "request_count": 1,
                    "api_origin": urlparse(str(url)).hostname,
                    "http_method": method,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "response_bytes": len(raw),
                    "response_sha256": bytes_sha(raw),
                    "row_count": row_count,
                    "credential_mode": "none",
                }
            )
        status = "INTEL_SPECIALIZED_OPEN_COMPLETED"
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
        schema_prefix="specialized-open-apis",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-specialized-open]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="specialized-open-apis-ticket-status-v1",
            display_name="全球专业细分开放API",
        )
    )
