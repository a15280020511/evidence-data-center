#!/usr/bin/env python3
"""Bounded runtime for institutional open knowledge APIs."""
from __future__ import annotations

import json
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
USER_AGENT = "evidence-data-center-institutional-knowledge/1.0"
QUERY_RE = re.compile(r"[^0-9A-Za-z\u00C0-\u024F\u3040-\u30FF\u3400-\u9FFF _.,:+()/&-]+")


def safe_text(value: Any, name: str, maximum: int, *, required: bool = True) -> str:
    rendered = str(value or "").strip()
    if not rendered and not required:
        return ""
    if not rendered or len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    return rendered


def safe_query(value: Any) -> str:
    rendered = safe_text(value, "query", 120)
    rendered = " ".join(QUERY_RE.sub(" ", rendered).split())
    if not rendered:
        raise ValueError("query contains no searchable text")
    return rendered


def reject_extra(parameters: Mapping[str, Any], allowed: set[str]) -> None:
    extra = set(parameters) - allowed
    if extra:
        raise ValueError(f"unsupported parameters: {sorted(extra)}")


def build_request(operation: str, parameters: Mapping[str, Any]):
    headers = {"Accept":"application/json, application/xml;q=0.9, text/xml;q=0.9", "User-Agent":USER_AGENT}
    query: list[tuple[str,str]] = []
    if operation == "catalog-capabilities":
        reject_extra(parameters, set())
        return None, "LOCAL", headers, query, "catalog"
    if operation == "source-access-matrix":
        reject_extra(parameters, set())
        return None, "LOCAL", headers, query, "matrix"
    if operation == "fraser-oai-identify":
        reject_extra(parameters, set())
        headers["Accept"] = "application/xml, text/xml;q=0.9"
        query.append(("verb","Identify"))
        return "https://fraser.stlouisfed.org/oai", "GET", headers, query, "fraser-oai"
    if operation == "fraser-oai-list-records":
        reject_extra(parameters, {"from_date","until_date","set"})
        headers["Accept"] = "application/xml, text/xml;q=0.9"
        query.extend([("verb","ListRecords"),("metadataPrefix","mods")])
        for field in ("from_date","until_date"):
            value = safe_text(parameters.get(field), field, 10, required=False)
            if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError(f"{field} must be YYYY-MM-DD")
            if value:
                query.append(("from" if field == "from_date" else "until", value))
        set_name = safe_text(parameters.get("set"), "set", 100, required=False)
        if set_name:
            if not re.fullmatch(r"[A-Za-z0-9._:-]+", set_name):
                raise ValueError("set is invalid")
            query.append(("set", set_name))
        return "https://fraser.stlouisfed.org/oai", "GET", headers, query, "fraser-oai"
    if operation == "osdr-datasets":
        reject_extra(parameters, set())
        query.append(("format","json"))
        return "https://visualization.osdr.nasa.gov/biodata/api/v2/datasets/", "GET", headers, query, "nasa-osdr-biodata"
    if operation == "osdr-dataset-metadata":
        reject_extra(parameters, {"accession"})
        accession = safe_text(parameters.get("accession"), "accession", 12)
        if not re.fullmatch(r"OSD-[0-9]{1,8}", accession):
            raise ValueError("accession is invalid")
        query.append(("format","json"))
        url = f"https://visualization.osdr.nasa.gov/biodata/api/v2/dataset/{quote(accession, safe='-')}/"
        return url, "GET", headers, query, "nasa-osdr-biodata"
    if operation == "japan-indicator-search":
        reject_extra(parameters, {"query"})
        query.extend([("Lang","EN"),("SearchIndicatorWord",safe_query(parameters.get("query")))])
        return "https://dashboard.e-stat.go.jp/api/1.0/Json/getIndicatorInfo", "GET", headers, query, "japan-statistics-dashboard"
    if operation == "japan-indicator-data":
        reject_extra(parameters, {"indicator_code","cycle","regional_rank","seasonal_adjustment"})
        code = safe_text(parameters.get("indicator_code"), "indicator_code", 19)
        if not re.fullmatch(r"[0-9]{19}", code):
            raise ValueError("indicator_code is invalid")
        cycle = bounded_int(parameters.get("cycle"), default=3, minimum=1, maximum=4, name="cycle")
        rank = bounded_int(parameters.get("regional_rank"), default=2, minimum=1, maximum=4, name="regional_rank")
        seasonal = bounded_int(parameters.get("seasonal_adjustment"), default=1, minimum=1, maximum=2, name="seasonal_adjustment")
        query.extend([("Lang","EN"),("IndicatorCode",code),("Cycle",str(cycle)),("RegionalRank",str(rank)),("IsSeasonalAdjustment",str(seasonal)),("MetaGetFlg","Y"),("SectionHeaderFlg","1")])
        return "https://dashboard.e-stat.go.jp/api/1.0/Json/getData", "GET", headers, query, "japan-statistics-dashboard"
    raise ValueError(f"unsupported operation: {operation}")


