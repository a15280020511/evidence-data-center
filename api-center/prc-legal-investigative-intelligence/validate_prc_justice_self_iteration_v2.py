#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import prc_justice_self_iteration as base
from prc_justice_self_iteration_v2 import (
    CandidateHostCap,
    observation_is_recent,
    validate_v2_contract,
)

HERE = Path(__file__).resolve().parent
POLICY = HERE / "prc-justice-self-iteration-policy.json"
MATRIX = HERE / "investigative-technology-intelligence-matrix.json"
LEDGER = HERE / "case-derived-investigative-capability-ledger.json"


def main() -> int:
    policy = base.load_json(POLICY)
    matrix = base.load_json(MATRIX)
    ledger = base.load_json(LEDGER)
    base_receipt = base.validate_contract(policy, matrix, ledger)
    receipt = validate_v2_contract(policy)

    assert base_receipt["status"] == "PASS"
    assert receipt["status"] == "PASS"
    assert receipt["latest_practice_only"] is True
    assert 1 <= receipt["freshness_window_days"] <= 90
    assert receipt["candidate_host_cap"] == 3
    assert receipt["secret_operational_details"] is False

    allowed = {str(x) for x in policy["primary_outcome_hosts"]}
    limiter = CandidateHostCap(allowed, per_host_cap=3)
    fake_rows = [
        {"url": f"https://www.spp.gov.cn/test/{idx}.shtml"}
        for idx in range(7)
    ] + [
        {"url": f"https://www.court.gov.cn/test/{idx}.html"}
        for idx in range(4)
    ]
    filtered = limiter.filter(fake_rows)
    assert len([r for r in filtered if "spp.gov.cn" in r["url"]]) == 3
    assert len([r for r in filtered if "court.gov.cn" in r["url"]]) == 3

    assert observation_is_recent({"publication_date": base.iso_date()}, policy) is True
    assert observation_is_recent({"publication_date": "2021-05-31"}, policy) is False
    assert observation_is_recent({"publication_date": "2022-08-30"}, policy) is False

    print(json.dumps({
        "status": "PASS",
        "base_contract": True,
        "freshness_gate": True,
        "historical_auto_absorption": False,
        "candidate_host_diversification": True,
        "candidate_host_cap": 3,
        "existing_observations": len(ledger.get("observations") or []),
        "reviewable": True,
        "verifiable": True,
        "absorbable": True,
        "iterable": True,
        "secret_operational_details": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
