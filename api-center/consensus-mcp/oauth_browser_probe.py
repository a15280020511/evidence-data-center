#!/usr/bin/env python3
"""Probe whether Consensus OAuth endpoints are usable from a browser helper.

The probe never registers a client and never requests a real token. It checks
CORS preflights plus one deliberately invalid form-encoded token POST so we can
see whether a browser simple POST would be readable cross-origin.
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


def preflight(url: str) -> dict[str, Any]:
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
        "preflight_permits_post": bool(
            response.status_code < 400
            and (allow_origin == "*" or allow_origin == ORIGIN)
            and "POST" in allow_methods.upper()
            and "content-type" in allow_headers.lower()
        ),
    }


def invalid_token_post() -> dict[str, Any]:
    response = requests.post(
        TOKEN_ENDPOINT,
        headers={
            "Origin": ORIGIN,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": UA,
        },
        data={
            "grant_type": "authorization_code",
            "code": "invalid-probe-code",
            "redirect_uri": "https://github.com/a15280020511/evidence-data-center/oauth/callback",
            "client_id": "invalid-probe-client",
            "code_verifier": "A" * 64,
        },
        timeout=20,
        allow_redirects=False,
    )
    headers = {key.lower(): value for key, value in response.headers.items()}
    allow_origin = headers.get("access-control-allow-origin", "")
    return {
        "status": response.status_code,
        "allow_origin": allow_origin,
        "response_content_type": headers.get("content-type", ""),
        "browser_can_read_simple_post": bool(
            allow_origin == "*" or allow_origin == ORIGIN
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    registration = preflight(REGISTRATION_ENDPOINT)
    token_preflight = preflight(TOKEN_ENDPOINT)
    token_simple_post = invalid_token_post()
    report = {
        "schema_version": "consensus-mcp-browser-oauth-probe-v2",
        "origin": ORIGIN,
        "registration_preflight": registration,
        "token_preflight": token_preflight,
        "token_simple_post": token_simple_post,
        "server_side_registration_required": not registration["preflight_permits_post"],
        "browser_token_exchange_possible_after_server_registration": token_simple_post["browser_can_read_simple_post"],
        "secret_values_exposed": False,
        "client_registered": False,
        "real_token_requested": False,
    }
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "registration_preflight_status": registration["status"],
        "registration_preflight_post": registration["preflight_permits_post"],
        "token_preflight_status": token_preflight["status"],
        "token_simple_post_status": token_simple_post["status"],
        "token_simple_post_cors": token_simple_post["browser_can_read_simple_post"],
        "browser_token_exchange_possible_after_server_registration": report["browser_token_exchange_possible_after_server_registration"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
