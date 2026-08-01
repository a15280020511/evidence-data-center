#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

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


xweather = load_module("xweather_task_diag", ROOT / "api-center/xweather/xweather_task.py")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_case(name: str) -> dict[str, Any]:
    case_dir = OUT / name
    case_dir.mkdir(parents=True, exist_ok=True)
    ticket = {
        "task_id": f"diag-{name}",
        "provider": "xweather",
        "operation": "places-closest",
        "objective": "Minimal Xweather authentication diagnostic",
        "parameters": {"p": "fuzhou,fujian,china", "limit": 1},
        "data_policy": {"classification": "public", "contains_personal_data": False},
        "acceptance": {
            "timeout_seconds": 60,
            "max_response_bytes": 2_000_000,
            "max_rows": 100,
        },
    }
    ticket_path = case_dir / "ticket.json"
    write_json(ticket_path, ticket)
    rc = xweather.execute(ticket_path, case_dir)
    diagnostics = json.loads((case_dir / "diagnostics.json").read_text(encoding="utf-8"))
    snapshot_path = case_dir / "snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8")) if snapshot_path.exists() else None
    return {
        "name": name,
        "return_code": rc,
        "status": diagnostics.get("status"),
        "failure": diagnostics.get("failure"),
        "metadata": diagnostics.get("metadata"),
        "snapshot_present": snapshot is not None,
    }


client_id = str(os.getenv("XWEATHER_CLIENT_ID") or "").strip()
client_secret = str(os.getenv("XWEATHER_CLIENT_SECRET") or "").strip()
looks_combined = bool(client_id and client_secret.startswith(client_id + "_"))
summary: dict[str, Any] = {
    "schema_version": "xweather-credential-format-diagnostic-v1",
    "credential_shape": {
        "client_id_present": bool(client_id),
        "client_secret_present": bool(client_secret),
        "client_id_length": len(client_id),
        "client_secret_length": len(client_secret),
        "secret_contains_underscore": "_" in client_secret,
        "secret_starts_with_client_id_and_underscore": looks_combined,
        "values_exposed": False,
    },
    "original_pair": run_case("original-pair"),
    "derived_from_combined_key": None,
    "secret_values_exposed": False,
}

if looks_combined:
    derived = client_secret[len(client_id) + 1 :]
    os.environ["XWEATHER_CLIENT_SECRET"] = derived
    summary["derived_from_combined_key"] = {
        "derived_secret_length": len(derived),
        "result": run_case("derived-secret-pair"),
    }

write_json(OUT / "summary.json", summary)
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0)
