#!/usr/bin/env python3
"""Remove the legacy Tianditu connector after managed-provider migration."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api-center"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_all(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"expected text not found in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    legacy_connector = API / "connectors/tianditu-place-search.connector.json"
    legacy_test = API / "tests/test_tianditu_connector.py"
    if not legacy_connector.is_file() or not legacy_test.is_file():
        raise RuntimeError("legacy Tianditu connector or test is already absent")
    legacy_connector.unlink()
    legacy_test.unlink()

    metadata_path = API / "catalog-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    removed = metadata["connectors"].pop("tianditu-place-search", None)
    if removed is None:
        raise RuntimeError("legacy Tianditu metadata entry not found")
    write_json(metadata_path, metadata)

    provider_path = API / "tianditu/provider-catalog.json"
    provider_catalog = json.loads(provider_path.read_text(encoding="utf-8"))
    provider_catalog["required_secret_environment_variable"] = "TIANDITU_API_KEY"
    provider_catalog["providers"][0]["required_secret_environment_variable"] = "TIANDITU_API_KEY"
    provider_catalog["replaced_legacy_connectors"] = [{
        "connector_id": "tianditu-place-search",
        "replacement": "tianditu managed provider with seven bounded place-search operations",
    }]
    write_json(provider_path, provider_catalog)

    for relative in (
        "tianditu/tianditu_task.py",
        "tianditu/tests/test_tianditu_task.py",
        "tests/test_api_catalog.py",
    ):
        replace_all(API / relative, "TIANDITU_TOKEN", "TIANDITU_API_KEY")

    replace_all(
        API / "tests/test_api_catalog.py",
        'self.assertEqual(catalog["exposed_parameter_count"], 792)',
        'self.assertEqual(catalog["exposed_parameter_count"], 790)',
    )
    replace_all(
        API / "tests/test_capability_maximization.py",
        'self.assertEqual(manifest["connector_count"], 69)',
        'self.assertEqual(manifest["connector_count"], 68)',
    )
    replace_all(
        API / "tests/test_capability_maximization.py",
        'self.assertEqual(manifest["enabled_connector_count"], 69)',
        'self.assertEqual(manifest["enabled_connector_count"], 68)',
    )

    subprocess.run(["python", "api-center/build_config.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "api-center/build_catalog_market_search.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "py_compile", "api-center/tianditu/tianditu_task.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "unittest", "discover", "-s", "api-center/tianditu/tests", "-v"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "unittest", "discover", "-s", "api-center/tests", "-v"], cwd=ROOT, check=True)

    manifest = json.loads((API / "connector-manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads((API / "api-catalog.json").read_text(encoding="utf-8"))
    assert manifest["connector_count"] == 68
    assert manifest["enabled_connector_count"] == 68
    assert "TIANDITU_API_KEY" not in manifest["required_secret_environment_variables"]
    assert all(row["id"] != "tianditu-place-search" for row in manifest["connectors"])
    assert catalog["connector_count"] == 68
    assert catalog["managed_provider_count"] == 16
    assert catalog["managed_operation_count"] == 131
    assert catalog["exposed_parameter_count"] == 790
    provider = next(row for row in catalog["managed_providers"] if row["provider_id"] == "tianditu")
    assert provider["required_secret_environment_variable_name"] == "TIANDITU_API_KEY"
    assert any(row["connector_id"] == "tianditu-place-search" for row in catalog["replaced_legacy_connectors"])
    print(json.dumps({
        "status": "PASS",
        "legacy_connector_removed": True,
        "connectors": 68,
        "managed_providers": 16,
        "managed_operations": 131,
        "exposed_parameters": 790,
        "secret": "TIANDITU_API_KEY",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
