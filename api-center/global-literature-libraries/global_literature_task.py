#!/usr/bin/env python3
"""Bounded runtime for fixed global literature and library sources."""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlsplit

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


def text(value: Any, name: str, maximum: int) -> str:
    rendered = str(value or "").strip()
    if not rendered or len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    return rendered


def backend_credential(name: str, *, required: bool) -> str:
    value = str(os.getenv(name) or "").strip()
    if required and not value:
        raise RuntimeError(f"required backend credential is not configured: {name}")
    if len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise RuntimeError(f"invalid backend credential: {name}")
    return value


def source_map() -> dict[str, Mapping[str, Any]]:
    matrix = load_json(MATRIX_PATH)
    rows = matrix.get("sources")
    if not isinstance(rows, list):
        raise RuntimeError("source matrix is invalid")
    return {str(row["source_id"]): row for row in rows if isinstance(row, Mapping)}


def source_for(source_id: Any, operation: str) -> Mapping[str, Any]:
    source_id = text(source_id, "source_id", 80)
    row = source_map().get(source_id)
    if row is None:
        raise ValueError("source_id is not enabled")
    if operation not in (row.get("operations") or []):
        raise ValueError(f"{source_id} does not support {operation}")
    base_url = str(row.get("base_url") or "")
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("source registry contains a non-HTTPS endpoint")
    return row


def credentials_for(row: Mapping[str, Any]) -> tuple[dict[str, str], list[tuple[str, str]], list[str]]:
    mode = str(row.get("credential_mode") or "none")
    name = str(row.get("credential_env") or "")
    headers: dict[str, str] = {}
    query: list[tuple[str, str]] = []
    used: list[str] = []
    if mode in {"none", ""}:
        return headers, query, used
    required = mode.startswith("required_")
    value = backend_credential(name, required=required)
    if not value:
        return headers, query, used
    used.append(name)
    source_id = str(row["source_id"])
    if source_id == "core":
        headers["Authorization"] = f"Bearer {value}"
    elif source_id == "semantic-scholar":
        headers["x-api-key"] = value
    elif source_id == "nasa-ads":
        headers["Authorization"] = f"Bearer {value}"
    elif source_id == "europeana":
        query.append(("wskey", value))
    elif source_id == "dpla":
        query.append(("api_key", value))
    elif source_id == "cinii":
        query.append(("appid", value))
    elif source_id == "doaj-oai":
        query.append(("api_key", value))
    else:
        raise RuntimeError(f"credential injection is not configured for {source_id}")
    return headers, query, used


def record_identifier(source_id: str, raw: Any) -> str:
    value = text(raw, "record_id", 300)
    patterns = {
        "core": r"^[0-9]{1,20}$",
        "openaire": r"^[A-Za-z0-9_.:-]{1,300}$",
        "semantic-scholar": r"^[A-Za-z0-9._:/-]{1,300}$",
        "europe-pmc": r"^[A-Za-z0-9._:-]{1,100}$",
        "zenodo": r"^[0-9]{1,20}$",
        "osf": r"^[A-Za-z0-9]{3,20}$",
        "figshare": r"^[0-9]{1,20}$",
        "econbiz": r"^[0-9]{1,30}$",
        "osti": r"^[0-9]{1,30}$",
        "nasa-ads": r"^[A-Za-z0-9.&:+-]{1,100}$",
        "library-of-congress": r"^[A-Za-z0-9._-]{1,100}$",
        "open-library": r"^OL[0-9]{1,12}[A-Z]$",
        "europeana": r"^/[A-Za-z0-9_./-]{1,260}$",
        "dpla": r"^[A-Fa-f0-9-]{8,80}$",
    }
    pattern = patterns.get(source_id)
    if pattern is None or not re.fullmatch(pattern, value):
        raise ValueError(f"record_id is invalid for {source_id}")
    return value


