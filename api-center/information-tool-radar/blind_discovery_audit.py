#!/usr/bin/env python3
"""Prove that a sensitive watch candidate was found by a generic query."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

TARGET_ALIASES = ("anna", "annas-archive", "安娜图书馆", "安娜档案")


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, Mapping):
            rows.append(dict(value))
    return rows


def audit(config: Mapping[str, Any], watchlist: Mapping[str, Any], candidates: list[Mapping[str, Any]]) -> dict[str, Any]:
    github_config = config.get("adapters", {}).get("github", {})
    generic_queries = [str(value) for value in github_config.get("best_match_queries") or []]
    generic_folded = {value.casefold() for value in generic_queries}
    errors: list[str] = []
    if not generic_queries:
        errors.append("best_match_queries missing")
    for query in generic_queries:
        folded = query.casefold()
        if any(alias in folded for alias in TARGET_ALIASES):
            errors.append(f"generic query contains target alias: {query}")

    repositories = {
        str(item.get("repository") or "").casefold()
        for item in watchlist.get("repository_candidates") or []
        if isinstance(item, Mapping)
    }
    hits: list[dict[str, Any]] = []
    for candidate in candidates:
        evidence = candidate.get("evidence") if isinstance(candidate.get("evidence"), Mapping) else {}
        query = str(evidence.get("query") or "")
        title = str(candidate.get("title") or "").casefold()
        locator = str(candidate.get("locator") or "").casefold().rstrip("/")
        matched_repository = next(
            (
                repository
                for repository in repositories
                if title == repository or locator.endswith("/" + repository)
            ),
            None,
        )
        if not matched_repository:
            continue
        if str(evidence.get("search_mode") or "") != "best_match":
            continue
        if query.casefold() not in generic_folded:
            continue
        if any(alias in query.casefold() for alias in TARGET_ALIASES):
            continue
        hits.append({
            "repository": matched_repository,
            "query": query,
            "search_mode": evidence.get("search_mode"),
            "locator": candidate.get("locator"),
        })

    status = "pass" if not errors and hits else "fail"
    return {
        "schema_version": "blind-discovery-audit-v1",
        "status": status,
        "metrics": {
            "generic_queries": len(generic_queries),
            "known_watch_repositories": len(repositories),
            "candidates_examined": len(candidates),
            "generic_hits": len(hits),
            "policy_errors": len(errors),
        },
        "generic_queries": generic_queries,
        "hits": hits,
        "errors": errors,
        "claim": "At least one known candidate was rediscovered by a query that contains no target name or alias.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--watchlist", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()

    report = audit(load_json(args.config), load_json(args.watchlist), read_jsonl(args.candidates))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["metrics"]}, ensure_ascii=False))
    if args.enforce and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
