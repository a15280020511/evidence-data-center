#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import global_source_discovery_v4 as planner
import trend_signals

HERE = Path(__file__).resolve().parent


def main() -> int:
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temporary_directory:
        trend_path = Path(temporary_directory) / "trend-signals.json"
        trend_path.write_text(
            json.dumps({"terms": [{"term": "open source robotics"}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        old_value = os.environ.get("TREND_SIGNALS_PATH")
        os.environ["TREND_SIGNALS_PATH"] = str(trend_path)
        try:
            queries, next_cursor = planner.query_set(
                config, 0, 40, ["Brazil", "Japan", "Nigeria", "France"]
            )
        finally:
            if old_value is None:
                os.environ.pop("TREND_SIGNALS_PATH", None)
            else:
                os.environ["TREND_SIGNALS_PATH"] = old_value

    assert len(queries) == 40
    assert next_cursor == 40
    prefixes = {query.split("::", 1)[0] for query in queries}
    required = {
        "source", "protocol", "institution", "publication", "regional_source",
        "intelligence_tool", "compute_tool", "incumbent_change", "multilingual", "trend",
    }
    assert required.issubset(prefixes), sorted(prefixes)
    trend_query_count = sum(query.startswith("trend::") for query in queries)
    assert trend_query_count == 4
    assert all(len(query) <= 220 for query in queries)
    github_queries = [planner.github_query(*planner.split_query(query)) for query in queries]
    assert all(1 <= len(query.split()) <= 8 for query in github_queries)
    assert not any('"' in query or "(" in query or ")" in query for query in github_queries)

    assert trend_signals.marker_matches("new ai model release", "ai")
    assert trend_signals.marker_matches("public api update", "api")
    assert not trend_signals.marker_matches("air quality warning", "ai")
    assert not trend_signals.marker_matches("famille royale britannique", "ai")
    assert not trend_signals.marker_matches("daily news", "ai")
    assert not trend_signals.usable_title("an")
    assert trend_signals.usable_title("AI")
    assert trend_signals.usable_title("芯片")
    assert trend_signals.usable_title("테슬라")

    print(json.dumps({
        "queries": len(queries),
        "families": sorted(prefixes),
        "trend_queries": trend_query_count,
        "github_max_tokens": max(len(query.split()) for query in github_queries),
        "trend_marker_boundary_tests": "passed",
        "trend_title_quality_tests": "passed",
        "trend_query_share_test": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
