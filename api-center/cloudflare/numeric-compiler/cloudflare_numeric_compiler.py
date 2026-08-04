#!/usr/bin/env python3
"""Compile public Chinese finance/business webpages into numeric baseline rows.

Cloudflare Browser Run /json performs one bounded AI extraction using a fixed profile.
GitHub Actions validates, converts and optionally appends only numeric Parquet rows to
the private Hugging Face compute baseline Dataset. Raw page text and model responses
are never persisted by this program.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import os
import re
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

import pyarrow as pa
import pyarrow.parquet as pq
import requests
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
CLOUDFLARE_ROOT = HERE.parent
API_CENTER_ROOT = HERE.parents[1]
HUGGINGFACE_ROOT = API_CENTER_ROOT / "huggingface"
sys.path.insert(0, str(HUGGINGFACE_ROOT))
import numeric_baseline_store as numeric_store  # noqa: E402

PROFILES_PATH = HERE / "profiles.json"
TICKET_SCHEMA_PATH = HERE / "ticket.schema.json"
CODEBOOK_PATH = HUGGINGFACE_ROOT / "numeric-baseline-library" / "china-finance-business-codebook.json"
REGISTRY_PATH = HUGGINGFACE_ROOT / "numeric-baseline-library" / "numeric-table-registry.json"

CLOUDFLARE_TOKEN_ENV = "CLOUDFLARE_API_TOKEN"
CLOUDFLARE_ACCOUNT_ENV = "CLOUDFLARE_ACCOUNT_ID"
HF_TOKEN_ENV = "HF_TOKEN"
HF_REPO_ENV = "HF_NUMERIC_BASELINE_DATASET_REPO"
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"
SOURCE_SYSTEM_ID = 7001
LICENSE_CODE_PUBLIC = 1
MAX_EXISTING_ROWS_PER_TABLE = 2_000_000
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.azure.internal",
    "kubernetes.default",
    "kubernetes.default.svc",
    "instance-data",
}
BLOCKED_SUFFIXES = (".local", ".internal", ".localhost", ".svc", ".cluster.local")


class NumericCompilerError(RuntimeError):
    """Raised when admission, extraction, conversion or storage is invalid."""


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: str | bytes) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def _hash64(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big", signed=False)


def _hash32(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:4], "big", signed=False)


def _secret(name: str) -> str:
    value = str(os.getenv(name) or "").strip()
    if not value:
        raise NumericCompilerError(f"missing required backend secret or variable: {name}")
    return value


def _safe_entity_key(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().upper())
    if not 2 <= len(text) <= 200 or any(ord(char) < 32 for char in text):
        raise NumericCompilerError("entity key is missing or invalid")
    return text


def _finite_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise NumericCompilerError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise NumericCompilerError(f"{name} must be finite")
    return number


def _date_epoch(value: Any, name: str) -> int:
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise NumericCompilerError(f"{name} must use YYYY-MM-DD")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise NumericCompilerError(f"{name} is not a valid date") from exc
    return int(parsed.timestamp())


def validate_public_https_url(value: Any) -> str:
    url = str(value or "").strip()
    if not 8 <= len(url) <= 2048:
        raise NumericCompilerError("url must contain 8 to 2048 characters")
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise NumericCompilerError("url must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise NumericCompilerError("url credentials and custom ports are forbidden")
    hostname = parsed.hostname.casefold().rstrip(".")
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(BLOCKED_SUFFIXES):
        raise NumericCompilerError("url targets a blocked hostname")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise NumericCompilerError("url targets a non-public IP address")
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise NumericCompilerError("url hostname could not be resolved") from exc
    addresses = {
        str(row[4][0]).split("%", 1)[0]
        for row in records
        if row and len(row) >= 5 and row[4]
    }
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise NumericCompilerError("url hostname does not resolve exclusively to public IPs")
    return urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, ""))


def _profile_map() -> dict[str, dict[str, Any]]:
    payload = _load_json(PROFILES_PATH)
    if payload.get("schema_version") != "cloudflare-cn-numeric-profiles-v1":
        raise NumericCompilerError("unsupported numeric extraction profile registry")
    if payload.get("status") != "production-control":
        raise NumericCompilerError("numeric extraction profiles are not production-control")
    if payload.get("arbitrary_prompt_allowed") is not False or payload.get("arbitrary_schema_allowed") is not False:
        raise NumericCompilerError("arbitrary prompt or schema is forbidden")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != 13:
        raise NumericCompilerError("exactly 13 China finance/business profiles are required")
    result: dict[str, dict[str, Any]] = {}
    for row in profiles:
        if not isinstance(row, Mapping):
            raise NumericCompilerError("profile row must be an object")
        profile_id = str(row.get("id") or "")
        if not re.fullmatch(r"cn-[a-z0-9-]{3,80}", profile_id) or profile_id in result:
            raise NumericCompilerError(f"invalid or duplicate profile: {profile_id!r}")
        result[profile_id] = dict(row)
    return result


def _control() -> dict[str, Any]:
    profiles = _profile_map()
    codebook = _load_json(CODEBOOK_PATH)
    registry = _load_json(REGISTRY_PATH)
    if codebook.get("schema_version") != "china-finance-business-codebook-v1":
        raise NumericCompilerError("unsupported China finance/business codebook")
    if codebook.get("storage_location") != "github-only" or codebook.get("huggingface_upload_allowed") is not False:
        raise NumericCompilerError("codebook must remain GitHub-only")
    tables = {row["id"]: row for row in registry.get("tables") or []}
    required_tables = {"provenance_index", "observations", "regime_events", "entity_links"}
    if not required_tables.issubset(tables):
        raise NumericCompilerError("numeric baseline tables required by compiler are missing")

    variable_codes = set((codebook.get("variables") or {}).keys())
    unit_codes = set((codebook.get("units") or {}).keys())
    event_codes = set((codebook.get("events") or {}).keys())
    relation_codes = set((codebook.get("relations") or {}).keys())
    target_for_kind = {"metric": "observations", "event": "regime_events", "link": "entity_links"}
    for profile_id, profile in profiles.items():
        kind = str(profile.get("kind") or "")
        if kind not in target_for_kind or profile.get("target_table") != target_for_kind[kind]:
            raise NumericCompilerError(f"profile target mismatch: {profile_id}")
        max_records = int(profile.get("max_records") or 0)
        if not 1 <= max_records <= 50:
            raise NumericCompilerError(f"profile record bound is invalid: {profile_id}")
        codes = set(profile.get("allowed_codes") or [])
        if not codes:
            raise NumericCompilerError(f"profile has no allowlisted codes: {profile_id}")
        allowed = variable_codes if kind == "metric" else event_codes if kind == "event" else relation_codes
        unknown = sorted(codes - allowed)
        if unknown:
            raise NumericCompilerError(f"profile {profile_id} references unknown codes: {', '.join(unknown)}")
        if kind == "metric":
            units = set(profile.get("allowed_units") or [])
            unknown_units = sorted(units - unit_codes)
            if not units or unknown_units:
                raise NumericCompilerError(f"profile {profile_id} has invalid units: {', '.join(unknown_units)}")
    return {"profiles": profiles, "codebook": codebook, "registry": registry}


def response_schema(profile: Mapping[str, Any]) -> dict[str, Any]:
    common_properties: dict[str, Any] = {
        "publication_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}
    }
    kind = str(profile["kind"])
    max_records = int(profile["max_records"])
    if kind == "metric":
        common_properties.update({
            "entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
            "geography_id": {"type": "integer", "minimum": 0, "maximum": 999999},
            "records": {
                "type": "array",
                "maxItems": max_records,
                "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": ["metric_code", "period_start", "period_end", "value", "lower_bound", "upper_bound", "unit_code", "confidence"],
                    "properties": {
                        "metric_code": {"type": "string", "enum": list(profile["allowed_codes"])},
                        "period_start": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                        "period_end": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                        "value": {"type": "number"},
                        "lower_bound": {"type": "number"},
                        "upper_bound": {"type": "number"},
                        "unit_code": {"type": "string", "enum": list(profile["allowed_units"])},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            }
        })
        required = ["publication_date", "entity_key", "geography_id", "records"]
    elif kind == "event":
        common_properties.update({
            "entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
            "geography_id": {"type": "integer", "minimum": 0, "maximum": 999999},
            "events": {
                "type": "array",
                "maxItems": max_records,
                "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": ["event_code", "start_date", "end_date", "magnitude", "direction_code", "probability", "status_code", "confidence"],
                    "properties": {
                        "event_code": {"type": "string", "enum": list(profile["allowed_codes"])},
                        "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                        "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                        "magnitude": {"type": "number"},
                        "direction_code": {"type": "integer", "enum": [-1, 0, 1]},
                        "probability": {"type": "number", "minimum": 0, "maximum": 1},
                        "status_code": {"type": "integer", "minimum": 0, "maximum": 65535},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            }
        })
        required = ["publication_date", "entity_key", "geography_id", "events"]
    else:
        common_properties.update({
            "links": {
                "type": "array",
                "maxItems": max_records,
                "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": ["source_entity_key", "target_entity_key", "relation_code", "weight", "start_date", "end_date", "confidence"],
                    "properties": {
                        "source_entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
                        "target_entity_key": {"type": "string", "minLength": 2, "maxLength": 200},
                        "relation_code": {"type": "string", "enum": list(profile["allowed_codes"])},
                        "weight": {"type": "number"},
                        "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                        "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            }
        })
        required = ["publication_date", "links"]
    return {
        "type": "object",
        "additionalProperties": false,
        "required": required,
        "properties": common_properties
    }


def validate_configuration() -> dict[str, Any]:
    control = _control()
    for profile in control["profiles"].values():
        Draft202012Validator.check_schema(response_schema(profile))
    return {
        "status": "CLOUDFLARE_NUMERIC_COMPILER_VALIDATED",
        "profile_count": len(control["profiles"]),
        "variable_count": len(control["codebook"]["variables"]),
        "unit_count": len(control["codebook"]["units"]),
        "event_count": len(control["codebook"]["events"]),
        "relation_count": len(control["codebook"]["relations"]),
        "arbitrary_prompt_allowed": False,
        "arbitrary_schema_allowed": False,
        "raw_text_persisted": False,
        "numeric_hf_payload_only": True,
        "direct_center_connection_allowed": False,
        "model_calls": 0
    }


def _load_ticket(value: Mapping[str, Any]) -> dict[str, Any]:
    ticket = dict(value)
    schema = _load_json(TICKET_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(ticket), key=lambda row: list(row.path))
    if errors:
        raise NumericCompilerError("ticket schema validation failed: " + "; ".join(row.message for row in errors[:5]))
    control = _control()
    if ticket["profile_id"] not in control["profiles"]:
        raise NumericCompilerError("profile_id is not allowlisted")
    ticket["url"] = validate_public_https_url(ticket["url"])
    return ticket


def prepare(event_path: Path, output_dir: Path) -> dict[str, Any]:
    event = _load_json(event_path)
    body = str(((event.get("issue") or {}).get("body")) or "").strip()
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise NumericCompilerError("issue body must be a single JSON ticket") from exc
    if not isinstance(value, Mapping):
        raise NumericCompilerError("issue body must contain a JSON object")
    ticket = _load_ticket(value)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "ticket.json", ticket)
    receipt = {
        "status": "CLOUDFLARE_NUMERIC_TICKET_ACCEPTED",
        "task_id": ticket["task_id"],
        "profile_id": ticket["profile_id"],
        "url_sha256": _sha256(ticket["url"]),
        "raw_url_persisted_to_hf": False,
        "raw_text_persisted": False,
        "direct_center_connection_allowed": False
    }
    _write_json(output_dir / "admission-receipt.json", receipt)
    return receipt


def _cloudflare_extract(ticket: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    account = _secret(CLOUDFLARE_ACCOUNT_ENV)
    if not re.fullmatch(r"[0-9a-fA-F]{32}", account):
        raise NumericCompilerError("CLOUDFLARE_ACCOUNT_ID must be a 32-character hexadecimal account ID")
    token = _secret(CLOUDFLARE_TOKEN_ENV)
    prompt = (
        str(profile["prompt"]).strip() + " " + str(profile["entity_instruction"]).strip() +
        " 输出必须严格符合JSON Schema。没有明确来源的字段不要猜测；无法确认时返回空数组。"
        " 不得输出自然语言解释、买卖建议、目标价、收益保证或个人数据。"
    )
    body = {
        "url": ticket["url"],
        "prompt": prompt,
        "response_format": {
            "type": "json_schema",
            "json_schema": response_schema(profile)
        }
    }
    timeout = int(ticket["acceptance"]["timeout_seconds"])
    max_bytes = int(ticket["acceptance"]["max_response_bytes"])
    response = requests.post(
        f"{CLOUDFLARE_API_BASE}/accounts/{account}/browser-rendering/json",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "gpts-intelligence-center-cn-numeric-compiler/1"
        },
        json=body,
        timeout=timeout,
        allow_redirects=False
    )
    raw = bytes(response.content or b"")
    if len(raw) > max_bytes:
        raise NumericCompilerError("Cloudflare response exceeds acceptance.max_response_bytes")
    if not response.ok:
        raise NumericCompilerError(f"Cloudflare Browser Run returned HTTP {response.status_code}")
    try:
        envelope = response.json()
    except ValueError as exc:
        raise NumericCompilerError("Cloudflare response is not JSON") from exc
    if not isinstance(envelope, Mapping) or envelope.get("success") is not True:
        raise NumericCompilerError("Cloudflare extraction did not report success")
    result = envelope.get("result")
    if not isinstance(result, Mapping):
        raise NumericCompilerError("Cloudflare extraction result is missing")
    validator = Draft202012Validator(response_schema(profile))
    errors = sorted(validator.iter_errors(result), key=lambda row: list(row.path))
    if errors:
        raise NumericCompilerError("Cloudflare JSON failed fixed schema: " + "; ".join(row.message for row in errors[:5]))
    return dict(result)


def _source_hash_halves(url: str) -> tuple[int, int]:
    digest = hashlib.sha256(url.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big"), int.from_bytes(digest[8:16], "big")


def _convert(ticket: Mapping[str, Any], profile: Mapping[str, Any], result: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    control = _control()
    codebook = control["codebook"]
    minimum_confidence = float(ticket["acceptance"]["minimum_confidence"])
    profile_id = str(ticket["profile_id"])
    publication_time = _date_epoch(result["publication_date"], "publication_date")
    provenance_id = _hash64("provenance:" + profile_id + ":" + ticket["url"] + ":" + _canonical(result))
    confidences: list[float] = []
    rows: list[dict[str, Any]] = []
    geography_id = int(result.get("geography_id") or 0)
    kind = str(profile["kind"])

    if kind == "metric":
        entity_key = _safe_entity_key(result["entity_key"])
        entity_id = _hash64("entity:" + entity_key)
        dataset_id = _hash64("profile:" + profile_id)
        for item in result["records"]:
            confidence = _finite_number(item["confidence"], "confidence")
            if confidence < minimum_confidence:
                continue
            value = _finite_number(item["value"], "value")
            lower = _finite_number(item["lower_bound"], "lower_bound")
            upper = _finite_number(item["upper_bound"], "upper_bound")
            if lower > value or value > upper:
                raise NumericCompilerError("metric bounds must satisfy lower_bound <= value <= upper_bound")
            start = _date_epoch(item["period_start"], "period_start")
            end = _date_epoch(item["period_end"], "period_end")
            if start > end:
                raise NumericCompilerError("period_start must not exceed period_end")
            rows.append({
                "provenance_id": provenance_id,
                "dataset_id": dataset_id,
                "variable_id": int(codebook["variables"][item["metric_code"]]),
                "entity_id": entity_id,
                "geography_id": geography_id,
                "period_start": start,
                "period_end": end,
                "value": value,
                "lower_bound": lower,
                "upper_bound": upper,
                "unit_id": int(codebook["units"][item["unit_code"]]),
                "missing_flag": 0
            })
            confidences.append(confidence)
        target_table = "observations"
    elif kind == "event":
        entity_key = _safe_entity_key(result["entity_key"])
        entity_id = _hash64("entity:" + entity_key)
        for item in result["events"]:
            confidence = _finite_number(item["confidence"], "confidence")
            if confidence < minimum_confidence:
                continue
            start = _date_epoch(item["start_date"], "start_date")
            end = _date_epoch(item["end_date"], "end_date")
            if start > end:
                raise NumericCompilerError("event start_date must not exceed end_date")
            magnitude = _finite_number(item["magnitude"], "magnitude")
            probability = _finite_number(item["probability"], "probability")
            if not 0 <= probability <= 1:
                raise NumericCompilerError("event probability must be between 0 and 1")
            event_code = str(item["event_code"])
            rows.append({
                "provenance_id": provenance_id,
                "event_id": _hash64(f"event:{profile_id}:{entity_key}:{event_code}:{start}:{end}:{magnitude}"),
                "entity_id": entity_id,
                "event_type_id": int(codebook["events"][event_code]),
                "start_time": start,
                "end_time": end,
                "magnitude": magnitude,
                "direction_code": int(item["direction_code"]),
                "probability": probability,
                "status_code": int(item["status_code"])
            })
            confidences.append(confidence)
        target_table = "regime_events"
    else:
        for item in result["links"]:
            confidence = _finite_number(item["confidence"], "confidence")
            if confidence < minimum_confidence:
                continue
            source_key = _safe_entity_key(item["source_entity_key"])
            target_key = _safe_entity_key(item["target_entity_key"])
            start = _date_epoch(item["start_date"], "start_date")
            end = _date_epoch(item["end_date"], "end_date")
            if start > end:
                raise NumericCompilerError("link start_date must not exceed end_date")
            relation_code = str(item["relation_code"])
            weight = _finite_number(item["weight"], "weight")
            rows.append({
                "provenance_id": provenance_id,
                "link_id": _hash64(f"link:{relation_code}:{source_key}:{target_key}:{start}:{end}"),
                "source_entity_id": _hash64("entity:" + source_key),
                "target_entity_id": _hash64("entity:" + target_key),
                "relation_id": int(codebook["relations"][relation_code]),
                "weight": weight,
                "start_time": start,
                "end_time": end,
                "confidence": confidence
            })
            confidences.append(confidence)
        target_table = "entity_links"

    if not rows:
        raise NumericCompilerError("no records met the fixed schema and minimum confidence")
    average_confidence = sum(confidences) / len(confidences)
    source_hi, source_lo = _source_hash_halves(ticket["url"])
    quality_flags = 1 | 2 | 4 | 8 | 16 | 64 | 128
    if geography_id == 0 and kind != "link":
        quality_flags |= 256
    if average_confidence < 0.8:
        quality_flags |= 512
    provenance = {
        "provenance_id": provenance_id,
        "source_hash_hi": source_hi,
        "source_hash_lo": source_lo,
        "source_system_id": SOURCE_SYSTEM_ID,
        "license_code": LICENSE_CODE_PUBLIC,
        "collection_time": int(time.time()),
        "publication_time": publication_time,
        "transform_id": _hash32("transform:" + profile_id),
        "version_id": 1,
        "quality_flags": quality_flags,
        "confidence": float(average_confidence)
    }
    return target_table, rows, provenance


def _columns_for_table(table_id: str) -> list[tuple[str, pa.DataType]]:
    control = numeric_store.validate_control_plane()
    if table_id not in control["tables"]:
        raise NumericCompilerError(f"numeric table is not registered: {table_id}")
    return control["tables"][table_id]


def _table_from_rows(table_id: str, rows: list[dict[str, Any]]) -> pa.Table:
    columns = _columns_for_table(table_id)
    schema = pa.schema([pa.field(name, dtype, nullable=False) for name, dtype in columns])
    arrays = [pa.array([row[name] for row in rows], type=field.type) for field in schema]
    return pa.Table.from_arrays(arrays, schema=schema)


def _write_numeric_table(path: Path, table: pa.Table) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table,
        path,
        compression="zstd",
        use_dictionary=False,
        write_statistics=True,
        version="2.6",
        data_page_version="2.0"
    )


def _resolve_hf_repo(api: HfApi, token: str) -> str:
    requested = str(os.getenv(HF_REPO_ENV) or "").strip()
    if requested:
        repo_id = requested
    else:
        identity = api.whoami(token=token)
        if not isinstance(identity, Mapping) or not identity.get("name"):
            raise NumericCompilerError("Hugging Face identity could not be resolved")
        repo_id = f"{identity['name']}/{numeric_store.DEFAULT_REPO_NAME}"
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", repo_id):
        raise NumericCompilerError("unsafe Hugging Face Dataset repo ID")
    return repo_id


def _append_to_hf(output_dir: Path, target_table: str, target_rows: list[dict[str, Any]], provenance: dict[str, Any]) -> dict[str, Any]:
    token = _secret(HF_TOKEN_ENV)
    api = HfApi()
    repo_id = _resolve_hf_repo(api, token)
    info = api.repo_info(repo_id=repo_id, repo_type="dataset", token=token)
    if not bool(getattr(info, "private", False)):
        raise NumericCompilerError("numeric baseline Dataset must remain private")

    table_ids = ["provenance_index", target_table]
    new_rows = {"provenance_index": [provenance], target_table: target_rows}
    upload_paths: dict[str, Path] = {}
    row_counts: dict[str, int] = {}
    for table_id in table_ids:
        remote_path = f"{numeric_store.REMOTE_ROOT}/{table_id}.parquet"
        local_existing = Path(hf_hub_download(
            repo_id=repo_id,
            filename=remote_path,
            repo_type="dataset",
            token=token,
            force_download=True
        ))
        numeric_store.validate_numeric_parquet(local_existing, _columns_for_table(table_id))
        existing = pq.read_table(local_existing)
        if existing.num_rows > MAX_EXISTING_ROWS_PER_TABLE:
            raise NumericCompilerError("numeric table exceeded controlled single-file ingestion capacity")
        if table_id == "provenance_index" and provenance["provenance_id"] in set(existing.column("provenance_id").to_pylist()):
            raise NumericCompilerError("duplicate provenance_id; source/profile/result was already ingested")
        appended = pa.concat_tables([existing, _table_from_rows(table_id, new_rows[table_id])])
        upload_path = output_dir / "upload" / f"{table_id}.parquet"
        _write_numeric_table(upload_path, appended)
        numeric_store.validate_numeric_parquet(upload_path, _columns_for_table(table_id))
        upload_paths[table_id] = upload_path
        row_counts[table_id] = appended.num_rows

    commit = api.create_commit(
        repo_id=repo_id,
        repo_type="dataset",
        token=token,
        commit_message="Append validated Cloudflare China finance numeric batch",
        operations=[
            CommitOperationAdd(
                path_in_repo=f"{numeric_store.REMOTE_ROOT}/{table_id}.parquet",
                path_or_fileobj=upload_paths[table_id]
            )
            for table_id in table_ids
        ]
    )

    for table_id in table_ids:
        remote_path = f"{numeric_store.REMOTE_ROOT}/{table_id}.parquet"
        verified_path = Path(hf_hub_download(
            repo_id=repo_id,
            filename=remote_path,
            repo_type="dataset",
            token=token,
            force_download=True
        ))
        checked = numeric_store.validate_numeric_parquet(verified_path, _columns_for_table(table_id))
        if checked["rows"] != row_counts[table_id]:
            raise NumericCompilerError(f"remote row-count verification failed: {table_id}")
    return {
        "repo_id": repo_id,
        "commit_oid": str(getattr(commit, "oid", "")),
        "target_table": target_table,
        "target_table_rows_after": row_counts[target_table],
        "provenance_rows_after": row_counts["provenance_index"],
        "existing_data_preserved": True
    }


def execute(ticket_path: Path, output_dir: Path, *, commit_to_hf: bool) -> dict[str, Any]:
    ticket = _load_ticket(_load_json(ticket_path))
    control = _control()
    profile = control["profiles"][ticket["profile_id"]]
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    result = _cloudflare_extract(ticket, profile)
    target_table, rows, provenance = _convert(ticket, profile, result)

    target_batch = _table_from_rows(target_table, rows)
    provenance_batch = _table_from_rows("provenance_index", [provenance])
    target_path = output_dir / "numeric-batch" / f"{target_table}.parquet"
    provenance_path = output_dir / "numeric-batch" / "provenance_index.parquet"
    _write_numeric_table(target_path, target_batch)
    _write_numeric_table(provenance_path, provenance_batch)
    target_check = numeric_store.validate_numeric_parquet(target_path, _columns_for_table(target_table))
    provenance_check = numeric_store.validate_numeric_parquet(provenance_path, _columns_for_table("provenance_index"))

    storage: dict[str, Any] = {"committed_to_hf": False}
    if commit_to_hf:
        storage = {"committed_to_hf": True, **_append_to_hf(output_dir, target_table, rows, provenance)}

    receipt = {
        "status": "CLOUDFLARE_NUMERIC_COMPILATION_COMPLETED",
        "task_id": ticket["task_id"],
        "profile_id": ticket["profile_id"],
        "profile_kind": profile["kind"],
        "target_table": target_table,
        "validated_numeric_rows": len(rows),
        "provenance_id": provenance["provenance_id"],
        "average_confidence": provenance["confidence"],
        "target_batch_sha256": target_check["sha256"],
        "provenance_batch_sha256": provenance_check["sha256"],
        "cloudflare_requests": 1,
        "workers_ai_managed_by_browser_run": True,
        "raw_page_text_persisted": False,
        "raw_ai_response_persisted": False,
        "huggingface_payload_numeric_only": True,
        "direct_center_connection_allowed": False,
        "gpts_relay_owner": "gpts-usage-center",
        "automatic_trading_allowed": False,
        "personalized_investment_advice_generated": False,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "storage": storage
    }
    _write_json(output_dir / "execution-receipt.json", receipt)
    return receipt


def render(output_dir: Path) -> str:
    execution_path = output_dir / "execution-receipt.json"
    if execution_path.exists():
        receipt = _load_json(execution_path)
        storage = receipt.get("storage") or {}
        lines = [
            f"Cloudflare numeric compiler result: `{receipt['status']}`",
            "",
            f"- Task ID: `{receipt['task_id']}`",
            f"- Profile: `{receipt['profile_id']}`",
            f"- Target table: `{receipt['target_table']}`",
            f"- Validated numeric rows: `{receipt['validated_numeric_rows']}`",
            f"- Average confidence: `{receipt['average_confidence']}`",
            f"- Cloudflare requests: `{receipt['cloudflare_requests']}`",
            f"- Raw page text persisted: `{str(receipt['raw_page_text_persisted']).lower()}`",
            f"- Raw AI response persisted: `{str(receipt['raw_ai_response_persisted']).lower()}`",
            f"- Numeric-only HF payload: `{str(receipt['huggingface_payload_numeric_only']).lower()}`",
            f"- Committed to HF: `{str(bool(storage.get('committed_to_hf'))).lower()}`",
            f"- Direct center connection allowed: `{str(receipt['direct_center_connection_allowed']).lower()}`"
        ]
        if storage.get("repo_id"):
            lines.append(f"- Private dataset: `{storage['repo_id']}`")
        return "\n".join(lines) + "\n"
    admission_path = output_dir / "admission-receipt.json"
    if admission_path.exists():
        receipt = _load_json(admission_path)
        return (
            f"Cloudflare numeric compiler admission: `{receipt['status']}`\n\n"
            f"- Task ID: `{receipt['task_id']}`\n"
            f"- Profile: `{receipt['profile_id']}`\n"
            "- Raw text persisted: `false`\n"
            "- Direct center connection allowed: `false`\n"
        )
    return "Cloudflare numeric compiler result: `NO_RECEIPT`\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--event-path", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("--ticket", type=Path, required=True)
    execute_parser.add_argument("--output-dir", type=Path, required=True)
    execute_parser.add_argument("--commit-to-hf", action="store_true")
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            args.output_dir.mkdir(parents=True, exist_ok=True)
            receipt = validate_configuration()
            _write_json(args.output_dir / "validation-receipt.json", receipt)
            print(_canonical(receipt))
        elif args.command == "prepare":
            receipt = prepare(args.event_path, args.output_dir)
            print(_canonical(receipt))
        elif args.command == "execute":
            receipt = execute(args.ticket, args.output_dir, commit_to_hf=args.commit_to_hf)
            print(_canonical(receipt))
        else:
            print(render(args.output_dir), end="")
        return 0
    except Exception as exc:
        message = str(exc).replace("\n", " ")[:1600]
        output_dir = getattr(args, "output_dir", None)
        if isinstance(output_dir, Path):
            output_dir.mkdir(parents=True, exist_ok=True)
            _write_json(output_dir / "failure-receipt.json", {
                "status": "CLOUDFLARE_NUMERIC_COMPILATION_FAILED",
                "error_type": type(exc).__name__,
                "message": message,
                "raw_page_text_persisted": False,
                "raw_ai_response_persisted": False,
                "secret_values_exposed": False
            })
        print(f"ERROR: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