def parse(raw: bytes, content_type: str) -> Any:
    if "json" in content_type.lower():
        return json.loads(raw.decode("utf-8"))
    text = raw.decode("utf-8", errors="replace")
    return {"content_type":content_type,"text":text[:2_000_000],"truncated":len(text)>2_000_000}


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = bounded_int(acceptance.get("timeout_seconds"), default=45, minimum=5, maximum=90, name="timeout_seconds")
    max_bytes = bounded_int(acceptance.get("max_response_bytes"), default=5_000_000, minimum=1024, maximum=10_000_000, name="max_response_bytes")
    started_at, started_perf = utc_now(), time.perf_counter()
    status, failure, snapshot = "INTEL_INSTITUTIONAL_KNOWLEDGE_FAILED", None, None
    metadata: dict[str,Any] = {"upstream_called":False,"request_count":0,"automatic_pagination":False,"resumption_token_following":False,"automatic_retry":False,"redirects_allowed":False,"write_operations_allowed":False,"secret_values_exposed":False,"model_calls":0}
    try:
        url, method, headers, query, source_id = build_request(operation, parameters)
        if method == "LOCAL":
            snapshot = {"provider":provider_row(CATALOG_PATH)} if source_id == "catalog" else {"source_access_matrix":load_json(MATRIX_PATH)}
        else:
            response = requests.get(str(url), params=query, headers=headers, timeout=timeout, allow_redirects=False)
            raw = response.content
            if len(raw) > max_bytes:
                raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
            if not 200 <= response.status_code < 300:
                raise RuntimeError(f"upstream HTTP {response.status_code}: {raw[:1000].decode('utf-8', errors='replace')}")
            content_type = response.headers.get("Content-Type", "")
            data = parse(raw, content_type)
            (output_dir / ("upstream-response.json" if "json" in content_type.lower() else "upstream-response.xml")).write_bytes(raw)
            snapshot = {"source_id":source_id,"operation":operation,"data":data}
            metadata.update({"upstream_called":True,"request_count":1,"api_origin":urlparse(str(url)).hostname,"http_method":method,"http_status":response.status_code,"content_type":content_type,"response_bytes":len(raw),"response_sha256":bytes_sha(raw),"credential_mode":"none"})
        status = "INTEL_INSTITUTIONAL_KNOWLEDGE_COMPLETED"
    except Exception as exc:
        failure = {"type":type(exc).__name__,"message":str(exc)[:2000]}
    return finish_execution(ticket=ticket, output_dir=output_dir, status=status, snapshot=snapshot, metadata=metadata, failure=failure, started_at=started_at, started_perf=started_perf, schema_prefix="institutional-open-knowledge")


if __name__ == "__main__":
    raise SystemExit(run_cli(execute=execute, ticket_prefix="[intel-institutional-knowledge]", schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH, status_schema="institutional-open-knowledge-ticket-status-v1", display_name="全球机构开放知识API"))
