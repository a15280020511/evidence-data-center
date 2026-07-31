#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"
HERE = API / "baostock"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


DATE = {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}
CODE = {"type": "string", "pattern": "^(sh|sz|bj)\\.[0-9]{6}$"}
EMPTY = {"type": "object", "additionalProperties": False, "properties": {}}

def schema(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        **({"required": required} if required else {}),
    }


operations = [
    ("catalog-capabilities", "读取本地 BaoStock 安全能力目录，不访问上游。", [], EMPTY),
    ("trade-dates", "读取指定日期范围内的交易日历。", ["start_date", "end_date"], schema({"start_date": DATE, "end_date": DATE}, ["start_date", "end_date"])),
    ("all-stocks", "读取指定交易日全部证券代码和交易状态。", ["day"], schema({"day": DATE}, ["day"])),
    ("stock-basic", "按证券代码或名称读取证券基础资料。", ["code", "code_name"], schema({"code": CODE, "code_name": {"type": "string", "minLength": 1, "maxLength": 80}, "max_rows": {"type": "integer", "minimum": 1, "maximum": 10000}})),
    ("history-k", "读取沪深京证券日/周/月或 5/15/30/60 分钟历史 K 线及估值字段。", ["code", "fields", "start_date", "end_date", "frequency", "adjustflag"], schema({"code": CODE, "fields": {"type": "string", "pattern": "^[A-Za-z0-9_,]+$", "maxLength": 1000}, "start_date": DATE, "end_date": DATE, "frequency": {"type": "string", "enum": ["d", "w", "m", "5", "15", "30", "60"]}, "adjustflag": {"type": "string", "enum": ["1", "2", "3"]}}, ["code", "fields", "start_date", "end_date"])),
    ("adjust-factor", "读取证券除权除息与复权因子。", ["code", "start_date", "end_date"], schema({"code": CODE, "start_date": DATE, "end_date": DATE}, ["code", "start_date", "end_date"])),
    ("stock-industry", "读取证券行业分类。", ["code", "date"], schema({"code": CODE, "date": DATE})),
    ("sz50-constituents", "读取上证 50 成分股。", ["date"], schema({"date": DATE})),
    ("hs300-constituents", "读取沪深 300 成分股。", ["date"], schema({"date": DATE})),
    ("zz500-constituents", "读取中证 500 成分股。", ["date"], schema({"date": DATE})),
    ("profit-data", "读取季度盈利能力数据。", ["code", "year", "quarter"], schema({"code": CODE, "year": {"type": "integer", "minimum": 1990, "maximum": 2100}, "quarter": {"type": "integer", "minimum": 1, "maximum": 4}}, ["code", "year", "quarter"])),
    ("operation-data", "读取季度营运能力数据。", ["code", "year", "quarter"], schema({"code": CODE, "year": {"type": "integer", "minimum": 1990, "maximum": 2100}, "quarter": {"type": "integer", "minimum": 1, "maximum": 4}}, ["code", "year", "quarter"])),
    ("growth-data", "读取季度成长能力数据。", ["code", "year", "quarter"], schema({"code": CODE, "year": {"type": "integer", "minimum": 1990, "maximum": 2100}, "quarter": {"type": "integer", "minimum": 1, "maximum": 4}}, ["code", "year", "quarter"])),
    ("balance-data", "读取季度偿债能力数据。", ["code", "year", "quarter"], schema({"code": CODE, "year": {"type": "integer", "minimum": 1990, "maximum": 2100}, "quarter": {"type": "integer", "minimum": 1, "maximum": 4}}, ["code", "year", "quarter"])),
    ("cash-flow-data", "读取季度现金流量数据。", ["code", "year", "quarter"], schema({"code": CODE, "year": {"type": "integer", "minimum": 1990, "maximum": 2100}, "quarter": {"type": "integer", "minimum": 1, "maximum": 4}}, ["code", "year", "quarter"])),
    ("dupont-data", "读取季度杜邦分析数据。", ["code", "year", "quarter"], schema({"code": CODE, "year": {"type": "integer", "minimum": 1990, "maximum": 2100}, "quarter": {"type": "integer", "minimum": 1, "maximum": 4}}, ["code", "year", "quarter"])),
    ("performance-express", "读取业绩快报。", ["code", "start_date", "end_date"], schema({"code": CODE, "start_date": DATE, "end_date": DATE}, ["start_date", "end_date"])),
    ("forecast-report", "读取业绩预告。", ["code", "start_date", "end_date"], schema({"code": CODE, "start_date": DATE, "end_date": DATE}, ["start_date", "end_date"])),
    ("deposit-rate", "读取中国存款基准利率。", ["start_date", "end_date"], schema({"start_date": DATE, "end_date": DATE}, ["start_date", "end_date"])),
    ("shibor", "读取上海银行间同业拆放利率。", ["start_date", "end_date"], schema({"start_date": DATE, "end_date": DATE}, ["start_date", "end_date"])),
]

