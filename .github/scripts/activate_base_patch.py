#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "api-center/global-literature-libraries/source-access-matrix.json"
PROVIDER_PATH = ROOT / "api-center/global-literature-libraries/provider-catalog.json"
TASK_PATH = ROOT / "api-center/global-literature-libraries/global_literature_task.py"
VALIDATOR_PATH = ROOT / "api-center/global-literature-libraries/validate_global_literature.py"
VALIDATE_WORKFLOW_PATH = ROOT / ".github/workflows/global-literature-validate.yml"
DOCS_PATH = ROOT / "api-center/global-literature-libraries/SCHOLARLY_INDEX_ACCESS.md"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_matrix() -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    sources = [row for row in matrix["sources"] if row.get("source_id") != "base"]
    base_row = {
        "source_id": "base",
        "name": "BASE (Bielefeld Academic Search Engine)",
        "category": "global-scholarly",
        "protocol": "rest-search",
        "base_url": "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi",
        "operations": ["literature-search"],
        "credential_mode": "none",
        "credential_env": "",
        "access_control": "ip_allowlist_required",
        "access_note": "BASE does not issue an API key for this interface. The execution platform public egress IP must be approved by BASE before live requests will succeed.",
        "license_policy": "Metadata discovery and source-provided links only; non-commercial BASE access terms and record-level rights apply.",
        "cost": "free after BASE IP approval",
    }
    insert_at = next(
        (index + 1 for index, row in enumerate(sources) if row.get("source_id") == "semantic-scholar"),
        0,
    )
    sources.insert(insert_at, base_row)
    matrix["sources"] = sources
    matrix["active_source_count"] = len(sources)
    for row in matrix.get("not_enabled", []):
        if row.get("source_id") == "base-oai":
            row["reason"] = (
                "The HTTP-only, IP-restricted BASE OAI harvesting endpoint remains disabled. "
                "The separate HTTPS BASE Search API is enabled as source_id base and still "
                "requires BASE approval of the execution egress IP."
            )
    write_json(MATRIX_PATH, matrix)


def patch_provider() -> None:
    document = json.loads(PROVIDER_PATH.read_text(encoding="utf-8"))
    provider = document["providers"][0]
    provider["description"] = (
        "固定接入BASE、Semantic Scholar等全球学术聚合、经济政策灰色文献、研究仓储、"
        "医学工程资料、预印本、国家图书馆、文化遗产与欧洲专利公开文献。"
    )
    provider["catalog_policy"] = (
        "仅开放10项固定只读操作和26个固定HTTPS来源；禁止任意URL、主机、路径、Header、"
        "客户端Key、动态Provider、付费墙绕过和未授权全文复制。"
    )
    provider["limits"]["source_count"] = 26
    operation = next(row for row in provider["operations"] if row["operation_id"] == "literature-search")
    source_enum = operation["parameter_schema"]["properties"]["source_id"]["enum"]
    source_enum = [value for value in source_enum if value != "base"]
    insert_at = source_enum.index("semantic-scholar") + 1 if "semantic-scholar" in source_enum else 0
    source_enum.insert(insert_at, "base")
    operation["parameter_schema"]["properties"]["source_id"]["enum"] = source_enum
    write_json(PROVIDER_PATH, document)


def patch_task() -> None:
    text = TASK_PATH.read_text(encoding="utf-8")
    marker = '    elif source_id == "semantic-scholar":\n'
    block = (
        '    elif source_id == "base":\n'
        '        url = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"\n'
        '        headers["Accept"] = "application/json, application/xml;q=0.8, text/xml;q=0.8"\n'
        '        query += [("func", "PerformSearch"), ("format", "json"), ("query", query_text), ("hits", str(limit)), ("offset", "0"), ("boost", "oa")]\n'
    )
    if block not in text:
        if text.count(marker) != 1:
            raise RuntimeError("semantic-scholar search marker is not unique")
        text = text.replace(marker, block + marker, 1)
    TASK_PATH.write_text(text, encoding="utf-8")


def patch_validator() -> None:
    text = VALIDATOR_PATH.read_text(encoding="utf-8")
    text = text.replace("        == 25\n", "        == 26\n", 1)
    marker = '    assert provider["limits"]["unauthorized_full_text_copying_allowed"] is False\n'
    block = (
        marker
        + '    base_source = next(row for row in sources if row["source_id"] == "base")\n'
        + '    assert base_source["credential_mode"] == "none"\n'
        + '    assert base_source["credential_env"] == ""\n'
        + '    assert base_source["access_control"] == "ip_allowlist_required"\n'
    )
    if "base_source = next(" not in text:
        if text.count(marker) != 1:
            raise RuntimeError("validator assertion marker is not unique")
        text = text.replace(marker, block, 1)
    VALIDATOR_PATH.write_text(text, encoding="utf-8")


def patch_validate_workflow() -> None:
    text = VALIDATE_WORKFLOW_PATH.read_text(encoding="utf-8")
    text = text.replace("assert receipt['source_count']==25", "assert receipt['source_count']==26")
    VALIDATE_WORKFLOW_PATH.write_text(text, encoding="utf-8")


def write_docs() -> None:
    DOCS_PATH.write_text(
        "# Scholarly index access configuration\n\n"
        "The three requested scholarly indexes are registered as follows.\n\n"
        "| Source | GitHub configuration name | Access mode |\n"
        "|---|---|---|\n"
        "| OpenAlex | `OPENALEX_API_KEY` | Required free API key; store as an Actions secret. |\n"
        "| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | Free API key; store as an Actions secret. Anonymous access remains possible at lower limits. |\n"
        "| BASE | No API key | BASE approves the caller public egress IP. The HTTPS Search API is registered, while the HTTP-only OAI harvesting endpoint remains disabled. |\n\n"
        "BASE live execution fails closed until BASE has approved a stable public egress IP used by the execution platform. Do not create a fake `BASE_API_KEY` secret.\n",
        encoding="utf-8",
    )


def main() -> None:
    patch_matrix()
    patch_provider()
    patch_task()
    patch_validator()
    patch_validate_workflow()
    write_docs()


if __name__ == "__main__":
    main()
