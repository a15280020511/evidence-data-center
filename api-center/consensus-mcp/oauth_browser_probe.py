#!/usr/bin/env python3
"""Probe whether Consensus OAuth endpoints are usable from a browser SPA.

The probe sends CORS preflight requests only. It never registers a client,
never requests an authorization code, and never handles tokens.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests

ORIGIN = "https://example.invalid"
REGISTRATION_ENDPOINT = "https://consensus.app/oauth/register/"
TOKEN_ENDPOINT = "https://consensus.app/oauth/token/"
UA = "evidence-data-center-consensus-browser-oauth-probe/1"


def probe(url: str) -> dict[str, Any]:
    response = requests.options(
        url,
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
            "User-Agent": UA,
        },
        timeout=20,
        allow_redirects=False,
    )
    headers = {key.lower(): value for key, value in response.headers.items()}
    allow_origin = headers.get("access-control-allow-origin", "")
    allow_methods = headers.get("access-control-allow-methods", "")
    allow_headers = headers.get("access-control-allow-headers", "")
    return {
        "status": response.status_code,
        "allow_origin": allow_origin,
        "allow_methods": allow_methods,
        "allow_headers": allow_headers,
        "browser_post_permitted": bool(
            response.status_code < 400
            and (allow_origin == "*" or allow_origin == ORIGIN)
            and "POST" in allow_methods.upper()
            and "content-type" in allow_headers.lower()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = {
        "schema_version": "consensus-mcp-browser-oauth-probe-v1",
        "origin": ORIGIN,
        "registration": probe(REGISTRATION_ENDPOINT),
        "token": probe(TOKEN_ENDPOINT),
        "secret_values_exposed": False,
        "client_registered": False,
        "token_requested": False,
    }
    report["browser_pkce_bridge_possible"] = bool(
        report["registration"]["browser_post_permitted"]
        and report["token"]["browser_post_permitted"]
    )
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "registration_status": report["registration"]["status"],
        "registration_browser_post": report["registration"]["browser_post_permitted"],
        "token_status": report["token"]["status"],
        "token_browser_post": report["token"]["browser_post_permitted"],
        "browser_pkce_bridge_possible": report["browser_pkce_bridge_possible"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