catalog = {
    "schema_version": "baostock-provider-catalog-v1",
    "secret_values_exposed": False,
    "replaced_legacy_connectors": [],
    "providers": [{
        "provider_id": "baostock",
        "display_name": "BaoStock 中国证券免费数据",
        "description": "通过官方 baostock Python 客户端读取中国证券历史行情、交易日历、证券基础、指数成分、财务能力指标、业绩报告和宏观利率数据。无需 API Key。",
        "enabled": True,
        "ticket_prefix": "[api-baostock]",
        "required_secret_environment_variable": "",
        "catalog_policy": "仅开放显式登记的 BaoStock 查询函数；禁止任意函数、任意网络地址、交易、下单、账户操作、写入和自定义代码。",
        "execution_policy": "每张票据只允许一次登录、一次白名单查询和一次登出；设置进程级 socket 超时、最大行数与序列化响应体积，结果生成 Snapshot、Diagnostics 和 Artifact。",
        "limits": {
            "queries_per_ticket_max": 1,
            "timeout_seconds_max": 60,
            "max_response_bytes": 5000000,
            "max_rows": 10000,
            "arbitrary_functions_allowed": False,
            "arbitrary_hosts_allowed": False,
            "arbitrary_code_allowed": False,
            "write_operations_allowed": False,
            "trading_or_order_execution_allowed": False,
            "credentials_required": False,
            "secret_values_exposed": False,
        },
        "operations": [
            {
                "operation_id": op_id,
                "description": description,
                "parameters": params,
                "parameter_schema": parameter_schema,
                "result_contract": {
                    "provider": "baostock",
                    "client_package": "baostock==0.9.3",
                    "read_only": True,
                    "credential_mode": "none",
                },
            }
            for op_id, description, params, parameter_schema in operations
        ],
    }],
}
write(HERE / "provider-catalog.json", json.dumps(catalog, ensure_ascii=False, indent=2))

operation_ids = [row[0] for row in operations]
ticket_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/a15280020511/evidence-data-center/api-center/baostock/ticket.schema.json",
    "title": "BaoStock managed read-only ticket",
    "type": "object",
    "additionalProperties": False,
    "required": ["task_id", "provider", "operation", "objective", "parameters", "data_policy", "acceptance"],
    "properties": {
        "task_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$"},
        "provider": {"const": "baostock"},
        "operation": {"type": "string", "enum": operation_ids},
        "objective": {"type": "string", "minLength": 1, "maxLength": 1000},
        "parameters": {"type": "object"},
        "data_policy": {
            "type": "object", "additionalProperties": False,
            "required": ["classification", "contains_personal_data"],
            "properties": {"classification": {"const": "public"}, "contains_personal_data": {"const": False}},
        },
        "acceptance": {
            "type": "object", "additionalProperties": False,
            "required": ["timeout_seconds", "max_response_bytes", "max_rows"],
            "properties": {
                "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 60},
                "max_response_bytes": {"type": "integer", "minimum": 1024, "maximum": 5000000},
                "max_rows": {"type": "integer", "minimum": 1, "maximum": 10000},
            },
        },
    },
}
write(HERE / "ticket.schema.json", json.dumps(ticket_schema, ensure_ascii=False, indent=2))
write(HERE / "requirements.txt", "baostock==0.9.3\njsonschema==4.26.0")
write(HERE / "README.md", """# BaoStock managed provider

- Ticket prefix: `[api-baostock]`
- Provider ID: `baostock`
- Credentials: none
- Package: `baostock==0.9.3`
- Policy: one login, one allowlisted read-only query, one logout per ticket
- Output: structured Snapshot, Diagnostics, Manifest and GitHub Actions Artifact

This integration does not expose arbitrary BaoStock functions, arbitrary hosts, Python code, trading, order execution or write operations.
""")

