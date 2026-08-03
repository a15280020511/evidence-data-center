#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "api-center/global-literature-libraries/source-access-matrix.json"
PROVIDER = ROOT / "api-center/global-literature-libraries/provider-catalog.json"
TASK = ROOT / "api-center/global-literature-libraries/global_literature_task.py"
VALIDATOR = ROOT / "api-center/global-literature-libraries/validate_global_literature.py"
DOCS = ROOT / "api-center/global-literature-libraries/SCHOLARLY_INDEX_ACCESS.md"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_matrix() -> None:
    document = json.loads(MATRIX.read_text(encoding="utf-8"))
    row = next(item for item in document["sources"] if item["source_id"] == "base")
    row["credential_mode"] = "required_free_key"
    row["credential_env"] = "BASE_API_KEY"
    row.pop("access_control", None)
    row.pop("access_note", None)
    row["access_note"] = "BASE HTTP Interface authenticates with the query parameter apikey. Store the issued key only in the BASE_API_KEY backend secret."
    row["cost"] = "free registration key"
    write_json(MATRIX, document)


def patch_provider() -> None:
    document = json.loads(PROVIDER.read_text(encoding="utf-8"))
    provider = document["providers"][0]
    names = list(provider.get("optional_secret_environment_variables") or [])
    if "BASE_API_KEY" not in names:
        insert_at = names.index("SEMANTIC_SCHOLAR_API_KEY") + 1 if "SEMANTIC_SCHOLAR_API_KEY" in names else len(names)
        names.insert(insert_at, "BASE_API_KEY")
    provider["optional_secret_environment_variables"] = names
    write_json(PROVIDER, document)


def patch_task() -> None:
    text = TASK.read_text(encoding="utf-8")
    marker = '    elif source_id == "semantic-scholar":\n        headers["x-api-key"] = value\n'
    replacement = marker + '    elif source_id == "base":\n        query.append(("apikey", value))\n'
    if 'elif source_id == "base":\n        query.append(("apikey", value))' not in text:
        if text.count(marker) != 1:
            raise RuntimeError("semantic-scholar credential marker is not unique")
        text = text.replace(marker, replacement, 1)
    TASK.write_text(text, encoding="utf-8")


def patch_validator() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    dummy_marker = '    "SEMANTIC_SCHOLAR_API_KEY": "fixture-semantic-key",\n'
    if '"BASE_API_KEY": "fixture-base-key"' not in text:
        if text.count(dummy_marker) != 1:
            raise RuntimeError("dummy secret marker is not unique")
        text = text.replace(dummy_marker, dummy_marker + '    "BASE_API_KEY": "fixture-base-key",\n', 1)
    old = (
        '    assert base_source["credential_mode"] == "none"\n'
        '    assert base_source["credential_env"] == ""\n'
        '    assert base_source["access_control"] == "ip_allowlist_required"\n'
    )
    new = (
        '    assert base_source["credential_mode"] == "required_free_key"\n'
        '    assert base_source["credential_env"] == "BASE_API_KEY"\n'
        '    assert "access_control" not in base_source\n'
    )
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError("BASE validator assertion block not found")
    VALIDATOR.write_text(text, encoding="utf-8")


def patch_docs() -> None:
    DOCS.write_text(
        "# Scholarly index access configuration\n\n"
        "The three requested scholarly indexes are registered as follows.\n\n"
        "| Source | GitHub configuration name | Access mode |\n"
        "|---|---|---|\n"
        "| OpenAlex | `OPENALEX_API_KEY` | Free API key; store as an Actions secret. |\n"
        "| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | Free API key; store as an Actions secret. Anonymous access remains possible at lower limits. |\n"
        "| BASE | `BASE_API_KEY` | Free BASE HTTP Interface key; injected only as the upstream `apikey` query parameter. |\n\n"
        "Do not paste keys into tickets or task parameters. The runtime accepts no client-supplied credentials and injects each key only from its dedicated backend secret.\n",
        encoding="utf-8",
    )


def main() -> None:
    patch_matrix()
    patch_provider()
    patch_task()
    patch_validator()
    patch_docs()


if __name__ == "__main__":
    main()
