#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
INDEX = HERE / "registry-index.json"
CONTRACT = HERE / "graph-contract.json"

ALLOWED_STATES = {
    "existing-active", "backbone-candidate", "catalog-only", "conditional-free",
    "application-required", "web-only", "deferred",
}
REQUIRED = {
    "source_id", "name", "domains", "regions", "source_type", "integration_state",
    "access_modes", "official_url", "api_url", "credential_mode", "cost_class",
    "license_note", "china_coverage", "canonical_ids", "existing_provider",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    index = load(INDEX)
    assert index["schema_version"] == "global-knowledge-registry-index-v1"
    assert load(CONTRACT)["schema_version"] == "global-knowledge-graph-contract-v1"
    rows = []
    for item in index["category_files"]:
        path = HERE.parent / Path(item["path"]).relative_to("api-center")
        payload = load(path)
        assert payload["source_count"] == len(payload["sources"]) == item["source_count"]
        rows.extend(payload["sources"])
    assert len(rows) == index["source_count"]
    ids = [row["source_id"] for row in rows]
    assert len(ids) == len(set(ids)), "duplicate source_id"
    for row in rows:
        assert set(row) == REQUIRED, f"unexpected fields for {row.get('source_id')}"
        assert row["integration_state"] in ALLOWED_STATES
        assert row["domains"] and row["regions"] and row["access_modes"]
        official = urlsplit(row["official_url"])
        assert official.scheme in {"https", "http"} and official.netloc
        if row["api_url"]:
            api = urlsplit(row["api_url"])
            assert api.scheme in {"https", "http"} and api.netloc
        if row["integration_state"] == "existing-active":
            assert row["existing_provider"], f"missing provider for {row['source_id']}"
        assert not any(marker in json.dumps(row, ensure_ascii=False).lower() for marker in [
            "api_key=", "bearer ", "secret=", "password=",
        ])
    expected = Counter(row["integration_state"] for row in rows)
    assert dict(sorted(expected.items())) == index["integration_state_counts"]
    print(json.dumps({
        "status": "PASS",
        "source_count": len(rows),
        "category_file_count": len(index["category_files"]),
        "integration_state_counts": index["integration_state_counts"],
        "secret_values_exposed": False,
        "network_used": False,
        "model_calls": 0,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
