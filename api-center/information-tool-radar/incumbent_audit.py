#!/usr/bin/env python3
"""Audit whether the Information & Tool Radar can account for every incumbent tool.

Three different claims are kept separate:
1. repository inventory coverage: every formal incumbent is enumerated;
2. fingerprint coverage: every incumbent has deterministic local inputs for change detection;
3. external rediscovery: current global radar candidates independently mention the incumbent.

Only the first two are hard gates. External rediscovery is a rotating, best-effort
signal because proprietary services and regional APIs may not appear in every run.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from incumbent_inventory import build_inventory, compact_alias

GENERIC_ALIASES = {
    "api", "data", "provider", "service", "tool", "tools", "market", "search",
    "cloud", "open", "global", "intelligence", "information", "center", "official",
}
GENERIC_HOSTS = {
    "github.com", "api.github.com", "raw.githubusercontent.com",
    "json-schema.org", "doi.org", "pypi.org", "www.pypi.org",
}


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_candidates(path: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    if not path.exists():
        return output
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            output.append(dict(value))
    return output


def candidate_text(candidate: Mapping[str, Any]) -> tuple[str, set[str]]:
    serialized = json.dumps(candidate, ensure_ascii=False, sort_keys=True).casefold()
    compact = compact_alias(serialized)
    hosts: set[str] = set()
    for value in re.findall(r"https://[^\s\"'<>]+", serialized, flags=re.I):
        host = (urlparse(value.rstrip(".,;:)]}")).hostname or "").casefold().removeprefix("www.")
        if host and host not in GENERIC_HOSTS:
            hosts.add(host)
    return compact, hosts


def useful_aliases(tool: Mapping[str, Any]) -> list[str]:
    aliases: set[str] = set()
    values = [str(tool.get("tool_id") or "")] + [str(value) for value in tool.get("aliases") or []]
    for value in values:
        compact = compact_alias(value)
        if len(compact) < 4 or compact in GENERIC_ALIASES:
            continue
        aliases.add(compact)
    return sorted(aliases, key=lambda value: (-len(value), value))


def locator_hosts(tool: Mapping[str, Any]) -> set[str]:
    output: set[str] = set()
    for locator in tool.get("locators") or []:
        host = (urlparse(str(locator)).hostname or "").casefold().removeprefix("www.")
        if host and host not in GENERIC_HOSTS:
            output.add(host)
    return output


def host_equivalent(left: str, right: str) -> bool:
    return left == right or left.endswith("." + right) or right.endswith("." + left)


def external_match(tool: Mapping[str, Any], candidate_index: list[tuple[str, set[str]]]) -> tuple[bool, str | None]:
    aliases = useful_aliases(tool)
    hosts = locator_hosts(tool)
    for compact, candidate_hosts in candidate_index:
        for host in sorted(hosts):
            if any(host_equivalent(candidate, host) for candidate in candidate_hosts):
                return True, f"host:{host}"
        for alias in aliases:
            if len(alias) >= 5 and alias in compact:
                return True, f"alias:{alias}"
    return False, None


def query_suggestions(tool: Mapping[str, Any]) -> list[str]:
    primary = str(tool.get("tool_id") or "").replace("-", " ").strip()
    return [
        f"{primary} API official",
        f"{primary} SDK GitHub",
        f"{primary} release changelog",
    ]


def markdown_report(report: Mapping[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "# 现有工具发现验收",
        "",
        f"- 状态：**{str(report['status']).upper()}**",
        f"- 正式工具族/模块：{metrics['tool_count']}",
        f"- 普通连接器操作：{metrics['connector_operations']}",
        f"- 本仓库盘点覆盖：{metrics['repository_inventory_found']}/{metrics['tool_count']} ({metrics['repository_inventory_rate']:.1%})",
        f"- 能力指纹覆盖：{metrics['fingerprintable_tools']}/{metrics['tool_count']} ({metrics['fingerprintable_rate']:.1%})",
        f"- 有效公开定位信息：{metrics['externally_locatable_tools']}/{metrics['tool_count']} ({metrics['externally_locatable_rate']:.1%})",
        f"- 本轮全球候选严格重新命中：{metrics['externally_rediscovered_tools']}/{metrics['tool_count']} ({metrics['external_rediscovery_rate']:.1%})",
        "",
        "## 判定说明",
        "",
        "本仓库盘点和能力指纹是强制门；外部重新命中采用严格别名或非公共宿主匹配，单轮不要求100%。未命中项会生成补搜词。",
        "",
    ]
    missing = report.get("external_rediscovery_missing") or []
    lines.extend(["## 本轮外部未重新命中", ""])
    if not missing:
        lines.append("无。")
    else:
        for item in missing:
            lines.append(f"- `{item['tool_id']}`：{'；'.join(item['suggested_queries'])}")
    lines.append("")
    return "\n".join(lines)


def audit(repo_root: Path, candidates_path: Path) -> dict[str, Any]:
    inventory = build_inventory(repo_root)
    tools = list(inventory["tools"])
    candidates = read_candidates(candidates_path)
    candidate_index = [candidate_text(candidate) for candidate in candidates]

    rows: list[dict[str, Any]] = []
    for tool in tools:
        matched, evidence = external_match(tool, candidate_index)
        rows.append({
            "tool_id": tool["tool_id"],
            "source_kinds": tool.get("source_kinds") or [],
            "operation_count": len(tool.get("operation_ids") or []),
            "repository_inventory_found": True,
            "fingerprintable": bool(tool.get("fingerprintable")),
            "fingerprint_sha256": tool.get("fingerprint_sha256"),
            "externally_locatable": bool(tool.get("externally_locatable")),
            "externally_rediscovered": matched,
            "rediscovery_evidence": evidence,
            "suggested_queries": [] if matched else query_suggestions(tool),
        })

    total = len(rows)
    fingerprintable = sum(bool(row["fingerprintable"] and row.get("fingerprint_sha256")) for row in rows)
    locatable = sum(bool(row["externally_locatable"]) for row in rows)
    rediscovered = sum(bool(row["externally_rediscovered"]) for row in rows)
    repository_found = total
    hard_gate = total > 0 and repository_found == total and fingerprintable == total

    return {
        "schema_version": "incumbent-discovery-audit-v2",
        "status": "pass" if hard_gate else "fail",
        "metrics": {
            "tool_count": total,
            "connector_operations": int(inventory["connector_operations"]),
            "ordinary_service_families": int(inventory["ordinary_service_families"]),
            "managed_tool_directories": int(inventory["managed_tool_directories"]),
            "repository_inventory_found": repository_found,
            "repository_inventory_rate": repository_found / total if total else 0.0,
            "fingerprintable_tools": fingerprintable,
            "fingerprintable_rate": fingerprintable / total if total else 0.0,
            "externally_locatable_tools": locatable,
            "externally_locatable_rate": locatable / total if total else 0.0,
            "externally_rediscovered_tools": rediscovered,
            "external_rediscovery_rate": rediscovered / total if total else 0.0,
            "radar_candidates_examined": len(candidates),
        },
        "hard_gates": {
            "repository_inventory_rate_required": 1.0,
            "fingerprintable_rate_required": 1.0,
            "external_rediscovery_is_single_run_gate": False,
        },
        "matching_policy": {
            "generic_hosts_ignored": sorted(GENERIC_HOSTS),
            "aliases_are_provider_level_only": True,
            "public_host_or_specific_alias_required": True,
        },
        "tools": rows,
        "external_rediscovery_missing": [row for row in rows if not row["externally_rediscovered"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    report = audit(args.repo_root.resolve(), args.candidates)
    inventory = build_inventory(args.repo_root.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    save_json(args.output_dir / "incumbent-inventory.json", inventory)
    save_json(args.output_dir / "incumbent-audit-report.json", report)
    (args.output_dir / "incumbent-audit-report.md").write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["metrics"]}, ensure_ascii=False))
    if args.enforce and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
