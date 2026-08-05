#!/usr/bin/env python3
"""Create the incumbent-tool monitoring lane for the Information & Tool Radar.

Known tools are seeds, not rediscovery accidents. This lane guarantees that every
formal incumbent is represented, fingerprinted and assigned bounded update queries.
It also compares current fingerprints with a reviewed repository baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from incumbent_inventory import build_inventory


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, Mapping) else {}


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def candidate_id(tool_id: str) -> str:
    return hashlib.sha256(f"incumbent\0{tool_id}".encode("utf-8")).hexdigest()


def rotation_bucket(tool_id: str, buckets: int = 7) -> int:
    return int(hashlib.sha256(tool_id.encode("utf-8")).hexdigest()[:8], 16) % buckets


def queries(tool_id: str) -> list[str]:
    name = tool_id.replace("-", " ")
    return [
        f"{name} official API documentation",
        f"{name} SDK repository release",
        f"{name} changelog deprecation pricing license vulnerability",
    ]


def inventory_state(inventory: Mapping[str, Any]) -> dict[str, Any]:
    tools = inventory.get("tools") if isinstance(inventory.get("tools"), list) else []
    return {
        "schema_version": "incumbent-fingerprint-state-v1",
        "tools": {
            str(tool.get("tool_id")): {
                "fingerprint_sha256": tool.get("fingerprint_sha256"),
                "fingerprint_paths": tool.get("fingerprint_paths") or [],
                "source_kinds": tool.get("source_kinds") or [],
            }
            for tool in tools
            if isinstance(tool, Mapping) and tool.get("tool_id")
        },
    }


def compare_state(current: Mapping[str, Any], baseline: Mapping[str, Any]) -> dict[str, Any]:
    current_tools = current.get("tools") if isinstance(current.get("tools"), Mapping) else {}
    baseline_tools = baseline.get("tools") if isinstance(baseline.get("tools"), Mapping) else {}
    current_ids = set(current_tools)
    baseline_ids = set(baseline_tools)
    changed = sorted(
        identifier for identifier in current_ids & baseline_ids
        if current_tools[identifier].get("fingerprint_sha256")
        != baseline_tools[identifier].get("fingerprint_sha256")
    )
    return {
        "baseline_present": bool(baseline_tools),
        "new_tools": sorted(current_ids - baseline_ids),
        "removed_tools": sorted(baseline_ids - current_ids),
        "changed_tools": changed,
        "unchanged_tools": sorted((current_ids & baseline_ids) - set(changed)),
    }


def build(repo_root: Path, global_candidates: Path, baseline_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    inventory = build_inventory(repo_root)
    tools = list(inventory["tools"])
    generated_at = utc_now()
    incumbent_rows: list[dict[str, Any]] = []
    plan_rows: list[dict[str, Any]] = []

    for tool in tools:
        tool_id = str(tool["tool_id"])
        locators = list(tool.get("locators") or [])
        repository_path = f"https://github.com/a15280020511/evidence-data-center/tree/main/api-center/{tool_id}"
        monitoring_mode = "external-provider-and-local-fingerprint" if locators else "internal-module-local-fingerprint"
        incumbent_rows.append({
            "candidate_id": candidate_id(tool_id),
            "adapter": "incumbent_inventory",
            "category": "incumbent_tool",
            "title": tool_id,
            "locator": locators[0] if locators else repository_path,
            "language": None,
            "country": None,
            "discovered_at": generated_at,
            "evidence": {
                "monitoring_mode": monitoring_mode,
                "aliases": tool.get("aliases") or [],
                "official_locators": locators,
                "fingerprint_sha256": tool.get("fingerprint_sha256"),
                "fingerprint_paths": tool.get("fingerprint_paths") or [],
                "source_kinds": tool.get("source_kinds") or [],
                "operation_ids": tool.get("operation_ids") or [],
            },
            "status": "incumbent_seed",
        })
        plan_rows.append({
            "tool_id": tool_id,
            "monitoring_mode": monitoring_mode,
            "rotation_bucket": rotation_bucket(tool_id),
            "queries": queries(tool_id),
            "official_locators": locators,
            "fingerprint_sha256": tool.get("fingerprint_sha256"),
            "signals": [
                "local_contract_fingerprint",
                "official_documentation_or_endpoint" if locators else "repository_contract_only",
                "release_and_changelog_search",
                "pricing_quota_license_search",
                "security_and_deprecation_search",
            ],
        })

    current_state = inventory_state(inventory)
    baseline = load_json(baseline_path)
    delta = compare_state(current_state, baseline)
    global_rows = read_jsonl(global_candidates)
    combined = global_rows + incumbent_rows

    tool_count = len(tools)
    fingerprinted = sum(bool(tool.get("fingerprint_sha256")) for tool in tools)
    seeded_ids = {row["title"] for row in incumbent_rows}
    inventory_ids = {str(tool["tool_id"]) for tool in tools}
    seeded = len(seeded_ids & inventory_ids)
    externally_locatable = sum(bool(tool.get("locators")) for tool in tools)
    status = "pass" if tool_count > 0 and seeded == tool_count and fingerprinted == tool_count else "fail"

    report = {
        "schema_version": "incumbent-watch-report-v1",
        "generated_at": generated_at,
        "status": status,
        "metrics": {
            "tool_count": tool_count,
            "seeded_tools": seeded,
            "seeded_coverage": seeded / tool_count if tool_count else 0.0,
            "fingerprinted_tools": fingerprinted,
            "fingerprint_coverage": fingerprinted / tool_count if tool_count else 0.0,
            "externally_locatable_tools": externally_locatable,
            "externally_locatable_rate": externally_locatable / tool_count if tool_count else 0.0,
            "internal_only_tools": tool_count - externally_locatable,
            "global_candidates": len(global_rows),
            "combined_candidates": len(combined),
            "rotation_buckets": 7,
        },
        "delta": delta,
        "policy": {
            "known_tools_are_seeded": True,
            "generic_search_is_not_required_to_rediscover_every_known_tool_each_run": True,
            "production_dependency_auto_upgrade": False,
            "changes_require_reviewed_baseline_update": True,
        },
    }
    plan = {
        "schema_version": "incumbent-watch-plan-v1",
        "generated_at": generated_at,
        "tool_count": tool_count,
        "daily_rotation_buckets": 7,
        "tools": plan_rows,
    }
    return report, incumbent_rows, combined, {"plan": plan, "state": current_state}


def markdown(report: Mapping[str, Any]) -> str:
    metrics = report["metrics"]
    delta = report["delta"]
    return "\n".join([
        "# 现有工具种子监测验收",
        "",
        f"- 状态：**{str(report['status']).upper()}**",
        f"- 现有工具：{metrics['tool_count']}",
        f"- 种子覆盖：{metrics['seeded_tools']}/{metrics['tool_count']} ({metrics['seeded_coverage']:.1%})",
        f"- 指纹覆盖：{metrics['fingerprinted_tools']}/{metrics['tool_count']} ({metrics['fingerprint_coverage']:.1%})",
        f"- 有外部定位信息：{metrics['externally_locatable_tools']}/{metrics['tool_count']} ({metrics['externally_locatable_rate']:.1%})",
        f"- 内部模块：{metrics['internal_only_tools']}",
        f"- 合并候选：{metrics['combined_candidates']}",
        "",
        "## 指纹差异",
        "",
        f"- 基线存在：{delta['baseline_present']}",
        f"- 新增：{len(delta['new_tools'])}",
        f"- 删除：{len(delta['removed_tools'])}",
        f"- 变化：{len(delta['changed_tools'])}",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--global-candidates", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    report, incumbent_rows, combined, extra = build(
        args.repo_root.resolve(), args.global_candidates, args.baseline
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "incumbent-candidates.jsonl", incumbent_rows)
    write_jsonl(args.output_dir / "combined-candidates.jsonl", combined)
    save_json(args.output_dir / "incumbent-watch-plan.json", extra["plan"])
    save_json(args.output_dir / "incumbent-fingerprint-state.json", extra["state"])
    save_json(args.output_dir / "incumbent-watch-report.json", report)
    (args.output_dir / "incumbent-watch-report.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["metrics"], "delta": report["delta"]}, ensure_ascii=False))
    if args.enforce and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