write(HERE / "baostock_task.py", r'''#!/usr/bin/env python3
"""Bounded read-only BaoStock execution control plane."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"

FUNCTIONS = {
    "trade-dates": "query_trade_dates",
    "all-stocks": "query_all_stock",
    "stock-basic": "query_stock_basic",
    "history-k": "query_history_k_data_plus",
    "adjust-factor": "query_adjust_factor",
    "stock-industry": "query_stock_industry",
    "sz50-constituents": "query_sz50_stocks",
    "hs300-constituents": "query_hs300_stocks",
    "zz500-constituents": "query_zz500_stocks",
    "profit-data": "query_profit_data",
    "operation-data": "query_operation_data",
    "growth-data": "query_growth_data",
    "balance-data": "query_balance_data",
    "cash-flow-data": "query_cash_flow_data",
    "dupont-data": "query_dupont_data",
    "performance-express": "query_performance_express_report",
    "forecast-report": "query_forecast_report",
    "deposit-rate": "query_deposit_rate_data",
    "shibor": "query_shibor_data",
}


class BaoStockError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def provider_catalog() -> Mapping[str, Any]:
    return load_json(CATALOG_PATH)["providers"][0]


def operation_catalog(operation: str) -> Mapping[str, Any]:
    for row in provider_catalog()["operations"]:
        if row["operation_id"] == operation:
            return row
    raise ValueError(f"unsupported BaoStock operation: {operation}")


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(f"{'.'.join(str(x) for x in item.absolute_path) or '$'}: {item.message}" for item in errors[:20]))
    schema = operation_catalog(str(ticket["operation"]))["parameter_schema"]
    errors = sorted(Draft202012Validator(schema).iter_errors(ticket.get("parameters") or {}), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(f"parameters.{'.'.join(str(x) for x in item.absolute_path)}: {item.message}" for item in errors[:20]))


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
        parsed = json.loads(body)
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        if not title.startswith("[api-baostock]"):
            raise ValueError("issue title must start with [api-baostock]")
        ticket = parsed
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "baostock-ticket-status-v1", "accepted": accepted, "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""), "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""), "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "credentials_required": False, "secret_values_exposed": False, "model_calls": 0,
    }
    write_json(output_dir / "ticket-status.json", status)
    write_output("accepted", "true" if accepted else "false")
    write_output("reason", reason)
    return 0 if accepted else 1


def _client() -> Any:
    try:
        return importlib.import_module("baostock")
    except ImportError as exc:
        raise BaoStockError("BAOSTOCK_CLIENT_MISSING", "baostock package is not installed") from exc


def _assert_success(result: Any, phase: str) -> None:
    code = str(getattr(result, "error_code", ""))
    if code != "0":
        message = str(getattr(result, "error_msg", "unknown upstream error"))[:2000]
        retryable = any(token in message.lower() for token in ("timeout", "connect", "network", "socket"))
        raise BaoStockError("BAOSTOCK_UPSTREAM_ERROR", f"{phase} failed ({code}): {message}", retryable=retryable)


def _invoke(client: Any, operation: str, parameters: Mapping[str, Any]) -> Any:
    fn = getattr(client, FUNCTIONS[operation], None)
    if not callable(fn):
        raise BaoStockError("BAOSTOCK_FUNCTION_UNAVAILABLE", f"installed client has no {FUNCTIONS[operation]}")
    p = dict(parameters)
    if operation == "history-k":
        return fn(p.pop("code"), p.pop("fields"), start_date=p.pop("start_date"), end_date=p.pop("end_date"), frequency=p.pop("frequency", "d"), adjustflag=p.pop("adjustflag", "3"))
    if operation in {"profit-data", "operation-data", "growth-data", "balance-data", "cash-flow-data", "dupont-data"}:
        return fn(code=p["code"], year=int(p["year"]), quarter=int(p["quarter"]))
    return fn(**p)


def _collect(result: Any, max_rows: int, max_bytes: int) -> dict[str, Any]:
    _assert_success(result, "query")
    fields = [str(item) for item in list(getattr(result, "fields", []) or [])]
    rows: list[dict[str, Any]] = []
    truncated = False
    while result.next():
        values = list(result.get_row_data())
        if len(rows) >= max_rows:
            truncated = True
            break
        rows.append({name: values[index] if index < len(values) else None for index, name in enumerate(fields)})
        if len(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > max_bytes:
            raise BaoStockError("BAOSTOCK_RESPONSE_TOO_LARGE", "normalized response exceeded max_response_bytes")
    return {"fields": fields, "rows": rows, "row_count": len(rows), "truncated": truncated}


def query_baostock(operation: str, parameters: Mapping[str, Any], *, timeout: int, max_rows: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any]]:
    client = _client()
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(float(timeout))
    logged_in = False
    try:
        login = client.login()
        _assert_success(login, "login")
        logged_in = True
        result = _invoke(client, operation, parameters)
        data = _collect(result, max_rows=max_rows, max_bytes=max_bytes)
        metadata = {
            "upstream_called": True, "client_package": "baostock", "credential_mode": "none",
            "credentials_required": False, "secret_value_exposed": False, "query_function": FUNCTIONS[operation],
            "row_count": data["row_count"], "truncated": data["truncated"], "transport_timeout_seconds": timeout,
        }
        return data, metadata
    except (OSError, TimeoutError) as exc:
        raise BaoStockError("BAOSTOCK_CONNECTION_FAILED", f"upstream connection failed: {type(exc).__name__}", retryable=True) from exc
    finally:
        if logged_in:
            try:
                client.logout()
            except Exception:
                pass
        socket.setdefaulttimeout(previous_timeout)


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket)
    operation = str(ticket["operation"])
    started_at = utc_now()
    try:
        if operation == "catalog-capabilities":
            result = load_json(CATALOG_PATH)
            metadata = {"upstream_called": False, "credential_mode": "none", "credentials_required": False, "secret_value_exposed": False, "operation_count": len(provider_catalog()["operations"])}
        else:
            acceptance = ticket["acceptance"]
            result, metadata = query_baostock(operation, ticket.get("parameters") or {}, timeout=int(acceptance["timeout_seconds"]), max_rows=int(acceptance["max_rows"]), max_bytes=int(acceptance["max_response_bytes"]))
        snapshot = {
            "schema_version": "baostock-api-snapshot-v1", "status": "API_BAOSTOCK_COMPLETED",
            "task_id": ticket["task_id"], "provider": "baostock", "operation": operation,
            "started_at": started_at, "completed_at": utc_now(), "ticket_sha256": canonical_sha(ticket),
            "metadata": metadata, "result": result, "credentials_required": False,
            "secret_values_exposed": False, "model_calls": 0,
        }
        snapshot["snapshot_sha256"] = canonical_sha(snapshot)
        write_json(output_dir / "baostock-snapshot.json", snapshot)
        write_json(output_dir / "artifact-manifest.json", {"schema_version": "baostock-artifact-manifest-v1", "files": ["ticket.json", "ticket-status.json", "baostock-snapshot.json"], "snapshot_sha256": snapshot["snapshot_sha256"], "secret_values_included": False})
        write_output("status", snapshot["status"])
        write_output("snapshot_sha256", snapshot["snapshot_sha256"])
        return 0
    except BaoStockError as exc:
        failure = {
            "schema_version": "baostock-diagnostics-v1", "status": "API_BAOSTOCK_FAILED",
            "task_id": ticket.get("task_id"), "provider": "baostock", "operation": operation,
            "started_at": started_at, "failed_at": utc_now(),
            "error": {"code": exc.code, "message": str(exc)[:4000], "retryable": exc.retryable},
            "credentials_required": False, "secret_values_exposed": False, "model_calls": 0,
        }
        failure["diagnostics_sha256"] = canonical_sha(failure)
        write_json(output_dir / "baostock-diagnostics.json", failure)
        write_json(output_dir / "artifact-manifest.json", {"schema_version": "baostock-artifact-manifest-v1", "files": ["ticket.json", "ticket-status.json", "baostock-diagnostics.json"], "diagnostics_sha256": failure["diagnostics_sha256"], "secret_values_included": False})
        write_output("status", failure["status"])
        write_output("error_code", exc.code)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    if phase in {"accepted", "rejected"}:
        status = load_json(output_dir / "ticket-status.json")
        heading = "API_BAOSTOCK_ACCEPTED" if status["accepted"] else "API_BAOSTOCK_REJECTED"
        print(f"## {heading}\n")
        print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{status.get('operation') or 'unknown'}`")
        print(f"- Ticket SHA-256: `{status.get('ticket_sha256') or 'unavailable'}`")
        if not status["accepted"]:
            print(f"- Reason: `{status.get('reason') or 'invalid ticket'}`")
        print("- Credentials required: `false`")
        print("- Secret values exposed: `false`")
        print("- Model calls: `0`")
        return 0
    snapshot = output_dir / "baostock-snapshot.json"
    if snapshot.exists():
        data = load_json(snapshot)
        metadata = data.get("metadata") or {}
        print("## API_BAOSTOCK_COMPLETED\n")
        print(f"- Task ID: `{data['task_id']}`")
        print(f"- Operation: `{data['operation']}`")
        print(f"- Upstream called: `{str(bool(metadata.get('upstream_called'))).lower()}`")
        print(f"- Query function: `{metadata.get('query_function') or 'local-catalog'}`")
        print(f"- Rows: `{metadata.get('row_count', 0)}`")
        print(f"- Snapshot SHA-256: `{data['snapshot_sha256']}`")
    else:
        data = load_json(output_dir / "baostock-diagnostics.json")
        print("## API_BAOSTOCK_FAILED\n")
        print(f"- Task ID: `{data.get('task_id') or 'unknown'}`")
        print(f"- Operation: `{data.get('operation') or 'unknown'}`")
        print(f"- Error code: `{data['error']['code']}`")
        print(f"- Message: `{data['error']['message']}`")
        print(f"- Retryable: `{str(bool(data['error']['retryable'])).lower()}`")
        print(f"- Diagnostics SHA-256: `{data['diagnostics_sha256']}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- Credentials required: `false`")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
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
''')

