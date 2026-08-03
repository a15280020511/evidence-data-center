#!/usr/bin/env python3
"""Execute one deterministic zero-network fixture for every governed operation."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from global_research_intelligence_task import CATALOG_PATH, execute

SAMPLES: dict[str, dict[str, Any]] = {
    "catalog-capabilities": {},
    "source-inventory": {},
    "think-tank-source-catalog": {"region": "china", "topic": "macro"},
    "search-arxiv": {
        "query": "all:China AND cat:econ.GN",
        "start": 0,
        "max_results": 5,
        "sort_by": "submittedDate",
        "sort_order": "descending"
    },
    "get-arxiv-entry": {"ids": ["2608.00001"]},
    "identify-un-digital-library": {},
    "list-un-digital-library-records": {
        "metadata_prefix": "oai_dc",
        "from": "2026-01-01",
        "until": "2026-08-03"
    },
    "get-un-digital-library-record": {
        "identifier": "oai:digitallibrary.un.org:12345",
        "metadata_prefix": "oai_dc"
    },
    "get-sec-submissions": {"cik": "320193"},
    "get-sec-company-facts": {"cik": "320193"},
    "get-sec-xbrl-frame": {
        "taxonomy": "us-gaap",
        "tag": "Assets",
        "unit": "USD",
        "period": "CY2025Q4I"
    },
    "list-congress-bills": {
        "congress": 119,
        "bill_type": "hr",
        "limit": 5,
        "offset": 0
    },
    "list-congress-hearings": {
        "congress": 119,
        "chamber": "house",
        "limit": 5,
        "offset": 0
    },
    "get-congress-crs-report": {"report_number": "R48200"},
    "search-courtlistener": {
        "query": "antitrust China",
        "type": "o",
        "order_by": "dateFiled desc",
        "page": 1
    },
    "get-courtlistener-opinion": {"opinion_id": 1},
    "search-nasdaq-data-link": {"query": "China commodity", "page": 1, "per_page": 5},
    "get-nasdaq-dataset": {
        "database_code": "FRED",
        "dataset_code": "GDP",
        "start_date": "2025-01-01",
        "end_date": "2026-01-01",
        "rows": 10,
        "order": "desc",
        "collapse": "monthly",
        "transform": "none"
    },
    "finnhub-company-news": {
        "symbol": "BABA",
        "from": "2026-07-01",
        "to": "2026-08-03"
    },
    "finnhub-transcripts-list": {"symbol": "BABA"},
    "finnhub-transcript": {"transcript_id": "fixture-transcript-1"},
    "scopus-search": {
        "query": "TITLE-ABS-KEY(China AND industrial policy)",
        "start": 0,
        "count": 5,
        "sort": "-coverDate",
        "view": "STANDARD"
    },
    "scopus-abstract": {"eid": "2-s2.0-123456789", "view": "META_ABS"}
}


def configure_fixture_environment() -> None:
    os.environ["GLOBAL_RESEARCH_FIXTURE_MODE"] = "1"
    os.environ["SEC_USER_AGENT"] = "Evidence Data Center test@example.com"
    os.environ["CONGRESS_API_KEY"] = "fixture-congress-key"
    os.environ["COURTLISTENER_API_TOKEN"] = "fixture-courtlistener-token"
    os.environ["NASDAQ_DATA_LINK_API_KEY"] = "fixture-nasdaq-key"
    os.environ["FINNHUB_API_KEY"] = "fixture-finnhub-key"
    os.environ["SCOPUS_API_KEY"] = "fixture-scopus-key"
    os.environ["SCOPUS_INST_TOKEN"] = "fixture-scopus-insttoken"


def validate(operation: str) -> dict[str, Any]:
    if operation not in SAMPLES:
        raise ValueError(f"unsupported validation operation: {operation}")
    configure_fixture_environment()
    ticket = {
        "task_id": f"global-research-{operation}",
        "provider": "global-research-intelligence",
        "operation": operation,
        "parameters": SAMPLES[operation],
        "data_policy": {
            "classification": "public",
            "contains_personal_data": False
        },
        "acceptance": {
            "timeout_seconds": 30,
            "max_response_bytes": 10000000
        }
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        ticket_path = root / "ticket.json"
        output_dir = root / "output"
        ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
        result = execute(ticket_path, output_dir)
        diagnostics = json.loads((output_dir / "diagnostics.json").read_text(encoding="utf-8"))
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        if result != 0:
            raise AssertionError(diagnostics)
        if diagnostics["status"] != "INTEL_GLOBAL_RESEARCH_COMPLETED":
            raise AssertionError(diagnostics)
        metadata = diagnostics["metadata"]
        if metadata["network_used"] is not False:
            raise AssertionError("fixture unexpectedly used network")
        if diagnostics["secret_values_exposed"] is not False:
            raise AssertionError("diagnostics exposed secret values")
        if diagnostics["model_calls"] != 0:
            raise AssertionError("model call count is not zero")
        if manifest["secret_values_exposed"] is not False:
            raise AssertionError("manifest exposed secret values")
        if not (output_dir / "snapshot.json").is_file():
            raise AssertionError("snapshot.json was not produced")
        return {
            "status": "PASS",
            "operation": operation,
            "network_used": False,
            "fixture_mode": True,
            "credential_used_backend_only": bool(metadata.get("secret_used")),
            "secret_values_exposed": False,
            "model_calls": 0,
            "artifact_file_count": len(manifest["files"]),
            "provider_catalog": str(CATALOG_PATH.name)
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=True, choices=sorted(SAMPLES))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = validate(args.operation)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
