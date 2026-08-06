#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

import radar_v5
import sensitive_watch

HERE = Path(__file__).resolve().parent
TARGET_ALIASES = ("anna", "annas-archive", "安娜图书馆", "安娜档案")


def main() -> int:
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    watchlist = json.loads(
        (HERE / "watchlists" / "annas-archive-metadata.json").read_text(encoding="utf-8")
    )

    github_config = config["adapters"]["github"]
    recent_queries = [str(value) for value in github_config["queries"]]
    best_match_queries = [str(value) for value in github_config["best_match_queries"]]
    all_queries = recent_queries + best_match_queries
    folded_queries = [value.casefold() for value in all_queries]
    assert "unofficial archive api python" in [value.casefold() for value in best_match_queries]
    assert "bibliographic metadata sdk" in [value.casefold() for value in best_match_queries]
    assert "digital library catalog api" in [value.casefold() for value in best_match_queries]
    assert all(
        not any(alias in query for alias in TARGET_ALIASES)
        for query in folded_queries
    )

    captured_urls: list[str] = []
    original_request_json = radar_v5.base.request_json

    def fake_request_json(url: str, **_: object) -> dict[str, list[object]]:
        captured_urls.append(url)
        return {"items": []}

    radar_v5.base.request_json = fake_request_json
    try:
        result = radar_v5.github(
            {
                "category": "code_tools",
                "endpoint": "https://api.github.com/search/repositories",
                "queries": ["recent tool release"],
                "best_match_queries": ["unofficial archive API Python"],
            },
            {"timeout": 1, "max_bytes": 1000, "max_records": 10},
        )
    finally:
        radar_v5.base.request_json = original_request_json

    assert result.success is True
    assert result.details["query_modes"] == {"recent": 1, "best_match": 1}
    assert len(captured_urls) == 2
    recent_params = urllib.parse.parse_qs(urllib.parse.urlparse(captured_urls[0]).query)
    best_params = urllib.parse.parse_qs(urllib.parse.urlparse(captured_urls[1]).query)
    assert recent_params["sort"] == ["updated"]
    assert recent_params["order"] == ["desc"]
    assert "sort" not in best_params
    assert "order" not in best_params

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
        "best_match_discovery_mode": "passed",
        "recent_change_mode_preserved": "passed",
        "metadata_only_policy": "passed",
        "production_connector_disabled": "passed",
        "download_and_bypass_prohibited": "passed",
        "second_stage_alias_expansion": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
