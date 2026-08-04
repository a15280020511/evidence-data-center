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
FULL_REQUIRED = {
    "source_id", "name", "domains", "regions", "source_type", "integration_state",
    "access_modes", "official_url", "api_url", "credential_mode", "cost_class",
    "license_note", "china_coverage", "canonical_ids", "existing_provider",
}
COMPACT_REQUIRED = {
    "source_id", "name", "domains", "regions", "source_type", "integration_state",
    "official_url", "api_url", "credential_mode", "cost_class", "china_coverage",
    "existing_provider",
}
SCHEMA_FIELDS = {
    "global-knowledge-registry-source-file-v1": FULL_REQUIRED,
    "global-knowledge-registry-compact-source-file-v1": COMPACT_REQUIRED,
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    index = load(INDEX)
    assert index["schema_version"] == "global-knowledge-registry-index-v1"
    contract = load(CONTRACT)
    assert contract["schema_version"] == "global-knowledge-graph-contract-v1"
    assert len(contract["node_types"]) == len(set(contract["node_types"]))
    assert len(contract["edge_types"]) == len(set(contract["edge_types"]))
    rows = []
    for item in index["category_files"]:
        path = HERE.parent / Path(item["path"]).relative_to("api-center")
        payload = load(path)
        expected_fields = SCHEMA_FIELDS.get(payload.get("schema_version"))
        assert expected_fields is not None, f"unsupported source schema: {path}"
        assert payload["source_count"] == len(payload["sources"]) == item["source_count"]
        rows.extend((row, expected_fields, path.name) for row in payload["sources"])
    assert len(rows) == index["source_count"]
    ids = [row["source_id"] for row, _, _ in rows]
    assert len(ids) == len(set(ids)), "duplicate source_id"
    for row, expected_fields, filename in rows:
        assert set(row) == expected_fields, f"unexpected fields for {row.get('source_id')} in {filename}"
        assert row["integration_state"] in ALLOWED_STATES
        assert row["domains"] and row["regions"]
        if "access_modes" in row:
            assert row["access_modes"]
        official = urlsplit(row["official_url"])
        assert official.scheme in {"https", "http"} and official.netloc
        if row["api_url"]:
            api = urlsplit(row["api_url"])
            assert api.scheme in {"https", "http"} and api.netloc
        if row["integration_state"] == "existing-active":
            assert row["existing_provider"], f"missing provider for {row['source_id']}"
        rendered = json.dumps(row, ensure_ascii=False).lower()
        assert not any(marker in rendered for marker in [
            "api_key=", "bearer ", "secret=", "password=",
        ])
    expected = Counter(row["integration_state"] for row, _, _ in rows)
    assert dict(sorted(expected.items())) == index["integration_state_counts"]
    print(json.dumps({
        "status": "PASS",
        "source_count": len(rows),
        "category_file_count": len(index["category_files"]),
        "node_type_count": len(contract["node_types"]),
        "edge_type_count": len(contract["edge_types"]),
        "integration_state_counts": index["integration_state_counts"],
        "secret_values_exposed": False,
        "network_used": False,
        "model_calls": 0,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
