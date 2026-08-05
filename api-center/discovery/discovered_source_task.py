#!/usr/bin/env python3
"""Execute one bounded read-only GET against a fixed URL in the discovered registry."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import socket
import urllib.parse
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "registry.json"
USER_AGENT = "evidence-data-center-discovered-source/1.0"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def output(name: str, value: str) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value.replace(chr(10), ' ')}\n")


def validate_public_https_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(str(value or ""))
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("registry URL is not a valid default-port HTTPS URL")
    host = parsed.hostname.casefold().rstrip(".")
    if host in {"localhost", "metadata.google.internal", "metadata.azure.internal", "kubernetes.default", "instance-data"} or host.endswith((".local", ".internal", ".localhost", ".svc", ".cluster.local")):
        raise ValueError("registry URL targets a blocked hostname")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not literal.is_global:
            raise ValueError("registry URL targets a non-public IP")
    else:
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        resolved = {str(record[4][0]).split("%", 1)[0] for record in records if record and len(record) >= 5 and record[4]}
        if not resolved or any(not ipaddress.ip_address(address).is_global for address in resolved):
            raise ValueError("registry URL resolves to a non-public IP")
    return urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, ""))


def source_map() -> dict[str, Mapping[str, Any]]:
    doc = load(REGISTRY)
    return {str(row["source_id"]): row for row in doc.get("sources") or [] if isinstance(row, Mapping) and row.get("status") == "integrated"}


def validate_ticket(ticket: Mapping[str, Any]) -> Mapping[str, Any]:
    allowed = {"schema_version", "task_id", "source_id", "operation", "acceptance"}
    if set(ticket) - allowed:
        raise ValueError("ticket contains unknown fields")
    if ticket.get("schema_version") != "discovered-source-ticket-v1":
        raise ValueError("unsupported schema_version")
    task_id = str(ticket.get("task_id") or "")
    if not task_id or len(task_id) > 128:
        raise ValueError("task_id is invalid")
    if ticket.get("operation") != "fetch-default":
        raise ValueError("only fetch-default is supported")
    source_id = str(ticket.get("source_id") or "")
    source = source_map().get(source_id)
    if source is None:
        raise ValueError("source_id is not in the integrated registry")
    if source.get("auth") != "none" or source.get("integration_mode") != "fixed-url-read-only-registry":
        raise ValueError("source is not eligible for anonymous fixed-URL execution")
    validate_public_https_url(str(source.get("url") or ""))
    return source


def prepare(event: Path, output_dir: Path) -> int:
    issue = load(event).get("issue") or {}
    accepted = False
    reason = ""
    ticket = None
    try:
        if not str(issue.get("title") or "").startswith("[intel-discovered-source]"):
            raise ValueError("issue title must start with [intel-discovered-source]")
        ticket = json.loads(str(issue.get("body") or ""))
        if not isinstance(ticket, Mapping):
            raise ValueError("ticket body must be a JSON object")
        source = validate_ticket(ticket)
        output_dir.mkdir(parents=True, exist_ok=True)
        write(output_dir / "ticket.json", ticket)
        write(output_dir / "source.json", source)
        accepted = True
    except Exception as exc:
        reason = f"{type(exc).__name__}: {str(exc)[:500]}"
    write(output_dir / "ticket-status.json", {"accepted": accepted, "reason": reason, "task_id": str((ticket or {}).get("task_id") or ""), "secret_values_exposed": False, "model_calls": 0})
    output("accepted", "true" if accepted else "false")
    output("reason", reason)
    return 0 if accepted else 1


def execute(ticket_path: Path, output_dir: Path) -> int:
    ticket = load(ticket_path)
    source = validate_ticket(ticket)
    acceptance = ticket.get("acceptance") if isinstance(ticket.get("acceptance"), Mapping) else {}
    timeout = max(5, min(60, int(acceptance.get("timeout_seconds") or 30)))
    max_bytes = max(1024, min(5_000_000, int(acceptance.get("max_response_bytes") or 1_000_000)))
    started = now()
    start = time.perf_counter()
    status = "INTEL_DISCOVERED_SOURCE_FAILED"
    failure = None
    metadata: dict[str, Any] = {"source_id": source["source_id"], "url": source["url"], "http_method": "GET", "request_count": 0, "write_operations_allowed": False, "automatic_retry": False, "automatic_pagination": False, "secret_values_exposed": False, "model_calls": 0}
    try:
        fixed_url = validate_public_https_url(str(source["url"]))
        request = urllib.request.Request(fixed_url, headers={"Accept": "application/json, application/xml, text/csv, text/html;q=0.8", "User-Agent": USER_AGENT}, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            validate_public_https_url(response.geturl())
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise RuntimeError("response exceeds acceptance.max_response_bytes")
            if not 200 <= int(response.status) < 400:
                raise RuntimeError(f"upstream HTTP {response.status}")
            (output_dir / "response.bin").write_bytes(raw)
            metadata.update({"request_count": 1, "http_status": int(response.status), "content_type": str(response.headers.get("Content-Type") or ""), "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest()})
        status = "INTEL_DISCOVERED_SOURCE_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:1000]}
    write(output_dir / "execution.json", {"status": status, "started_at": started, "finished_at": now(), "duration_ms": round((time.perf_counter() - start) * 1000, 3), "ticket": ticket, "source": source, "metadata": metadata, "failure": failure})
    output("status", status)
    return 0 if status.endswith("COMPLETED") else 1


def render(output_dir: Path, phase: str, artifact_url: str) -> int:
    if phase == "accepted":
        status = load(output_dir / "ticket-status.json")
        print(f"已接受自动发现来源票据。task_id=`{status.get('task_id')}`。仅执行注册表固定 HTTPS URL 的一次只读 GET。")
        return 0
    if phase == "rejected":
        status = load(output_dir / "ticket-status.json")
        print(f"票据被拒绝：{status.get('reason')}")
        return 0
    execution = load(output_dir / "execution.json")
    print(f"执行状态：`{execution.get('status')}`\n\n来源：`{execution.get('source', {}).get('source_id')}`\n\nArtifact：{artifact_url or '未生成'}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--event-path", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    e = sub.add_parser("execute")
    e.add_argument("--ticket", type=Path, required=True)
    e.add_argument("--output-dir", type=Path, required=True)
    r = sub.add_parser("render")
    r.add_argument("--output-dir", type=Path, required=True)
    r.add_argument("--phase", choices=["accepted", "rejected", "completed"], required=True)
    r.add_argument("--artifact-url", default="")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        return prepare(args.event_path, args.output_dir)
    if args.command == "execute":
        return execute(args.ticket, args.output_dir)
    return render(args.output_dir, args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
