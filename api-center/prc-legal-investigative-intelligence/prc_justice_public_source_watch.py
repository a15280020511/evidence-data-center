#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

HERE = Path(__file__).resolve().parent
DEFAULT_TARGETS = HERE / "prc-justice-watch-targets.json"
BLOCK_MARKERS = (
    "captcha",
    "verify you are human",
    "access denied",
    "人机验证",
    "验证码",
    "访问过于频繁",
    "安全验证",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_targets(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "prc-justice-watch-targets-v1":
        raise ValueError("unexpected watch target schema")
    targets = data.get("targets") or []
    rules = data.get("rules") or {}
    maximum = int(data.get("max_targets", 20))
    if not isinstance(targets, list) or not targets or len(targets) > maximum or maximum > 20:
        raise ValueError("watch targets must contain 1..20 rows")
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for row in targets:
        if not isinstance(row, dict):
            raise ValueError("watch target must be object")
        target_id = str(row.get("id") or "")
        url = str(row.get("url") or "")
        parsed = urlparse(url)
        if not target_id or target_id in seen_ids:
            raise ValueError(f"duplicate/empty target id: {target_id}")
        if url in seen_urls:
            raise ValueError(f"duplicate url: {url}")
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError(f"HTTPS public URL required: {url}")
        if parsed.username or parsed.password:
            raise ValueError("credentials in URL are forbidden")
        seen_ids.add(target_id)
        seen_urls.add(url)
    expected_false = [
        "allow_form_submission",
        "allow_login",
        "allow_captcha_solving",
        "allow_waf_bypass",
        "allow_proxy_rotation",
        "allow_hidden_api_discovery",
    ]
    for key in expected_false:
        if rules.get(key) is not False:
            raise ValueError(f"{key} must remain false")
    if rules.get("same_request_no_retry") is not True:
        raise ValueError("same_request_no_retry must remain true")
    if int(rules.get("request_interval_seconds", 0)) < 10:
        raise ValueError("request_interval_seconds must be >= 10")
    if int(rules.get("max_response_bytes_per_target", 0)) > 524288:
        raise ValueError("max_response_bytes_per_target exceeds 512 KiB")
    return data


def probe(row: dict, max_bytes: int) -> dict:
    url = str(row["url"])
    started = time.perf_counter()
    result = {
        "id": row["id"],
        "name": row.get("name"),
        "url": url,
        "checked_at": utc_now(),
        "status": "ERROR",
        "http_status": None,
        "elapsed_ms": None,
        "bytes_hashed": 0,
        "sha256": None,
        "etag": None,
        "last_modified": None,
        "content_type": None,
        "redirect_location": None,
        "access_control_marker": False,
        "error": None,
    }
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "evidence-data-center-public-source-watch/1.0",
                "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.8,*/*;q=0.2",
            },
            timeout=(5, 15),
            stream=True,
            allow_redirects=False,
        )
        result["http_status"] = response.status_code
        result["etag"] = response.headers.get("ETag")
        result["last_modified"] = response.headers.get("Last-Modified")
        result["content_type"] = response.headers.get("Content-Type")
        result["redirect_location"] = response.headers.get("Location") if 300 <= response.status_code < 400 else None

        digest = hashlib.sha256()
        sample = bytearray()
        total = 0
        if response.status_code == 200:
            for chunk in response.iter_content(chunk_size=16384):
                if not chunk:
                    continue
                remaining = max_bytes - total
                if remaining <= 0:
                    break
                piece = chunk[:remaining]
                digest.update(piece)
                if len(sample) < 131072:
                    sample.extend(piece[: 131072 - len(sample)])
                total += len(piece)
                if total >= max_bytes:
                    break
            lowered = sample.decode("utf-8", errors="ignore").lower()
            blocked = any(marker in lowered for marker in BLOCK_MARKERS)
            result["access_control_marker"] = blocked
            result["bytes_hashed"] = total
            result["sha256"] = digest.hexdigest() if total else None
            result["status"] = "BLOCKED_ACCESS_CONTROL" if blocked else "AVAILABLE"
        elif response.status_code in {401, 403, 429}:
            result["status"] = "BLOCKED_OR_RATE_LIMITED"
        elif 300 <= response.status_code < 400:
            result["status"] = "REDIRECT_RECORDED_NOT_FOLLOWED"
        else:
            result["status"] = "HTTP_UNAVAILABLE"
    except requests.RequestException as exc:
        result["status"] = "NETWORK_ERROR"
        result["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    finally:
        result["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--output", type=Path, default=Path("prc-justice-source-watch.json"))
    parser.add_argument("--mode", choices=["validate", "live"], default="validate")
    args = parser.parse_args()

    config = load_targets(args.targets)
    targets = config["targets"]
    rules = config["rules"]
    report = {
        "schema_version": "prc-justice-public-source-watch-report-v1",
        "generated_at": utc_now(),
        "mode": args.mode,
        "target_count": len(targets),
        "network_used": args.mode == "live",
        "automatic_retry": False,
        "automatic_login": False,
        "captcha_solving": False,
        "waf_bypass": False,
        "proxy_rotation": False,
        "results": [],
    }

    if args.mode == "live":
        interval = int(rules["request_interval_seconds"])
        max_bytes = int(rules["max_response_bytes_per_target"])
        for index, row in enumerate(targets):
            report["results"].append(probe(row, max_bytes))
            if index + 1 < len(targets):
                time.sleep(interval)
    else:
        report["results"] = [
            {"id": row["id"], "url": row["url"], "status": "CONFIG_VALIDATED"}
            for row in targets
        ]

    counts: dict[str, int] = {}
    for row in report["results"]:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    report["status_counts"] = counts
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "mode": args.mode,
        "target_count": len(targets),
        "status_counts": counts,
        "output": str(args.output),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
