#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import global_source_discovery_v4 as planner
import trend_signals

HERE = Path(__file__).resolve().parent


def main() -> int:
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    queries, next_cursor = planner.query_set(config, 0, 40, ["Brazil", "Japan", "Nigeria", "France"])
    assert len(queries) == 40
    assert next_cursor == 40
    prefixes = {query.split("::", 1)[0] for query in queries}
    required = {
        "source", "protocol", "institution", "publication", "regional_source",
        "intelligence_tool", "compute_tool", "incumbent_change", "multilingual",
    }
    assert required.issubset(prefixes), sorted(prefixes)
    assert sum(query.startswith("trend::") for query in queries) <= 4
    assert all(len(query) <= 220 for query in queries)
    github_queries = [planner.github_query(*planner.split_query(query)) for query in queries]
    assert all(1 <= len(query.split()) <= 8 for query in github_queries)
    assert not any('"' in query or "(" in query or ")" in query for query in github_queries)

    assert trend_signals.marker_matches("new ai model release", "ai")
    assert trend_signals.marker_matches("public api update", "api")
    assert not trend_signals.marker_matches("air quality warning", "ai")
    assert not trend_signals.marker_matches("famille royale britannique", "ai")
    assert not trend_signals.marker_matches("daily news", "ai")

    print(json.dumps({
        "queries": len(queries),
        "families": sorted(prefixes),
        "trend_queries": sum(query.startswith("trend::") for query in queries),
        "github_max_tokens": max(len(query.split()) for query in github_queries),
        "trend_marker_boundary_tests": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
