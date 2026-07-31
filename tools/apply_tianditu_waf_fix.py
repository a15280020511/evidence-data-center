#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "api-center/tianditu/tianditu_task.py"
TEST = ROOT / "api-center/tianditu/tests/test_tianditu_task.py"
CATALOG = ROOT / "api-center/tianditu/provider-catalog.json"
WORKFLOW = ROOT / ".github/workflows/tianditu-api-ticket.yml"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_task() -> None:
    text = TASK.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import os\nimport time\nimport urllib.error",
        "import os\nimport re\nimport shutil\nimport subprocess\nimport tempfile\nimport time\nimport urllib.error",
        "imports",
    )
    marker = '''QUERY_TYPES = {
    "viewport-search": 2,
    "nearby-search": 3,
    "polygon-search": 10,
    "administrative-search": 12,
    "category-search": 13,
    "statistics-search": 14,
}
'''
    addition = marker + '''BROWSER_HEADERS = {
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://lbs.tianditu.gov.cn/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


class TiandituRequestError(RuntimeError):
    def __init__(self, code: str, message: str, metadata: Mapping[str, Any]) -> None:
        super().__init__(message)
        self.code = code
        self.metadata = dict(metadata)
'''
    text = replace_once(text, marker, addition, "constants")

    old_transport = '''def read_response(request: urllib.request.Request, timeout: int, max_bytes: int) -> tuple[int, bytes, str]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read(max_bytes + 1)
            content_type = str(response.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        content_type = str(exc.headers.get("Content-Type") or "") if exc.headers else ""
    except urllib.error.URLError as exc:
        raise RuntimeError("Tianditu upstream connection failed") from exc
    if len(raw) > max_bytes:
        raise RuntimeError(f"response exceeds acceptance.max_response_bytes={max_bytes}")
    if not 200 <= status < 300:
        message = raw[:1000].decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Tianditu upstream HTTP {status}: {message}")
    return status, raw, content_type
'''
    new_transport = r'''def safe_headers(headers: Mapping[str, Any] | None) -> dict[str, str]:
    if not headers:
        return {"content_type": "", "server": ""}
    return {
        "content_type": str(headers.get("Content-Type") or ""),
        "server": str(headers.get("Server") or "")[:200],
    }


def response_too_large(raw: bytes, max_bytes: int) -> None:
    if len(raw) > max_bytes:
        raise TiandituRequestError(
            "TIANDITU_RESPONSE_TOO_LARGE",
            f"response exceeds acceptance.max_response_bytes={max_bytes}",
            {"upstream_called": True},
        )


def read_response(request: urllib.request.Request, timeout: int, max_bytes: int) -> tuple[int, bytes, dict[str, Any]]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read(max_bytes + 1)
            header_meta = safe_headers(response.headers)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(max_bytes + 1)
        header_meta = safe_headers(exc.headers)
    except urllib.error.URLError as exc:
        raise TiandituRequestError(
            "TIANDITU_CONNECTION_ERROR",
            f"Tianditu upstream connection failed: {type(exc.reason).__name__}",
            {
                "upstream_called": True,
                "transport": "python-urllib",
                "transport_attempts": ["python-urllib"],
                "connection_error": type(exc.reason).__name__,
            },
        ) from exc
    response_too_large(raw, max_bytes)
    return status, raw, {
        **header_meta,
        "upstream_called": True,
        "transport": "python-urllib",
        "transport_attempts": ["python-urllib"],
    }


def parse_curl_headers(raw: str) -> dict[str, str]:
    blocks = [block for block in re.split(r"\r?\n\r?\n", raw.strip()) if block.strip()]
    block = blocks[-1] if blocks else ""
    headers: dict[str, str] = {}
    for line in block.splitlines()[1:]:
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().casefold()] = value.strip()
    return {
        "content_type": headers.get("content-type", ""),
        "server": headers.get("server", "")[:200],
    }


def curl_response(url: str, timeout: int, max_bytes: int) -> tuple[int, bytes, dict[str, Any]]:
    curl = shutil.which("curl")
    if not curl:
        raise TiandituRequestError(
            "TIANDITU_CURL_UNAVAILABLE",
            "curl transport is unavailable for the CloudWAF compatibility retry",
            {"upstream_called": False, "transport": "curl-http1.1"},
        )
    with tempfile.TemporaryDirectory() as tmp:
        body_path = Path(tmp) / "body.bin"
        header_path = Path(tmp) / "headers.txt"
        config_lines = [f'url = "{url.replace(chr(34), r"\"")}"']
        for name, value in BROWSER_HEADERS.items():
            config_lines.append(f'header = "{name}: {value}"')
        completed = subprocess.run(
            [
                curl,
                "--silent",
                "--show-error",
                "--http1.1",
                "--compressed",
                "--connect-timeout",
                str(min(timeout, 15)),
                "--max-time",
                str(timeout),
                "--dump-header",
                str(header_path),
                "--output",
                str(body_path),
                "--write-out",
                "%{http_code}",
                "--config",
                "-",
            ],
            input="\n".join(config_lines) + "\n",
            text=True,
            capture_output=True,
            timeout=timeout + 5,
            check=False,
        )
        raw = body_path.read_bytes() if body_path.exists() else b""
        response_too_large(raw, max_bytes)
        status_text = completed.stdout.strip()[-3:]
        status = int(status_text) if status_text.isdigit() else 0
        header_meta = parse_curl_headers(
            header_path.read_text(encoding="iso-8859-1", errors="replace")
            if header_path.exists()
            else ""
        )
        if completed.returncode != 0 and status == 0:
            raise TiandituRequestError(
                "TIANDITU_CONNECTION_ERROR",
                f"Tianditu curl transport failed with exit code {completed.returncode}",
                {
                    **header_meta,
                    "upstream_called": True,
                    "transport": "curl-http1.1",
                    "transport_attempts": ["curl-http1.1"],
                    "curl_exit_code": completed.returncode,
                },
            )
        return status, raw, {
            **header_meta,
            "upstream_called": True,
            "transport": "curl-http1.1",
            "transport_attempts": ["curl-http1.1"],
            "curl_exit_code": completed.returncode,
        }


def cloud_waf_blocked(status: int, raw: bytes, server: str) -> bool:
    sample = raw[:5000].decode("utf-8", errors="ignore").casefold()
    return status == 418 or "cloudwaf" in server.casefold() or "访问被拦截" in sample


def compact_response_message(raw: bytes) -> str:
    text = raw[:4000].decode("utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:500]
'''
    text = replace_once(text, old_transport, new_transport, "transport")

    old_call = '''def call_tianditu(operation: str, parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    post = build_post_str(operation, parameters)
    query = urllib.parse.urlencode(
        {
            "postStr": json.dumps(post, ensure_ascii=False, separators=(",", ":")),
            "type": "query",
            "tk": provider_key(),
        }
    )
    request = urllib.request.Request(
        f"{ENDPOINT}?{query}",
        headers={"Accept": "application/json", "User-Agent": "gpts-evidence-data-center-tianditu/1"},
        method="GET",
    )
    http_status, raw, content_type = read_response(request, timeout, max_bytes)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Tianditu upstream returned invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("Tianditu upstream JSON root must be an object")
    code, description = business_status(payload)
    if code is not None and code != "1000":
        raise RuntimeError(f"Tianditu business status {code}: {description or 'request failed'}")
    redacted = redact_direct_phones(dict(payload))
    result_count: int | None = None
    try:
        result_count = int(payload.get("count")) if payload.get("count") is not None else None
    except (TypeError, ValueError):
        result_count = None
    return redacted, {
        "http_status": http_status,
        "business_status": code,
        "content_type": content_type,
        "request_origin": "api.tianditu.gov.cn",
        "request_path": "/v2/search",
        "query_type": post["queryType"],
        "credential_mode": "query-token",
        "credential_secret_name": SECRET_ENV,
        "upstream_called": True,
        "result_count": result_count,
        "direct_phone_fields_redacted": True,
    }
'''
    new_call = r'''def request_metadata(post: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "request_origin": "api.tianditu.gov.cn",
        "request_path": "/v2/search",
        "query_type": post["queryType"],
        "credential_mode": "query-token",
        "credential_secret_name": SECRET_ENV,
        "runner_environment": str(os.getenv("RUNNER_ENVIRONMENT") or "unknown"),
        "direct_phone_fields_redacted": True,
    }


def call_tianditu(operation: str, parameters: Mapping[str, Any], timeout: int, max_bytes: int) -> tuple[Any, dict[str, Any]]:
    post = build_post_str(operation, parameters)
    query = urllib.parse.urlencode(
        {
            "postStr": json.dumps(post, ensure_ascii=False, separators=(",", ":")),
            "type": "query",
            "tk": provider_key(),
        },
        quote_via=urllib.parse.quote,
    )
    url = f"{ENDPOINT}?{query}"
    request = urllib.request.Request(url, headers=BROWSER_HEADERS, method="GET")
    http_status, raw, transport_meta = read_response(request, timeout, max_bytes)
    attempts = list(transport_meta.get("transport_attempts") or [])
    if cloud_waf_blocked(http_status, raw, str(transport_meta.get("server") or "")):
        try:
            http_status, raw, curl_meta = curl_response(url, timeout, max_bytes)
            attempts.extend(curl_meta.get("transport_attempts") or [])
            transport_meta = {**curl_meta, "transport_attempts": attempts}
        except TiandituRequestError as exc:
            exc.metadata = {
                **request_metadata(post),
                **transport_meta,
                **exc.metadata,
                "transport_attempts": attempts + list(exc.metadata.get("transport_attempts") or []),
                "waf_blocked": True,
                "first_http_status": http_status,
            }
            raise
    base_meta = {
        **request_metadata(post),
        **transport_meta,
        "http_status": http_status,
        "waf_blocked": cloud_waf_blocked(
            http_status, raw, str(transport_meta.get("server") or "")
        ),
    }
    if base_meta["waf_blocked"]:
        raise TiandituRequestError(
            "TIANDITU_WAF_BLOCKED",
            (
                "Tianditu CloudWAF blocked both bounded direct transports; "
                "use a mainland self-hosted runner via repository variable TIANDITU_RUNNER_LABEL"
            ),
            base_meta,
        )
    if not 200 <= http_status < 300:
        raise TiandituRequestError(
            "TIANDITU_HTTP_ERROR",
            f"Tianditu upstream HTTP {http_status}: {compact_response_message(raw)}",
            base_meta,
        )
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TiandituRequestError(
            "TIANDITU_INVALID_JSON",
            "Tianditu upstream returned invalid JSON",
            base_meta,
        ) from exc
    if not isinstance(payload, Mapping):
        raise TiandituRequestError(
            "TIANDITU_INVALID_JSON",
            "Tianditu upstream JSON root must be an object",
            base_meta,
        )
    code, description = business_status(payload)
    if code is not None and code != "1000":
        raise TiandituRequestError(
            "TIANDITU_BUSINESS_ERROR",
            f"Tianditu business status {code}: {description or 'request failed'}",
            {**base_meta, "business_status": code},
        )
    redacted = redact_direct_phones(dict(payload))
    result_count: int | None = None
    try:
        result_count = int(payload.get("count")) if payload.get("count") is not None else None
    except (TypeError, ValueError):
        result_count = None
    return redacted, {
        **base_meta,
        "business_status": code,
        "result_count": result_count,
    }
'''
    text = replace_once(text, old_call, new_call, "call")

    old_except = '''    except (RuntimeError, ValueError, urllib.error.URLError) as exc:
        failure = {"code": "TIANDITU_UPSTREAM_ERROR", "message": str(exc)}
'''
    new_except = '''    except TiandituRequestError as exc:
        metadata = dict(exc.metadata)
        failure = {"code": exc.code, "message": str(exc)}
    except ValueError as exc:
        failure = {"code": "TIANDITU_VALIDATION_ERROR", "message": str(exc)}
    except RuntimeError as exc:
        failure = {"code": "TIANDITU_CONFIGURATION_ERROR", "message": str(exc)}
'''
    text = replace_once(text, old_except, new_except, "execute-errors")

    old_render = '''    print(f"- Upstream called: `{str(bool(result['metadata'].get('upstream_called'))).lower()}`")
    print(f"- Snapshot SHA256: `{result['snapshot_sha256']}`")
'''
    new_render = '''    print(f"- Upstream called: `{str(bool(result['metadata'].get('upstream_called'))).lower()}`")
    if result["metadata"].get("http_status") is not None:
        print(f"- HTTP status: `{result['metadata']['http_status']}`")
    if result["metadata"].get("transport_attempts"):
        print(f"- Transport attempts: `{','.join(result['metadata']['transport_attempts'])}`")
    if result["metadata"].get("waf_blocked") is not None:
        print(f"- WAF blocked: `{str(bool(result['metadata']['waf_blocked'])).lower()}`")
    print(f"- Snapshot SHA256: `{result['snapshot_sha256']}`")
'''
    text = replace_once(text, old_render, new_render, "render")
    TASK.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    text = TEST.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'self.headers = {"Content-Type": "application/json"}',
        'self.headers = {"Content-Type": "application/json", "Server": "Tianditu"}',
        "fake-headers",
    )
    old_business = '''        with mock.patch.dict(os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True), mock.patch.object(
            module.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ):
            with self.assertRaisesRegex(RuntimeError, "business status 2001"):
                module.call_tianditu(
                    "administrative-search",
                    {"keyword": "学校", "specify": "156110108"},
                    30,
                    1000000,
                )
'''
    new_business = '''        with mock.patch.dict(os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True), mock.patch.object(
            module.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ):
            with self.assertRaisesRegex(module.TiandituRequestError, "business status 2001") as raised:
                module.call_tianditu(
                    "administrative-search",
                    {"keyword": "学校", "specify": "156110108"},
                    30,
                    1000000,
                )
            self.assertEqual(raised.exception.code, "TIANDITU_BUSINESS_ERROR")
'''
    text = replace_once(text, old_business, new_business, "business-test")
    insert = '''
    def test_waf_failure_records_real_upstream_attempt_and_curl_retry(self) -> None:
        ticket = self.ticket(
            "administrative-search",
            {"keyword": "学校", "specify": "福州市", "count": 1},
        )
        waf = module.TiandituRequestError(
            "TIANDITU_WAF_BLOCKED",
            "Tianditu CloudWAF blocked both bounded direct transports",
            {
                "upstream_called": True,
                "http_status": 418,
                "waf_blocked": True,
                "transport": "curl-http1.1",
                "transport_attempts": ["python-urllib", "curl-http1.1"],
            },
        )
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True
        ), mock.patch.object(module, "call_tianditu", side_effect=waf):
            ticket_path = Path(tmp) / "ticket.json"
            out = Path(tmp) / "out"
            ticket_path.write_text(json.dumps(ticket, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(module.execute(ticket_path, out), 1)
            result = json.loads((out / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["failure"]["code"], "TIANDITU_WAF_BLOCKED")
            self.assertTrue(result["metadata"]["upstream_called"])
            self.assertEqual(result["metadata"]["http_status"], 418)
            self.assertEqual(
                result["metadata"]["transport_attempts"],
                ["python-urllib", "curl-http1.1"],
            )

    def test_browser_compatible_headers_are_used(self) -> None:
        payload = {"count": "0", "status": {"infocode": 1000, "cndesc": "服务正常"}}
        with mock.patch.dict(os.environ, {"TIANDITU_API_KEY": "secret-value"}, clear=True), mock.patch.object(
            module.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ) as mocked:
            module.call_tianditu(
                "administrative-search",
                {"keyword": "学校", "specify": "福州市", "count": 1},
                30,
                1000000,
            )
            request = mocked.call_args.args[0]
            self.assertIn("Mozilla/5.0", request.headers["User-agent"])
            self.assertEqual(request.headers["Referer"], "https://lbs.tianditu.gov.cn/")
            self.assertNotIn("+", request.full_url.split("postStr=", 1)[1].split("&type=", 1)[0])
'''
    text = replace_once(text, '\n\nif __name__ == "__main__":\n', insert + '\n\nif __name__ == "__main__":\n', "new-tests")
    TEST.write_text(text, encoding="utf-8")


def patch_catalog() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    provider = catalog["providers"][0]
    provider["execution_policy"] = (
        "TIANDITU_API_KEY 仅在后端 tk 查询参数注入且不会写入日志或 Artifact；"
        "每张票据最多执行一次业务请求，遇到 CloudWAF 418 时仅追加一次固定 curl HTTP/1.1 兼容重试；"
        "记录真实 upstream_called、HTTP 状态、WAF 分类与传输尝试。若 GitHub 托管出口仍被拦截，"
        "可通过仓库变量 TIANDITU_RUNNER_LABEL 切换到中国大陆自托管 Runner。"
    )
    limits = provider["limits"]
    limits["transport_attempts_max"] = 2
    limits["cloud_waf_detection"] = True
    limits["arbitrary_proxy_urls_allowed"] = False
    limits["self_hosted_runner_supported"] = True
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_workflow() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    runs-on: ubuntu-24.04\n",
        "    runs-on: ${{ vars.TIANDITU_RUNNER_LABEL || 'ubuntu-24.04' }}\n",
        "runner-selection",
    )
    WORKFLOW.write_text(text, encoding="utf-8")


def main() -> int:
    patch_task()
    patch_tests()
    patch_catalog()
    patch_workflow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