write(HERE / "tests/test_baostock_task.py", r'''from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("baostock_task", ROOT / "baostock_task.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class Result:
    error_code = "0"
    error_msg = "success"
    fields = ["calendar_date", "is_trading_day"]
    def __init__(self) -> None:
        self.rows = [["2026-07-01", "1"], ["2026-07-02", "1"]]
        self.index = -1
    def next(self) -> bool:
        self.index += 1
        return self.index < len(self.rows)
    def get_row_data(self):
        return self.rows[self.index]


class Login:
    error_code = "0"
    error_msg = "success"


class BaoStockTests(unittest.TestCase):
    def ticket(self, operation="trade-dates"):
        parameters = {"start_date": "2026-07-01", "end_date": "2026-07-02"} if operation == "trade-dates" else {}
        return {
            "task_id": "baostock-test-001", "provider": "baostock", "operation": operation,
            "objective": "test", "parameters": parameters,
            "data_policy": {"classification": "public", "contains_personal_data": False},
            "acceptance": {"timeout_seconds": 10, "max_response_bytes": 100000, "max_rows": 100},
        }

    def test_catalog_has_fixed_readonly_surface(self):
        provider = module.provider_catalog()
        self.assertEqual(provider["provider_id"], "baostock")
        self.assertEqual(len(provider["operations"]), 20)
        self.assertEqual(provider["required_secret_environment_variable"], "")
        self.assertFalse(provider["limits"]["arbitrary_functions_allowed"])
        self.assertFalse(provider["limits"]["trading_or_order_execution_allowed"])

    def test_rejects_arbitrary_parameters(self):
        ticket = self.ticket()
        ticket["parameters"]["host"] = "example.com"
        with self.assertRaises(ValueError):
            module.validate_ticket(ticket)

    def test_mocked_upstream_execution(self):
        calls = []
        fake = types.SimpleNamespace(
            login=lambda: Login(),
            logout=lambda: calls.append("logout"),
            query_trade_dates=lambda **kwargs: (calls.append(kwargs) or Result()),
        )
        old = sys.modules.get("baostock")
        sys.modules["baostock"] = fake
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ticket_path = root / "ticket.json"
                ticket_path.write_text(json.dumps(self.ticket()), encoding="utf-8")
                self.assertEqual(module.execute(ticket_path, root), 0)
                snapshot = json.loads((root / "baostock-snapshot.json").read_text())
                self.assertEqual(snapshot["status"], "API_BAOSTOCK_COMPLETED")
                self.assertEqual(snapshot["result"]["row_count"], 2)
                self.assertFalse(snapshot["credentials_required"])
                self.assertIn("logout", calls)
        finally:
            if old is None:
                sys.modules.pop("baostock", None)
            else:
                sys.modules["baostock"] = old

    def test_catalog_execution_needs_no_package_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ticket_path = root / "ticket.json"
            ticket_path.write_text(json.dumps(self.ticket("catalog-capabilities")), encoding="utf-8")
            self.assertEqual(module.execute(ticket_path, root), 0)
            snapshot = json.loads((root / "baostock-snapshot.json").read_text())
            self.assertFalse(snapshot["metadata"]["upstream_called"])


if __name__ == "__main__":
    unittest.main()
''')

