#!/usr/bin/env python3
"""Production hardening wrapper for scheduled PRC justice self-iteration.

Adds two quality gates to the v1 engine:
1. diversify discovery candidates so one blocked official host cannot consume the
   whole bounded primary-fetch budget;
2. automatically absorb only *recent* practice inside the configured freshness
   window. Older official cases remain discoverable as historical references but
   are not written into the latest-practice ledger by automation.
"""
from __future__ import annotations

import argparse
import copy
import json
import urllib.parse
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Mapping

import prc_justice_self_iteration as base

HERE = Path(__file__).resolve().parent
DEFAULT_POLICY = HERE / "prc-justice-self-iteration-policy.json"
DEFAULT_MATRIX = HERE / "investigative-technology-intelligence-matrix.json"
DEFAULT_LEDGER = HERE / "case-derived-investigative-capability-ledger.json"
DEFAULT_HOST_CANDIDATE_CAP = 3


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value or "").strip())
    except ValueError:
        return None


def freshness_cutoff(policy: Mapping[str, Any], today: date | None = None) -> date:
    today = today or base.utc_now().date()
    days = int(policy["cadence"]["maximum_age_days_for_search"])
    return today - timedelta(days=days)


def observation_is_recent(
    observation: Mapping[str, Any],
    policy: Mapping[str, Any],
    today: date | None = None,
) -> bool:
    today = today or base.utc_now().date()
    published = parse_iso_date(str(observation.get("publication_date") or ""))
    if published is None:
        return False
    if published > today + timedelta(days=1):
        return False
    return published >= freshness_cutoff(policy, today)


