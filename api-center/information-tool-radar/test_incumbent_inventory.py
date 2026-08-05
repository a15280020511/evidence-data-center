#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import incumbent_audit
import incumbent_inventory


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        api_center = root / "api-center"
        write_json(api_center / "connector-manifest.json", {
            "connector_count": 2,
            "enabled_connector_count": 2,
            "connectors": [
                {
                    "id": "open-meteo-weather",
                    "enabled": True,
                    "backend_host": "https://api.open-meteo.com",
                    "file": "connectors/open-meteo-weather.connector.json",
                },
                {
                    "id": "open-meteo-air-quality",
                    "enabled": True,
                    "backend_host": "https://air-quality-api.open-meteo.com",
                    "file": "connectors/open-meteo-air-quality.connector.json",
                },
            ],
        })
        write_json(api_center / "connectors/open-meteo-weather.connector.json", {"enabled": True})
        write_json(api_center / "connectors/open-meteo-air-quality.connector.json", {"enabled": True})
        provider = api_center / "example-provider"
        write_json(provider / "provider-catalog.json", {
            "provider_id": "example-provider",
            "name": "Example Provider",
            "base_url": "https://api.example.org",
        })
        (provider / "example_provider_task.py").write_text("# fixture\n", encoding="utf-8")
        (provider / "README.md").write_text("# Example Provider\n\nhttps://api.example.org/docs\n", encoding="utf-8")

        inventory = incumbent_inventory.build_inventory(root)
        assert inventory["connector_operations"] == 2
        assert inventory["ordinary_service_families"] == 1
        assert inventory["managed_tool_directories"] == 1
        assert inventory["tool_count"] == 2
        identifiers = {item["tool_id"] for item in inventory["tools"]}
        assert identifiers == {"open-meteo", "example-provider"}
        assert all(item["fingerprintable"] for item in inventory["tools"])
        assert all(item["externally_locatable"] for item in inventory["tools"])

        candidates = root / "candidates.jsonl"
        candidates.write_text(
            json.dumps({
                "title": "Example Provider SDK",
                "locator": "https://github.com/example/provider",
            }) + "\n",
            encoding="utf-8",
        )
        report = incumbent_audit.audit(root, candidates)
        assert report["status"] == "pass"
        assert report["metrics"]["repository_inventory_rate"] == 1.0
        assert report["metrics"]["fingerprintable_rate"] == 1.0
        assert report["metrics"]["externally_rediscovered_tools"] == 1
        missing = {item["tool_id"] for item in report["external_rediscovery_missing"]}
        assert missing == {"open-meteo"}
        assert report["hard_gates"]["external_rediscovery_is_single_run_gate"] is False

    print(json.dumps({
        "inventory_generation": "passed",
        "connector_family_grouping": "passed",
        "managed_provider_detection": "passed",
        "fingerprint_gate": "passed",
        "external_rediscovery_separation": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
