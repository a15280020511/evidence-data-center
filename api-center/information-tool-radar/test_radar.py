#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import radar
import radar_v2
import radar_v4


def main() -> int:
    first = radar.make_candidate(
        "github", "code_tools", "Example Tool", "https://github.com/example/tool", {"query": "example"}
    )
    second = radar.make_candidate(
        "github", "code_tools", "Example Tool", "https://github.com/example/tool", {"query": "different"}
    )
    assert first["candidate_id"] == second["candidate_id"]
    assert len(radar.deduplicate([first, second])) == 1

    manifest_result = radar.AdapterResult("gdelt", "global_events")
    added = radar_v2._manifest_candidates(
        manifest_result,
        "20260805 https://data.gdeltproject.org/example.csv.gz\n",
        "https://data.gdeltproject.org/gdeltv3/web/ngrams/LASTUPDATE.TXT",
        10,
    )
    assert added == 1

    jsonl = (
        '{"timestamp":"20200101000000","original":"https://example.org/a"}\n'
        '{"timestamp":"20210101000000","original":"https://example.org/b"}\n'
    ).encode("utf-8")
    archive_rows = radar_v4.parse_cdx_payload(jsonl)
    assert len(archive_rows) == 2
    assert archive_rows[1]["original"].endswith("/b")

    results = [
        radar.AdapterResult(
            name="common_crawl",
            category="present_web",
            success=True,
            candidates=[radar.make_candidate(
                "common_crawl", "present_web", "Index", "https://index.commoncrawl.org", {}, status="reference"
            )],
            probes=1,
            successful_probes=1,
        ),
        radar.AdapterResult(
            name="crossref",
            category="research_data",
            success=True,
            candidates=[radar.make_candidate(
                "crossref", "research_data", "Paper", "https://doi.org/10.1/example", {}, status="reference"
            )],
            probes=1,
            successful_probes=1,
        ),
        radar.AdapterResult(
            name="datacite",
            category="research_data",
            success=False,
            candidates=[],
            probes=1,
            successful_probes=0,
            errors=["optional outage"],
        ),
    ]
    config = {
        "minimum_required_adapter_success_rate": 1.0,
        "minimum_category_coverage": 1.0,
        "adapters": {
            "common_crawl": {"enabled": True, "required_for_gate": True, "category": "present_web"},
            "crossref": {"enabled": True, "required_for_gate": True, "category": "research_data"},
            "datacite": {"enabled": True, "required_for_gate": False, "category": "research_data"},
        },
    }
    report, candidates = radar_v4.build_report(config, results)
    assert report["status"] == "pass"
    assert report["metrics"]["required_adapter_success_rate"] == 1.0
    assert report["metrics"]["all_adapter_success_rate"] == 0.6667
    assert report["degraded_optional_adapters"] == ["datacite"]
    assert not report["required_adapter_failures"]
    assert len(candidates) == 2
    assert report["safety"]["installs_or_executes_discovered_code"] is False

    markdown = radar.markdown_report(report)
    assert "信息工具雷达覆盖测试" in markdown

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "report.json"
        radar.save_json(path, report)
        assert json.loads(path.read_text(encoding="utf-8"))["status"] == "pass"

    print(json.dumps({
        "candidate_identity": "passed",
        "deduplication": "passed",
        "fallback_manifest": "passed",
        "archive_jsonl": "passed",
        "required_gate": "passed",
        "optional_failure_visibility": "passed",
        "safety_invariants": "passed"
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