write(ROOT / ".github/workflows/baostock-api-ticket.yml", '''name: Managed BaoStock API Center

on:
  issues:
    types: [opened, reopened]

permissions:
  contents: read
  issues: write
  actions: read

concurrency:
  group: api-baostock-ticket-${{ github.event.issue.number }}
  cancel-in-progress: false

jobs:
  execute-baostock-api:
    if: >-
      github.actor == github.repository_owner &&
      startsWith(github.event.issue.title, '[api-baostock]')
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      ISSUE_NUMBER: ${{ github.event.issue.number }}
    steps:
      - name: Checkout pinned source
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - name: Set up isolated Python
        uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: api-center/baostock/requirements.txt
      - name: Install pinned dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/baostock/requirements.txt
          python -m pip check
      - name: Compile managed provider control plane
        run: python -m py_compile api-center/baostock/baostock_task.py
      - name: Parse and authorize BaoStock ticket
        id: prepare
        continue-on-error: true
        run: python api-center/baostock/baostock_task.py prepare --event-path "$GITHUB_EVENT_PATH" --output-dir baostock-artifacts
      - name: Comment accepted ticket
        if: steps.prepare.outputs.accepted == 'true'
        run: |
          python api-center/baostock/baostock_task.py render --output-dir baostock-artifacts --phase accepted > baostock-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@baostock-comment.md
      - name: Comment rejected ticket
        if: steps.prepare.outputs.accepted != 'true'
        run: |
          python api-center/baostock/baostock_task.py render --output-dir baostock-artifacts --phase rejected > baostock-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@baostock-comment.md
      - name: Execute bounded read-only BaoStock operation
        id: execute
        if: steps.prepare.outputs.accepted == 'true'
        continue-on-error: true
        run: python api-center/baostock/baostock_task.py execute --ticket baostock-artifacts/ticket.json --output-dir baostock-artifacts
      - name: Upload BaoStock evidence
        id: upload
        if: always()
        continue-on-error: true
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: baostock-api-ticket-${{ github.event.issue.number }}-${{ github.run_id }}
          path: baostock-artifacts/
          if-no-files-found: error
          retention-days: 30
      - name: Publish verified result or structured failure
        if: always() && steps.prepare.outputs.accepted == 'true'
        env:
          ARTIFACT_URL: ${{ steps.upload.outputs.artifact-url }}
        run: |
          python api-center/baostock/baostock_task.py render --output-dir baostock-artifacts --phase completed --artifact-url "$ARTIFACT_URL" > baostock-comment.md
          gh api --method POST "repos/${GITHUB_REPOSITORY}/issues/${ISSUE_NUMBER}/comments" -F body=@baostock-comment.md
      - name: Mark rejected or failed execution
        if: >-
          always() &&
          (steps.prepare.outputs.accepted != 'true' ||
           steps.execute.outputs.status != 'API_BAOSTOCK_COMPLETED' ||
           steps.upload.outcome != 'success')
        run: exit 1
''')

