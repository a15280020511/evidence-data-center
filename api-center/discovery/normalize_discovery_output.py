#!/usr/bin/env python3
"""Normalize discovery output so catalog/repository references are never reported as operational integrations."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_HOSTS = {"github.com", "raw.githubusercontent.com"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run(args: argparse.Namespace) -> int:
    registry_doc = load(args.registry)
    candidates_doc = load(args.candidates)
    result = load(args.result)

    candidate_map = {
        row["source_id"]: dict(row)
        for row in candidates_doc.get("candidates") or []
        if isinstance(row, dict) and row.get("source_id")
    }
    kept = []
    demoted = 0
    for source in registry_doc.get("sources") or []:
        row = dict(source)
        if str(row.get("host") or "").casefold() in REPOSITORY_HOSTS:
            row.update(
                trusted_domain=False,
                source_type="repository_reference",
                status="repository_reference",
                integration_mode="metadata_only",
            )
            candidate_map[row["source_id"]] = row
            demoted += 1
        else:
            kept.append(row)

    candidates = sorted(
        candidate_map.values(),
        key=lambda row: (-int(row.get("score") or 0), str(row.get("source_id") or "")),
    )
    updated_at = now()
    registry_doc.update(
        schema_version="global-source-registry-v2",
        updated_at=updated_at,
        source_count=len(kept),
        sources=sorted(kept, key=lambda row: str(row.get("source_id") or "")),
    )
    candidates_doc.update(
        schema_version="global-source-candidates-v2",
        updated_at=updated_at,
        candidate_count=len(candidates),
        candidates=candidates,
    )
    save(args.registry, registry_doc)
    save(args.candidates, candidates_doc)

    operational = [row for row in kept if row.get("source_type") != "web_read"]
    web_sources = [row for row in kept if row.get("source_type") == "web_read"]
    catalog_count = sum(1 for row in candidates if row.get("status") == "catalog_reference")
    repository_count = sum(1 for row in candidates if row.get("status") == "repository_reference")
    keyed = [row for row in candidates if row.get("status") == "key_required_high_value"]

    result["integrated_operational"] = len(operational)
    result["integrated_web_read"] = len(web_sources)
    result["catalog_references"] = catalog_count
    result["repository_references"] = repository_count
    result["candidates"] = len(candidates)
    result["keyed"] = len(keyed)
    result["normalization"] = {"github_rows_demoted": demoted}
    save(args.result, result)

    lines = [
        "# 全球来源自动发现日报",
        "",
        f"- 运行时间：{updated_at}",
        f"- 轮换查询数：{result.get('queries', 0)}",
        f"- 本轮原始发现：{result.get('discovered', 0)}",
        f"- 本轮安全探测：{result.get('probed', 0)}",
        f"- 可直接调用的 API/MCP/数据端点：{len(operational)}",
        f"- 已登记可直接读取的机构网页/报告：{len(web_sources)}",
        f"- OpenAPI 目录参考：{catalog_count}",
        f"- 代码仓库/MCP 项目参考：{repository_count}",
        f"- 高价值需 Key：{len(keyed)}",
        f"- 本轮通知渠道：{(result.get('notification') or {}).get('channel', 'none')}",
        f"- 非阻断错误：{len(result.get('errors') or [])}",
        "",
        "自动接入只统计真实端点或可直接读取的公开页面。OpenAPI 说明文件和 GitHub/MCP 代码仓库仅作为目录参考，不执行其中的命令、包、容器或本地 MCP 服务。",
    ]
    if operational:
        lines += ["", "## 可直接调用的数据端点", ""] + [
            f"- `{row['source_id']}` | {row['source_type']} | {row.get('score', 0)} | {row.get('title', '')} | {row.get('url', '')}"
            for row in operational[-25:]
        ]
    if web_sources:
        lines += ["", "## 可直接读取的机构网页/报告", ""] + [
            f"- `{row['source_id']}` | {row.get('score', 0)} | {row.get('title', '')} | {row.get('url', '')}"
            for row in web_sources[-25:]
        ]
    if keyed:
        lines += ["", "## 高价值需 Key", ""] + [
            f"- {row.get('score', 0)} | {row.get('title', '')} | {row.get('url', '')}" for row in keyed[:25]
        ]
    errors = result.get("errors") or []
    if errors:
        lines += ["", "## 非阻断错误", ""] + [f"- {item}" for item in errors[:20]]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "normalized", "github_rows_demoted": demoted, "operational": len(operational), "web_read": len(web_sources), "catalog": catalog_count, "repositories": repository_count}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
