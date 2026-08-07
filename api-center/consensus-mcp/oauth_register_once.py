#!/usr/bin/env python3
"""One-time Dynamic Client Registration for the Consensus native OAuth bridge.

The resulting client_id is public configuration. If the authorization server
returns any secret-like values, they are deliberately omitted from output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests

REGISTRATION_ENDPOINT = "https://consensus.app/oauth/register/"
REDIRECT_URI = "http://127.0.0.1:8765/callback"
UA = "evidence-data-center-consensus-oauth-registration/1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    request_body = {
        "client_name": "Evidence Data Center Consensus MCP",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": "search",
    }
    response = requests.post(
        REGISTRATION_ENDPOINT,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
        json=request_body,
        timeout=20,
        allow_redirects=False,
    )
    try:
        payload: Any = response.json()
    except ValueError:
        payload = {"text": response.text[:1000]}

    report: dict[str, Any] = {
        "schema_version": "consensus-mcp-oauth-client-registration-v1",
        "status": "fail",
        "http_status": response.status_code,
        "registration_endpoint": REGISTRATION_ENDPOINT,
        "redirect_uri": REDIRECT_URI,
        "secret_values_exposed": False,
    }
    if 200 <= response.status_code < 300 and isinstance(payload, dict) and payload.get("client_id"):
        report.update({
            "status": "pass",
            "client": {
                "client_id": str(payload["client_id"]),
                "client_name": str(payload.get("client_name") or request_body["client_name"]),
                "redirect_uris": payload.get("redirect_uris") or request_body["redirect_uris"],
                "grant_types": payload.get("grant_types") or request_body["grant_types"],
                "response_types": payload.get("response_types") or request_body["response_types"],
                "token_endpoint_auth_method": str(payload.get("token_endpoint_auth_method") or "none"),
                "scope": str(payload.get("scope") or "search"),
            },
            "secret_like_fields_returned_but_omitted": sorted(
                key for key in payload
                if key in {"client_secret", "registration_access_token"}
            ),
        })
    else:
        safe_error = payload if isinstance(payload, dict) else {"error": "non-json response"}
        safe_error = {
            str(k): v for k, v in safe_error.items()
            if str(k) not in {"client_secret", "registration_access_token", "access_token", "refresh_token"}
        }
        report["error"] = safe_error

    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "http_status": report["http_status"],
        "client_id_present": bool((report.get("client") or {}).get("client_id")),
        "secret_values_exposed": False,
    }))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
