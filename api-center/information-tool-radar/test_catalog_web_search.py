#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import catalog_web_search as target

HERE = Path(__file__).resolve().parent


def main() -> int:
    production_registry = json.loads(
        (HERE / "catalog-domains.json").read_text(encoding="utf-8")
    )
    assert production_registry.get("domains") == []
    assert production_registry["policy"]["no_persisted_domains"] is True
    assert production_registry["policy"]["resolve_from_wikimedia_each_run"] is True

    parser = target.SearchResultParser()
    parser.feed(
        '<a href="/md5/abc"><span>孙子兵法</span></a>'
        '<a href="/download/secret">must not capture</a>'
    )
    assert parser.titles == ["孙子兵法"]

    candidate = target.redirect_candidate(
        "https://current.example",
        "https://new-domain.example/search?q=x",
    )
    assert candidate == {
        "source_domain": "https://current.example",
        "candidate_domain": "https://new-domain.example",
        "status": "unapproved-not-followed",
    }
    assert target.normalize_domain("https://Example.org/") == "https://example.org"

    print(json.dumps({
        "no_domain_registry": "passed",
        "metadata_only_parser": "passed",
        "redirect_not_followed": "passed",
        "low_level_probe_library": "passed",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
