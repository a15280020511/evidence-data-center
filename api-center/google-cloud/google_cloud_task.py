#!/usr/bin/env python3
"""Managed, read-only BigQuery and Earth Engine execution for API-center tickets."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote

import requests
import sqlglot
from sqlglot import exp
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
BIGQUERY_SERVICE_ACCOUNT_ENV = "BIGQUERY_SERVICE_ACCOUNT_JSON"
EARTH_ENGINE_SERVICE_ACCOUNT_ENV = "EARTH_ENGINE_SERVICE_ACCOUNT_JSON"
DEFAULT_BIGQUERY_PROJECTS = {"bigquery-public-data", "gdelt-bq", "patents-public-data"}
PROJECT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")
RESOURCE_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,1023}$")
WORKLOAD_TAG_RE = re.compile(r"^[A-Za-z0-9_-]{1,63}$")
BIGQUERY_DENIED = re.compile(
    r"\b(?:CREATE|INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|TRUNCATE|EXPORT|LOAD|CALL|"
    r"GRANT|REVOKE|BEGIN|COMMIT|ROLLBACK|DECLARE|SET|ASSERT|EXECUTE\s+IMMEDIATE|"
    r"EXTERNAL_QUERY|REMOTE_FUNCTION|CONNECTION)\b",
    re.IGNORECASE,
)
BIGQUERY_UNQUALIFIED_FROM = re.compile(
    r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+){0,1})\b",
    re.IGNORECASE,
)
BIGQUERY_BACKTICK_REF = re.compile(r"`([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_*$-]+)`")
EE_DENIED_FUNCTION_PARTS = (
    "export",
    "createasset",
    "deleteasset",
    "setasset",
    "copyasset",
    "renameasset",
    "ingest",
    "upload",
    "import",
    "thumbnail",
    "video",
    "mapid",
    "getdownloadurl",
    "getthumburl",
)
EE_STAC_ROOT = "https://storage.googleapis.com/earthengine-stac/catalog/catalog.json"
EE_STAC_OBJECTS = "https://storage.googleapis.com/storage/v1/b/earthengine-stac/o"
EE_STAC_MEDIA_PREFIX = "https://storage.googleapis.com/earthengine-stac/"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def _catalog_operations() -> dict[tuple[str, str], Mapping[str, Any]]:
    catalog = load_json(CATALOG_PATH)
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for provider in catalog["providers"]:
        provider_id = str(provider["provider_id"])
        for operation in provider["operations"]:
            result[(provider_id, str(operation["operation_id"]))] = operation
    return result


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}"
            for item in errors[:20]
        )
        raise ValueError(rendered)
    key = (str(ticket["provider"]), str(ticket["operation"]))
    operation = _catalog_operations().get(key)
    if operation is None:
        raise ValueError(f"unsupported provider operation: {key[0]}/{key[1]}")
    allowed = {str(name) for name in operation.get("parameters", [])}
    unexpected = sorted(set(ticket.get("parameters", {})) - allowed)
    if unexpected:
        raise ValueError(f"non-allowlisted parameters: {unexpected}")


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = load_json(event_path)
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    accepted = False
    reason = ""
    ticket: Mapping[str, Any] | None = None
    try:
        if not title.startswith("[api-gcp]"):
            raise ValueError("issue title must start with [api-gcp]")
        parsed = json.loads(body)
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "google-cloud-ticket-status-v1",
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", "true" if accepted else "false")
    write_output("reason", reason)
    return 0 if accepted else 1


def _credential_secret_name(provider: str, operation: str) -> str | None:
    if provider == "bigquery":
        return BIGQUERY_SERVICE_ACCOUNT_ENV
    if provider == "earth-engine" and operation in {
        "catalog-algorithms",
        "compute-value-readonly",
    }:
        return EARTH_ENGINE_SERVICE_ACCOUNT_ENV
    return None


def _credentials(secret_name: str) -> tuple[service_account.Credentials, str]:
    if secret_name not in {
        BIGQUERY_SERVICE_ACCOUNT_ENV,
        EARTH_ENGINE_SERVICE_ACCOUNT_ENV,
    }:
        raise ValueError(f"unsupported Google credential secret: {secret_name}")
    raw = str(os.getenv(secret_name) or "").strip()
    if not raw:
        raise RuntimeError(f"missing repository Secret {secret_name}")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{secret_name} is not valid JSON") from exc
    if not isinstance(info, Mapping):
        raise RuntimeError(f"{secret_name} must contain a service-account JSON object")
    project_id = str(info.get("project_id") or "")
    if not PROJECT_ID_RE.fullmatch(project_id):
        raise RuntimeError(f"{secret_name} has no valid project_id")
    scopes = ["https://www.googleapis.com/auth/cloud-platform.read-only"]
    if secret_name == BIGQUERY_SERVICE_ACCOUNT_ENV:
        scopes.append("https://www.googleapis.com/auth/bigquery.readonly")
    else:
        scopes.append("https://www.googleapis.com/auth/earthengine.readonly")
    credentials = service_account.Credentials.from_service_account_info(
        dict(info),
        scopes=scopes,
    )
    credentials.refresh(GoogleAuthRequest())
    if not credentials.token:
        raise RuntimeError("Google OAuth token refresh returned no token")
    return credentials, project_id


def _allowed_bigquery_projects() -> set[str]:
    projects = set(DEFAULT_BIGQUERY_PROJECTS)
    raw = str(os.getenv("BIGQUERY_ALLOWED_PUBLIC_PROJECTS") or "")
    for item in raw.split(","):
        candidate = item.strip()
        if candidate:
            if not PROJECT_ID_RE.fullmatch(candidate):
                raise ValueError(f"invalid BIGQUERY_ALLOWED_PUBLIC_PROJECTS entry: {candidate}")
            projects.add(candidate)
    return projects


def _require_project(value: Any) -> str:
    project = str(value or "")
    if not PROJECT_ID_RE.fullmatch(project):
        raise ValueError("project_id is invalid")
    if project not in _allowed_bigquery_projects():
        raise ValueError(f"project_id is not in the public-project allowlist: {project}")
    return project


def _require_resource(value: Any, name: str) -> str:
    text = str(value or "")
    if not RESOURCE_ID_RE.fullmatch(text):
        raise ValueError(f"{name} is invalid")
    return text


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int, name: str) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None,
    params: Mapping[str, Any] | None = None,
    body: Mapping[str, Any] | None = None,
    timeout: int = 30,
    max_bytes: int = 10_000_000,
) -> tuple[dict[str, Any], dict[str, Any]]:
    headers = {"Accept": "application/json", "User-Agent": "gpts-google-cloud-api-center/1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(
        method,
        url,
        headers=headers,
        params=dict(params or {}),
        json=dict(body) if body is not None else None,
        timeout=timeout,
    )
    raw = response.content
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds internal limit of {max_bytes} bytes")
    try:
        payload = response.json() if raw else {}
    except ValueError as exc:
        raise RuntimeError(f"upstream returned non-JSON HTTP {response.status_code}") from exc
    if not response.ok:
        message = payload.get("error") if isinstance(payload, Mapping) else payload
        raise RuntimeError(f"upstream HTTP {response.status_code}: {message}")
    metadata = {
        "http_status": response.status_code,
        "content_type": response.headers.get("Content-Type", ""),
        "request_url": response.url.split("?", 1)[0],
    }
    return dict(payload), metadata


def _bigquery_catalog(operation: str, params: Mapping[str, Any], token: str, billing_project: str, timeout: int) -> tuple[Any, dict[str, Any]]:
    base = "https://bigquery.googleapis.com/bigquery/v2"
    if operation == "catalog-projects":
        return {
            "public_projects": sorted(_allowed_bigquery_projects()),
            "billing_project": billing_project,
            "billing_project_data_access_enabled": False,
        }, {"http_status": 200, "catalog_source": "repository-policy"}
    project = _require_project(params.get("project_id"))
    max_results = _bounded_int(params.get("max_results"), default=100, minimum=1, maximum=1000, name="max_results")
    query: dict[str, Any] = {"maxResults": max_results}
    if params.get("page_token"):
        query["pageToken"] = str(params["page_token"])
    if operation == "catalog-datasets":
        query["all"] = "true"
        return _http_json("GET", f"{base}/projects/{quote(project)}/datasets", token=token, params=query, timeout=timeout)
    dataset = _require_resource(params.get("dataset_id"), "dataset_id")
    prefix = f"{base}/projects/{quote(project)}/datasets/{quote(dataset)}"
    if operation == "catalog-tables":
        return _http_json("GET", f"{prefix}/tables", token=token, params=query, timeout=timeout)
    if operation == "catalog-routines":
        return _http_json("GET", f"{prefix}/routines", token=token, params=query, timeout=timeout)
    if operation == "catalog-models":
        return _http_json("GET", f"{prefix}/models", token=token, params=query, timeout=timeout)
    if operation == "catalog-table":
        table = _require_resource(params.get("table_id"), "table_id")
        return _http_json("GET", f"{prefix}/tables/{quote(table)}", token=token, timeout=timeout)
    raise ValueError(f"unsupported BigQuery catalog operation: {operation}")


def _strip_sql_comments(sql: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n\r]*", " ", without_blocks)


def _validate_readonly_sql(sql: str) -> tuple[str, set[str]]:
    if not sql or len(sql) > 20_000:
        raise ValueError("sql must contain 1 to 20000 characters")
    clean = _strip_sql_comments(sql).strip()
    if clean.endswith(";"):
        clean = clean[:-1].rstrip()
    if ";" in clean:
        raise ValueError("multiple SQL statements are forbidden")
    if not re.match(r"^(?:SELECT|WITH)\b", clean, flags=re.IGNORECASE):
        raise ValueError("only a single SELECT or WITH query is allowed")
    if BIGQUERY_DENIED.search(clean):
        raise ValueError("query contains a forbidden write, script, export, or external operation")
    try:
        statements = sqlglot.parse(clean, read="bigquery")
    except sqlglot.errors.ParseError as exc:
        raise ValueError(f"invalid GoogleSQL: {exc}") from exc
    if len(statements) != 1 or statements[0] is None:
        raise ValueError("exactly one GoogleSQL statement is required")
    tree = statements[0]
    if not any(True for _ in tree.find_all(exp.Select)):
        raise ValueError("query must contain a SELECT")
    cte_names = {
        str(cte.alias_or_name or "").casefold()
        for cte in tree.find_all(exp.CTE)
        if str(cte.alias_or_name or "")
    }
    projects: set[str] = set()
    for table in tree.find_all(exp.Table):
        name = str(table.name or "")
        project = str(table.catalog or "")
        dataset = str(table.db or "")
        if not project and not dataset and name.casefold() in cte_names:
            continue
        if not project or not dataset:
            raise ValueError(
                f"physical BigQuery table {name or '<unknown>'} must use a fully qualified project.dataset.table name"
            )
        projects.add(project)
    disallowed = sorted(projects - _allowed_bigquery_projects())
    if disallowed:
        raise ValueError(f"query references non-allowlisted projects: {disallowed}")
    return clean, projects


def _decode_bq_value(field: Mapping[str, Any], value: Any) -> Any:
    field_type = str(field.get("type") or "")
    mode = str(field.get("mode") or "NULLABLE")
    if value is None:
        return None
    if mode == "REPEATED" and isinstance(value, list):
        nested = dict(field)
        nested["mode"] = "NULLABLE"
        return [_decode_bq_value(nested, item.get("v") if isinstance(item, Mapping) else item) for item in value]
    if field_type in {"RECORD", "STRUCT"} and isinstance(value, Mapping):
        cells = value.get("f") if isinstance(value.get("f"), list) else []
        children = field.get("fields") if isinstance(field.get("fields"), list) else []
        return {
            str(child.get("name") or index): _decode_bq_value(child, cells[index].get("v") if index < len(cells) and isinstance(cells[index], Mapping) else None)
            for index, child in enumerate(children)
        }
    if field_type in {"INTEGER", "INT64"}:
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if field_type in {"FLOAT", "FLOAT64", "NUMERIC", "BIGNUMERIC"}:
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    if field_type in {"BOOLEAN", "BOOL"}:
        return str(value).lower() == "true"
    return value


def _decode_bq_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = payload.get("schema", {}).get("fields", []) if isinstance(payload.get("schema"), Mapping) else []
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    decoded: list[dict[str, Any]] = []
    for row in rows:
        cells = row.get("f") if isinstance(row, Mapping) and isinstance(row.get("f"), list) else []
        decoded.append({
            str(field.get("name") or index): _decode_bq_value(
                field,
                cells[index].get("v") if index < len(cells) and isinstance(cells[index], Mapping) else None,
            )
            for index, field in enumerate(fields)
        })
    return decoded


def _bigquery_query(params: Mapping[str, Any], token: str, billing_project: str, timeout: int) -> tuple[Any, dict[str, Any]]:
    sql, referenced_projects = _validate_readonly_sql(str(params.get("sql") or ""))
    maximum_bytes = _bounded_int(
        params.get("maximum_bytes_billed"),
        default=1_000_000_000,
        minimum=1_000_000,
        maximum=10_000_000_000,
        name="maximum_bytes_billed",
    )
    max_rows = _bounded_int(params.get("max_rows"), default=1000, minimum=1, maximum=5000, name="max_rows")
    timeout_ms = _bounded_int(params.get("timeout_ms"), default=30_000, minimum=1000, maximum=120_000, name="timeout_ms")
    location = str(params.get("location") or "US")
    if not re.fullmatch(r"[A-Za-z0-9-]{2,32}", location):
        raise ValueError("location is invalid")
    query_parameters: list[Any] = []
    raw_query_parameters = str(params.get("query_parameters_json") or "").strip()
    if raw_query_parameters:
        parsed = json.loads(raw_query_parameters)
        if not isinstance(parsed, list) or len(parsed) > 50:
            raise ValueError("query_parameters_json must be an array of at most 50 entries")
        query_parameters = parsed
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{quote(billing_project)}/queries"
    common = {
        "query": sql,
        "useLegacySql": False,
        "location": location,
        "maximumBytesBilled": str(maximum_bytes),
        "parameterMode": "NAMED" if query_parameters else None,
        "queryParameters": query_parameters or None,
    }
    common = {key: value for key, value in common.items() if value is not None}
    dry_run, dry_meta = _http_json(
        "POST",
        url,
        token=token,
        body={**common, "dryRun": True},
        timeout=timeout,
    )
    estimated = int(dry_run.get("totalBytesProcessed") or 0)
    if estimated > maximum_bytes:
        raise RuntimeError(
            f"dry-run estimates {estimated} bytes, above maximum_bytes_billed={maximum_bytes}"
        )
    result, exec_meta = _http_json(
        "POST",
        url,
        token=token,
        body={
            **common,
            "dryRun": False,
            "maxResults": max_rows,
            "timeoutMs": timeout_ms,
            "useQueryCache": True,
            "jobTimeoutMs": str(timeout_ms),
            "requestId": hashlib.sha256(sql.encode("utf-8")).hexdigest()[:32],
        },
        timeout=max(timeout, (timeout_ms // 1000) + 5),
    )
    if not result.get("jobComplete", False):
        raise RuntimeError("BigQuery job did not complete within the allowed synchronous timeout")
    return {
        "schema": result.get("schema") or {},
        "rows": _decode_bq_rows(result),
        "total_rows": int(result.get("totalRows") or 0),
        "returned_rows": len(result.get("rows") or []),
        "estimated_bytes_processed": estimated,
        "total_bytes_processed": int(result.get("totalBytesProcessed") or estimated),
        "total_bytes_billed": int(result.get("totalBytesBilled") or 0),
        "cache_hit": bool(result.get("cacheHit")),
        "referenced_projects": sorted(referenced_projects),
        "location": location,
    }, {**exec_meta, "dry_run_http_status": dry_meta["http_status"]}


def _public_json(url: str, *, params: Mapping[str, Any] | None, timeout: int) -> tuple[dict[str, Any], dict[str, Any]]:
    return _http_json("GET", url, token=None, params=params, timeout=timeout)


def _earth_engine_dataset_search(params: Mapping[str, Any], timeout: int) -> tuple[Any, dict[str, Any]]:
    search = str(params.get("search") or "").strip().casefold()
    if not search or len(search) > 100:
        raise ValueError("search must contain 1 to 100 characters")
    max_results = _bounded_int(params.get("max_results"), default=20, minimum=1, maximum=100, name="max_results")
    page_token = str(params.get("page_token") or "")
    matches: list[dict[str, Any]] = []
    pages = 0
    next_token = page_token or None
    while pages < 20 and len(matches) < max_results:
        query: dict[str, Any] = {"prefix": "catalog/", "maxResults": 1000}
        if next_token:
            query["pageToken"] = next_token
        listing, _ = _public_json(EE_STAC_OBJECTS, params=query, timeout=timeout)
        for item in listing.get("items") or []:
            name = str(item.get("name") or "")
            if not name.endswith(".json") or search not in name.casefold():
                continue
            try:
                payload, _ = _public_json(EE_STAC_MEDIA_PREFIX + quote(name, safe="/"), params=None, timeout=timeout)
            except RuntimeError:
                payload = {}
            matches.append({
                "object_path": name,
                "id": payload.get("id"),
                "title": payload.get("title") or payload.get("description"),
                "type": payload.get("type"),
                "license": payload.get("license"),
            })
            if len(matches) >= max_results:
                break
        pages += 1
        next_token = str(listing.get("nextPageToken") or "") or None
        if not next_token:
            break
    return {
        "search": search,
        "matches": matches,
        "scanned_pages": pages,
        "next_page_token": next_token,
    }, {"http_status": 200, "catalog_source": "gs://earthengine-stac"}


def _validate_stac_path(value: Any) -> str:
    path = str(value or "")
    if not path.startswith("catalog/") or not path.endswith(".json"):
        raise ValueError("object_path must start with catalog/ and end with .json")
    if len(path) > 512 or ".." in path or "\\" in path or "?" in path or "#" in path:
        raise ValueError("object_path contains a forbidden sequence")
    return path


def _earth_engine_algorithms(params: Mapping[str, Any], token: str, billing_project: str, timeout: int) -> tuple[Any, dict[str, Any]]:
    payload, metadata = _http_json(
        "GET",
        f"https://earthengine.googleapis.com/v1/projects/{quote(billing_project)}/algorithms",
        token=token,
        timeout=timeout,
        max_bytes=25_000_000,
    )
    algorithms = payload.get("algorithms") if isinstance(payload.get("algorithms"), list) else []
    search = str(params.get("search") or "").strip().casefold()
    if search:
        algorithms = [
            row for row in algorithms
            if search in str(row.get("name") or "").casefold()
            or search in str(row.get("description") or "").casefold()
        ]
    offset = _bounded_int(params.get("offset"), default=0, minimum=0, maximum=max(0, len(algorithms)), name="offset")
    max_results = _bounded_int(params.get("max_results"), default=50, minimum=1, maximum=200, name="max_results")
    selected = algorithms[offset: offset + max_results]
    return {
        "search": search,
        "offset": offset,
        "returned": len(selected),
        "total_matching": len(algorithms),
        "algorithms": selected,
    }, metadata


def _walk_expression(value: Any, *, depth: int = 0) -> tuple[int, int, list[str], list[str]]:
    if depth > 30:
        raise ValueError("Earth Engine expression exceeds maximum depth 30")
    nodes = 1
    max_depth = depth
    functions: list[str] = []
    strings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"functionName", "function_name"} and isinstance(item, str):
                functions.append(item)
            child_nodes, child_depth, child_functions, child_strings = _walk_expression(item, depth=depth + 1)
            nodes += child_nodes
            max_depth = max(max_depth, child_depth)
            functions.extend(child_functions)
            strings.extend(child_strings)
    elif isinstance(value, list):
        for item in value:
            child_nodes, child_depth, child_functions, child_strings = _walk_expression(item, depth=depth + 1)
            nodes += child_nodes
            max_depth = max(max_depth, child_depth)
            functions.extend(child_functions)
            strings.extend(child_strings)
    elif isinstance(value, str):
        strings.append(value)
    return nodes, max_depth, functions, strings


def _validate_ee_expression(raw: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not raw or len(raw) > 20_000:
        raise ValueError("expression_json must contain 1 to 20000 characters")
    expression = json.loads(raw)
    if not isinstance(expression, Mapping):
        raise ValueError("expression_json root must be an object")
    nodes, depth, functions, strings = _walk_expression(expression)
    if nodes > 500:
        raise ValueError("Earth Engine expression exceeds maximum node count 500")
    denied = sorted({
        function for function in functions
        if any(part in re.sub(r"[^a-z]", "", function.casefold()) for part in EE_DENIED_FUNCTION_PARTS)
    })
    if denied:
        raise ValueError(f"Earth Engine expression contains forbidden algorithms: {denied[:10]}")
    for text in strings:
        lowered = text.casefold()
        if "http://" in lowered or "https://" in lowered or lowered.startswith("gs://"):
            raise ValueError("external URLs and buckets are forbidden in Earth Engine expressions")
        if lowered.startswith("users/"):
            raise ValueError("private user Earth Engine assets are forbidden")
        if lowered.startswith("projects/") and not lowered.startswith("projects/earthengine-public/assets/"):
            raise ValueError("non-public project Earth Engine assets are forbidden")
    return dict(expression), {
        "node_count": nodes,
        "max_depth": depth,
        "algorithm_count": len(functions),
        "algorithms": sorted(set(functions)),
    }


def _earth_engine(operation: str, params: Mapping[str, Any], token: str | None, billing_project: str | None, timeout: int) -> tuple[Any, dict[str, Any]]:
    if operation == "catalog-capabilities":
        catalog = load_json(CATALOG_PATH)
        provider = next(row for row in catalog["providers"] if row["provider_id"] == "earth-engine")
        return provider, {"http_status": 200, "catalog_source": "repository-policy"}
    if operation == "catalog-dataset-root":
        return _public_json(EE_STAC_ROOT, params=None, timeout=timeout)
    if operation == "catalog-dataset-search":
        return _earth_engine_dataset_search(params, timeout)
    if operation == "catalog-dataset":
        path = _validate_stac_path(params.get("object_path"))
        return _public_json(EE_STAC_MEDIA_PREFIX + quote(path, safe="/"), params=None, timeout=timeout)
    if not token or not billing_project:
        raise RuntimeError(f"missing repository Secret {SERVICE_ACCOUNT_ENV}")
    if operation == "catalog-algorithms":
        return _earth_engine_algorithms(params, token, billing_project, timeout)
    if operation == "compute-value-readonly":
        expression, audit = _validate_ee_expression(str(params.get("expression_json") or ""))
        workload_tag = str(params.get("workload_tag") or "gpts-api-center")
        if not WORKLOAD_TAG_RE.fullmatch(workload_tag):
            raise ValueError("workload_tag is invalid")
        payload, metadata = _http_json(
            "POST",
            f"https://earthengine.googleapis.com/v1/projects/{quote(billing_project)}/value:compute",
            token=token,
            body={"expression": expression, "workloadTag": workload_tag},
            timeout=timeout,
            max_bytes=10_000_000,
        )
        return {"result": payload.get("result"), "expression_audit": audit, "workload_tag": workload_tag}, metadata
    raise ValueError(f"unsupported Earth Engine operation: {operation}")


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    acceptance = dict(ticket.get("acceptance") or {})
    timeout = _bounded_int(acceptance.get("timeout_seconds"), default=30, minimum=1, maximum=120, name="timeout_seconds")
    max_response_bytes = _bounded_int(acceptance.get("max_response_bytes"), default=500_000, minimum=1024, maximum=1_000_000, name="max_response_bytes")
    started = time.perf_counter()
    started_at = utc_now()
    status = "API_GCP_FAILED"
    data: Any = None
    metadata: dict[str, Any] = {}
    failure: dict[str, Any] | None = None
    credential_secret_name = _credential_secret_name(provider, operation)
    try:
        token: str | None = None
        billing_project: str | None = None
        if credential_secret_name:
            credentials, billing_project = _credentials(credential_secret_name)
            token = str(credentials.token)
        if provider == "bigquery":
            assert token and billing_project
            if operation == "query-readonly":
                data, metadata = _bigquery_query(parameters, token, billing_project, timeout)
            else:
                data, metadata = _bigquery_catalog(operation, parameters, token, billing_project, timeout)
        elif provider == "earth-engine":
            data, metadata = _earth_engine(operation, parameters, token, billing_project, timeout)
        else:
            raise ValueError(f"unsupported provider: {provider}")
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(encoded) > max_response_bytes:
            raise RuntimeError(f"result exceeds acceptance.max_response_bytes={max_response_bytes}")
        status = "API_GCP_COMPLETED"
    except RuntimeError as exc:
        text = str(exc)
        blocked = text.startswith("missing repository Secret")
        status = "API_GCP_BLOCKED" if blocked else "API_GCP_FAILED"
        failure = {
            "code": "GOOGLE_CLOUD_CREDENTIALS_MISSING" if blocked else "GOOGLE_CLOUD_UPSTREAM_ERROR",
            "message": text,
            "retryable": not blocked,
        }
    except (ValueError, json.JSONDecodeError) as exc:
        failure = {"code": "GOOGLE_CLOUD_REQUEST_REJECTED", "message": str(exc), "retryable": False}
    snapshot = {
        "schema_version": "google-cloud-api-snapshot-v1",
        "status": status,
        "created_at": utc_now(),
        "started_at": started_at,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "task_id": str(ticket["task_id"]),
        "provider": provider,
        "operation": operation,
        "objective": str(ticket.get("objective") or ""),
        "ticket_sha256": canonical_sha(ticket),
        "parameters": parameters,
        "data_policy": dict(ticket["data_policy"]),
        "data": data,
        "upstream_metadata": metadata,
        "failure": failure,
        "security": {
            "secret_values_included": False,
            "authorization_header_recorded": False,
            "public_non_personal_data_only": True,
            "bigquery_write_allowed": False,
            "earth_engine_export_or_asset_write_allowed": False,
        },
        "model_calls": 0,
    }
    snapshot["snapshot_sha256"] = canonical_sha(snapshot)
    write_json(output_dir / "gcp-snapshot.json", snapshot)
    diagnostics = {
        "schema_version": "google-cloud-api-diagnostics-v1",
        "status": status,
        "provider": provider,
        "operation": operation,
        "failure": failure,
        "credential_secret_name": credential_secret_name,
        "credential_secret_value_exposed": False,
    }
    write_json(output_dir / "gcp-diagnostics.json", diagnostics)
    summary = [
        f"# {status}",
        "",
        f"- Task ID: `{ticket['task_id']}`",
        f"- Provider: `{provider}`",
        f"- Operation: `{operation}`",
        f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`",
        f"- Model calls: `0`",
    ]
    if failure:
        summary.extend([f"- Error code: `{failure['code']}`", f"- Message: {failure['message']}"])
    (output_dir / "gcp-summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "google-cloud-artifact-manifest-v1",
        "files": ["ticket.json", "ticket-status.json", "gcp-snapshot.json", "gcp-diagnostics.json", "gcp-summary.md"],
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "secret_values_included": False,
    }
    write_json(output_dir / "artifact-manifest.json", manifest)
    write_output("status", status)
    write_output("snapshot_sha256", snapshot["snapshot_sha256"])
    return 0 if status == "API_GCP_COMPLETED" else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    if phase == "accepted":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_GCP_ACCEPTED")
        print()
        print(f"- Task ID: `{status.get('task_id') or ''}`")
        print(f"- Provider: `{status.get('provider') or ''}`")
        print(f"- Operation: `{status.get('operation') or ''}`")
        print(f"- Ticket SHA256: `{status.get('ticket_sha256') or ''}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        status = load_json(output_dir / "ticket-status.json")
        print("## API_GCP_REJECTED")
        print()
        print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        return 0
    snapshot = load_json(output_dir / "gcp-snapshot.json")
    print(f"## {snapshot['status']}")
    print()
    print(f"- Task ID: `{snapshot['task_id']}`")
    print(f"- Provider: `{snapshot['provider']}`")
    print(f"- Operation: `{snapshot['operation']}`")
    print(f"- Snapshot SHA256: `{snapshot['snapshot_sha256']}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- Model calls: `0`")
    if snapshot.get("failure"):
        print(f"- Error code: `{snapshot['failure']['code']}`")
        print(f"- Message: {snapshot['failure']['message']}")
    else:
        excerpt = json.dumps(snapshot.get("data"), ensure_ascii=False, indent=2)
        if len(excerpt) > 30_000:
            excerpt = excerpt[:30_000] + "\n... [truncated; full result in Artifact]"
        print()
        print("```json")
        print(excerpt)
        print("```")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--event-path", required=True)
    prepare_parser.add_argument("--output-dir", required=True)
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--ticket", required=True)
    execute_parser.add_argument("--output-dir", required=True)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--output-dir", required=True)
    render_parser.add_argument("--phase", choices=["accepted", "rejected", "completed"], required=True)
    render_parser.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare":
        return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute":
        return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
