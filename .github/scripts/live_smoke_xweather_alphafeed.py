#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "live-smoke-artifacts"
OUT.mkdir(parents=True, exist_ok=True)


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
    return {
        "task_id": task_id,
        "provider": provider,
        "operation": operation,
        "objective": f"Live upstream smoke test for {provider}/{operation}",
        "parameters": dict(parameters),
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {
            "timeout_seconds": 90,
            "max_response_bytes": 10_000_000,
            "max_rows": 5000,
        },
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
    rc = execute(ticket_path, case_dir)
    diagnostics = json.loads((case_dir / "diagnostics.json").read_text(encoding="utf-8"))
    snapshot = None
    snapshot_path = case_dir / "snapshot.json"
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
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


def first_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, list) and value and isinstance(value[0], Mapping):
        return dict(value[0])
    return {}


def response_value(case: Mapping[str, Any]) -> Any:
    snap = case.get("snapshot")
    if not isinstance(snap, Mapping):
        return None
    data = snap.get("data")
    if isinstance(data, Mapping) and "response" in data:
        return data.get("response")
    return data


def period_range(case: Mapping[str, Any]) -> dict[str, Any]:
    response = response_value(case)
    root = first_mapping(response)
    periods = root.get("periods") if isinstance(root, Mapping) else None
    if not isinstance(periods, list):
        return {"count": 0, "first": None, "last": None}
    def stamp(row: Any) -> Any:
        if not isinstance(row, Mapping):
            return None
        ob = row.get("ob") if isinstance(row.get("ob"), Mapping) else row
        return (
            ob.get("dateTimeISO")
            or ob.get("validTime")
            or ob.get("timestamp")
            or row.get("dateTimeISO")
            or row.get("validTime")
            or row.get("timestamp")
        )
    return {
        "count": len(periods),
        "first": stamp(periods[0]) if periods else None,
        "last": stamp(periods[-1]) if periods else None,
    }


def summarize(case: Mapping[str, Any]) -> dict[str, Any]:
    base = {
        "name": case["name"],
        "provider": case["provider"],
        "operation": case["operation"],
        "status": case["status"],
        "failure": case["failure"],
        "metadata": case["metadata"],
    }
    if case["status"] not in {"API_ALPHAFEED_COMPLETED", "API_XWEATHER_COMPLETED"}:
        return base
    response = response_value(case)
    if case["provider"] == "alphafeed":
        rows = response if isinstance(response, list) else [response]
        clean = [row for row in rows if isinstance(row, Mapping)]
        base["row_count"] = len(clean)
        base["sample"] = []
        for row in clean[:3]:
            base["sample"].append({
                key: row.get(key)
                for key in (
                    "symbol", "last_price", "trade_date", "trade_time",
                    "open", "high", "low", "close", "volume",
                )
                if key in row
            })
        return base
    root = first_mapping(response)
    place = root.get("place") if isinstance(root.get("place"), Mapping) else {}
    loc = root.get("loc") if isinstance(root.get("loc"), Mapping) else {}
    profile = root.get("profile") if isinstance(root.get("profile"), Mapping) else {}
    ob = root.get("ob") if isinstance(root.get("ob"), Mapping) else {}
    periods = root.get("periods") if isinstance(root.get("periods"), list) else []
    base.update({
        "resolved_place": {
            "name": place.get("name") or root.get("name"),
            "state": place.get("state") or root.get("state"),
            "country": place.get("country") or root.get("country"),
            "lat": loc.get("lat") or root.get("lat"),
            "long": loc.get("long") or root.get("long"),
            "timezone": profile.get("tz") or root.get("tz"),
        },
        "observation": {
            "station_id": root.get("id"),
            "date_time": ob.get("dateTimeISO") or root.get("dateTimeISO"),
            "temp_c": ob.get("tempC") or root.get("tempC"),
            "humidity": ob.get("humidity") or root.get("humidity"),
            "weather": ob.get("weather") or root.get("weather"),
        },
        "period_range": period_range(case),
    })
    if periods:
        first = periods[0] if isinstance(periods[0], Mapping) else {}
        last = periods[-1] if isinstance(periods[-1], Mapping) else {}
        base["first_period"] = {
            key: first.get(key)
            for key in (
                "dateTimeISO", "validTime", "maxTempC", "minTempC", "tempC",
                "weather", "weatherPrimary", "pop", "precipMM", "humidity",
            )
            if key in first
        }
        base["last_period"] = {
            key: last.get(key)
            for key in (
                "dateTimeISO", "validTime", "maxTempC", "minTempC", "tempC",
                "weather", "weatherPrimary", "pop", "precipMM", "humidity",
            )
            if key in last
        }
    return base


cases: list[dict[str, Any]] = []

cases.append(run_case(
    "alphafeed-quotes",
    "alphafeed",
    "quotes",
    {"symbols": ["600519.SH", "000001.SZ"]},
    alphafeed.execute,
))
cases.append(run_case(
    "alphafeed-klines",
    "alphafeed",
    "klines",
    {"symbol": "600519.SH", "period": "1d", "count": 5, "adjust": "forward"},
    alphafeed.execute,
))

xweather_cases = [
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
]
for name, operation, parameters in xweather_cases:
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
status_by_name = {case["name"]: case["status"] for case in cases}
failed = [
    name for name in required
    if status_by_name.get(name) not in {"API_ALPHAFEED_COMPLETED", "API_XWEATHER_COMPLETED"}
]
raise SystemExit(1 if failed else 0)