write(ROOT / ".github/workflows/baostock-provider-validate.yml", '''name: Validate BaoStock Provider

on:
  pull_request:
    paths:
      - "api-center/baostock/**"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/baostock-*.yml"
  push:
    branches: [main]
    paths:
      - "api-center/baostock/**"
      - "api-center/build_catalog_market_search.py"
      - "api-center/api-catalog.json"
      - "api-center/api-catalog.md"
      - ".github/workflows/baostock-*.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate-baostock:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: api-center/baostock/requirements.txt
      - name: Install dependencies
        run: |
          python -m pip install --disable-pip-version-check --no-input -r api-center/baostock/requirements.txt
          python -m pip check
      - name: Compile and test
        run: |
          python -m py_compile api-center/baostock/baostock_task.py api-center/baostock/tests/test_baostock_task.py
          python -m unittest discover -s api-center/baostock/tests -p 'test_*.py' -v
          python api-center/build_catalog_market_search.py
          git diff --exit-code -- api-center/api-catalog.json api-center/api-catalog.md
          git diff --check
''')

# Register the provider in the deterministic catalog builder.
build_path = API / "build_catalog_market_search.py"
text = build_path.read_text(encoding="utf-8")
text = text.replace('TUSHARE_CATALOG = HERE / "tushare/provider-catalog.json"\n', 'TUSHARE_CATALOG = HERE / "tushare/provider-catalog.json"\nBAOSTOCK_CATALOG = HERE / "baostock/provider-catalog.json"\n')
text = text.replace('    "tushare": 20,\n', '    "tushare": 20,\n    "baostock": 20,\n')
text = text.replace('    TUSHARE_CATALOG,\n', '    TUSHARE_CATALOG,\n    BAOSTOCK_CATALOG,\n')
text = text.replace('        "tushare/provider-catalog.json",\n', '        "tushare/provider-catalog.json",\n        "baostock/provider-catalog.json",\n')
build_path.write_text(text, encoding="utf-8")

