#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "live-smoke-artifacts"
OUT.mkdir(parents=True, exist_ok=True)


def hydrate_transient_xweather_client_id() -> None:
    if str(os.getenv("XWEATHER_CLIENT_ID") or "").strip():
        return
    event_path = Path(str(os.getenv("GITHUB_EVENT_PATH") or ""))
    if not event_path.is_file():
        return
    event = json.loads(event_path.read_text(encoding="utf-8"))
    pull_request = event.get("pull_request") if isinstance(event, Mapping) else None
    body = str(pull_request.get("body") or "") if isinstance(pull_request, Mapping) else ""
    match = re.search(r"<!--\s*XWEATHER_TEST_CLIENT_ID:([^\s<>]+)\s*-->", body)
    if match:
        os.environ["XWEATHER_CLIENT_ID"] = match.group(1)


hydrate_transient_xweather_client_id()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


alphafeed = load_module(
    "alphafeed_task_live",
    ROOT / "api-center/alphafeed/alphafeed_task.py",
)
xweather = load_module(
    "xweather_task_live",
    ROOT / "api-center/xweather/xweather_task.py",
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ticket(provider: str, operation: str, parameters: Mapping[str, Any], task_id: str) -> dict[str, Any]:
    acceptance: dict[str, Any] = {
        "timeout_seconds": 90,
        "max_response_bytes": 10_000_000,
    }
    if provider == "xweather":
        acceptance["max_rows"] = 5000
    return {
        "task_id": task_id,
        "provider": provider,
        "operation": operation,
        "objective": f"Live upstream smoke test for {provider}/{operation}",
        "parameters": dict(parameters),
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": acceptance,
    }


def run_case(
    name: str,
    provider: str,
    operation: str,
    parameters: Mapping[str, Any],
    execute: Callable[[Path, Path], int],
) -> dict[str, Any]:
    case_dir = OUT / name
    case_dir.mkdir(parents=True, exist_ok=True)
    ticket_path = case_dir / "ticket.json"
    write_json(ticket_path, ticket(provider, operation, parameters, f"live-{name}"))
    try:
        rc = execute(ticket_path, case_dir)
    except Exception as exc:
        return {
            "name": name,
            "provider": provider,
            "operation": operation,
            "return_code": 1,
            "status": "HARNESS_FAILED",
            "failure": {"type": type(exc).__name__, "message": str(exc)[:1000]},
            "metadata": {},
            "snapshot": None,
        }
    diagnostics = json.loads((case_dir / "diagnostics.json").read_text(encoding="utf-8"))
    snapshot_path = case_dir / "snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8")) if snapshot_path.exists() else None
    return {
        "name": name,
        "provider": provider,
        "operation": operation,
        "return_code": rc,
        "status": diagnostics.get("status"),
        "failure": diagnostics.get("failure"),
        "metadata": diagnostics.get("metadata"),
        "snapshot": snapshot,
    }


def response_value(case: Mapping[str, Any]) -> Any:
    snapshot = case.get("snapshot")
    if not isinstance(snapshot, Mapping):
        return None
    data = snapshot.get("data")
    if isinstance(data, Mapping) and "response" in data:
        return data.get("response")
    return data


def first_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, list) and value and isinstance(value[0], Mapping):
        return dict(value[0])
    return {}


def stamp(row: Any) -> Any:
    if not isinstance(row, Mapping):
        return None
    nested = row.get("ob") if isinstance(row.get("ob"), Mapping) else row
    return (
        nested.get("dateTimeISO")
        or nested.get("validTime")
        or nested.get("trade_date")
        or nested.get("trade_time")
        or nested.get("timestamp")
    )


