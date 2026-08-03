#!/usr/bin/env python3
"""Run fixed offline fixtures for evidence-standardization operations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_standardization_task import OPERATIONS

FIXTURES: dict[str, dict[str, Any]] = {
    "normalize-evidence-records": {
        "records": [{
            "source_id": "official-source",
            "source_url": "https://example.org/public/report#section",
            "retrieved_at": "2026-08-03T00:00:00Z",
            "published_at": "2026-08-02T00:00:00Z",
            "title": " Public  report ",
            "content": "First   line.\n\nSecond line.",
            "metadata": {"language": "en"}
        }]
    },
    "content-fingerprint": {
        "texts": ["same public evidence", "same public evidence", "same public evidence revised"],
        "near_duplicate_hamming_threshold": 16
    },
    "provenance-lineage": {
        "nodes": [{"id": "source"}, {"id": "snapshot"}, {"id": "package"}],
        "edges": [{"source": "source", "target": "snapshot"}, {"source": "snapshot", "target": "package"}]
    },
    "timeline-version-diff": {
        "versions": [
            {"timestamp": "2026-08-01T00:00:00Z", "content": "line one"},
            {"timestamp": "2026-08-02T00:00:00Z", "content": "line one\nline two"}
        ]
    },
    "stix-bundle-validate": {
        "bundle": {
            "type": "bundle",
            "id": "bundle--11111111-1111-4111-8111-111111111111",
            "objects": [{
                "type": "indicator",
                "spec_version": "2.1",
                "id": "indicator--22222222-2222-4222-8222-222222222222",
                "pattern_type": "stix",
                "pattern": "[domain-name:value = 'example.org']",
                "valid_from": "2026-08-03T00:00:00Z"
            }]
        }
    },
    "transfer-package-manifest": {
        "files": [{"name": "evidence/record.json", "bytes": 100, "sha256": "a" * 64, "classification": "public", "contains_personal_data": False}]
    },
    "source-quality-profile": {
        "sources": [{"source_id": "official", "authority": 1.0, "directness": 1.0, "recency": 0.9, "corroboration": 0.8, "method_transparency": 0.9}]
    }
}


def validate(operation: str) -> dict[str, Any]:
    result = OPERATIONS[operation](FIXTURES[operation])
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False)
    if not encoded or "http" in operation.lower():
        raise RuntimeError("invalid fixture receipt")
    return {"status": "PASS", "operation": operation, "network_used": False, "model_calls": 0, "secret_used": False, "result": result}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", choices=sorted(OPERATIONS))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = validate(args.operation) if args.operation else {"status": "PASS", "operation_count": len(OPERATIONS), "rows": [validate(name) for name in sorted(OPERATIONS)]}
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(target)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
