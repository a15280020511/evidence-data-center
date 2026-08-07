#!/usr/bin/env python3
"""Discover sanitized OAuth metadata advertised by the Consensus MCP resource."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import requests

MCP_URL = "https://mcp.consensus.app/mcp"
UA = "evidence-data-center-consensus-oauth-probe/1"


def save(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_get(url: str) -> tuple[int, dict[str, str], Any]:
    r = requests.get(url, headers={"Accept": "application/json", "User-Agent": UA}, timeout=20, allow_redirects=False)
    try:
        body = r.json()
    except ValueError:
        body = {"text": r.text[:1000]}
    return r.status_code, {k.lower(): v for k, v in r.headers.items()}, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "evidence-data-center-oauth-probe", "version": "1.0"},
        },
    }
    r = requests.post(
        MCP_URL,
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
        json=init,
        timeout=20,
        allow_redirects=False,
    )
    www = r.headers.get("WWW-Authenticate", "")
    match = re.search(r'resource_metadata="([^"]+)"', www, flags=re.I)
    candidates = []
    if match:
        candidates.append(match.group(1))
    candidates.extend([
        "https://mcp.consensus.app/.well-known/oauth-protected-resource/mcp",
        "https://mcp.consensus.app/.well-known/oauth-protected-resource",
    ])

    resource = None
    resource_url = None
    resource_status = None
    for url in dict.fromkeys(candidates):
        status, _, body = safe_get(url)
        if status == 200 and isinstance(body, dict):
            resource, resource_url, resource_status = body, url, status
            break
        if resource_status is None:
            resource_status = status

    auth_metadata = None
    auth_url = None
    auth_status = None
    if isinstance(resource, dict):
        servers = resource.get("authorization_servers") or []
        if isinstance(servers, list) and servers:
            base = str(servers[0]).rstrip("/")
            for url in [
                base + "/.well-known/oauth-authorization-server",
                base + "/.well-known/openid-configuration",
            ]:
                status, _, body = safe_get(url)
                if status == 200 and isinstance(body, dict):
                    auth_metadata, auth_url, auth_status = body, url, status
                    break
                if auth_status is None:
                    auth_status = status

    report = {
        "schema_version": "consensus-mcp-oauth-probe-v1",
        "mcp_status_without_token": r.status_code,
        "www_authenticate": www[:2000],
        "resource_metadata_url": resource_url,
        "resource_metadata_status": resource_status,
        "resource_metadata": resource,
        "authorization_metadata_url": auth_url,
        "authorization_metadata_status": auth_status,
        "authorization_metadata": auth_metadata,
        "supports_client_credentials": bool(
            isinstance(auth_metadata, dict)
            and "client_credentials" in (auth_metadata.get("grant_types_supported") or [])
        ),
        "supports_authorization_code": bool(
            isinstance(auth_metadata, dict)
            and "authorization_code" in (auth_metadata.get("grant_types_supported") or [])
        ),
        "registration_endpoint_present": bool(
            isinstance(auth_metadata, dict) and auth_metadata.get("registration_endpoint")
        ),
        "secret_values_exposed": False,
    }
    save(args.output, report)
    print(json.dumps({
        "mcp_status_without_token": report["mcp_status_without_token"],
        "resource_metadata_status": report["resource_metadata_status"],
        "authorization_metadata_status": report["authorization_metadata_status"],
        "supports_client_credentials": report["supports_client_credentials"],
        "supports_authorization_code": report["supports_authorization_code"],
        "registration_endpoint_present": report["registration_endpoint_present"],
    }))
    return 0 if resource is not None and auth_metadata is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
