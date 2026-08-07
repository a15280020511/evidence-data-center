#!/usr/bin/env python3
"""Bridge approved PRC open-intelligence providers into the generic [api] route.

The governance control plane always dispatches intelligence work as ``[api]``
issues. This module lets the existing API executor run four fixed local
read-only connector IDs without creating a second governance route or a
browser/network bypass.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
BRIDGE_PATH = HERE / "generic-bridge.json"
TASK_PATH = HERE / "prc_open_intelligence_task.py"

HARD_STOP_CODES = {
    "AUTHORIZATION_DENIED",
    "RATE_LIMITED",
    "TECHNICAL_MEASURE_ENCOUNTERED",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def bridge_catalog() -> dict[str, dict[str, Any]]:
    payload = _load_json(BRIDGE_PATH)
    rows = payload.get("connectors") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError("generic-bridge.json has no connectors array")
    catalog: dict[str, dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise ValueError("bridge connector row must be an object")
        connector_id = str(raw.get("connector_id") or "")
        provider = str(raw.get("provider") or "")
        operation = str(raw.get("operation") or "")
        if not connector_id or not provider or not operation:
            raise ValueError("bridge connector row is incomplete")
        if connector_id in catalog:
            raise ValueError(f"duplicate bridge connector id: {connector_id}")
        catalog[connector_id] = dict(raw)
    return catalog


def _load_task_module():
    spec = importlib.util.spec_from_file_location("prc_open_intelligence_task_bridge", TASK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load PRC open-intelligence executor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _data_present(provider: str, operation: str, data: Any) -> bool:
    if not isinstance(data, Mapping):
        return data not in (None, "", [], {})
    if provider == "china-check" and operation == "company-search":
        rows = data.get("companies")
        return isinstance(rows, list) and bool(rows)
    if provider == "sinofacts" and operation == "company-search":
        rows = data.get("matches")
        return isinstance(rows, list) and bool(rows)
    if provider == "sinofacts" and operation == "company-profile" and "match" in data:
        return data.get("match") is not None
    if provider == "china-check" and operation == "company-snapshot":
        snapshot = data.get("snapshot")
        if isinstance(snapshot, Mapping):
            return bool(snapshot)
    return bool(data)


def execute_request(
    connector_id: str,
    parameters: Mapping[str, Any],
    *,
    timeout_seconds: int,
    max_response_bytes: int,
    allow_empty: bool,
) -> dict[str, Any]:
    catalog = bridge_catalog()
    spec = catalog.get(connector_id)
    if spec is None:
        raise ValueError(f"unknown PRC local connector: {connector_id}")
    provider = str(spec["provider"])
    operation = str(spec["operation"])
    task = _load_task_module()
    try:
        if provider == "china-check":
            data, metadata = task._china_check(
                operation,
                dict(parameters),
                int(timeout_seconds),
                int(max_response_bytes),
            )
        elif provider == "sinofacts" and operation == "company-search":
            data, metadata = task._sinofacts_search(
                dict(parameters),
                int(timeout_seconds),
                int(max_response_bytes),
            )
        elif provider == "sinofacts" and operation == "company-profile":
            data, metadata = task._sinofacts_profile(
                dict(parameters),
                int(timeout_seconds),
                int(max_response_bytes),
            )
        else:
            raise ValueError(f"unsupported PRC local bridge target: {provider}/{operation}")
    except task.ProviderStop as exc:
        state_by_code = {
            "AUTHORIZATION_DENIED": "authorization_denied",
            "RATE_LIMITED": "rate_limited",
            "TECHNICAL_MEASURE_ENCOUNTERED": "technical_measure",
            "BOUNDED_LIMIT_EXCEEDED": "bounded_limit_exceeded",
            "UPSTREAM_NETWORK_ERROR": "network_error",
            "UPSTREAM_HTTP_ERROR": "http_error",
            "UPSTREAM_PROTOCOL_ERROR": "protocol_error",
            "UPSTREAM_CONTRACT_DRIFT": "contract_drift",
            "UPSTREAM_TOOL_ERROR": "business_error",
            "LICENSE_SCOPE_BLOCKED": "license_blocked",
        }
        return {
            "success": False,
            "state": state_by_code.get(exc.code, "upstream_error"),
            "message": str(exc),
            "data_present": False,
            "response": None,
            "upstream_metadata": {},
            "source_side_hard_stop": exc.code in HARD_STOP_CODES,
            "error_type": exc.code,
            "retryable": bool(exc.retryable),
            "provider": provider,
            "operation": operation,
        }

    present = _data_present(provider, operation, data)
    successful = present or bool(allow_empty)
    return {
        "success": successful,
        "state": "success" if present else ("success_empty" if allow_empty else "empty"),
        "message": "" if successful else "provider request completed but no accepted company data was found",
        "data_present": present,
        "response": data,
        "upstream_metadata": metadata,
        "source_side_hard_stop": False,
        "error_type": None,
        "retryable": False,
        "provider": provider,
        "operation": operation,
    }
