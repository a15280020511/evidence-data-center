#!/usr/bin/env python3
"""One-time local PKCE bootstrap for a Consensus Free account.

Run this on a trusted computer where Python and your browser share localhost.
It opens the Consensus authorization page, receives the callback only on
127.0.0.1, exchanges the code for tokens, and stores them in a local file with
0600 permissions. Tokens are never sent to GitHub or printed by default.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import requests

HERE = Path(__file__).resolve().parent
CLIENT_PATH = HERE / "oauth-client.json"
UA = "evidence-data-center-consensus-oauth-bootstrap/1"


class BootstrapError(RuntimeError):
    pass


def load_client() -> dict[str, Any]:
    value = json.loads(CLIENT_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BootstrapError("oauth-client.json must contain an object")
    required = (
        "client_id",
        "redirect_uri",
        "authorization_endpoint",
        "token_endpoint",
        "resource",
        "scope",
    )
    for key in required:
        if not str(value.get(key) or "").strip():
            raise BootstrapError(f"oauth-client.json missing {key}")
    return value


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def make_pkce() -> tuple[str, str]:
    verifier = b64url(secrets.token_bytes(48))
    challenge = b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def secure_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    finally:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def token_exchange(client: dict[str, Any], code: str, verifier: str, timeout: int) -> dict[str, Any]:
    try:
        response = requests.post(
            str(client["token_endpoint"]),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": UA,
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": str(client["redirect_uri"]),
                "client_id": str(client["client_id"]),
                "code_verifier": verifier,
                "resource": str(client["resource"]),
            },
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise BootstrapError(f"token exchange connection failed: {type(exc).__name__}") from exc
    try:
        payload = response.json()
    except ValueError as exc:
        raise BootstrapError(f"token endpoint returned HTTP {response.status_code} with invalid JSON") from exc
    if not 200 <= response.status_code < 300:
        if isinstance(payload, dict):
            error = str(payload.get("error") or "oauth_error")[:200]
            description = str(payload.get("error_description") or "")[:500]
            raise BootstrapError(f"token exchange failed: {error}: {description}")
        raise BootstrapError(f"token exchange failed with HTTP {response.status_code}")
    if not isinstance(payload, dict) or not str(payload.get("access_token") or "").strip():
        raise BootstrapError("token exchange response missing access_token")
    if not str(payload.get("refresh_token") or "").strip():
        raise BootstrapError("token exchange response missing refresh_token")
    return payload


class CallbackState:
    code: str | None = None
    state: str | None = None
    error: str | None = None
    event = threading.Event()


def callback_handler(expected_path: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != expected_path:
                self.send_response(404)
                self.end_headers()
                return
            values = parse_qs(parsed.query)
            CallbackState.code = (values.get("code") or [None])[0]
            CallbackState.state = (values.get("state") or [None])[0]
            CallbackState.error = (values.get("error") or [None])[0]
            body = (
                "<html><body><h2>Consensus authorization received.</h2>"
                "<p>You may close this tab and return to the terminal.</p></body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            CallbackState.event.set()

    return Handler


def bootstrap(output: Path, timeout: int, no_browser: bool) -> dict[str, Any]:
    client = load_client()
    redirect = urlparse(str(client["redirect_uri"]))
    if redirect.scheme != "http" or redirect.hostname != "127.0.0.1" or not redirect.port:
        raise BootstrapError("registered redirect_uri must be an explicit 127.0.0.1 loopback URL")

    verifier, challenge = make_pkce()
    expected_state = b64url(secrets.token_bytes(24))
    query = {
        "response_type": "code",
        "client_id": str(client["client_id"]),
        "redirect_uri": str(client["redirect_uri"]),
        "scope": str(client["scope"]),
        "state": expected_state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "resource": str(client["resource"]),
    }
    authorization_url = str(client["authorization_endpoint"]) + "?" + urlencode(query)

    CallbackState.code = None
    CallbackState.state = None
    CallbackState.error = None
    CallbackState.event.clear()
    server = HTTPServer(("127.0.0.1", int(redirect.port)), callback_handler(redirect.path or "/"))
    server.timeout = 1

    print("Open this authorization URL in a browser on this same computer:\n")
    print(authorization_url)
    print()
    if not no_browser:
        webbrowser.open(authorization_url, new=1, autoraise=True)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not CallbackState.event.is_set():
        server.handle_request()
    server.server_close()

    if not CallbackState.event.is_set():
        raise BootstrapError("authorization timed out before localhost callback was received")
    if CallbackState.error:
        raise BootstrapError(f"authorization server returned error: {CallbackState.error}")
    if not CallbackState.code:
        raise BootstrapError("callback did not contain an authorization code")
    if CallbackState.state != expected_state:
        raise BootstrapError("OAuth state mismatch")

    token = token_exchange(client, CallbackState.code, verifier, timeout=min(60, max(10, timeout)))
    stored = {
        "schema_version": "consensus-mcp-local-oauth-token-v1",
        "client_id": client["client_id"],
        "scope": str(token.get("scope") or client["scope"]),
        "token_type": str(token.get("token_type") or "Bearer"),
        "access_token": str(token["access_token"]),
        "refresh_token": str(token["refresh_token"]),
        "expires_in": token.get("expires_in") if isinstance(token.get("expires_in"), (int, float)) else None,
        "resource": client["resource"],
        "created_at_unix": int(time.time()),
    }
    secure_write(output, stored)
    return {
        "status": "pass",
        "token_file": str(output),
        "refresh_token_present": True,
        "access_token_present": True,
        "scope": stored["scope"],
        "expires_in": stored["expires_in"],
        "secret_values_exposed": False,
    }


def show_refresh_token(token_file: Path) -> int:
    value = json.loads(token_file.read_text(encoding="utf-8"))
    refresh = str(value.get("refresh_token") or "").strip() if isinstance(value, dict) else ""
    if not refresh:
        raise BootstrapError("token file has no refresh_token")
    print(refresh)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_bootstrap = sub.add_parser("bootstrap")
    p_bootstrap.add_argument(
        "--output",
        type=Path,
        default=Path.home() / ".config" / "evidence-data-center" / "consensus-oauth-token.json",
    )
    p_bootstrap.add_argument("--timeout", type=int, default=300)
    p_bootstrap.add_argument("--no-browser", action="store_true")

    p_show = sub.add_parser("show-refresh-token")
    p_show.add_argument(
        "--token-file",
        type=Path,
        default=Path.home() / ".config" / "evidence-data-center" / "consensus-oauth-token.json",
    )

    args = parser.parse_args()
    try:
        if args.command == "show-refresh-token":
            return show_refresh_token(args.token_file)
        if args.timeout < 30 or args.timeout > 900:
            raise BootstrapError("timeout must be between 30 and 900 seconds")
        report = bootstrap(args.output.expanduser(), args.timeout, args.no_browser)
    except (BootstrapError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc), "secret_values_exposed": False}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
