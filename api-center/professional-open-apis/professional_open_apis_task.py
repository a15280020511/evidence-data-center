#!/usr/bin/env python3
"""Bounded runtime for professional, industry and institutional open APIs."""
from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urljoin, urlparse

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
USER_AGENT = "evidence-data-center-professional-open-apis/1"
RESERVED_QUERY_RE = re.compile(r"[+\-!(){}\[\]^\"~*?:\\/]|\b(?:AND|OR|NOT)\b", re.IGNORECASE)
ISBN_RE = re.compile(r"^(?:\d{9}[\dX]|\d{13})$")
SITE_RE = re.compile(r"^[A-Za-z0-9_-]{4,24}$")
PARAMETER_CODE_RE = re.compile(r"^\d{5}$")


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


def normalize_isbn(value: Any) -> str:
    text = re.sub(r"[-\s]", "", safe_text(value, "isbn", 32)).upper()
    if not ISBN_RE.fullmatch(text):
        raise ValueError("isbn must be ISBN-10 or ISBN-13")
    return text


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
    if operation == "data-gov-uk-search":
        query = safe_plain_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit")
        return (
            "https://data.gov.uk/api/3/action/package_search",
            "GET",
            [("q", query), ("rows", str(limit)), ("start", "0")],
            None,
            "ckan",
            "application/json",
        )
    if operation == "pubchem-compound-properties":
        name = safe_plain_query(parameters.get("name"), "name", 120)
        allowed = {
            "MolecularFormula",
            "MolecularWeight",
            "CanonicalSMILES",
            "IsomericSMILES",
            "InChI",
            "InChIKey",
            "XLogP",
            "TPSA",
            "Complexity",
            "HBondDonorCount",
            "HBondAcceptorCount",
            "RotatableBondCount",
            "ExactMass",
            "MonoisotopicMass",
            "Charge",
            "HeavyAtomCount",
        }
        requested = parameters.get("properties") or [
            "MolecularFormula",
            "MolecularWeight",
            "CanonicalSMILES",
            "InChIKey",
        ]
        if not isinstance(requested, list) or not 1 <= len(requested) <= 8:
            raise ValueError("properties must contain 1 to 8 items")
        properties = [safe_text(item, "property", 40) for item in requested]
        if len(properties) != len(set(properties)) or any(item not in allowed for item in properties):
            raise ValueError("properties contains a duplicate or non-allowlisted property")
        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            f"{quote(name, safe='')}/property/{','.join(properties)}/JSON"
        )
        return url, "GET", [], None, "pubchem", "application/json"
    if operation == "usgs-water-instantaneous":
        site = safe_text(parameters.get("site"), "site", 24, 4)
        if not SITE_RE.fullmatch(site):
            raise ValueError("site contains unsupported characters")
        period = str(parameters.get("period") or "PT6H")
        if period not in {"PT1H", "PT6H", "P1D", "P7D", "P30D"}:
            raise ValueError("period is not allowlisted")
        codes = parameters.get("parameter_codes") or ["00060", "00065"]
        if not isinstance(codes, list) or not 1 <= len(codes) <= 10:
            raise ValueError("parameter_codes must contain 1 to 10 items")
        normalized = [str(code).strip() for code in codes]
        if len(normalized) != len(set(normalized)) or any(not PARAMETER_CODE_RE.fullmatch(code) for code in normalized):
            raise ValueError("parameter_codes contains an invalid or duplicate code")
        return (
            "https://waterservices.usgs.gov/nwis/iv/",
            "GET",
            [
                ("format", "json"),
                ("sites", site),
                ("parameterCd", ",".join(normalized)),
                ("period", period),
                ("siteStatus", "all"),
            ],
            None,
            "usgs-water",
            "application/json",
        )
    if operation == "worms-taxon-search":
        name = safe_plain_query(parameters.get("name"), "name", 160)
        like = bool(parameters.get("like", True))
        marine_only = bool(parameters.get("marine_only", False))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        return (
            f"https://www.marinespecies.org/rest/AphiaRecordsByName/{quote(name, safe='')}",
            "GET",
            [
                ("like", str(like).lower()),
                ("marine_only", str(marine_only).lower()),
                ("offset", "1"),
                ("limit", str(limit)),
            ],
            None,
            "worms",
            "application/json",
        )
    if operation == "idref-authority-search":
        query = safe_plain_query(parameters.get("query"))
        index = str(parameters.get("index") or "all")
        allowed_indexes = {
            "all",
            "persname_t",
            "corpname_t",
            "subjectheading_t",
            "geogname_t",
            "famname_t",
            "uniformtitle_t",
            "trademark_t",
        }
        if index not in allowed_indexes:
            raise ValueError("index is not allowlisted")
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        return (
            "https://www.idref.fr/Sru/Solr",
            "GET",
            [
                ("q", f"{index}:{query}"),
                ("wt", "json"),
                ("version", "2.2"),
                ("start", "0"),
                ("rows", str(limit)),
                ("indent", "off"),
                ("fl", "ppn_z,persname_t,corpname_t,subjectheading_t,geogname_t,famname_t,uniformtitle_t,trademark_t"),
            ],
            None,
            "idref",
            "application/json",
        )
    if operation == "sudoc-isbn-lookup":
        isbn = normalize_isbn(parameters.get("isbn"))
        return (
            f"https://www.sudoc.fr/services/isbn2ppn/{isbn}",
            "GET",
            [],
            None,
            "sudoc-xml",
            "application/xml,text/xml",
        )
    if operation == "ons-datasets":
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        return (
            "https://api.beta.ons.gov.uk/v1/datasets",
            "GET",
            [("limit", str(limit)), ("offset", "0")],
            None,
            "ons",
            "application/json",
        )
    if operation == "agris-ods-index":
        if parameters:
            raise ValueError("agris-ods-index accepts no parameters")
        return (
            "https://agris.fao.org/agris_ods/",
            "GET",
            [],
            None,
            "agris-html",
            "text/html,application/xhtml+xml",
        )
    raise ValueError(f"unsupported operation: {operation}")