def summarize(case: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": case["name"],
        "provider": case["provider"],
        "operation": case["operation"],
        "status": case["status"],
        "failure": case["failure"],
        "metadata": case["metadata"],
    }
    if case["status"] not in {"API_ALPHAFEED_COMPLETED", "API_XWEATHER_COMPLETED"}:
        return result
    response = response_value(case)
    if case["provider"] == "alphafeed":
        if isinstance(response, Mapping) and isinstance(response.get("data"), list):
            rows = response["data"]
        elif isinstance(response, list):
            rows = response
        else:
            rows = [response]
        clean = [dict(row) for row in rows if isinstance(row, Mapping)]
        result["row_count"] = len(clean)
        result["sample"] = [
            {
                key: row.get(key)
                for key in (
                    "symbol", "last_price", "trade_date", "trade_time",
                    "open", "high", "low", "close", "volume",
                )
                if key in row
            }
            for row in clean[:3]
        ]
        if clean:
            result["range"] = {"first": stamp(clean[0]), "last": stamp(clean[-1])}
        return result

    root = first_mapping(response)
    place = root.get("place") if isinstance(root.get("place"), Mapping) else {}
    loc = root.get("loc") if isinstance(root.get("loc"), Mapping) else {}
    profile = root.get("profile") if isinstance(root.get("profile"), Mapping) else {}
    ob = root.get("ob") if isinstance(root.get("ob"), Mapping) else {}
    periods = root.get("periods") if isinstance(root.get("periods"), list) else []
    result["resolved_place"] = {
        "name": place.get("name") or root.get("name"),
        "state": place.get("state") or root.get("state"),
        "country": place.get("country") or root.get("country"),
        "lat": loc.get("lat") if "lat" in loc else root.get("lat"),
        "long": loc.get("long") if "long" in loc else root.get("long"),
        "timezone": profile.get("tz") or root.get("tz"),
    }
    result["observation"] = {
        "station_id": root.get("id"),
        "date_time": ob.get("dateTimeISO") or root.get("dateTimeISO"),
        "temp_c": ob.get("tempC") if "tempC" in ob else root.get("tempC"),
        "humidity": ob.get("humidity") if "humidity" in ob else root.get("humidity"),
        "weather": ob.get("weather") or root.get("weather"),
    }
    result["period_range"] = {
        "count": len(periods),
        "first": stamp(periods[0]) if periods else None,
        "last": stamp(periods[-1]) if periods else None,
    }
    if periods:
        for label, row in (("first_period", periods[0]), ("last_period", periods[-1])):
            if isinstance(row, Mapping):
                result[label] = {
                    key: row.get(key)
                    for key in (
                        "dateTimeISO", "validTime", "maxTempC", "minTempC", "tempC",
                        "weather", "weatherPrimary", "pop", "precipMM", "humidity",
                    )
                    if key in row
                }
    return result


cases: list[dict[str, Any]] = [
    run_case(
        "alphafeed-quotes", "alphafeed", "quotes",
        {"symbols": ["600519.SH", "000001.SZ"]}, alphafeed.execute,
    ),
    run_case(
        "alphafeed-klines", "alphafeed", "klines",
        {"symbol": "600519.SH", "period": "1d", "count": 5, "adjust": "forward"},
        alphafeed.execute,
    ),
]

for name, operation, parameters in [
    ("xweather-fujian-place", "places-closest", {"p": "fujian,china", "limit": 5}),
    ("xweather-fuzhou-place", "places-closest", {"p": "fuzhou,fujian,china", "limit": 3}),
    ("xweather-fuzhou-observation", "observations-current", {"location": "fuzhou,fujian,china"}),
    ("xweather-fuzhou-current", "conditions", {"location": "26.0745,119.2965", "filter": "1hr", "limit": 1}),
    ("xweather-fuzhou-forecast", "forecasts", {"location": "fuzhou,fujian,china", "filter": "day", "limit": 15}),
    ("xweather-fuzhou-recent-history", "observations-summary", {
        "location": "fuzhou,fujian,china", "from": "2026-07-25", "to": "2026-07-31", "limit": 7,
    }),
    ("xweather-fuzhou-2011-history", "observations-summary", {
        "location": "fuzhou,fujian,china", "from": "2011-08-02", "to": "2011-08-02", "limit": 1,
    }),
    ("xweather-fuzhou-2004-condition", "conditions", {
        "location": "26.0745,119.2965", "at_time": "2004-01-15T12:00:00", "filter": "1hr", "limit": 1,
    }),
]:
    cases.append(run_case(name, "xweather", operation, parameters, xweather.execute))

summary = {
    "schema_version": "alphafeed-xweather-live-smoke-v1",
    "credentials_configured": {
        "ALPHAFEED_API_KEY": bool(str(os.getenv("ALPHAFEED_API_KEY") or "").strip()),
        "XWEATHER_CLIENT_ID": bool(str(os.getenv("XWEATHER_CLIENT_ID") or "").strip()),
        "XWEATHER_CLIENT_SECRET": bool(str(os.getenv("XWEATHER_CLIENT_SECRET") or "").strip()),
    },
    "cases": [summarize(case) for case in cases],
    "secret_values_exposed": False,
}
write_json(OUT / "summary.json", summary)
print(json.dumps(summary, ensure_ascii=False, indent=2))

required = {
    "alphafeed-quotes",
    "alphafeed-klines",
    "xweather-fuzhou-place",
    "xweather-fuzhou-observation",
    "xweather-fuzhou-current",
    "xweather-fuzhou-forecast",
    "xweather-fuzhou-recent-history",
}
completed = {"API_ALPHAFEED_COMPLETED", "API_XWEATHER_COMPLETED"}
status_by_name = {case["name"]: case["status"] for case in cases}
failed = [name for name in required if status_by_name.get(name) not in completed]
raise SystemExit(1 if failed else 0)
