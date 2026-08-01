#!/usr/bin/env python3
"""Fail-closed BaoStock daily quota reservation backed by one GitHub issue comment."""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
POLICY_PATH = HERE / "quota-policy.json"
SHANGHAI_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
FENCED_JSON_RE = re.compile(r"```json\s*(\{.*\})\s*```", re.DOTALL)


class QuotaError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_output(name: str, value: Any) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def now_shanghai() -> datetime:
    return datetime.now(SHANGHAI_TZ)


def fenced_json(value: Mapping[str, Any]) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def parse_ledger_body(body: str) -> dict[str, Any]:
    match = FENCED_JSON_RE.search(body)
    raw = match.group(1) if match else body.strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "quota ledger comment is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "quota ledger root must be an object")
    return dict(value)


def default_state(date_text: str, policy: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "baostock-quota-ledger-v1",
        "provider": "baostock",
        "timezone": "Asia/Shanghai",
        "date": date_text,
        "daily_limit": int(policy["daily_request_limit"]),
        "request_count": 0,
        "blacklisted": False,
        "blacklist_reason": None,
        "last_reserved_at": None,
        "last_run_id": None,
        "last_issue_number": None,
        "notes": "Machine-managed; do not edit manually.",
    }


def normalize_state(state: Mapping[str, Any], today: str, policy: Mapping[str, Any]) -> dict[str, Any]:
    if str(state.get("provider") or "") != "baostock":
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "quota ledger provider mismatch")
    if str(state.get("timezone") or "") != "Asia/Shanghai":
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "quota ledger timezone mismatch")
    limit = int(policy["daily_request_limit"])
    if int(state.get("daily_limit", -1)) != limit:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "quota ledger daily limit mismatch")
    if str(state.get("date") or "") != today:
        return default_state(today, policy)
    try:
        count = int(state.get("request_count", 0))
    except (TypeError, ValueError) as exc:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "quota ledger request_count is invalid") from exc
    if count < 0:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "quota ledger request_count cannot be negative")
    result = dict(state)
    result["request_count"] = count
    result["blacklisted"] = bool(result.get("blacklisted", False))
    return result


