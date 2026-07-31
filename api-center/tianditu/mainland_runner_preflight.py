#!/usr/bin/env python3
"""Verify that a Tianditu job is using the registered fixed mainland egress."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

IP_ENDPOINTS = (
    "https://myip.ipip.net",
    "https://api.ipify.org",
    "https://ipv4.icanhazip.com",
)
IP_PATTERN = re.compile(r"(?<![0-9.])(?:\d{1,3}\.){3}\d{1,3}(?![0-9.])")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def public_ipv4(value: str, name: str) -> str:
    text = str(value or "").strip()
    try:
        address = ipaddress.ip_address(text)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a valid IPv4 address") from exc
    if address.version != 4 or not address.is_global:
        raise RuntimeError(f"{name} must be a globally routable IPv4 address")
    return str(address)


def extract_ipv4(raw: bytes) -> str:
    text = raw[:512].decode("utf-8", errors="replace")
    for match in IP_PATTERN.findall(text):
        try:
            return public_ipv4(match, "detected egress IP")
        except RuntimeError:
            continue
    raise RuntimeError("public IPv4 reflector returned no globally routable IPv4 address")


def fetch_public_ipv4(
    timeout: int = 10,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> tuple[str, str]:
    failures: list[str] = []
    for endpoint in IP_ENDPOINTS:
        request = urllib.request.Request(
            endpoint,
            headers={
                "Accept": "text/plain",
                "User-Agent": "evidence-data-center-tianditu-egress-check/1",
            },
            method="GET",
        )
        try:
            with opener(request, timeout=timeout) as response:
                raw = response.read(513)
            if len(raw) > 512:
                raise RuntimeError("response exceeded 512 bytes")
            return extract_ipv4(raw), endpoint
        except (OSError, RuntimeError, urllib.error.URLError) as exc:
            failures.append(f"{endpoint}: {type(exc).__name__}")
    raise RuntimeError("unable to determine public IPv4; " + "; ".join(failures))


def verify(
    expected_ip: str,
    runner_environment: str,
    runner_os: str,
    runner_arch: str,
    timeout: int = 10,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> dict[str, object]:
    if runner_environment.strip().casefold() != "self-hosted":
        raise RuntimeError("Tianditu requires a self-hosted runner; GitHub-hosted fallback is forbidden")
    if runner_os.strip().casefold() != "linux":
        raise RuntimeError("Tianditu mainland runner must use Linux")
    if runner_arch.strip().casefold() not in {"x64", "amd64"}:
        raise RuntimeError("Tianditu mainland runner must use x64 architecture")
    expected = public_ipv4(expected_ip, "TIANDITU_EXPECTED_EGRESS_IP")
    actual, reflector = fetch_public_ipv4(timeout=timeout, opener=opener)
    if actual != expected:
        raise RuntimeError("runner public IPv4 does not match TIANDITU_EXPECTED_EGRESS_IP")
    digest = hashlib.sha256(actual.encode("ascii")).hexdigest()
    return {
        "schema_version": "tianditu-egress-verification-v1",
        "verified": True,
        "verified_at": utc_now(),
        "runner_environment": "self-hosted",
        "runner_os": "Linux",
        "runner_arch": "X64",
        "public_ipv4_sha256": digest,
        "reflector_origin": urllib.parse.urlsplit(reflector).hostname,
        "raw_public_ipv4_stored": False,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_output(name: str, value: str) -> None:
    target = os.getenv("GITHUB_OUTPUT")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-ip", required=True)
    parser.add_argument("--runner-environment", required=True)
    parser.add_argument("--runner-os", required=True)
    parser.add_argument("--runner-arch", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()
    try:
        result = verify(
            args.expected_ip,
            args.runner_environment,
            args.runner_os,
            args.runner_arch,
            timeout=max(3, min(args.timeout, 20)),
        )
    except RuntimeError as exc:
        print(f"Tianditu fixed-egress verification failed: {exc}")
        write_output("egress_verified", "false")
        return 1
    print("::add-mask::" + args.expected_ip.strip())
    write_json(Path(args.output), result)
    write_output("egress_verified", "true")
    write_output("public_ipv4_sha256", str(result["public_ipv4_sha256"]))
    print("Tianditu fixed mainland egress verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
