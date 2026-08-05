#!/usr/bin/env python3
"""Bounded runtime for public government, university and research APIs."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
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
USER_AGENT = "evidence-data-center-public-institution/1.1"
PLAIN_TEXT_RE = re.compile(r"[^0-9A-Za-z\u00C0-\u024F\u3040-\u30FF\u3400-\u9FFF _.,:+*/-]+")
DATAFLOW_RE = re.compile(r"^[A-Z0-9_,.:-]{1,80}$")
DATA_KEY_RE = re.compile(r"^[A-Za-z0-9.*+_,:-]{1,300}$")
UUID_RE = re.compile(
    r"^[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-"
    r"[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}$"
)
CHEMSYS_RE = re.compile(r"^[A-Z][a-z]?(?:-[A-Z][a-z]?){0,7}$")
NIPO_OBJECT_RE = re.compile(r"^[A-Za-z0-9-]{1,80}$")
NIPO_APPLICATION_RE = re.compile(r"^[A-Za-z0-9./-]{1,80}$")
NIPO_TYPES = {1, 2, 3, 4, 5, 6, 10, 11, 12, 13}
NIPO_STATES = {1, 2}


def safe_text(value: Any, name: str, maximum: int, *, required: bool = True) -> str:
    rendered = str(value or "").strip()
    if not rendered and not required:
        return ""
    if not rendered or len(rendered) > maximum or any(ord(ch) < 32 for ch in rendered):
        raise ValueError(f"{name} is invalid")
    return rendered


def safe_query(
    value: Any,
    name: str = "query",
    maximum: int = 200,
    *,
    required: bool = True,
) -> str:
    rendered = safe_text(value, name, maximum, required=required)
    if not rendered:
        return ""
    rendered = PLAIN_TEXT_RE.sub(" ", rendered)
    rendered = " ".join(rendered.split())
    if required and not rendered:
        raise ValueError(f"{name} contains no searchable text")
    return rendered


def credential(name: str, *, required: bool) -> str:
    value = str(os.getenv(name) or "").strip()
    if required and not value:
        raise RuntimeError(f"required backend credential is not configured: {name}")
    if len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise RuntimeError(f"invalid backend credential: {name}")
    return value


def operation_parameters(parameters: Mapping[str, Any], allowed: set[str]) -> None:
    unsupported = set(parameters) - allowed
    if unsupported:
        raise ValueError(f"unsupported parameters: {sorted(unsupported)}")


def nipo_enum(value: Any, name: str, allowed: set[int], *, required: bool = False) -> int | None:
    if value in (None, ""):
        if required:
            raise ValueError(f"{name} is required")
        return None
    try:
        rendered = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} is invalid") from exc
    if rendered not in allowed:
        raise ValueError(f"{name} is invalid")
    return rendered


def nipo_date(value: Any, name: str, *, required: bool = False) -> datetime | None:
    rendered = safe_text(value, name, 10, required=required)
    if not rendered:
        return None
    try:
        return datetime.strptime(rendered, "%d.%m.%Y")
    except ValueError as exc:
        raise ValueError(f"{name} must use dd.mm.yyyy") from exc


def append_nipo_date_window(
    query: list[tuple[str, str]],
    parameters: Mapping[str, Any],
    prefix: str,
) -> bool:
    start_name = f"{prefix}_from"
    end_name = f"{prefix}_to"
    start = nipo_date(parameters.get(start_name), start_name)
    end = nipo_date(parameters.get(end_name), end_name)
    if (start is None) != (end is None):
        raise ValueError(f"{start_name} and {end_name} must be supplied together")
    if start is None or end is None:
        return False
    if start > end:
        raise ValueError(f"{start_name} must not be after {end_name}")
    if (end - start).days > 31:
        raise ValueError(f"{prefix} window must not exceed 31 days")
    query.extend(
        [
            (start_name, start.strftime("%d.%m.%Y")),
            (end_name, end.strftime("%d.%m.%Y")),
        ]
    )
    return True


def build_request(operation: str, parameters: Mapping[str, Any]):
    headers = {
        "Accept": "application/json, application/xml;q=0.8, text/xml;q=0.8, text/csv;q=0.7",
        "User-Agent": USER_AGENT,
    }
    query: list[tuple[str, str]] = []
    credentials_used: list[str] = []
    source_id = "local"

    if operation == "catalog-capabilities":
        operation_parameters(parameters, set())
        return None, "LOCAL", headers, query, None, credentials_used, "catalog"
    if operation == "source-access-matrix":
        operation_parameters(parameters, set())
        return None, "LOCAL", headers, query, None, credentials_used, "matrix"

    if operation == "singapore-collections":
        operation_parameters(parameters, {"page"})
        source_id = "singapore-data-gov"
        page = bounded_int(parameters.get("page"), default=1, minimum=1, maximum=100, name="page")
        query.append(("page", str(page)))
        key = credential("SINGAPORE_DATA_GOV_API_KEY", required=False)
        if key:
            headers["x-api-key"] = key
            credentials_used.append("SINGAPORE_DATA_GOV_API_KEY")
        return (
            "https://api-production.data.gov.sg/v2/public/api/collections",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "singapore-collection-metadata":
        operation_parameters(parameters, {"collection_id", "include_dataset_metadata"})
        source_id = "singapore-data-gov"
        collection_id = bounded_int(
            parameters.get("collection_id"),
            default=0,
            minimum=1,
            maximum=1_000_000_000,
            name="collection_id",
        )
        include = bool(parameters.get("include_dataset_metadata", True))
        query.append(("withDatasetMetadata", "true" if include else "false"))
        key = credential("SINGAPORE_DATA_GOV_API_KEY", required=False)
        if key:
            headers["x-api-key"] = key
            credentials_used.append("SINGAPORE_DATA_GOV_API_KEY")
        url = (
            "https://api-production.data.gov.sg/v2/public/api/collections/"
            f"{collection_id}/metadata"
        )
        return url, "GET", headers, query, None, credentials_used, source_id

    if operation == "abs-dataflows":
        operation_parameters(parameters, set())
        source_id = "australia-abs-data-api"
        headers["Accept"] = (
            "application/vnd.sdmx.structure+json;version=2.0.0, application/xml;q=0.8"
        )
        query.extend([("detail", "allstubs"), ("references", "none")])
        return (
            "https://data.api.abs.gov.au/rest/dataflow/ABS/all/latest",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "abs-data":
        operation_parameters(parameters, {"dataflow", "data_key", "last_n_observations"})
        source_id = "australia-abs-data-api"
        dataflow = safe_text(parameters.get("dataflow"), "dataflow", 80)
        data_key = safe_text(parameters.get("data_key"), "data_key", 300)
        if not DATAFLOW_RE.fullmatch(dataflow) or not DATA_KEY_RE.fullmatch(data_key):
            raise ValueError("ABS dataflow or data_key is invalid")
        last_n = bounded_int(
            parameters.get("last_n_observations"),
            default=1,
            minimum=1,
            maximum=24,
            name="last_n_observations",
        )
        query.extend([("format", "jsondata"), ("lastNObservations", str(last_n))])
        url = (
            "https://data.api.abs.gov.au/rest/data/"
            f"{quote(dataflow, safe=',.:-')}/{quote(data_key, safe='.*+_,:-')}"
        )
        return url, "GET", headers, query, None, credentials_used, source_id

    if operation == "cnra-dataset-search":
        operation_parameters(parameters, {"query", "limit"})
        source_id = "california-cnra-ckan"
        search = safe_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        query.extend([("q", search), ("rows", str(limit)), ("start", "0")])
        return (
            "https://data.cnra.ca.gov/api/3/action/package_search",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "bps-domain-list":
        operation_parameters(parameters, {"domain_type", "province_code"})
        source_id = "indonesia-bps"
        domain_type = str(parameters.get("domain_type") or "all").strip().lower()
        if domain_type not in {"all", "prov", "kab", "kabbyprov"}:
            raise ValueError("domain_type is invalid")
        query.append(("type", domain_type))
        province = str(parameters.get("province_code") or "").strip()
        if domain_type == "kabbyprov":
            if not re.fullmatch(r"[0-9]{2,4}", province):
                raise ValueError("province_code is required for kabbyprov")
            query.append(("prov", province))
        key = credential("BPS_API_KEY", required=True)
        query.append(("key", key))
        credentials_used.append("BPS_API_KEY")
        return (
            "https://webapi.bps.go.id/v1/api/domain",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "estat-stats-list":
        operation_parameters(parameters, {"query", "limit"})
        source_id = "japan-estat"
        search = safe_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=100, name="limit")
        app_id = credential("ESTAT_APP_ID", required=True)
        query.extend([("appId", app_id), ("searchWord", search), ("limit", str(limit)), ("lang", "E")])
        credentials_used.append("ESTAT_APP_ID")
        return (
            "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "estat-stats-data":
        operation_parameters(parameters, {"stats_data_id", "limit"})
        source_id = "japan-estat"
        stats_id = safe_text(parameters.get("stats_data_id"), "stats_data_id", 80)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", stats_id):
            raise ValueError("stats_data_id is invalid")
        limit = bounded_int(parameters.get("limit"), default=100, minimum=1, maximum=1000, name="limit")
        app_id = credential("ESTAT_APP_ID", required=True)
        query.extend([("appId", app_id), ("statsDataId", stats_id), ("limit", str(limit)), ("lang", "E")])
        credentials_used.append("ESTAT_APP_ID")
        return (
            "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "materials-summary-search":
        operation_parameters(parameters, {"chemical_system", "limit"})
        source_id = "materials-project"
        chemsys = safe_text(parameters.get("chemical_system"), "chemical_system", 60)
        if not CHEMSYS_RE.fullmatch(chemsys):
            raise ValueError("chemical_system is invalid")
        limit = bounded_int(parameters.get("limit"), default=10, minimum=1, maximum=20, name="limit")
        key = credential("MATERIALS_PROJECT_API_KEY", required=True)
        headers["X-API-KEY"] = key
        credentials_used.append("MATERIALS_PROJECT_API_KEY")
        fields = (
            "material_id,formula_pretty,chemsys,band_gap,density,volume,"
            "is_stable,energy_above_hull"
        )
        query.extend([("chemsys", chemsys), ("_fields", fields), ("_limit", str(limit))])
        return (
            "https://api.materialsproject.org/materials/summary/",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "india-resource-get":
        operation_parameters(parameters, {"resource_id", "limit"})
        source_id = "india-data-gov"
        resource_id = safe_text(parameters.get("resource_id"), "resource_id", 36)
        if not UUID_RE.fullmatch(resource_id):
            raise ValueError("resource_id must be a UUID")
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        key = credential("INDIA_DATA_GOV_API_KEY", required=True)
        query.extend([("api-key", key), ("format", "json"), ("offset", "0"), ("limit", str(limit))])
        credentials_used.append("INDIA_DATA_GOV_API_KEY")
        url = f"https://api.data.gov.in/resource/{resource_id}"
        return url, "GET", headers, query, None, credentials_used, source_id

    if operation == "brazil-dataset-list":
        operation_parameters(parameters, {"query", "page"})
        source_id = "brazil-dados-gov"
        page = bounded_int(parameters.get("page"), default=1, minimum=1, maximum=1000, name="page")
        search = safe_query(parameters.get("query"), required=False)
        token = credential("BRAZIL_DADOS_GOV_TOKEN", required=True)
        headers["Authorization"] = f"Bearer {token}"
        credentials_used.append("BRAZIL_DADOS_GOV_TOKEN")
        query.extend([("pagina", str(page)), ("dadosAbertos", "true"), ("isPrivado", "false")])
        if search:
            query.append(("nomeConjuntoDados", search))
        return (
            "https://dados.gov.br/dados/api/publico/conjuntos-dados",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "asu-dataverse-search":
        operation_parameters(parameters, {"query", "limit"})
        source_id = "asu-dataverse"
        search = safe_query(parameters.get("query"))
        limit = bounded_int(parameters.get("limit"), default=20, minimum=1, maximum=50, name="limit")
        query.extend([("q", search), ("type", "dataset"), ("per_page", str(limit)), ("start", "0")])
        return (
            "https://dataverse.asu.edu/api/search",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "asu-oai-identify":
        operation_parameters(parameters, set())
        source_id = "asu-dataverse"
        headers["Accept"] = "application/xml, text/xml;q=0.9"
        query.append(("verb", "Identify"))
        return (
            "https://dataverse.asu.edu/oai",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "uk-api-catalogue-csv":
        operation_parameters(parameters, set())
        source_id = "uk-api-catalogue"
        headers["Accept"] = "text/csv, text/plain;q=0.9"
        return (
            "https://raw.githubusercontent.com/co-cddo/api-catalogue/main/data/catalogue.csv",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "nipo-open-data-search":
        operation_parameters(
            parameters,
            {
                "obj_type",
                "obj_state",
                "app_date_from",
                "app_date_to",
                "reg_date_from",
                "reg_date_to",
                "last_update_from",
                "last_update_to",
                "app_number",
            },
        )
        source_id = "ukraine-nipo"
        obj_type = nipo_enum(parameters.get("obj_type"), "obj_type", NIPO_TYPES)
        obj_state = nipo_enum(parameters.get("obj_state"), "obj_state", NIPO_STATES)
        if obj_type is not None:
            query.append(("obj_type", str(obj_type)))
        if obj_state is not None:
            query.append(("obj_state", str(obj_state)))

        has_window = False
        for prefix in ("app_date", "reg_date", "last_update"):
            has_window = append_nipo_date_window(query, parameters, prefix) or has_window

        app_number = safe_text(
            parameters.get("app_number"),
            "app_number",
            80,
            required=False,
        )
        if app_number:
            if not NIPO_APPLICATION_RE.fullmatch(app_number):
                raise ValueError("app_number is invalid")
            query.append(("app_number", app_number))

        if not app_number:
            if obj_type is None:
                raise ValueError("obj_type is required for bounded NIPO list queries")
            if not has_window:
                raise ValueError(
                    "a complete application, registration or last-update date window is required"
                )

        return (
            "https://sis.nipo.gov.ua/api/v1/open-data/",
            "GET",
            headers,
            query,
            None,
            credentials_used,
            source_id,
        )

    if operation == "nipo-open-data-record":
        operation_parameters(parameters, {"object_id", "obj_type"})
        source_id = "ukraine-nipo"
        object_id = safe_text(parameters.get("object_id"), "object_id", 80)
        if not NIPO_OBJECT_RE.fullmatch(object_id):
            raise ValueError("object_id is invalid")
        obj_type = nipo_enum(parameters.get("obj_type"), "obj_type", NIPO_TYPES)
        if obj_type is not None:
            query.append(("obj_type", str(obj_type)))
        url = (
            "https://sis.nipo.gov.ua/api/v1/open-data/"
            f"{quote(object_id, safe='-')}/"
        )
        return url, "GET", headers, query, None, credentials_used, source_id

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
    status = "INTEL_PUBLIC_INSTITUTION_APIS_FAILED"
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
            lowered = content_type.lower()
            if "json" in lowered:
                suffix = "json"
            elif "csv" in lowered or operation == "uk-api-catalogue-csv":
                suffix = "csv"
            else:
                suffix = "txt"
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
        status = "INTEL_PUBLIC_INSTITUTION_APIS_COMPLETED"
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
        schema_prefix="global-public-institution",
    )


if __name__ == "__main__":
    raise SystemExit(
        run_cli(
            execute=execute,
            ticket_prefix="[intel-public-institution]",
            schema_path=SCHEMA_PATH,
            catalog_path=CATALOG_PATH,
            status_schema="global-public-institution-ticket-status-v1",
            display_name="全球公共机构与科研数据库API",
        )
    )
