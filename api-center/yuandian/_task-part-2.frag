    if isinstance(value, Mapping):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        text = PHONE_RE.sub("[REDACTED_PHONE]", value)
        text = ID_RE.sub("[REDACTED_ID]", text)
        return EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    return value


def _execute_operation(operation: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    if operation == "catalog-capabilities":
        return {"provider": "yuandian-law", "catalog": CATALOG, "readonly_api_snapshot": SNAPSHOT}
    if operation == "catalog-live":
        category = parameters.get("category_id")
        rows = fetch_live_catalog(int(category) if category not in (None, "") else None,
                                  _bounded_int(parameters.get("page_size"), 200, 1, 200, "page_size"))
        return {
            "provider": "yuandian-law", "operation": operation, "api_count": len(rows),
            "snapshot_api_count": len(SNAPSHOT["apis"]), "rows": _redact(rows),
        }
    if operation == "invoke-readonly-api":
        route_key = str(parameters.get("route_key") or "")
        live = {row["route_key"]: row for row in fetch_live_catalog()}
        api = live.get(route_key)
        if api is None:
            raise ValueError("route_key is not present in the current official YuanDian catalog")
    else:
        api = FIXED_APIS[operation]
        route_key = str(api["route_key"])
    method = str(api["http_method"]).upper()
    api_key = _resolve_api_key()
    if not api_key:
        raise ValueError("YUANDIAN_API_KEY is required for YuanDian business API calls")
    arguments = dict(parameters.get("arguments") or {})
    timeout = _bounded_int(parameters.get("timeout_seconds"), 60, 5, 120, "timeout_seconds")
    max_bytes = _bounded_int(parameters.get("max_response_bytes"), 1_000_000, 1024, 5_000_000, "max_response_bytes")
    payload = _request_json(method, _fixed_url(route_key), api_key=api_key, arguments=arguments,
                            timeout=timeout, max_bytes=max_bytes)
    _business_success(payload)
    return {
        "provider": "yuandian-law", "operation": operation, "route_key": route_key,
        "http_method": method, "upstream_called": True,
        "response": _redact(payload), "direct_personal_identifiers_redacted": True,
    }


def _manifest(output_dir: Path) -> None:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "artifact-manifest.json":
            files.append({"path": str(path.relative_to(output_dir)), "size_bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(output_dir / "artifact-manifest.json", {"version": 1, "files": files})


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    try:
        validate_ticket(ticket)
        data = _execute_operation(str(ticket["operation"]), dict(ticket.get("parameters") or {}))
        snapshot = {
            "schema_version": "yuandian-snapshot-v1", "status": "API_YUANDIAN_COMPLETED",
            "task_id": ticket["task_id"], "provider": ticket["provider"], "operation": ticket["operation"],
            "ticket_sha256": canonical_sha(ticket), "data": data,
            "security": {"model_calls": 0, "arbitrary_urls_allowed": False, "arbitrary_headers_allowed": False,
                         "write_operations_allowed": False, "secret_values_included": False,
                         "direct_personal_identifiers_redacted": True},
        }
        write_json(output_dir / "yuandian-snapshot.json", snapshot)
        write_json(output_dir / "yuandian-audit.json", {"status": "PASS", "snapshot_sha256": canonical_sha(snapshot),
                                                         "model_calls": 0, "fixed_origin": OFFICIAL_ORIGIN})
        (output_dir / "yuandian-summary.md").write_text(
            "# API_YUANDIAN_COMPLETED\n\n"
            f"- Task ID: `{ticket['task_id']}`\n- Operation: `{ticket['operation']}`\n"
            f"- Snapshot SHA256: `{canonical_sha(snapshot)}`\n", encoding="utf-8")
        output("status", "API_YUANDIAN_COMPLETED")
        _manifest(output_dir)
        return 0
    except Exception as exc:
        failure = {
            "schema_version": "yuandian-snapshot-v1", "status": "API_YUANDIAN_FAILED",
            "task_id": str(ticket.get("task_id") or ""), "provider": str(ticket.get("provider") or ""),
            "operation": str(ticket.get("operation") or ""),
            "failure": {"code": "YUANDIAN_UPSTREAM_OR_REQUEST_FAILED", "error_type": type(exc).__name__,
                        "message": str(exc), "retryable": isinstance(exc, (OSError, TimeoutError, urllib.error.URLError))},
            "security": {"model_calls": 0, "arbitrary_urls_allowed": False, "arbitrary_headers_allowed": False,
                         "write_operations_allowed": False, "secret_values_included": False,
                         "direct_personal_identifiers_redacted": True},
        }
        write_json(output_dir / "yuandian-snapshot.json", failure)
        write_json(output_dir / "yuandian-error.json", {"error_type": type(exc).__name__, "message": str(exc),
                                                         "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-20000:]})
        output("status", "API_YUANDIAN_FAILED")
        _manifest(output_dir)
        return 1


def render(output_dir: Path, phase: str, artifact_url: str = "") -> int:
    status = json.loads((output_dir / "ticket-status.json").read_text(encoding="utf-8"))
    if phase == "accepted":
        print("## API_YUANDIAN_ACCEPTED")
        print(f"\n- Task ID: `{status.get('task_id')}`\n- Operation: `{status.get('operation')}`\n- Model calls: `0`")
        return 0
    if phase == "rejected":
        print("## API_YUANDIAN_REJECTED")
        print(f"\n- Reason: `{status.get('reason') or 'unknown'}`")
        return 0
    snapshot = json.loads((output_dir / "yuandian-snapshot.json").read_text(encoding="utf-8"))
    print(f"## {snapshot['status']}")
    print(f"\n- Task ID: `{snapshot.get('task_id')}`\n- Operation: `{snapshot.get('operation')}`")
    if snapshot["status"] == "API_YUANDIAN_COMPLETED":
        print(f"- Snapshot SHA256: `{canonical_sha(snapshot)}`\n- Artifact: {artifact_url or 'unavailable'}")
        print("\n```json")
        print(json.dumps(snapshot["data"], ensure_ascii=False, indent=2)[:45000])
        print("```")
    else:
        print(f"- Error: `{snapshot.get('failure', {}).get('message') or 'unknown'}`\n- Artifact: {artifact_url or 'unavailable'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--event-path", required=True); p.add_argument("--output-dir", required=True)
    p = sub.add_parser("execute"); p.add_argument("--ticket", required=True); p.add_argument("--output-dir", required=True)
    p = sub.add_parser("render"); p.add_argument("--output-dir", required=True); p.add_argument("--phase", choices=["accepted", "rejected", "completed"], required=True); p.add_argument("--artifact-url", default="")
    args = parser.parse_args()
    if args.command == "prepare": return prepare(Path(args.event_path), Path(args.output_dir))
    if args.command == "execute": return execute(Path(args.ticket), Path(args.output_dir))
    return render(Path(args.output_dir), args.phase, args.artifact_url)


if __name__ == "__main__":
    raise SystemExit(main())
