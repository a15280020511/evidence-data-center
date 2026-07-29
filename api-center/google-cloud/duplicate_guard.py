#!/usr/bin/env python3
"""Reject duplicate [api-gcp] task IDs or equivalent ticket bodies across Issues."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Mapping


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def ticket_fingerprint(ticket: Mapping[str, Any]) -> str:
    normalized = {str(key): value for key, value in ticket.items() if key != "task_id"}
    return canonical_sha(normalized)


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def _api_json(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "managed-google-cloud-api-center",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def duplicate_reason(
    ticket: Mapping[str, Any],
    *,
    repository: str,
    current_issue: int,
    token: str,
) -> str:
    if not repository or "/" not in repository:
        raise ValueError("GITHUB_REPOSITORY is missing or invalid")
    if current_issue < 1:
        raise ValueError("ISSUE_NUMBER is missing or invalid")
    if not token:
        raise ValueError("GITHUB_TOKEN is missing")
    task_id = str(ticket.get("task_id") or "")
    fingerprint = ticket_fingerprint(ticket)
    for page in range(1, 6):
        rows = _api_json(
            f"https://api.github.com/repos/{repository}/issues"
            f"?state=all&per_page=100&page={page}",
            token,
        )
        if not isinstance(rows, list):
            raise ValueError("GitHub issues API did not return an array")
        for row in rows:
            if not isinstance(row, Mapping) or "pull_request" in row:
                continue
            issue_number = int(row.get("number") or 0)
            if issue_number == current_issue:
                continue
            if not str(row.get("title") or "").startswith("[api-gcp]"):
                continue
            try:
                prior = json.loads(str(row.get("body") or ""))
            except json.JSONDecodeError:
                continue
            if not isinstance(prior, Mapping):
                continue
            if str(prior.get("task_id") or "") == task_id:
                return f"duplicate task_id; previously submitted in Issue #{issue_number}"
            if ticket_fingerprint(prior) == fingerprint:
                return (
                    "duplicate ticket content with a different task_id; "
                    f"previously submitted in Issue #{issue_number}"
                )
        if len(rows) < 100:
            break
    return ""


def check(ticket_path: Path, status_path: Path) -> int:
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if not isinstance(ticket, Mapping) or not isinstance(status, Mapping):
        raise ValueError("ticket and ticket-status must be JSON objects")
    reason = duplicate_reason(
        ticket,
        repository=str(os.getenv("GITHUB_REPOSITORY") or ""),
        current_issue=int(os.getenv("ISSUE_NUMBER") or 0),
        token=str(os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""),
    )
    duplicate = bool(reason)
    if duplicate:
        updated = dict(status)
        updated["accepted"] = False
        updated["reason"] = reason
        status_path.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    write_output("duplicate", "true" if duplicate else "false")
    write_output("reason", reason)
    return 2 if duplicate else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", required=True)
    parser.add_argument("--status", required=True)
    args = parser.parse_args()
    return check(Path(args.ticket), Path(args.status))


if __name__ == "__main__":
    raise SystemExit(main())
