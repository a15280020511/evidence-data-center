#!/usr/bin/env python3
"""Bounded read-only NIH/NCBI/FDA public-health execution."""
from __future__ import annotations

import os
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
USER_AGENT = "a15280020511-evidence-data-center/1.0"
ALLOWED_HOSTS = {
    "eutils.ncbi.nlm.nih.gov",
    "api.fda.gov",
    "wsearch.nlm.nih.gov",
    "clinicaltables.nlm.nih.gov",
}
OPENFDA_PATHS = {
    "drug-event": "/drug/event.json",
    "drug-label": "/drug/label.json",
    "drug-enforcement": "/drug/enforcement.json",
    "device-event": "/device/event.json",
    "device-recall": "/device/recall.json",
    "food-enforcement": "/food/enforcement.json",
}
CLINICAL_TABLE_PATHS = {
    "conditions": "/api/conditions/v3/search",
    "icd10cm": "/api/icd10cm/v3/search",
    "rxterms": "/api/rxterms/v3/search",
    "loinc": "/api/loinc_items/v3/search",
}


def _fixed_url(host: str, path: str) -> str:
    if host not in ALLOWED_HOSTS or not path.startswith("/") or "://" in path:
        raise ValueError("request target is not allowlisted")
    url = f"https://{host}{path}"
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != host:
        raise ValueError("request target failed fixed-host validation")
    return url


def _optional_key(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def build_request(operation: str, parameters: Mapping[str, Any]) -> tuple[str | None, dict[str, Any], str]:
    if operation == "catalog-capabilities":
        return None, {}, "local"
    if operation == "pubmed-search":
        query = str(parameters.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": bounded_int(parameters.get("retmax"), default=20, minimum=1, maximum=200, name="retmax"),
            "retstart": bounded_int(parameters.get("retstart"), default=0, minimum=0, maximum=100000, name="retstart"),
            "sort": str(parameters.get("sort") or "relevance"),
        }
        for key in ("datetype", "mindate", "maxdate"):
            if parameters.get(key) is not None:
                params[key] = str(parameters[key])
        api_key = _optional_key("NCBI_API_KEY")
        if api_key:
            params["api_key"] = api_key
        if os.getenv("NCBI_TOOL", "").strip():
            params["tool"] = os.environ["NCBI_TOOL"].strip()
        if os.getenv("NCBI_EMAIL", "").strip():
            params["email"] = os.environ["NCBI_EMAIL"].strip()
        return _fixed_url("eutils.ncbi.nlm.nih.gov", "/entrez/eutils/esearch.fcgi"), params, "json"
    if operation == "pubmed-fetch":
        pmids = parameters.get("pmids") or []
        if not isinstance(pmids, list) or not 1 <= len(pmids) <= 50:
            raise ValueError("pmids must contain 1 to 50 values")
        ids = [str(value) for value in pmids]
        if any(not value.isdigit() or len(value) > 12 for value in ids):
            raise ValueError("pmids contains an invalid PMID")
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "rettype": str(parameters.get("rettype") or "abstract"),
        }
        api_key = _optional_key("NCBI_API_KEY")
        if api_key:
            params["api_key"] = api_key
        if os.getenv("NCBI_TOOL", "").strip():
            params["tool"] = os.environ["NCBI_TOOL"].strip()
        if os.getenv("NCBI_EMAIL", "").strip():
            params["email"] = os.environ["NCBI_EMAIL"].strip()
        return _fixed_url("eutils.ncbi.nlm.nih.gov", "/entrez/eutils/efetch.fcgi"), params, "xml"
    if operation == "openfda-query":
        dataset = str(parameters.get("dataset") or "")
        path = OPENFDA_PATHS.get(dataset)
        if path is None:
            raise ValueError("dataset is not allowlisted")
        params = {
            "limit": bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit"),
            "skip": bounded_int(parameters.get("skip"), default=0, minimum=0, maximum=25000, name="skip"),
        }
        if parameters.get("search") is not None:
            params["search"] = str(parameters["search"])
        if parameters.get("count") is not None:
            params["count"] = str(parameters["count"])
        api_key = _optional_key("OPENFDA_API_KEY")
        if api_key:
            params["api_key"] = api_key
        return _fixed_url("api.fda.gov", path), params, "json"
    if operation == "medlineplus-search":
        language = str(parameters.get("language") or "en")
        db = "healthTopicsSpanish" if language == "es" else "healthTopics"
        params = {
            "db": db,
            "term": str(parameters.get("query") or ""),
            "rettype": "brief",
            "retmax": bounded_int(parameters.get("retmax"), default=10, minimum=1, maximum=50, name="retmax"),
            "retstart": bounded_int(parameters.get("retstart"), default=0, minimum=0, maximum=1000, name="retstart"),
        }
        return _fixed_url("wsearch.nlm.nih.gov", "/ws/query"), params, "medlineplus_xml"
    if operation == "clinical-tables-search":
        dataset = str(parameters.get("dataset") or "")
        path = CLINICAL_TABLE_PATHS.get(dataset)
        if path is None:
            raise ValueError("dataset is not allowlisted")
        params = {
            "terms": str(parameters.get("terms") or ""),
            "maxList": bounded_int(parameters.get("max_list"), default=20, minimum=1, maximum=100, name="max_list"),
            "offset": bounded_int(parameters.get("offset"), default=0, minimum=0, maximum=7500, name="offset"),
        }
        return _fixed_url("clinicaltables.nlm.nih.gov", path), params, "json"
    raise ValueError(f"unsupported operation: {operation}")