def reserve_state(
    state: Mapping[str, Any],
    *,
    today: str,
    reserved_at: str,
    run_id: int,
    issue_number: int,
    policy: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = normalize_state(state, today, policy)
    limit = int(policy["daily_request_limit"])
    count = int(current["request_count"])
    if bool(current.get("blacklisted")) or count >= limit:
        current["blacklisted"] = True
        current["blacklist_reason"] = f"daily limit {limit} reached; further BaoStock access is blocked for {today}"
        receipt = {
            "schema_version": "baostock-quota-receipt-v1",
            "status": "BAOSTOCK_DAILY_BLACKLISTED",
            "allowed": False,
            "reservation_required": True,
            "date": today,
            "timezone": "Asia/Shanghai",
            "daily_limit": limit,
            "request_count": count,
            "remaining_requests": 0,
            "blacklisted": True,
            "blacklist_reason": current["blacklist_reason"],
            "run_id": run_id,
            "issue_number": issue_number,
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        return current, receipt
    count += 1
    current.update(
        {
            "request_count": count,
            "last_reserved_at": reserved_at,
            "last_run_id": run_id,
            "last_issue_number": issue_number,
        }
    )
    if count >= limit:
        current["blacklisted"] = True
        current["blacklist_reason"] = f"the {limit}th request was reserved; local blacklist is active for the remainder of {today}"
    else:
        current["blacklisted"] = False
        current["blacklist_reason"] = None
    receipt = {
        "schema_version": "baostock-quota-receipt-v1",
        "status": "BAOSTOCK_QUOTA_RESERVED",
        "allowed": True,
        "reservation_required": True,
        "date": today,
        "timezone": "Asia/Shanghai",
        "daily_limit": limit,
        "request_count": count,
        "remaining_requests": max(0, limit - count),
        "blacklisted": bool(current["blacklisted"]),
        "blacklist_reason": current["blacklist_reason"],
        "run_id": run_id,
        "issue_number": issue_number,
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    return current, receipt


def github_json(method: str, url: str, *, token: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "evidence-data-center-baostock-quota/1",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(1_000_001)
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(200_000)
    except OSError as exc:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_UNAVAILABLE", f"GitHub quota ledger connection failed: {type(exc).__name__}") from exc
    if status < 200 or status >= 300:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_UNAVAILABLE", f"GitHub quota ledger HTTP {status}")
    if len(raw) > 1_000_000:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "GitHub quota ledger response too large")
    try:
        value = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "GitHub quota ledger returned invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise QuotaError("BAOSTOCK_QUOTA_LEDGER_INVALID", "GitHub quota ledger response root must be an object")
    return dict(value)


def write_failure(output_dir: Path, code: str, message: str, policy: Mapping[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema_version": "baostock-quota-receipt-v1",
        "status": "BAOSTOCK_QUOTA_BLOCKED",
        "allowed": False,
        "reservation_required": True,
        "error": {"code": code, "message": message[:2000]},
        "date": now_shanghai().date().isoformat(),
        "timezone": "Asia/Shanghai",
        "daily_limit": int(policy["daily_request_limit"]),
        "request_count": None,
        "remaining_requests": None,
        "blacklisted": True,
        "blacklist_reason": "fail-closed quota control",
        "secret_values_exposed": False,
        "model_calls": 0,
    }
    write_json(output_dir / "baostock-quota-receipt.json", receipt)
    write_json(
        output_dir / "artifact-manifest.json",
        {
            "schema_version": "baostock-artifact-manifest-v1",
            "files": ["ticket.json", "ticket-status.json", "baostock-quota-receipt.json"],
            "quota_status": receipt["status"],
            "secret_values_included": False,
        },
    )
    return receipt


def reserve(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    policy = load_json(POLICY_PATH)
    ticket = load_json(ticket_path)
    operation = str(ticket.get("operation") or "")
    if operation == "catalog-capabilities":
        receipt = {
            "schema_version": "baostock-quota-receipt-v1",
            "status": "BAOSTOCK_QUOTA_NOT_REQUIRED",
            "allowed": True,
            "reservation_required": False,
            "date": now_shanghai().date().isoformat(),
            "timezone": "Asia/Shanghai",
            "daily_limit": int(policy["daily_request_limit"]),
            "request_count": None,
            "remaining_requests": None,
            "blacklisted": False,
            "blacklist_reason": None,
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        write_json(output_dir / "baostock-quota-receipt.json", receipt)
        write_output("allowed", "true")
        write_output("status", receipt["status"])
        return 0
    token = str(os.getenv("GITHUB_TOKEN") or "").strip()
    repository = str(os.getenv("GITHUB_REPOSITORY") or "").strip()
    try:
        run_id = int(os.getenv("GITHUB_RUN_ID") or 0)
        issue_number = int(os.getenv("ISSUE_NUMBER") or 0)
    except ValueError as exc:
        receipt = write_failure(output_dir, "BAOSTOCK_QUOTA_RUNTIME_INVALID", "invalid workflow identifiers", policy)
        write_output("allowed", "false")
        write_output("status", receipt["status"])
        return 1
    if not token or not repository or run_id <= 0 or issue_number <= 0:
        receipt = write_failure(output_dir, "BAOSTOCK_QUOTA_RUNTIME_INVALID", "missing GitHub quota runtime context", policy)
        write_output("allowed", "false")
        write_output("status", receipt["status"])
        return 1
    comment_id = int(policy["ledger_comment_id"])
    url = f"https://api.github.com/repos/{repository}/issues/comments/{comment_id}"
    try:
        comment = github_json("GET", url, token=token)
        state = parse_ledger_body(str(comment.get("body") or ""))
        current = now_shanghai()
        updated, receipt = reserve_state(
            state,
            today=current.date().isoformat(),
            reserved_at=current.isoformat(),
            run_id=run_id,
            issue_number=issue_number,
            policy=policy,
        )
        github_json("PATCH", url, token=token, payload={"body": fenced_json(updated)})
        write_json(output_dir / "baostock-quota-receipt.json", receipt)
        if not receipt["allowed"]:
            write_json(
                output_dir / "artifact-manifest.json",
                {
                    "schema_version": "baostock-artifact-manifest-v1",
                    "files": ["ticket.json", "ticket-status.json", "baostock-quota-receipt.json"],
                    "quota_status": receipt["status"],
                    "secret_values_included": False,
                },
            )
        write_output("allowed", "true" if receipt["allowed"] else "false")
        write_output("status", receipt["status"])
        write_output("request_count", receipt["request_count"])
        write_output("blacklisted", "true" if receipt["blacklisted"] else "false")
        return 0 if receipt["allowed"] else 1
    except QuotaError as exc:
        receipt = write_failure(output_dir, exc.code, str(exc), policy)
        write_output("allowed", "false")
        write_output("status", receipt["status"])
        write_output("blacklisted", "true")
        return 1


def finalize_manifest(output_dir: Path) -> int:
    manifest_path = output_dir / "artifact-manifest.json"
    manifest = load_json(manifest_path) if manifest_path.exists() else {
        "schema_version": "baostock-artifact-manifest-v1",
        "files": [],
        "secret_values_included": False,
    }
    files = [str(item) for item in manifest.get("files", [])]
    if "baostock-quota-receipt.json" not in files:
        files.append("baostock-quota-receipt.json")
    manifest["files"] = files
    receipt_path = output_dir / "baostock-quota-receipt.json"
    if receipt_path.exists():
        receipt = load_json(receipt_path)
        manifest["quota_status"] = receipt.get("status")
        manifest["quota_request_count"] = receipt.get("request_count")
        manifest["quota_blacklisted"] = receipt.get("blacklisted")
    manifest["secret_values_included"] = False
    write_json(manifest_path, manifest)
    return 0


def render(output_dir: Path, artifact_url: str = "") -> int:
    receipt = load_json(output_dir / "baostock-quota-receipt.json")
    heading = receipt.get("status") or "BAOSTOCK_QUOTA_UNKNOWN"
    print(f"## {heading}\n")
    print(f"- Allowed: `{str(bool(receipt.get('allowed'))).lower()}`")
    print(f"- Date: `{receipt.get('date') or 'unknown'}`")
    print(f"- Timezone: `{receipt.get('timezone') or 'Asia/Shanghai'}`")
    print(f"- Daily limit: `{receipt.get('daily_limit')}`")
    print(f"- Request count: `{receipt.get('request_count')}`")
    print(f"- Remaining requests: `{receipt.get('remaining_requests')}`")
    print(f"- Blacklisted: `{str(bool(receipt.get('blacklisted'))).lower()}`")
    if receipt.get("blacklist_reason"):
        print(f"- Blacklist reason: `{receipt['blacklist_reason']}`")
    if receipt.get("error"):
        print(f"- Error code: `{receipt['error']['code']}`")
        print(f"- Message: `{receipt['error']['message']}`")
    print(f"- Artifact: {artifact_url or 'unavailable'}")
    print("- Secret values exposed: `false`")
    print("- Model calls: `0`")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    reserve_parser = sub.add_parser("reserve")
    reserve_parser.add_argument("--ticket", required=True)
    reserve_parser.add_argument("--output-dir", required=True)
    finalize_parser = sub.add_parser("finalize-manifest")
    finalize_parser.add_argument("--output-dir", required=True)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--output-dir", required=True)
    render_parser.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "reserve":
        return reserve(Path(args.ticket), Path(args.output_dir))
    if args.command == "finalize-manifest":
        return finalize_manifest(Path(args.output_dir))
    return render(Path(args.output_dir), args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
