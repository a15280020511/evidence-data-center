#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import sensitive_watch

HERE = Path(__file__).resolve().parent
TARGET_ALIASES = ("anna", "annas-archive", "安娜图书馆", "安娜档案")


def main() -> int:
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    watchlist = json.loads(
        (HERE / "watchlists" / "annas-archive-metadata.json").read_text(encoding="utf-8")
    )

    queries = [str(value) for value in config["adapters"]["github"]["queries"]]
    folded_queries = [value.casefold() for value in queries]
    assert "unofficial archive api python" in folded_queries
    assert "bibliographic metadata sdk" in folded_queries
    assert "digital library catalog api" in folded_queries
    assert all(
        not any(alias in query for alias in TARGET_ALIASES)
        for query in folded_queries
    )

    assert sensitive_watch.validate_watchlist(watchlist) == []
    assert watchlist["integration_mode"] == "monitoring-only"
    assert watchlist["production_connector"] is False
    assert watchlist["discovery_policy"]["target_name_required"] is False
    assert watchlist["discovery_policy"]["second_stage_alias_expansion"] is True

    forbidden = "\n".join(watchlist["forbidden_operations"]).casefold()
    for phrase in (
        "download books or documents",
        "resolve direct download links",
        "bypass captcha",
        "install or execute third-party code",
        "retrieve copyrighted content",
    ):
        assert phrase in forbidden

    print(json.dumps({
        "generic_query_without_target_name": "passed",
        "metadata_only_policy": "passed",
        "production_connector_disabled": "passed",
        "download_and_bypass_prohibited": "passed",
        "second_stage_alias_expansion": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
