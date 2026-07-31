#!/usr/bin/env python3
"""Maximum-safe read-only adapter for the YuanDian legal open platform."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
CATALOG = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((HERE / "readonly-apis.snapshot.json").read_text(encoding="utf-8"))
PROVIDER = CATALOG["providers"][0]
OPERATIONS = {str(row["operation_id"]): row for row in PROVIDER["operations"]}
FIXED_APIS = {str(row["operation_id"]): row for row in SNAPSHOT["apis"]}
ROUTE_SNAPSHOT = {str(row["route_key"]): row for row in SNAPSHOT["apis"]}
OFFICIAL_ORIGIN = "https://open.chineselaw.com"
CATALOG_URL = f"{OFFICIAL_ORIGIN}/api/apis?pageNum=1&pageSize=200&sortBy=latest"
ROUTE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,95}$")
ARGUMENT_RE = re.compile(r"^[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\-\u4e00-\u9fff]{0,95}$")
FORBIDDEN_ARGUMENT_NAMES = {
    "url", "uri", "endpoint", "host", "headers", "header", "authorization",
    "cookie", "api_key", "apikey", "token", "secret", "password", "method",
}
SECRET_KEY_RE = re.compile(r"(?:api.?key|authorization|cookie|token|secret|password)", re.I)
PERSONAL_KEY_RE = re.compile(
    r"(?:身份证|证件号|公民身份|手机号|手机号码|联系电话|联系手机|邮箱|电子邮箱|email|phone|mobile|id.?card)",
    re.I,
)
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
ID_RE = re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={str(value).replace(chr(10), ' ')}\n")


def _bounded_int(value: Any, default: int, minimum: int, maximum: int, name: str) -> int:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    parsed = int(value)
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _validate_json_value(value: Any, *, depth: int = 0) -> None:
    if depth > 6:
        raise ValueError("arguments exceed maximum nesting depth 6")
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, str):
        if len(value) > 20000:
            raise ValueError("argument string exceeds 20000 characters")
        return
    if isinstance(value, Mapping):
        if len(value) > 60:
            raise ValueError("arguments object exceeds 60 properties")
        for raw_key, item in value.items():
            key = str(raw_key)
            if not ARGUMENT_RE.fullmatch(key):
                raise ValueError(f"unsafe argument name: {key}")
            if key.lower() in FORBIDDEN_ARGUMENT_NAMES or SECRET_KEY_RE.search(key):
                raise ValueError(f"forbidden request-control or secret argument: {key}")
            _validate_json_value(item, depth=depth + 1)
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        if len(value) > 200:
            raise ValueError("argument array exceeds 200 items")
        for item in value:
            _validate_json_value(item, depth=depth + 1)
        return
    raise ValueError(f"unsupported argument value type: {type(value).__name__}")


def _validate_schema(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(str(x) for x in error.absolute_path) or '$'}: {error.message}"
            for error in errors[:20]
        ))


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    _validate_schema(ticket)
    if str(ticket.get("provider")) != "yuandian-law":
        raise ValueError("provider must be yuandian-law")
    operation = str(ticket.get("operation") or "")
    row = OPERATIONS.get(operation)
    if row is None:
        raise ValueError(f"unsupported YuanDian operation: {operation}")
    parameters = ticket.get("parameters") or {}
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be an object")
    allowlist = {str(name) for name in row.get("parameters") or []}
    unexpected = sorted(set(parameters) - allowlist)
    if unexpected:
        raise ValueError(f"non-allowlisted parameters: {unexpected}")
    if operation == "catalog-capabilities" and parameters:
        raise ValueError("catalog-capabilities accepts no parameters")
    if operation == "catalog-live":
        _bounded_int(parameters.get("page_size"), 200, 1, 200, "page_size")
        category = parameters.get("category_id")
        if category not in (None, "", 6, 7, 9, 10):
            raise ValueError("category_id must be one of 6, 7, 9, 10")
        return
    if operation == "invoke-readonly-api":
        route_key = str(parameters.get("route_key") or "")
        if not ROUTE_RE.fullmatch(route_key):
            raise ValueError("route_key has an unsafe format")
    arguments = parameters.get("arguments") or {}
    if not isinstance(arguments, Mapping):
        raise ValueError("arguments must be an object")
    _validate_json_value(arguments)
    _bounded_int(parameters.get("timeout_seconds"), 60, 5, 120, "timeout_seconds")
    _bounded_int(parameters.get("max_response_bytes"), 1_000_000, 1024, 5_000_000, "max_response_bytes")


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = json.loads(event_path.read_text(encoding="utf-8"))
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    accepted = False
    reason = ""