def validate_json_response(kind: str, data: Any) -> tuple[int | None, Any]:
    if kind == "worms":
        if not isinstance(data, list):
            raise RuntimeError("WoRMS response contract failed")
        return len(data), data
    if not isinstance(data, Mapping):
        raise RuntimeError("upstream JSON response must be an object")
    if kind == "ckan":
        result = data.get("result")
        if data.get("success") is not True or not isinstance(result, Mapping) or not isinstance(result.get("results"), list):
            raise RuntimeError("data.gov.uk CKAN response contract failed")
        return len(result["results"]), data
    if kind == "pubchem":
        table = data.get("PropertyTable")
        rows = table.get("Properties") if isinstance(table, Mapping) else None
        if not isinstance(rows, list):
            raise RuntimeError("PubChem response contract failed")
        return len(rows), data
    if kind == "usgs-water":
        value = data.get("value")
        rows = value.get("timeSeries") if isinstance(value, Mapping) else None
        if not isinstance(rows, list):
            raise RuntimeError("USGS water response contract failed")
        return len(rows), data
    if kind == "idref":
        response = data.get("response")
        rows = response.get("docs") if isinstance(response, Mapping) else None
        if not isinstance(rows, list):
            raise RuntimeError("IdRef response contract failed")
        return len(rows), data
    if kind == "ons":
        rows = data.get("items")
        if not isinstance(rows, list):
            raise RuntimeError("ONS datasets response contract failed")
        return len(rows), data
    raise RuntimeError("unknown JSON response contract")


def parse_xml_response(kind: str, raw: bytes) -> tuple[int, Mapping[str, Any]]:
    if kind != "sudoc-xml":
        raise RuntimeError("unknown XML response contract")
    root = ET.fromstring(raw)
    values: list[str] = []
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1].lower()
        text = str(element.text or "").strip()
        if text and (local == "ppn" or re.fullmatch(r"\d{9}[\dX]?", text, re.IGNORECASE)):
            values.append(text)
    values = list(dict.fromkeys(values))
    if not values:
        serialized = raw[:500].decode("utf-8", errors="replace")
        raise RuntimeError(f"Sudoc ISBN response contract failed: {serialized}")
    return len(values), {"ppn": values}


def parse_agris_index(raw: bytes) -> tuple[int, Mapping[str, Any]]:
    text = raw.decode("utf-8", errors="replace")
    if "AGRIS" not in text.upper():
        raise RuntimeError("AGRIS ODS index response contract failed")
    hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", text, flags=re.IGNORECASE)
    links: list[str] = []
    for href in hrefs:
        candidate = urljoin("https://agris.fao.org/agris_ods/", href)
        if candidate.startswith("https://agris.fao.org/agris_ods/") and any(
            token in candidate.lower() for token in (".zip", ".xml", ".rdf", ".gz", ".csv")
        ):
            links.append(candidate)
    links = list(dict.fromkeys(links))[:100]
    return len(links), {"download_links": links, "index_available": True}


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
    status = "INTEL_PROFESSIONAL_OPEN_FAILED"
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
            if kind == "sudoc-xml":
                row_count, data = parse_xml_response(kind, raw)
                output_name = "response.xml"
            elif kind == "agris-html":
                row_count, data = parse_agris_index(raw)
                output_name = "response.html"
            else:
                try:
                    parsed = response.json()
                except ValueError as exc:
                    raise RuntimeError("upstream returned invalid JSON") from exc
                row_count, data = validate_json_response(kind, parsed)
                output_name = "response.json"
            (output_dir / output_name).write_bytes(raw)
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
        status = "INTEL_PROFESSIONAL_OPEN_COMPLETED"
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
        schema_prefix="professional-open-apis",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-professional-open]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="professional-open-apis-ticket-status-v1",
            display_name="全球专业行业开放API",
        )
    )
