#!/usr/bin/env python3
"""Resolve a short-lived Consensus OAuth access token from a GitHub Secret.

The long-lived refresh token is read only from CONSENSUS_MCP_REFRESH_TOKEN.
The resulting access token is masked and written only to GITHUB_ENV for the
current runner process. No token is written to repository files or artifacts.

If Consensus rotates refresh tokens, the resolver fails closed because this
repository's current GitHub integration cannot safely rewrite Actions Secrets.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests

HERE = Path(__file__).resolve().parent
CLIENT_PATH = HERE / "oauth-client.json"
REFRESH_ENV = "CONSENSUS_MCP_REFRESH_TOKEN"
BEARER_ENV = "CONSENSUS_MCP_BEARER_TOKEN"
UA = "evidence-data-center-consensus-oauth-refresh/1"


class OAuthRefreshError(RuntimeError):
    pass


def load_client() -> dict[str, Any]:
    value = json.loads(CLIENT_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OAuthRefreshError("oauth-client.json must contain an object")
    for key in ("client_id", "token_endpoint", "resource", "scope"):
        if not str(value.get(key) or "").strip():
            raise OAuthRefreshError(f"oauth-client.json missing {key}")
    return value


def write_github_output(name: str, value: str) -> None:
    target = str(os.getenv("GITHUB_OUTPUT") or "").strip()
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value.replace(chr(10), ' ')}\n")


def write_github_env(name: str, value: str) -> None:
    target = str(os.getenv("GITHUB_ENV") or "").strip()
    if not target:
        raise OAuthRefreshError("GITHUB_ENV is required for runner token injection")
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def mask(value: str) -> None:
    if value:
        print(f"::add-mask::{value}")


def safe_error_payload(response: requests.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        return {"http_status": response.status_code, "error": "non-json OAuth response"}
    if not isinstance(body, dict):
        return {"http_status": response.status_code, "error": "unexpected OAuth response"}
    return {
        "http_status": response.status_code,
        "error": str(body.get("error") or "oauth_error")[:200],
        "error_description": str(body.get("error_description") or "")[:500],
    }


def resolve(timeout: int) -> dict[str, Any]:
    existing = str(os.getenv(BEARER_ENV) or "").strip()
    if existing:
        mask(existing)
        write_github_output("credential_mode", "preprovisioned-bearer")
        write_github_output("refresh_token_rotated", "false")
        return {
            "status": "pass",
            "credential_mode": "preprovisioned-bearer",
            "refresh_token_rotated": False,
            "token_endpoint_called": False,
        }

    refresh_token = str(os.getenv(REFRESH_ENV) or "").strip()
    if not refresh_token:
        raise OAuthRefreshError(f"missing GitHub Secret {REFRESH_ENV}")
    mask(refresh_token)

    client = load_client()
    try:
        response = requests.post(
            str(client["token_endpoint"]),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": UA,
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": str(client["client_id"]),
                "scope": str(client["scope"]),
                "resource": str(client["resource"]),
            },
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise OAuthRefreshError(f"OAuth token endpoint connection failed: {type(exc).__name__}") from exc

    if not 200 <= response.status_code < 300:
        raise OAuthRefreshError(json.dumps(safe_error_payload(response), ensure_ascii=False))
    try:
        payload = response.json()
    except ValueError as exc:
        raise OAuthRefreshError("OAuth token endpoint returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise OAuthRefreshError("OAuth token endpoint returned unexpected JSON")

    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise OAuthRefreshError("OAuth refresh response missing access_token")
    mask(access_token)

    returned_refresh = str(payload.get("refresh_token") or "").strip()
    rotated = bool(returned_refresh and returned_refresh != refresh_token)
    if returned_refresh:
        mask(returned_refresh)
    write_github_output("refresh_token_rotated", "true" if rotated else "false")
    if rotated:
        raise OAuthRefreshError(
            "Consensus rotated the refresh token. Automatic server-side refresh is fail-closed because the current GitHub integration cannot safely rewrite Actions Secrets; rerun the local OAuth bootstrap and update CONSENSUS_MCP_REFRESH_TOKEN."
        )

    write_github_env(BEARER_ENV, access_token)
    write_github_output("credential_mode", "free-account-refresh-token")
    expires_in = payload.get("expires_in")
    scope = str(payload.get("scope") or client["scope"])
    return {
        "status": "pass",
        "credential_mode": "free-account-refresh-token",
        "refresh_token_rotated": False,
        "token_endpoint_called": True,
        "token_type": str(payload.get("token_type") or "Bearer"),
        "expires_in": expires_in if isinstance(expires_in, (int, float)) else None,
        "scope": scope,
        "secret_values_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    if args.timeout < 5 or args.timeout > 60:
        raise SystemExit("timeout must be between 5 and 60 seconds")
    try:
        report = resolve(args.timeout)
    except OAuthRefreshError as exc:
        write_github_output("credential_mode", "failed")
        print(json.dumps({"status": "fail", "error": str(exc), "secret_values_exposed": False}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
