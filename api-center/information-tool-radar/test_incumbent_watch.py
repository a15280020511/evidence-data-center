#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import incumbent_watch


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def fixture_repo(root: Path) -> None:
    api_center = root / "api-center"
    write_json(api_center / "connector-manifest.json", {
        "connectors": [
            {
                "id": "worldbank-countries",
                "enabled": True,
                "backend_host": "https://api.worldbank.org",
                "file": "connectors/worldbank-countries.connector.json",
            }
        ]
    })
    write_json(api_center / "connectors/worldbank-countries.connector.json", {"enabled": True})
    provider = api_center / "internal-module"
    write_json(provider / "provider-catalog.json", {"provider_id": "internal-module"})
    (provider / "internal_module_task.py").write_text("# fixture\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fixture_repo(root)
        global_candidates = root / "global.jsonl"
        global_candidates.write_text(json.dumps({"title": "unrelated", "locator": "https://example.org"}) + "\n", encoding="utf-8")
        baseline = root / "baseline.json"
        report, incumbent_rows, combined, extra = incumbent_watch.build(root, global_candidates, baseline)
        assert report["status"] == "pass"
        assert report["metrics"]["tool_count"] == 2
        assert report["metrics"]["seeded_coverage"] == 1.0
        assert report["metrics"]["fingerprint_coverage"] == 1.0
        assert len(incumbent_rows) == 2
        assert len(combined) == 3
        assert report["delta"]["baseline_present"] is False
        assert sorted(report["delta"]["new_tools"]) == ["internal-module", "world-bank"]
        assert len(extra["plan"]["tools"]) == 2

        write_json(baseline, extra["state"])
        report2, _, _, _ = incumbent_watch.build(root, global_candidates, baseline)
        assert report2["delta"]["baseline_present"] is True
        assert report2["delta"]["new_tools"] == []
        assert report2["delta"]["removed_tools"] == []
        assert report2["delta"]["changed_tools"] == []
        assert len(report2["delta"]["unchanged_tools"]) == 2

    print(json.dumps({
        "seeded_coverage": "passed",
        "fingerprint_coverage": "passed",
        "combined_candidates": "passed",
        "rotation_plan": "passed",
        "baseline_delta": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
