#!/usr/bin/env python3
"""Deterministic local HTTP backend used only by repository integration tests."""
from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

OBSERVATIONS = {
    "source": "three-center-mock-api",
    "observed_at": "2026-07-27T00:00:00Z",
    "values": [97, 101, 99, 103, 100, 98, 102, 104, 96, 100],
    "unit": "synthetic-index",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "ThreeCenterMock/1.0"

    def _send(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlsplit(self.path).path
        if path == "/observations":
            self._send(200, OBSERVATIONS)
        elif path == "/slow":
            time.sleep(3)
            self._send(200, {"status": "late"})
        elif path == "/failure":
            self._send(503, {"status": "upstream-failure"})
        elif path == "/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"status": "not-found"})

    def log_message(self, fmt: str, *args: object) -> None:
        print("mock-api", self.address_string(), fmt % args, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=19090)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
