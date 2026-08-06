#!/usr/bin/env python3
"""Bounded metadata-only monitor for sensitive third-party source wrappers."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

USER_AGENT = (
    "evidence-data-center-sensitive-source-watch/1 "
    "(+https://github.com/a15280020511/evidence-data-center)"
)
REQUIRED_FORBIDDEN_PHRASES = (
    "download books or documents",
    "resolve direct download links",
    "bypass captcha",
    "install or execute third-party code",
    "retrieve copyrighted content",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def validate_watchlist(watchlist: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if watchlist.get("integration_mode") != "monitoring-only":
        errors.append("integration_mode must be monitoring-only")
    if watchlist.get("production_connector") is not False:
        errors.append("production_connector must be false")
    if watchlist.get("current_status") != "watchlist-not-production":
        errors.append("current_status must be watchlist-not-production")

    forbidden = "\n".join(str(value).casefold() for value in watchlist.get("forbidden_operations") or [])
    for phrase in REQUIRED_FORBIDDEN_PHRASES:
        if phrase.casefold() not in forbidden:
            errors.append(f"missing forbidden policy: {phrase}")

    discovery = watchlist.get("discovery_policy")
    if not isinstance(discovery, Mapping):
        errors.append("discovery_policy missing")
    else:
        queries = [str(value).strip() for value in discovery.get("generic_queries") or []]
        if not queries:
            errors.append("generic_queries missing")
        target_aliases = ("anna", "annas-archive", "安娜图书馆", "安娜档案")
        for query in queries:
            folded = query.casefold()
            if any(alias in folded for alias in target_aliases):
                errors.append(f"generic query contains target alias: {query}")
        if discovery.get("target_name_required") is not False:
            errors.append("target_name_required must be false")

    repositories = watchlist.get("repository_candidates")
    if not isinstance(repositories, list) or not repositories:
        errors.append("repository_candidates missing")
    else:
        for item in repositories:
            if not isinstance(item, Mapping) or "/" not in str(item.get("repository") or ""):
                errors.append("invalid repository candidate")
    return errors


def fetch_repository(repository: str, timeout: int, max_bytes: int) -> Mapping[str, Any]:
    url = f"https://api.github.com/repos/{repository}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise RuntimeError(f"response exceeded {max_bytes} bytes")
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError("GitHub repository response was not an object")
    return value


def monitor(watchlist: Mapping[str, Any], timeout: int = 12, max_bytes: int = 500_000) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy_errors = validate_watchlist(watchlist)
    rows: list[dict[str, Any]] = []
    live_success = 0
    for candidate in watchlist.get("repository_candidates") or []:
        if not isinstance(candidate, Mapping):
            continue
        repository = str(candidate.get("repository") or "")
        row: dict[str, Any] = {
            "repository": repository,
            "role": candidate.get("role"),
            "review_status": candidate.get("review_status"),
            "observed_at": utc_now(),
            "metadata_only": True,
            "live_success": False,
        }
        try:
            data = fetch_repository(repository, timeout=timeout, max_bytes=max_bytes)
            license_data = data.get("license") if isinstance(data.get("license"), Mapping) else {}
            row.update({
                "live_success": True,
                "archived": bool(data.get("archived", False)),
                "disabled": bool(data.get("disabled", False)),
                "fork": bool(data.get("fork", False)),
                "language": data.get("language"),
                "license_spdx": license_data.get("spdx_id"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "pushed_at": data.get("pushed_at"),
                "default_branch": data.get("default_branch"),
                "html_url": data.get("html_url"),
            })
            live_success += 1
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, RuntimeError) as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"[:300]
        rows.append(row)

    report = {
        "schema_version": "sensitive-source-watch-report-v1",
        "watch_id": watchlist.get("watch_id"),
        "generated_at": utc_now(),
        "status": "pass" if not policy_errors else "fail",
        "live_status": "ok" if live_success == len(rows) and rows else "degraded",
        "metrics": {
            "repository_candidates": len(rows),
            "live_metadata_successes": live_success,
            "policy_errors": len(policy_errors),
        },
        "policy_errors": policy_errors,
        "policy": {
            "metadata_only": True,
            "production_connector": False,
            "package_installation": False,
            "code_execution": False,
            "content_download": False,
            "direct_link_resolution": False,
            "access_control_bypass": False,
        },
        "repositories": rows,
    }
    return report, rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watchlist", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce-policy", action="store_true")
    args = parser.parse_args()

    report, rows = monitor(load_json(args.watchlist))
    save_json(args.output_dir / "sensitive-source-watch-report.json", report)
    write_jsonl(args.output_dir / "sensitive-source-watch-candidates.jsonl", rows)
    print(json.dumps({"status": report["status"], "live_status": report["live_status"], **report["metrics"]}, ensure_ascii=False))
    if args.enforce_policy and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