def _parse_medlineplus(raw: bytes) -> dict[str, Any]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise RuntimeError("MedlinePlus returned invalid XML") from exc
    documents: list[dict[str, Any]] = []
    for document in root.findall(".//document"):
        row: dict[str, Any] = {}
        for key in ("rank", "url"):
            if document.get(key):
                row[key] = document.get(key)
        for content in document.findall("./content"):
            name = content.get("name") or "content"
            text = "".join(content.itertext()).strip()
            if text:
                row[name] = text
        documents.append(row)
    return {"document_count": len(documents), "documents": documents}


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket["acceptance"])
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=120, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=20_000_000, name="max_response_bytes")
    started_at = utc_now()
    started_perf = time.perf_counter()
    status = "INTEL_NIH_PUBLIC_HEALTH_FAILED"
    failure = None
    snapshot: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = {
        "upstream_called": False,
        "credential_mode": "optional",
        "secret_values_exposed": False,
        "automatic_pagination": False,
        "requests_per_ticket": 0,
    }
    try:
        url, query, response_kind = build_request(operation, parameters)
        if url is None:
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            response = requests.get(
                url,
                params=query,
                headers={"Accept": "application/json, application/xml;q=0.9, text/xml;q=0.8", "User-Agent": USER_AGENT},
                timeout=timeout,
                allow_redirects=False,
            )
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not response.ok:
                text = raw[:1000].decode("utf-8", errors="replace")
                raise RuntimeError(f"upstream HTTP {response.status_code}: {text}")
            metadata.update({
                "upstream_called": True,
                "requests_per_ticket": 1,
                "api_host": urlparse(url).hostname,
                "request_path": urlparse(url).path,
                "http_status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "response_bytes": len(raw),
                "response_sha256": bytes_sha(raw),
                "optional_key_used": bool(
                    (operation.startswith("pubmed-") and _optional_key("NCBI_API_KEY"))
                    or (operation == "openfda-query" and _optional_key("OPENFDA_API_KEY"))
                ),
            })
            if response_kind == "json":
                try:
                    data = response.json()
                except ValueError as exc:
                    raise RuntimeError("upstream returned invalid JSON") from exc
                (output_dir / "response.json").write_bytes(raw)
                snapshot = {"provider": "nih-public-health", "operation": operation, "data": data}
                if isinstance(data, Mapping):
                    if isinstance(data.get("results"), list):
                        metadata["row_count"] = len(data["results"])
                    elif isinstance(data.get("esearchresult"), Mapping):
                        metadata["row_count"] = len(data["esearchresult"].get("idlist") or [])
                elif isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
                    metadata["row_count"] = len(data[1])
            elif response_kind == "medlineplus_xml":
                parsed = _parse_medlineplus(raw)
                (output_dir / "response.xml").write_bytes(raw)
                snapshot = {"provider": "nih-public-health", "operation": operation, "data": parsed}
                metadata["row_count"] = parsed["document_count"]
            else:
                try:
                    root = ET.fromstring(raw)
                except ET.ParseError as exc:
                    raise RuntimeError("PubMed returned invalid XML") from exc
                count = len(root.findall(".//PubmedArticle"))
                (output_dir / "response.xml").write_bytes(raw)
                snapshot = {
                    "provider": "nih-public-health",
                    "operation": operation,
                    "format": "xml",
                    "article_count": count,
                    "response_sha256": bytes_sha(raw),
                }
                metadata["row_count"] = count
        status = "INTEL_NIH_PUBLIC_HEALTH_COMPLETED"
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
        schema_prefix="nih-public-health",
    )


if __name__ == "__main__":
    raise SystemExit(run_cli(
        execute=execute,
        ticket_prefix="[intel-nih-health]",
        schema_path=SCHEMA_PATH,
        catalog_path=CATALOG_PATH,
        status_schema="nih-public-health-ticket-status-v1",
        display_name="NIH Public Health",
    ))