# Update deterministic invariants.
test_path = API / "tests/test_api_catalog.py"
text = test_path.read_text(encoding="utf-8")
text = text.replace('    "tushare": 20,\n', '    "tushare": 20,\n    "baostock": 20,\n', 1)
text = text.replace('self.assertEqual(catalog["managed_provider_count"], 17)', 'self.assertEqual(catalog["managed_provider_count"], 18)')
text = text.replace('self.assertEqual(catalog["enabled_managed_provider_count"], 17)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 18)')
text = text.replace('self.assertEqual(catalog["managed_operation_count"], 145)', 'self.assertEqual(catalog["managed_operation_count"], 165)')
text = text.replace('            "tushare/provider-catalog.json",\n', '            "tushare/provider-catalog.json",\n            "baostock/provider-catalog.json",\n')
text = text.replace('        self.assertEqual(\n            providers["tushare"]["ticket_prefix"],', '        self.assertEqual(providers["baostock"]["ticket_prefix"], "[api-baostock]")\n        self.assertEqual(providers["baostock"]["required_secret_environment_variable_name"], "")\n        self.assertFalse(providers["baostock"]["limits"]["arbitrary_functions_allowed"])\n        self.assertFalse(providers["baostock"]["limits"]["trading_or_order_execution_allowed"])\n\n        self.assertEqual(\n            providers["tushare"]["ticket_prefix"],')
test_path.write_text(text, encoding="utf-8")

