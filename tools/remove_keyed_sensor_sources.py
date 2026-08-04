#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOVED_GLOBAL = {
    "gfw-events",
    "gie-storage",
    "kpx-current-supply",
    "kpx-generation-mix",
}
REMOVED_PUBLIC = {"global-fishing-watch-vessels"}
REMOVED_SECRETS = {
    "GLOBAL_FISHING_WATCH_API_TOKEN",
    "GIE_API_KEY",
    "KOREA_DATA_GO_KR_SERVICE_KEY",
}


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def dump(path: str, value) -> None:
    (ROOT / path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def remove_operations_from_catalog(path: str, removed: set[str]) -> None:
    data = load(path)
    for provider in data.get("providers", []):
        provider["operations"] = [
            row for row in provider.get("operations", [])
            if row.get("operation_id") not in removed
        ]
        optional = provider.get("optional_secret_environment_variables")
        if isinstance(optional, list):
            provider["optional_secret_environment_variables"] = [
                item for item in optional if item not in REMOVED_SECRETS
            ]
        limits = provider.get("limits") or {}
        optional = limits.get("optional_secret_environment_variables")
        if isinstance(optional, list):
            limits["optional_secret_environment_variables"] = [
                item for item in optional if item not in REMOVED_SECRETS
            ]
        for key in (
            "noncommercial_only_operations",
            "development_only_until_production_approval",
        ):
            if isinstance(limits.get(key), list):
                limits[key] = [item for item in limits[key] if item not in removed]
        provider["limits"] = limits
    dump(path, data)


def remove_operations_from_schema(path: str, removed: set[str]) -> None:
    data = load(path)
    enum = data["properties"]["operation"]["enum"]
    data["properties"]["operation"]["enum"] = [
        item for item in enum if item not in removed
    ]
    dump(path, data)


def replace(path: str, pattern: str, replacement: str, *, flags: int = 0) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    updated = re.sub(pattern, replacement, text, flags=flags)
    target.write_text(updated, encoding="utf-8")


def remove_lines(path: str, needles: set[str]) -> None:
    target = ROOT / path
    rows = target.read_text(encoding="utf-8").splitlines()
    kept = [row for row in rows if not any(needle in row for needle in needles)]
    target.write_text("\n".join(kept) + "\n", encoding="utf-8")


def patch_global_runtime() -> None:
    path = "api-center/global-sensor-backbone/global_sensor_backbone_task.py"
    remove_lines(path, REMOVED_SECRETS)
    replace(
        path,
        r"\nGFW_DATASETS = \{.*?\n\}\n\n",
        "\n",
        flags=re.S,
    )
    replace(
        path,
        r"\n    if operation == \"gfw-events\":.*?(?=\n    if operation == \"entsog-operational-data\":)",
        "",
        flags=re.S,
    )
    replace(
        path,
        r"\ndef _safe_failure\(exc: Exception\) -> str:\n.*?(?=\n\ndef execute\()",
        "\ndef _safe_failure(exc: Exception) -> str:\n    return str(exc)[:2000]\n",
        flags=re.S,
    )
    replace(
        path,
        r"\n\s*\"gfw-events\": \"non-commercial-only\",",
        "",
    )


def patch_public_runtime() -> None:
    path = "api-center/public-data-geospatial/public_data_geospatial_task.py"
    replace(
        path,
        r"\n    if operation=='global-fishing-watch-vessels':.*?(?=\n    if operation=='opencharge-map-poi':)",
        "",
        flags=re.S,
    )


def patch_tests() -> None:
    path = "api-center/global-sensor-backbone/tests/test_global_sensor_backbone_task.py"
    replace(path, r"^import os\n", "", flags=re.M)
    replace(path, r"^from unittest\.mock import patch\n", "", flags=re.M)
    replace(
        path,
        r"\n    def test_secret_operations_fail_when_unconfigured\(self\) -> None:\n.*?(?=\n    def test_nasa_power_rejects_unknown_temporal_mode)",
        "",
        flags=re.S,
    )


def patch_docs_and_workflows() -> None:
    remove_lines(
        ".github/workflows/global-sensor-backbone-api-ticket.yml",
        REMOVED_SECRETS,
    )
    remove_lines(
        ".github/workflows/public-data-geospatial-api-ticket.yml",
        {"GLOBAL_FISHING_WATCH_API_TOKEN"},
    )
    path = ROOT / "api-center/public-data-geospatial/README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("当前开放 **35** 项", "当前开放 **34** 项")
    text = text.replace("、海洋船舶", "")
    text = re.sub(
        r"^- `global-fishing-watch-vessels`.*\n",
        "",
        text,
        flags=re.M,
    )
    text = text.replace("、`GLOBAL_FISHING_WATCH_API_TOKEN`", "")
    path.write_text(text, encoding="utf-8")


def patch_catalog_builder() -> None:
    path = ROOT / "api-center/build_catalog_market_search.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace('"public-data-geospatial": 35,', '"public-data-geospatial": 34,')
    text = text.replace(
        "not isinstance(operations, list) or len(operations) != 21",
        "not isinstance(operations, list) or len(operations) != 17",
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    remove_operations_from_catalog(
        "api-center/global-sensor-backbone/provider-catalog.json",
        REMOVED_GLOBAL,
    )
    remove_operations_from_schema(
        "api-center/global-sensor-backbone/ticket.schema.json",
        REMOVED_GLOBAL,
    )
    remove_operations_from_catalog(
        "api-center/public-data-geospatial/provider-catalog.json",
        REMOVED_PUBLIC,
    )
    remove_operations_from_schema(
        "api-center/public-data-geospatial/ticket.schema.json",
        REMOVED_PUBLIC,
    )
    patch_global_runtime()
    patch_public_runtime()
    patch_tests()
    patch_docs_and_workflows()
    patch_catalog_builder()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
