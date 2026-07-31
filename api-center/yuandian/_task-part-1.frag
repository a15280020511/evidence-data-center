    ticket: Mapping[str, Any] | None = None
    try:
        parsed = json.loads(str(issue.get("body") or ""))
        if not isinstance(parsed, Mapping):
            raise ValueError("ticket body must be a JSON object")
        validate_ticket(parsed)
        if not str(issue.get("title") or "").startswith("[api-yuandian]"):
            raise ValueError("issue title must start with [api-yuandian]")
        ticket = dict(parsed)
        write_json(output_dir / "ticket.json", ticket)
        accepted = True
    except (json.JSONDecodeError, ValueError) as exc:
        reason = str(exc)
    status = {
        "schema_version": "yuandian-ticket-status-v1",
        "accepted": accepted,
        "reason": reason,
        "task_id": str((ticket or {}).get("task_id") or ""),
        "provider": str((ticket or {}).get("provider") or ""),
        "operation": str((ticket or {}).get("operation") or ""),
        "ticket_sha256": canonical_sha(ticket) if ticket else None,
        "model_calls": 0,
        "secret_values_exposed": False,
    }
    write_json(output_dir / "ticket-status.json", status)
    output("accepted", "true" if accepted else "false")
    output("reason", reason)
    return 0 if accepted else 1


def _resolve_api_key() -> str:
    for name in ("YUANDIAN_API_KEY", "YD_API_KEY"):
        value = str(os.getenv(name) or "").strip()
        if value:
            return value
    raw = str(os.getenv("API_CENTER_SECRETS_JSON") or "")
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        if isinstance(data, Mapping):
            for name in ("YUANDIAN_API_KEY", "YD_API_KEY"):
                value = str(data.get(name) or "").strip()
                if value:
                    return value
    return ""


def _fixed_url(route_key: str) -> str:
    if not ROUTE_RE.fullmatch(route_key):
        raise ValueError("route_key has an unsafe format")
    url = f"{OFFICIAL_ORIGIN}/open/{route_key}"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "open.chineselaw.com":
        raise ValueError("only the fixed YuanDian HTTPS origin is allowed")
    return url


def _read_json_response(request: urllib.request.Request, timeout: int, max_bytes: int) -> Any:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(max_bytes + 1)
        status = int(getattr(response, "status", 200))
    if len(raw) > max_bytes:
        raise ValueError(f"YuanDian response exceeds {max_bytes} bytes")
    if status < 200 or status >= 300:
        raise RuntimeError(f"YuanDian HTTP status {status}")
    return json.loads(raw.decode("utf-8-sig"))


def _request_json(method: str, url: str, *, api_key: str = "", arguments: Mapping[str, Any] | None = None,
                  timeout: int = 60, max_bytes: int = 1_000_000) -> Any:
    method = method.upper()
    if method not in {"GET", "POST"}:
        raise ValueError("only GET and POST YuanDian APIs are allowed")
    headers = {"Accept": "application/json", "User-Agent": "managed-yuandian-api-center/1"}
    if api_key:
        headers["X-API-Key"] = api_key
    body = None
    args = dict(arguments or {})
    if method == "GET":
        query = urllib.parse.urlencode(args, doseq=True)
        if query:
            url = f"{url}{'&' if '?' in url else '?'}{query}"
    else:
        headers["Content-Type"] = "application/json; charset=utf-8"
        body = json.dumps(args, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _read_json_response(urllib.request.Request(url, data=body, headers=headers, method=method), timeout, max_bytes)


def _catalog_rows(payload: Any) -> list[Mapping[str, Any]]:
    queue = [payload]
    while queue:
        value = queue.pop(0)
        if isinstance(value, list) and all(isinstance(row, Mapping) for row in value):
            return list(value)
        if isinstance(value, Mapping):
            for key in ("records", "list", "rows", "content", "items", "data"):
                candidate = value.get(key)
                if isinstance(candidate, (list, Mapping)):
                    queue.append(candidate)
    raise ValueError("YuanDian catalog response did not contain an API list")


def _normalize_catalog_row(row: Mapping[str, Any]) -> dict[str, Any] | None:
    route_key = str(row.get("routeKey") or row.get("route_key") or "")
    method = str(row.get("httpMethod") or row.get("method") or "").upper()
    if not ROUTE_RE.fullmatch(route_key) or method not in {"GET", "POST"}:
        return None
    return {
        "id": row.get("id"),
        "name": str(row.get("name") or row.get("apiName") or route_key),
        "category": str(row.get("categoryName") or row.get("category") or ""),
        "category_id": row.get("categoryId"),
        "route_key": route_key,
        "http_method": method,
        "description": str(row.get("description") or row.get("summary") or ""),
        "price": row.get("price"),
        "charge_type": row.get("chargeType"),
        "request_params": row.get("requestParams") or row.get("request_params") or [],
        "response_params": row.get("responseParams") or row.get("response_params") or [],
        "full_document": row.get("fullDocument") or "",
        "read_only": True,
    }


def fetch_live_catalog(category_id: int | None = None, page_size: int = 200) -> list[dict[str, Any]]:
    query = {"pageNum": 1, "pageSize": page_size, "sortBy": "latest"}
    if category_id is not None:
        query["categoryId"] = category_id
    url = f"{OFFICIAL_ORIGIN}/api/apis?{urllib.parse.urlencode(query)}"
    payload = _request_json("GET", url, timeout=30, max_bytes=5_000_000)
    rows = [_normalize_catalog_row(row) for row in _catalog_rows(payload)]
    return [row for row in rows if row is not None]


def _business_success(payload: Any) -> None:
    if not isinstance(payload, Mapping):
        return
    code = payload.get("code")
    if code is not None and str(code) not in {"0", "200", "201"}:
        raise RuntimeError(f"YuanDian business code {code}: {payload.get('message') or payload.get('msg') or ''}")
    status = str(payload.get("status") or "").lower()
    if status in {"failed", "failure", "error", "unauthorized", "forbidden"}:
        raise RuntimeError(f"YuanDian business status {status}")


def _redact(value: Any, key: str = "") -> Any:
    if SECRET_KEY_RE.search(key) or PERSONAL_KEY_RE.search(key):
        return "[REDACTED]"