class CandidateHostCap:
    """Bound unique discovery URLs per official host before primary fetching."""

    def __init__(self, allowed_hosts: set[str], per_host_cap: int = DEFAULT_HOST_CANDIDATE_CAP) -> None:
        self.allowed_hosts = {host.casefold() for host in allowed_hosts}
        self.per_host_cap = max(1, int(per_host_cap))
        self.seen: dict[str, set[str]] = {}

    def filter(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in rows:
            url = str(row.get("url") or "")
            host = str(urllib.parse.urlsplit(url).hostname or "").casefold().rstrip(".")
            if not host or not base.host_allowed(host, self.allowed_hosts):
                out.append(row)
                continue
            bucket = self.seen.setdefault(host, set())
            if url in bucket:
                out.append(row)
                continue
            if len(bucket) >= self.per_host_cap:
                continue
            bucket.add(url)
            out.append(row)
        return out


def wrap_search_function(
    function: Callable[..., list[dict[str, Any]]],
    limiter: CandidateHostCap,
) -> Callable[..., list[dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return limiter.filter(function(*args, **kwargs))

    return wrapped


def rewrite_candidate_records_for_history(
    output_dir: Path,
    stale_observation_ids: set[str],
) -> None:
    path = output_dir / "candidate-observations.jsonl"
    if not path.exists() or not stale_observation_ids:
        return
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if str(row.get("observation_id") or "") in stale_observation_ids:
            row["status"] = "HISTORICAL_REFERENCE_ONLY"
            row["reason"] = "outside_latest_practice_window"
        rows.append(row)
    base.save_jsonl(path, rows)


def apply_recent_observations(
    *,
    policy: dict[str, Any],
    ledger: dict[str, Any],
    output_dir: Path,
    ledger_path: Path,
    write_ledger: bool,
) -> dict[str, Any]:
    report_path = output_dir / "self-iteration-report.json"
    observations_path = output_dir / "new-observations.json"
    report = base.load_json(report_path)
    generated = base.load_json(observations_path)
    proposed = [dict(row) for row in generated.get("observations") or [] if isinstance(row, Mapping)]

    recent = [row for row in proposed if observation_is_recent(row, policy)]
    stale = [row for row in proposed if not observation_is_recent(row, policy)]
    stale_ids = {str(row.get("observation_id") or "") for row in stale if row.get("observation_id")}
    rewrite_candidate_records_for_history(output_dir, stale_ids)

    existing_rows = [dict(row) for row in ledger.get("observations") or [] if isinstance(row, Mapping)]
    existing_ids = {str(row.get("observation_id") or "") for row in existing_rows}
    existing_urls = {str(row.get("primary_source_url") or "") for row in existing_rows}
    existing_fingerprints = {str(row.get("source_fingerprint") or "") for row in existing_rows}
    accepted: list[dict[str, Any]] = []
    for row in recent:
        oid = str(row.get("observation_id") or "")
        url = str(row.get("primary_source_url") or "")
        fingerprint = str(row.get("source_fingerprint") or "")
        if not oid or not url or not fingerprint:
            continue
        if oid in existing_ids or url in existing_urls or fingerprint in existing_fingerprints:
            continue
        accepted.append(row)
        existing_ids.add(oid)
        existing_urls.add(url)
        existing_fingerprints.add(fingerprint)

    if accepted:
        original = copy.deepcopy(existing_rows)
        ledger["observations"] = existing_rows + accepted
        assert ledger["observations"][: len(original)] == original
        base.recompute_rollup(ledger, policy)
        ledger["reviewed_at"] = base.iso_date()
        if write_ledger:
            base.save_json(ledger_path, ledger)

    cutoff = freshness_cutoff(policy)
    report["quality_hardening_version"] = "v2"
    report["latest_practice_only"] = True
    report["freshness_window_days"] = int(policy["cadence"]["maximum_age_days_for_search"])
    report["freshness_cutoff_date"] = cutoff.isoformat()
    report["generated_observation_count_before_freshness"] = len(proposed)
    report["historical_reference_count"] = len(stale)
    report["historical_reference_ids"] = sorted(stale_ids)
    report["new_observation_count"] = len(accepted)
    report["new_observation_ids"] = [str(row["observation_id"]) for row in accepted]
    report["ledger_changed"] = bool(accepted)
    report["auto_merge_eligible"] = bool(
        accepted
        and not report.get("safety_boundary_triggered")
        and all(row.get("verification_status") == "PRIMARY_OBSERVED" for row in accepted)
    )
    report["candidate_host_cap"] = DEFAULT_HOST_CANDIDATE_CAP
    base.save_json(report_path, report)
    base.save_json(observations_path, {"observations": accepted, "historical_references": stale})
    return report


def validate_v2_contract(policy: Mapping[str, Any]) -> dict[str, Any]:
    days = int(policy["cadence"]["maximum_age_days_for_search"])
    assert 1 <= days <= 90
    assert int(policy["limits"]["minimum_seconds_between_prc_primary_fetches"]) >= 10
    assert policy["limits"]["automatic_retry"] is False

    today = date(2026, 8, 7)
    fresh = {"publication_date": "2026-08-01"}
    stale = {"publication_date": "2022-08-30"}
    future = {"publication_date": "2027-01-01"}
    assert observation_is_recent(fresh, policy, today=today) is True
    assert observation_is_recent(stale, policy, today=today) is False
    assert observation_is_recent(future, policy, today=today) is False

    allowed = {str(x) for x in policy["primary_outcome_hosts"]}
    limiter = CandidateHostCap(allowed, per_host_cap=2)
    rows = [
        {"url": f"https://www.spp.gov.cn/example/{n}.shtml"}
        for n in range(4)
    ] + [{"url": "https://www.court.gov.cn/example/1.html"}]
    filtered = limiter.filter(rows)
    assert sum("spp.gov.cn" in row["url"] for row in filtered) == 2
    assert sum("court.gov.cn" in row["url"] for row in filtered) == 1

    return {
        "status": "PASS",
        "quality_hardening_version": "v2",
        "latest_practice_only": True,
        "freshness_window_days": days,
        "candidate_host_cap": DEFAULT_HOST_CANDIDATE_CAP,
        "dependency_validation_required": True,
        "reviewable": True,
        "verifiable": True,
        "absorbable": True,
        "iterable": True,
        "secret_operational_details": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("validate", "live"), default="validate")
    parser.add_argument("--profile", choices=("auto", "daily", "weekly"), default="auto")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output-dir", default="prc-justice-self-iteration-artifact")
    parser.add_argument("--write-ledger", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    policy = base.load_json(args.policy)
    matrix = base.load_json(args.matrix)
    ledger = base.load_json(args.ledger)

    base_receipt = base.validate_contract(policy, matrix, ledger)
    v2_receipt = validate_v2_contract(policy)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base.save_json(
        output_dir / "contract-validation.json",
        {"base": base_receipt, "production_hardening": v2_receipt},
    )
    if args.mode == "validate":
        print(json.dumps(v2_receipt, ensure_ascii=False))
        return 0

    allowed_hosts = {
        str(x).casefold()
        for x in list(policy["primary_outcome_hosts"]) + list(policy["source_view_hosts"])
    }
    limiter = CandidateHostCap(allowed_hosts, per_host_cap=DEFAULT_HOST_CANDIDATE_CAP)
    original_tavily = base.search_tavily
    original_exa = base.search_exa
    base.search_tavily = wrap_search_function(original_tavily, limiter)  # type: ignore[assignment]
    base.search_exa = wrap_search_function(original_exa, limiter)  # type: ignore[assignment]

    run_args = argparse.Namespace(
        profile=args.profile,
        output_dir=str(output_dir),
        ledger=str(args.ledger),
        write_ledger=False,
    )
    working_ledger = copy.deepcopy(ledger)
    result = base.run_live(run_args, policy, matrix, working_ledger)
    if result != 0:
        return result

    report = apply_recent_observations(
        policy=policy,
        ledger=ledger,
        output_dir=output_dir,
        ledger_path=args.ledger,
        write_ledger=args.write_ledger,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
