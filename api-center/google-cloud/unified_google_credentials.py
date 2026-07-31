#!/usr/bin/env python3
"""Expand the single repository Google credential bundle into ephemeral runtime variables."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

BUNDLE_ENV = "GOOGLE_CREDENTIALS_JSON"


def parse_bundle(raw: str) -> tuple[dict[str, Any], str]:
    text = raw.strip()
    if not text:
        raise RuntimeError(f"missing repository Secret {BUNDLE_ENV}")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{BUNDLE_ENV} is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{BUNDLE_ENV} must contain a JSON object")
    service_account = value.get("service_account")
    api_key = str(value.get("data_commons_api_key") or "").strip()
    if not isinstance(service_account, Mapping):
        raise RuntimeError(f"{BUNDLE_ENV}.service_account must be a JSON object")
    required = {"type", "project_id", "private_key_id", "private_key", "client_email", "token_uri"}
    missing = sorted(required - set(service_account))
    if missing:
        raise RuntimeError(f"{BUNDLE_ENV}.service_account is missing fields: {missing}")
    if str(service_account.get("type") or "") != "service_account":
        raise RuntimeError(f"{BUNDLE_ENV}.service_account.type must be service_account")
    if not api_key:
        raise RuntimeError(f"{BUNDLE_ENV}.data_commons_api_key is required")
    return dict(service_account), api_key


def append_multiline(path: Path, name: str, value: str) -> None:
    delimiter = f"GOOGLE_BUNDLE_{name}_EOF"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def export_runtime(raw: str, github_env: Path) -> None:
    service_account, data_commons_api_key = parse_bundle(raw)
    encoded = json.dumps(service_account, ensure_ascii=False, separators=(",", ":"))
    append_multiline(github_env, "BIGQUERY_SERVICE_ACCOUNT_JSON", encoded)
    append_multiline(github_env, "EARTH_ENGINE_SERVICE_ACCOUNT_JSON", encoded)
    append_multiline(github_env, "GOOGLE_DATA_COMMONS_API_KEY", data_commons_api_key)


def main() -> int:
    github_env = str(os.getenv("GITHUB_ENV") or "").strip()
    if not github_env:
        raise RuntimeError("GITHUB_ENV is required")
    export_runtime(str(os.getenv(BUNDLE_ENV) or ""), Path(github_env))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