cap_path = API / "tests/test_capability_maximization.py"
text = cap_path.read_text(encoding="utf-8")
text = text.replace('            145,\n', '            165,\n', 1)
text = text.replace('            "tushare": 20,\n', '            "tushare": 20,\n            "baostock": 20,\n', 1)
anchor = '        knowledge = json.loads(\n'
block = '''        baostock = json.loads(\n            (ROOT / "baostock/provider-catalog.json").read_text(encoding="utf-8")\n        )\n        baostock_provider = baostock["providers"][0]\n        self.assertEqual(baostock_provider["required_secret_environment_variable"], "")\n        self.assertFalse(baostock_provider["limits"]["arbitrary_functions_allowed"])\n        self.assertFalse(baostock_provider["limits"]["arbitrary_hosts_allowed"])\n        self.assertFalse(baostock_provider["limits"]["write_operations_allowed"])\n        self.assertFalse(baostock_provider["limits"]["trading_or_order_execution_allowed"])\n\n'''
text = text.replace(anchor, block + anchor, 1)
cap_path.write_text(text, encoding="utf-8")

# Update the validation workflow's hard-coded provider totals and expected provider map.
workflow = ROOT / ".github/workflows/api-catalog-validate.yml"
text = workflow.read_text(encoding="utf-8")
text = text.replace("assert catalog['managed_provider_count'] == 17", "assert catalog['managed_provider_count'] == 18")
text = text.replace("assert catalog['enabled_managed_provider_count'] == 17", "assert catalog['enabled_managed_provider_count'] == 18")
text = text.replace("assert catalog['managed_operation_count'] == 145", "assert catalog['managed_operation_count'] == 165")
text = text.replace("              'tushare': 20,\n", "              'tushare': 20,\n              'baostock': 20,\n")
text = text.replace("assert sum(len(row['operations']) for row in providers.values()) == 145", "assert sum(len(row['operations']) for row in providers.values()) == 165")
text = text.replace("              'managed_providers': 17,", "              'managed_providers': 18,")
text = text.replace("              'managed_operations': 145,", "              'managed_operations': 165,")
text = text.replace("            api-center/tushare/provider-catalog.json\n", "            api-center/tushare/provider-catalog.json\n            api-center/baostock/provider-catalog.json\n")
workflow.write_text(text, encoding="utf-8")

# Register dependency updates.
dependabot = ROOT / ".github/dependabot.yml"
text = dependabot.read_text(encoding="utf-8")
entry = '''  - package-ecosystem: "pip"\n    directory: "/api-center/baostock"\n    schedule:\n      interval: "weekly"\n    open-pull-requests-limit: 5\n\n'''
if 'directory: "/api-center/baostock"' not in text:
    text = text.replace("updates:\n", "updates:\n" + entry, 1)
dependabot.write_text(text, encoding="utf-8")

readme = API / "README.md"
text = readme.read_text(encoding="utf-8")
section = '''\n## BaoStock 中国证券免费数据\n\n`api-center/baostock/` 通过官方 `baostock==0.9.3` Python 客户端提供免密、只读的中国证券数据。正式票据前缀为 `[api-baostock]`，无需 Repository Secret。固定开放 20 项能力，覆盖交易日历、全部证券、证券基础、历史 K 线、复权因子、行业、三类主要指数成分、六类财务能力指标、业绩快报/预告、存款利率和 Shibor。每张票据只允许一次登录、一次白名单查询和一次登出，禁止任意函数、任意主机、代码执行、交易、下单和写入。\n'''
if "## BaoStock 中国证券免费数据" not in text:
    marker = "## Tushare Pro 中国金融数据"
    text = text.replace(marker, section + "\n" + marker, 1)
readme.write_text(text, encoding="utf-8")

# Remove the one-shot generator from the final branch.
Path(__file__).unlink()