def build_search(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    query_text = text(parameters.get("query"), "query", 500)
    limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
    headers, credential_query, credentials = credentials_for(row)
    headers.update({"Accept": "application/json, application/xml;q=0.8, text/xml;q=0.8", "User-Agent": "evidence-data-center-literature/1.0"})
    method = "GET"
    body = None
    query: list[tuple[str, str]] = list(credential_query)

    if source_id == "core":
        url = "https://api.core.ac.uk/v3/search/works"
        query += [("q", query_text), ("limit", str(limit)), ("offset", "0")]
    elif source_id == "openaire":
        url = "https://api.openaire.eu/graph/v3/research-products"
        query += [("search", query_text), ("page", "1"), ("pageSize", str(limit))]
    elif source_id == "semantic-scholar":
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        fields = "paperId,title,abstract,year,authors,externalIds,url,openAccessPdf,citationCount,publicationTypes"
        query += [("query", query_text), ("limit", str(limit)), ("fields", fields)]
    elif source_id == "europe-pmc":
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        query += [("query", query_text), ("format", "json"), ("pageSize", str(limit)), ("resultType", "core")]
    elif source_id == "zenodo":
        url = "https://zenodo.org/api/records"
        query += [("q", query_text), ("size", str(limit)), ("page", "1"), ("sort", "bestmatch")]
    elif source_id == "osf":
        url = "https://api.osf.io/v2/preprints/"
        query += [("filter[title]", query_text), ("page[size]", str(limit))]
    elif source_id == "figshare":
        method = "POST"
        url = "https://api.figshare.com/v2/articles/search"
        body = {"search_for": query_text, "limit": limit, "order": "published_date", "order_direction": "desc"}
    elif source_id == "dryad":
        url = "https://datadryad.org/api/v2/search"
        query += [("q", query_text), ("page", "1")]
    elif source_id == "econbiz":
        url = "https://api.econbiz.de/v1/search"
        query += [("q", query_text), ("size", str(limit)), ("from", "1")]
    elif source_id == "osti":
        url = "https://www.osti.gov/api/v1/records"
        query += [("q", query_text), ("rows", str(limit)), ("page", "1")]
    elif source_id == "nasa-ads":
        url = "https://api.adsabs.harvard.edu/v1/search/query"
        query += [("q", query_text), ("rows", str(limit)), ("start", "0"), ("fl", "bibcode,title,author,year,abstract,doi,citation_count,property")]
    elif source_id == "library-of-congress":
        url = "https://www.loc.gov/search/"
        query += [("q", query_text), ("fo", "json"), ("c", str(limit)), ("sp", "1")]
    elif source_id == "open-library":
        url = "https://openlibrary.org/search.json"
        query += [("q", query_text), ("limit", str(limit)), ("page", "1"), ("fields", "key,title,author_name,first_publish_year,isbn,language,subject,edition_count")]
    elif source_id == "europeana":
        url = "https://api.europeana.eu/record/v2/search.json"
        query += [("query", query_text), ("rows", str(limit)), ("start", "1")]
    elif source_id == "dpla":
        url = "https://api.dp.la/v2/items"
        query += [("q", query_text), ("page_size", str(limit)), ("page", "1")]
    elif source_id == "cinii":
        url = "https://cir.nii.ac.jp/opensearch/articles"
        query += [("q", query_text), ("count", str(limit)), ("start", "1"), ("lang", "en"), ("format", "json")]
    elif source_id == "gallica":
        url = "https://gallica.bnf.fr/SRU"
        headers["Accept"] = "application/xml, text/xml;q=0.9"
        query += [("version", "1.2"), ("operation", "searchRetrieve"), ("query", query_text), ("maximumRecords", str(limit)), ("startRecord", "1")]
    else:
        raise ValueError(f"unsupported search source: {source_id}")
    return method, url, headers, query, body, credentials


def build_record(row: Mapping[str, Any], parameters: Mapping[str, Any]):
    source_id = str(row["source_id"])
    record_id = record_identifier(source_id, parameters.get("record_id"))
    headers, query, credentials = credentials_for(row)
    headers.update({"Accept": "application/json, application/xml;q=0.8", "User-Agent": "evidence-data-center-literature/1.0"})
    method = "GET"
    body = None

    if source_id == "core":
        url = f"https://api.core.ac.uk/v3/works/{record_id}"
    elif source_id == "openaire":
        url = f"https://api.openaire.eu/graph/v3/research-products/{quote(record_id, safe=':_-')}"
    elif source_id == "semantic-scholar":
        url = f"https://api.semanticscholar.org/graph/v1/paper/{quote(record_id, safe='')}"
        query += [("fields", "paperId,title,abstract,year,authors,externalIds,url,openAccessPdf,citationCount,publicationTypes")]
    elif source_id == "europe-pmc":
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        query += [("query", f"EXT_ID:{record_id}"), ("format", "json"), ("pageSize", "1"), ("resultType", "core")]
    elif source_id == "zenodo":
        url = f"https://zenodo.org/api/records/{record_id}"
    elif source_id == "osf":
        url = f"https://api.osf.io/v2/preprints/{record_id}/"
    elif source_id == "figshare":
        url = f"https://api.figshare.com/v2/articles/{record_id}"
    elif source_id == "econbiz":
        url = f"https://api.econbiz.de/v1/record/{record_id}"
    elif source_id == "osti":
        url = f"https://www.osti.gov/api/v1/records/{record_id}"
    elif source_id == "nasa-ads":
        url = "https://api.adsabs.harvard.edu/v1/search/query"
        query += [("q", f'bibcode:"{record_id}"'), ("rows", "1"), ("fl", "bibcode,title,author,year,abstract,doi,citation_count,property")]
    elif source_id == "library-of-congress":
        url = f"https://www.loc.gov/item/{record_id}/"
        query += [("fo", "json")]
    elif source_id == "open-library":
        url = f"https://openlibrary.org/works/{record_id}.json"
    elif source_id == "europeana":
        url = f"https://api.europeana.eu/record/v2{record_id}.json"
    elif source_id == "dpla":
        url = f"https://api.dp.la/v2/items/{record_id}"
    else:
        raise ValueError(f"unsupported record source: {source_id}")
    return method, url, headers, query, body, credentials


def build(operation: str, parameters: Mapping[str, Any]):
    if operation == "literature-search":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_search(row, parameters)
    if operation == "literature-record":
        row = source_for(parameters.get("source_id"), operation)
        return row, build_record(row, parameters)
    if operation == "preprint-feed":
        row = source_for(parameters.get("source_id"), operation)
        source_id = str(row["source_id"])
        from_date = text(parameters.get("from_date"), "from_date", 10)
        until_date = text(parameters.get("until_date"), "until_date", 10)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", from_date) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", until_date):
            raise ValueError("from_date and until_date must be YYYY-MM-DD")
        cursor = bounded_int(parameters.get("cursor"), default=0, minimum=0, maximum=9999, name="cursor")
        url = f"https://api.biorxiv.org/details/{source_id}/{from_date}/{until_date}/{cursor}/json"
        return row, ("GET", url, {"Accept":"application/json","User-Agent":"evidence-data-center-literature/1.0"}, [], None, [])
    if operation in {"oai-identify", "oai-list-records", "oai-get-record"}:
        row = source_for(parameters.get("source_id"), operation)
        headers, query, credentials = credentials_for(row)
        headers.update({"Accept":"application/xml, text/xml;q=0.9","User-Agent":"evidence-data-center-literature/1.0"})
        if operation == "oai-identify":
            query += [("verb", "Identify")]
        elif operation == "oai-list-records":
            query += [("verb", "ListRecords"), ("metadataPrefix", text(parameters.get("metadata_prefix"), "metadata_prefix", 64))]
            if parameters.get("from_date"):
                query.append(("from", text(parameters["from_date"], "from_date", 10)))
            if parameters.get("until_date"):
                query.append(("until", text(parameters["until_date"], "until_date", 10)))
            if parameters.get("set"):
                query.append(("set", text(parameters["set"], "set", 200)))
        else:
            query += [("verb", "GetRecord"), ("identifier", text(parameters.get("identifier"), "identifier", 300)), ("metadataPrefix", text(parameters.get("metadata_prefix"), "metadata_prefix", 64))]
        return row, ("GET", str(row["base_url"]), headers, query, None, credentials)
    if operation == "sru-search":
        row = source_for(parameters.get("source_id"), operation)
        query_text = text(parameters.get("query"), "query", 500)
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        record_schema = str(parameters.get("record_schema") or "dc")
        if record_schema not in {"dc", "dcndl"}:
            raise ValueError("record_schema is not allowlisted")
        query = [("operation","searchRetrieve"),("version","1.2"),("query",query_text),("maximumRecords",str(limit)),("startRecord","1"),("recordSchema",record_schema)]
        return row, ("GET", str(row["base_url"]), {"Accept":"application/xml,text/xml;q=0.9","User-Agent":"evidence-data-center-literature/1.0"}, query, None, [])
    if operation == "patent-publication-get":
        row = source_for(parameters.get("source_id"), operation)
        number = text(parameters.get("publication_number"), "publication_number", 30)
        if not re.fullmatch(r"EP[0-9]{6,10}N[A-Z][0-9]", number):
            raise ValueError("publication_number is invalid")
        output_format = str(parameters.get("format") or "")
        if output_format not in {"formats","xml","html","pdf"}:
            raise ValueError("format is not allowlisted")
        suffix = "" if output_format == "formats" else f"/document.{output_format}"
        url = f"https://data.epo.org/publication-server/rest/v1.2/patents/{number}{suffix}"
        accept = {"formats":"text/html","xml":"application/xml","html":"text/html","pdf":"application/pdf"}[output_format]
        return row, ("GET", url, {"Accept":accept,"User-Agent":"evidence-data-center-literature/1.0"}, [], None, [])
    raise ValueError(f"unsupported operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    started_at = utc_now()
    started_perf = time.perf_counter()
    fixture = os.getenv("GLOBAL_LITERATURE_FIXTURE_MODE") == "1"
    snapshot = None
    failure = None
    status = "INTEL_LITERATURE_FAILED"
    metadata: dict[str, Any] = {"fixture_mode":fixture,"network_used":False,"upstream_called":False,"request_count":0,"credential_names":[],"automatic_pagination_used":False,"automatic_retry_used":False,"secret_values_exposed":False,"model_calls":0}
    try:
        if operation == "catalog-capabilities":
            snapshot = provider_row(CATALOG_PATH)
        elif operation == "source-access-matrix":
            snapshot = load_json(MATRIX_PATH)
        elif fixture:
            row, request = build(operation, ticket.get("parameters") or {})
            method, url, headers, query, body, credentials = request
            snapshot = {"fixture":True,"operation":operation,"source_id":row["source_id"],"method":method,"origin":f"{urlsplit(url).scheme}://{urlsplit(url).netloc}","path_template_verified":True,"query_names":[name for name,_ in query],"body_present":body is not None,"credential_names":credentials}
        else:
            row, request = build(operation, ticket.get("parameters") or {})
            method, url, headers, query, body, credentials = request
            acceptance = ticket.get("acceptance") or {}
            timeout = bounded_int(acceptance.get("timeout_seconds"), default=60, minimum=5, maximum=90, name="timeout_seconds")
            max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5000000, minimum=1024, maximum=15000000, name="max_response_bytes")
            response = requests.request(method, url, headers=headers, params=query, json=body, timeout=timeout, allow_redirects=False)
            raw = response.content
            metadata.update({"network_used":True,"upstream_called":True,"request_count":1,"source_id":row["source_id"],"source_name":row["name"],"source_category":row["category"],"credential_names":credentials,"http_status":response.status_code,"response_bytes":len(raw),"response_sha256":bytes_sha(raw),"request_origin":f"{urlsplit(url).scheme}://{urlsplit(url).netloc}","license_policy":row["license_policy"],"cost":row["cost"]})
            if 300 <= response.status_code < 400:
                raise RuntimeError("redirects are forbidden")
            response.raise_for_status()
            if len(raw) > max_bytes:
                raise RuntimeError("response exceeds max_response_bytes")
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" in content_type:
                target = output_dir / "source-document.pdf"
                target.write_bytes(raw)
                data: Any = {"content_type":content_type,"artifact_file":target.name}
            elif "json" in content_type:
                data = response.json()
            else:
                data = {"content_type":content_type,"text":response.text}
            snapshot = {"provider":"global-literature-libraries","operation":operation,"source_id":row["source_id"],"source_name":row["name"],"license_policy":row["license_policy"],"data":data}
        status = "INTEL_LITERATURE_COMPLETED"
    except Exception as exc:
        failure = {"type":type(exc).__name__,"message":str(exc)[:1500]}
    return finish_execution(ticket=ticket,output_dir=output_dir,status=status,snapshot=snapshot,metadata=metadata,failure=failure,started_at=started_at,started_perf=started_perf,schema_prefix="intel-literature")


def main() -> int:
    return run_cli(execute=execute,ticket_prefix="[intel-literature]",schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH,status_schema="intel-literature-ticket-status-v1",display_name="全球开放文献与资料库")


if __name__ == "__main__":
    raise SystemExit(main())
