
#!/usr/bin/env python3
"""Fixed, read-only AKShare adapter for formal API-center tickets."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / "ticket.schema.json").read_text(encoding="utf-8"))
CATALOG = json.loads((HERE / "provider-catalog.json").read_text(encoding="utf-8"))
OPERATIONS = {
    str(item["operation_id"]): item
    for provider in CATALOG["providers"]
    for item in provider["operations"]
}
OPERATION_PROVIDERS = {
    str(item["operation_id"]): str(provider["provider_id"])
    for provider in CATALOG["providers"]
    for item in provider["operations"]
}
SYMBOL_RE = re.compile(r"^[0-9]{6}$")
ASHARE_SYMBOL_RE = re.compile(r"^(?:sh|sz)[0-9]{6}$")
DATE_RE = re.compile(r"^[0-9]{8}$")
ISO_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def output(name: str, value: Any) -> None:
    path = os.getenv("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
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


def _symbol(value: Any) -> str:
    symbol = str(value or "")
    if not SYMBOL_RE.fullmatch(symbol):
        raise ValueError("symbol must be a six-digit A-share code")
    return symbol


def validate_ticket(ticket: Mapping[str, Any]) -> None:
    validator = Draft202012Validator(SCHEMA)
    errors = sorted(validator.iter_errors(ticket), key=lambda item: list(item.absolute_path))
    if errors:
        raise ValueError("; ".join(
            f"{'.'.join(str(x) for x in error.absolute_path) or '$'}: {error.message}"
            for error in errors[:20]
        ))
    provider = str(ticket["provider"])
    operation = str(ticket["operation"])
    row = OPERATIONS.get(operation)
    if row is None:
        raise ValueError(f"unsupported managed A-share operation: {operation}")
    expected_provider = OPERATION_PROVIDERS.get(operation)
    if provider != expected_provider:
        raise ValueError(
            f"operation {operation} belongs to provider {expected_provider}, not {provider}"
        )
    allowed = {str(item) for item in row.get("parameters") or []}
    unexpected = sorted(set(ticket.get("parameters") or {}) - allowed)
    if unexpected:
        raise ValueError(f"non-allowlisted parameters: {unexpected}")
    params = ticket.get("parameters") or {}
    if operation in {"stock-a-share-history", "stock-company-info", "stock-financial-indicators"}:
        _symbol(params.get("symbol"))
    if operation == "stock-a-share-history":
        if str(params.get("period") or "daily") not in {"daily", "weekly", "monthly"}:
            raise ValueError("period must be daily, weekly, or monthly")
        if str(params.get("adjust") or "") not in {"", "qfq", "hfq"}:
            raise ValueError("adjust must be empty, qfq, or hfq")
        for name in ("start_date", "end_date"):
            if name in params and not DATE_RE.fullmatch(str(params[name])):
                raise ValueError(f"{name} must use YYYYMMDD")
    if operation == "ashare-get-price":
        if not ASHARE_SYMBOL_RE.fullmatch(str(params.get("symbol") or "")):
            raise ValueError("symbol must use sh600000 or sz000001 format")
        if str(params.get("frequency") or "1d") not in {
            "1d", "1w", "1M", "1m", "5m", "15m", "30m", "60m"
        }:
            raise ValueError("unsupported Ashare frequency")
        if str(params.get("source") or "auto") not in {"auto", "tencent", "sina"}:
            raise ValueError("source must be auto, tencent, or sina")
        end_date = str(params.get("end_date") or "")
        if end_date and not ISO_DATE_RE.fullmatch(end_date):
            raise ValueError("end_date must use YYYY-MM-DD")
        _bounded_int(params.get("count"), 120, 1, 1000, "count")
        _bounded_int(params.get("timeout_seconds"), 15, 5, 30, "timeout_seconds")
    else:
        _bounded_int(params.get("max_rows"), 500, 1, 5000, "max_rows")
        _bounded_int(params.get("timeout_seconds"), 20, 5, 60, "timeout_seconds")


def prepare(event_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    event = json.loads(event_path.read_text(encoding="utf-8"))
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    accepted = False
    reason = ""
    ticket = None
    try:
        parsed = json.loads(str(issue.get("body") or ""))
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        expected_prefix = (
            "[api-ashare]" if str(parsed.get("provider") or "") == "ashare"
            else "[api-akshare]"
        )
        if not str(issue.get("title") or "").startswith(expected_prefix):
            raise ValueError(f"issue title must start with {expected_prefix}")
        ticket = dict(parsed)
        accepted = True
        write_json(output_dir / "ticket.json", ticket)
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "akshare-ticket-status-v1",
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "model_calls": 0,
        "secret_values_exposed": False,
    }
    write_json(output_dir / "ticket-status.json", status)
    output("accepted", "true" if accepted else "false")
    output("reason", reason)
    return 0 if accepted else 1


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except (ValueError, TypeError):
            pass
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime().isoformat()
        except (ValueError, TypeError):
            pass
    text = str(value)
    return None if text in {"nan", "NaN", "NaT", "<NA>"} else text


def _records(frame: Any, max_rows: int) -> list[dict[str, Any]]:
    if not hasattr(frame, "head") or not hasattr(frame, "to_dict"):
        raise RuntimeError("AKShare operation did not return a tabular object")
    raw = frame.head(max_rows).to_dict("records")
    return [_json_safe(dict(row)) for row in raw]



def _http_json(url: str, timeout: int) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json,text/plain,*/*", "User-Agent": "managed-ashare-api-center/1"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Ashare upstream response exceeds 2000000 bytes")
    return json.loads(raw.decode("utf-8"))


def _normal_price_row(raw: Any, mapping: Mapping[str, int] | None = None) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return {
            "time": str(raw.get("day") or raw.get("time") or ""),
            "open": float(raw["open"]), "close": float(raw["close"]),
            "high": float(raw["high"]), "low": float(raw["low"]),
            "volume": float(raw["volume"]),
        }
    if not isinstance(raw, (list, tuple)) or mapping is None:
        raise ValueError("Ashare upstream row has an unsupported shape")
    return {
        "time": str(raw[mapping["time"]]), "open": float(raw[mapping["open"]]),
        "close": float(raw[mapping["close"]]), "high": float(raw[mapping["high"]]),
        "low": float(raw[mapping["low"]]), "volume": float(raw[mapping["volume"]]),
    }


def _ashare_tencent(symbol: str, frequency: str, count: int, end_date: str, timeout: int) -> list[dict[str, Any]]:
    if frequency in {"1d", "1w", "1M"}:
        unit = {"1d": "day", "1w": "week", "1M": "month"}[frequency]
        param = f"{symbol},{unit},,{end_date},{count},qfq"
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urllib.parse.urlencode({"param": param})
        payload = _http_json(url, timeout)
        stock = payload["data"][symbol]
        rows = stock.get(f"qfq{unit}") or stock.get(unit)
    else:
        minutes = int(frequency[:-1])
        key = f"m{minutes}"
        param = f"{symbol},{key},,{count}"
        url = "https://ifzq.gtimg.cn/appstock/app/kline/mkline?" + urllib.parse.urlencode({"param": param})
        payload = _http_json(url, timeout)
        rows = payload["data"][symbol][key]
    if not isinstance(rows, list):
        raise ValueError("Tencent Ashare endpoint returned no rows")
    mapping = {"time": 0, "open": 1, "close": 2, "high": 3, "low": 4, "volume": 5}
    normalized = [_normal_price_row(row, mapping) for row in rows[-count:]]
    return [row for row in normalized if not end_date or row["time"][:10] <= end_date]


def _ashare_sina(symbol: str, frequency: str, count: int, end_date: str, timeout: int) -> list[dict[str, Any]]:
    scale = {"1d": 240, "1w": 1200, "1M": 7200, "1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60}[frequency]
    fetch_count = min(5000, count * 5 if end_date else count)
    query = urllib.parse.urlencode({"symbol": symbol, "scale": scale, "ma": 5, "datalen": fetch_count})
    url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?" + query
    payload = _http_json(url, timeout)
    if not isinstance(payload, list):
        raise ValueError("Sina Ashare endpoint returned no rows")
    normalized = [_normal_price_row(row) for row in payload]
    return [row for row in normalized if not end_date or row["time"][:10] <= end_date][-count:]


def _ashare_get_price(params: Mapping[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or "")
    frequency = str(params.get("frequency") or "1d")
    count = _bounded_int(params.get("count"), 120, 1, 1000, "count")
    end_date = str(params.get("end_date") or "")
    source = str(params.get("source") or "auto")
    timeout = _bounded_int(params.get("timeout_seconds"), 15, 5, 30, "timeout_seconds")
    handlers = {"tencent": _ashare_tencent, "sina": _ashare_sina}
    order = ["tencent", "sina"] if source == "auto" else [source]
    failures: list[dict[str, str]] = []
    for name in order:
        try:
            rows = handlers[name](symbol, frequency, count, end_date, timeout)
            if not rows:
                raise ValueError("upstream returned an empty normalized price series")
            return {
                "provider": "ashare", "operation": "ashare-get-price",
                "symbol": symbol, "frequency": frequency, "requested_count": count,
                "row_count": len(rows), "source_used": name,
                "fallback_used": name != order[0], "rows": rows,
            }
        except (KeyError, TypeError, ValueError, OSError, TimeoutError, urllib.error.URLError) as exc:
            failures.append({"source": name, "error_type": type(exc).__name__, "message": str(exc)})
    raise RuntimeError(f"all fixed Ashare sources failed: {failures}")

def _execute_operation(operation: str, params: Mapping[str, Any]) -> dict[str, Any]:
    max_rows = _bounded_int(params.get("max_rows"), 500, 1, 5000, "max_rows")
    timeout = _bounded_int(params.get("timeout_seconds"), 20, 5, 60, "timeout_seconds")
    if operation == "catalog-capabilities":
        return {"provider": "akshare", "catalog": CATALOG}
    if operation == "ashare-get-price":
        return _ashare_get_price(params)
    import akshare as ak
    if operation == "stock-a-share-spot":
        frame = ak.stock_zh_a_spot_em()
        symbols = {
            item.strip() for item in str(params.get("symbols") or "").split(",") if item.strip()
        }
        if symbols:
            invalid = sorted(item for item in symbols if not SYMBOL_RE.fullmatch(item))
            if invalid:
                raise ValueError(f"invalid symbols: {invalid}")
            if hasattr(frame, "columns") and "代码" in list(frame.columns):
                frame = frame[frame["代码"].astype(str).isin(symbols)]
        rows = _records(frame, max_rows)
    elif operation == "stock-a-share-history":
        rows = _records(
            ak.stock_zh_a_hist(
                symbol=_symbol(params.get("symbol")),
                period=str(params.get("period") or "daily"),
                start_date=str(params.get("start_date") or "19700101"),
                end_date=str(params.get("end_date") or "20500101"),
                adjust=str(params.get("adjust") or ""),
                timeout=timeout,
            ),
            max_rows,
        )
    elif operation == "stock-company-info":
        rows = _records(
            ak.stock_individual_info_em(symbol=_symbol(params.get("symbol")), timeout=timeout),
            max_rows,
        )
    elif operation == "stock-financial-indicators":
        rows = _records(
            ak.stock_financial_analysis_indicator_em(
                symbol=_symbol(params.get("symbol")),
                indicator=str(params.get("indicator") or "按报告期"),
            ),
            max_rows,
        )
    else:
        raise ValueError(f"unsupported AKShare operation: {operation}")
    return {
        "provider": OPERATION_PROVIDERS[operation],
        "operation": operation,
        "row_count": len(rows),
        "rows": rows,
    }


def _manifest(output_dir: Path) -> None:
    rows = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "artifact-manifest.json":
            rows.append({
                "path": str(path.relative_to(output_dir)),
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    write_json(output_dir / "artifact-manifest.json", {"version": 1, "files": rows})


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    try:
        validate_ticket(ticket)
        data = _execute_operation(str(ticket["operation"]), dict(ticket.get("parameters") or {}))
        snapshot = {
            "schema_version": "akshare-snapshot-v1",
            "status": "API_AKSHARE_COMPLETED",
            "task_id": ticket["task_id"],
            "provider": ticket["provider"],
            "operation": ticket["operation"],
            "ticket_sha256": canonical_sha(ticket),
            "data": data,
            "security": {
                "model_calls": 0,
                "arbitrary_functions_allowed": False,
                "arbitrary_urls_allowed": False,
                "brokerage_execution_allowed": False,
                "secret_values_included": False,
            },
        }
        write_json(output_dir / "akshare-snapshot.json", snapshot)
        write_json(output_dir / "akshare-audit.json", {
            "status": "PASS",
            "snapshot_sha256": canonical_sha(snapshot),
            "model_calls": 0,
            "network_provider": f"{ticket['provider']} fixed public-data function",
        })
        (output_dir / "akshare-summary.md").write_text(
            "# API_AKSHARE_COMPLETED\n\n"
            f"- Task ID: `{ticket['task_id']}`\n"
            f"- Operation: `{ticket['operation']}`\n"
            f"- Snapshot SHA256: `{canonical_sha(snapshot)}`\n",
            encoding="utf-8",
        )
        output("status", "API_AKSHARE_COMPLETED")
        _manifest(output_dir)
        return 0
    except Exception as exc:
        failure = {
            "schema_version": "akshare-snapshot-v1",
            "status": "API_AKSHARE_FAILED",
            "task_id": str(ticket.get("task_id") or ""),
            "provider": str(ticket.get("provider") or ""),
            "operation": str(ticket.get("operation") or ""),
            "failure": {
                "code": "AKSHARE_UPSTREAM_OR_REQUEST_FAILED",
                "error_type": type(exc).__name__,
                "message": str(exc),
                "retryable": isinstance(exc, (OSError, TimeoutError, ConnectionError)),
            },
            "security": {
                "model_calls": 0,
                "arbitrary_functions_allowed": False,
                "arbitrary_urls_allowed": False,
                "brokerage_execution_allowed": False,
                "secret_values_included": False,
            },
        }
        write_json(output_dir / "akshare-snapshot.json", failure)
        write_json(output_dir / "akshare-error.json", {
            "error_type": type(exc).__name__,
            "message": str(exc),
            "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-20000:],
        })
        output("status", "API_AKSHARE_FAILED")
        _manifest(output_dir)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    status = json.loads((output_dir / "ticket-status.json").read_text(encoding="utf-8"))
    if phase == "accepted":
        print("## API_AKSHARE_ACCEPTED")
        print(f"\n- Task ID: `{status.get('task_id')}`")
        print(f"- Operation: `{status.get('operation')}`")
        print("- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## API_AKSHARE_REJECTED")
        print(f"\n- Reason: `{status.get('reason') or 'unknown'}`")
        return 0
    snapshot = json.loads((output_dir / "akshare-snapshot.json").read_text(encoding="utf-8"))
    print(f"## {snapshot['status']}")
    print(f"\n- Task ID: `{snapshot.get('task_id')}`")
    print(f"- Operation: `{snapshot.get('operation')}`")
    if snapshot["status"] == "API_AKSHARE_COMPLETED":
        print(f"- Snapshot SHA256: `{canonical_sha(snapshot)}`")
        data = json.dumps(snapshot["data"], ensure_ascii=False, indent=2)
        print(f"- Artifact: {artifact_url or 'unavailable'}")
        print("\n```json")
        print(data[:45000])
        print("```")
    else:
        print(f"- Error: `{snapshot.get('failure', {}).get('message') or 'unknown'}`")
        print(f"- Artifact: {artifact_url or 'unavailable'}")
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
