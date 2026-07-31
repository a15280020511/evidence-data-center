#!/usr/bin/env python3
"""Authorize, validate, de-duplicate, and render independent [api] tickets."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "api-ticket.schema.json"
MANIFEST_PATH = HERE / "connector-manifest.json"
CONNECTORS_DIR = HERE / "connectors"
MAX_BODY_CHARS = 100_000
ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
TRUSTED_STATE_PREFIXES = (
    "## API_ACCEPTED",
    "## API_COMPLETED",
    "## API_PARTIAL",
    "## API_BLOCKED",
    "## API_FAILED",
    "## API_REJECTED",
)


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


SCHEMA = _load_json(SCHEMA_PATH)
Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = Draft202012Validator(SCHEMA)


def _write_output(name: str, value: Any) -> None:
    path = os.getenv("GITHUB_OUTPUT")
    if not path:
        return
    text = str(value).replace("\n", " ").replace("\r", " ")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={text}\n")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _api_json(url: str) -> Any:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "independent-api-center",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _trusted_comments(repo: str, issue_number: int) -> Iterable[str]:
    if not repo or not os.getenv("GITHUB_TOKEN"):
        return []
    rows = _api_json(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments?per_page=100"
    )
    if not isinstance(rows, list):
        return []
    comments: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        user = row.get("user") if isinstance(row.get("user"), Mapping) else {}
        if str(user.get("login") or "") != "github-actions[bot]":
            continue
        body = str(row.get("body") or "").strip()
        if body.startswith(TRUSTED_STATE_PREFIXES):
            comments.append(body)
    return comments


def _duplicate_reason(
    repo: str,
    current_issue: int,
    packet: Mapping[str, Any],
    fingerprint: str,
) -> str:
    if not repo or not os.getenv("GITHUB_TOKEN"):
        return ""
    task_id = str(packet.get("task_id") or "")
    for page in range(1, 6):
        rows = _api_json(
            f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}"
        )
        if not isinstance(rows, list):
            break
        for row in rows:
            if not isinstance(row, Mapping) or row.get("pull_request"):
                continue
            number = int(row.get("number") or 0)
            if number == current_issue:
                continue
            if not str(row.get("title") or "").startswith("[api]"):
                continue
            try:
                prior = json.loads(
                    str(row.get("body") or ""),
                    parse_constant=_reject_constant,
                )
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(prior, Mapping):
                continue
            same_id = str(prior.get("task_id") or "") == task_id
            same_fingerprint = canonical_sha(prior) == fingerprint
            if same_id or same_fingerprint:
                reason = "task_id" if same_id else "ticket fingerprint"
                return f"duplicate {reason}; previously submitted in Issue #{number}"
        if len(rows) < 100:
            break
    return ""


def _connector_catalog(root: Path = HERE) -> dict[str, dict[str, Any]]:
    manifest = _load_json(root / "connector-manifest.json")
    rows = manifest.get("connectors") if isinstance(manifest, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError("connector-manifest.json has no connectors array")
    catalog: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        connector_id = str(row.get("id") or "")
        file_name = str(row.get("file") or "")
        if not connector_id or not file_name:
            continue
        path = root / file_name
        connector = _load_json(path)
        if not isinstance(connector, Mapping):
            raise ValueError(f"{file_name} must contain an object")
        if str(connector.get("id") or "") != connector_id:
            raise ValueError(f"connector manifest mismatch for {connector_id}")
        catalog[connector_id] = dict(connector)
    return catalog


def _render_path_parameters(
    connector: Mapping[str, Any],
    request_id: str,
    supplied: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, Any], str]:
    raw_specs = connector.get("path_parameters")
    specs = raw_specs if isinstance(raw_specs, Mapping) else {}
    query_parameters = dict(supplied)
    endpoint = str(connector["endpoint"])
    rendered: dict[str, str] = {}
    for raw_name, raw_spec in specs.items():
        name = str(raw_name)
        if name not in query_parameters:
            raise ValueError(f"request {request_id} is missing required path parameter: {name}")
        raw_value = query_parameters.pop(name)
        if isinstance(raw_value, (dict, list, tuple, set)) or raw_value is None:
            raise ValueError(f"request {request_id} path parameter {name} must be scalar")
        value = str(raw_value)
        max_length = int(raw_spec.get("max_length", 128))
        if not value or len(value) > max_length:
            raise ValueError(
                f"request {request_id} path parameter {name} has invalid length"
            )
        if value in {".", ".."} or any(
            char in value for char in ("/", "\\", "?", "#", "%", "\x00", "\r", "\n")
        ):
            raise ValueError(
                f"request {request_id} path parameter {name} contains a forbidden character"
            )
        pattern = str(raw_spec["pattern"])
        if re.fullmatch(pattern, value) is None:
            raise ValueError(
                f"request {request_id} path parameter {name} does not match its allowlist"
            )
        endpoint = endpoint.replace(
            "{" + name + "}", urllib.parse.quote(value, safe="-._~:")
        )
        rendered[name] = value
    if "{" in endpoint or "}" in endpoint:
        raise ValueError(f"request {request_id} leaves an unresolved path placeholder")
    return rendered, query_parameters, endpoint


def _validate_parameter_rules(
    connector: Mapping[str, Any],
    request_id: str,
    parameters: Mapping[str, Any],
) -> None:
    rules = connector.get("parameter_rules")
    if not isinstance(rules, Mapping):
        return
    property_rules = rules.get("properties")
    if isinstance(property_rules, Mapping):
        for name, spec_raw in property_rules.items():
            if name not in parameters or not isinstance(spec_raw, Mapping):
                continue
            value = parameters[name]
            expected = str(spec_raw.get("type") or "")
            type_ok = True
            if expected == "string":
                type_ok = isinstance(value, str)
            elif expected == "integer":
                type_ok = isinstance(value, int) and not isinstance(value, bool)
            elif expected == "number":
                type_ok = isinstance(value, (int, float)) and not isinstance(value, bool)
            elif expected == "boolean":
                type_ok = isinstance(value, bool)
            if expected and not type_ok:
                raise ValueError(f"request {request_id} parameter {name} must be {expected}")
            if "enum" in spec_raw and value not in list(spec_raw.get("enum") or []):
                raise ValueError(f"request {request_id} parameter {name} is outside its enum")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if "minimum" in spec_raw and value < spec_raw["minimum"]:
                    raise ValueError(f"request {request_id} parameter {name} is below minimum")
                if "maximum" in spec_raw and value > spec_raw["maximum"]:
                    raise ValueError(f"request {request_id} parameter {name} is above maximum")
            if isinstance(value, str):
                if "min_length" in spec_raw and len(value) < int(spec_raw["min_length"]):
                    raise ValueError(f"request {request_id} parameter {name} is too short")
                if "max_length" in spec_raw and len(value) > int(spec_raw["max_length"]):
                    raise ValueError(f"request {request_id} parameter {name} is too long")
                pattern = spec_raw.get("pattern")
                if pattern and re.fullmatch(str(pattern), value) is None:
                    raise ValueError(f"request {request_id} parameter {name} does not match its pattern")
    for group in rules.get("required_any_of") or []:
        present = [
            str(name)
            for name in group
            if str(name) in parameters and parameters[str(name)] not in ("", None)
        ]
        if not present:
            raise ValueError(
                f"request {request_id} requires at least one of {list(group)}"
            )
    for group in rules.get("mutually_exclusive") or []:
        present = [
            str(name)
            for name in group
            if str(name) in parameters and parameters[str(name)] not in ("", None)
        ]
        if len(present) > 1:
            raise ValueError(
                f"request {request_id} parameters are mutually exclusive: {present}"
            )


def _validate_and_plan(packet: Mapping[str, Any], root: Path = HERE) -> dict[str, Any]:
    catalog = _connector_catalog(root)
    request_ids: set[str] = set()
    planned: list[dict[str, Any]] = []
    required_secrets: set[str] = set()

    for index, raw_request in enumerate(packet["requests"]):
        request_row = dict(raw_request)
        request_id = str(request_row["request_id"])
        connector_id = str(request_row["connector_id"])
        if request_id in request_ids:
            raise ValueError(f"duplicate request_id: {request_id}")
        request_ids.add(request_id)

        connector = catalog.get(connector_id)
        if not connector:
            raise ValueError(f"requests[{index}].connector_id is not in the connector inventory")
        if connector.get("enabled") is not True:
            raise ValueError(f"connector {connector_id} is disabled")
        if str(connector.get("method") or "") != "GET":
            raise ValueError(
                f"connector {connector_id} is not eligible for [api] v1; only enabled GET connectors are allowed"
            )
        contract = connector.get("response_contract")
        if not isinstance(contract, Mapping):
            raise ValueError(
                f"connector {connector_id} lacks a declarative response_contract"
            )

        supplied_parameters = dict(request_row.get("parameters") or {})
        path_parameters, parameters, endpoint = _render_path_parameters(
            connector, request_id, supplied_parameters
        )
        allowed_parameters = {
            str(item) for item in connector.get("input_query_strings", [])
        }
        allowed_parameters.update(
            str(item) for item in (connector.get("path_parameters") or {})
        )
        secret_query = connector.get("secret_query")
        if isinstance(secret_query, Mapping):
            secret_name = str(secret_query.get("name") or "")
            secret_env = str(secret_query.get("env") or "")
            if secret_name in parameters:
                raise ValueError(
                    f"request {request_id} attempts to supply a backend-only secret parameter"
                )
            if secret_env:
                if not ENV_NAME_RE.fullmatch(secret_env):
                    raise ValueError(f"connector {connector_id} has an invalid secret env name")
                required_secrets.add(secret_env)
        secret_header = connector.get("secret_header")
        if isinstance(secret_header, Mapping):
            secret_env = str(secret_header.get("env") or "")
            if secret_env:
                if not ENV_NAME_RE.fullmatch(secret_env):
                    raise ValueError(f"connector {connector_id} has an invalid secret env name")
                required_secrets.add(secret_env)

        unexpected = sorted(set(supplied_parameters) - allowed_parameters)
        if unexpected:
            raise ValueError(
                f"request {request_id} contains non-allowlisted parameters: {unexpected}"
            )
        _validate_parameter_rules(connector, request_id, parameters)
        planned.append(
            {
                "request_id": request_id,
                "connector_id": connector_id,
                "endpoint": endpoint,
                "method": "GET",
                "path_parameters": path_parameters,
                "parameters": parameters,
                "allow_empty": bool(request_row.get("allow_empty", False)),
                "response_contract": dict(contract),
                "response_quality": dict(connector.get("response_quality") or {}),
                "quality_checks": dict(request_row.get("quality_checks") or {}),
                "connector_sha256": canonical_sha(connector),
            }
        )

    if len(required_secrets) > 1:
        raise ValueError(
            "ordinary [api] tickets may use only one keyed upstream API service; "
            "split cross-provider requests into separate tickets. Google managed "
            "provider tickets use their dedicated workflow and are exempt"
        )
    selected_secret = next(iter(required_secrets), "")

    acceptance = dict(packet["acceptance"])
    request_count = len(planned)
    minimum = int(acceptance["minimum_successful_requests"])
    if minimum > request_count:
        raise ValueError(
            "acceptance.minimum_successful_requests exceeds the number of requests"
        )
    if acceptance["require_all"] and minimum != request_count:
        raise ValueError(
            "require_all=true requires minimum_successful_requests to equal the request count"
        )
    return {
        "schema_version": "api-request-plan-v1",
        "task_id": str(packet["task_id"]),
        "objective": str(packet["objective"]),
        "ticket_sha256": canonical_sha(packet),
        "data_policy": dict(packet["data_policy"]),
        "acceptance": {
            "require_all": bool(acceptance["require_all"]),
            "minimum_successful_requests": minimum,
            "timeout_seconds": int(acceptance.get("timeout_seconds", 15)),
            "max_attempts": int(acceptance.get("max_attempts", 2)),
            "max_response_bytes_per_request": int(
                acceptance.get("max_response_bytes_per_request", 100_000)
            ),
        },
        "secret_isolation_policy": "one-keyed-upstream-per-ticket",
        "required_secret_environment_variable": selected_secret,
        "required_secret_environment_variables": sorted(required_secrets),
        "requests": planned,
    }


def _status(
    *,
    accepted: bool,
    reason: str,
    packet: Mapping[str, Any] | None,
    issue_number: int,
    fingerprint: str | None,
    request_count: int = 0,
) -> dict[str, Any]:
    return {
        "version": 1,
        "accepted": accepted,
        "reason": reason,
        "issue_number": issue_number,
        "task_id": str((packet or {}).get("task_id") or ""),
        "ticket_sha256": fingerprint,
        "request_count": request_count,
        "analysis_owner": "web-gpt",
        "execution_owner": "github-api-center",
        "model_calls": 0,
        "arbitrary_urls_allowed": False,
    }


def prepare(args: argparse.Namespace) -> int:
    event = _load_json(Path(args.event_path))
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    sender = event.get("sender") if isinstance(event.get("sender"), Mapping) else {}
    actor = str(sender.get("login") or "")
    owner = str(os.getenv("REPOSITORY_OWNER") or "")
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    issue_number = int(issue.get("number") or 0)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    packet: Mapping[str, Any] | None = None
    plan: Mapping[str, Any] | None = None
    fingerprint: str | None = None
    errors: list[str] = []
    if not title.startswith("[api]"):
        errors.append("Issue title must start with [api]")
    if not owner or actor != owner:
        errors.append("only the repository owner may submit API tickets")
    if len(body) > MAX_BODY_CHARS:
        errors.append(f"Issue body exceeds {MAX_BODY_CHARS} characters")
    try:
        parsed = json.loads(body, parse_constant=_reject_constant)
        if isinstance(parsed, Mapping):
            packet = parsed
        else:
            errors.append("Issue body JSON root must be an object")
    except (json.JSONDecodeError, ValueError) as exc:
        errors.append(f"invalid JSON: {exc}")

    if packet is not None:
        validation_errors = sorted(
            VALIDATOR.iter_errors(packet),
            key=lambda item: list(item.absolute_path),
        )
        for error in validation_errors[:20]:
            path = ".".join(str(item) for item in error.absolute_path) or "$"
            errors.append(f"{path}: {error.message}")
        if not validation_errors:
            fingerprint = canonical_sha(packet)
            try:
                plan = _validate_and_plan(packet)
            except (OSError, ValueError, TypeError) as exc:
                errors.append(str(exc))
            current_comments = list(
                _trusted_comments(os.getenv("GITHUB_REPOSITORY", ""), issue_number)
            )
            if any(
                body.startswith(("## API_COMPLETED", "## API_PARTIAL"))
                for body in current_comments
            ):
                errors.append("this API Issue already completed")
            elif any(
                body.startswith("## API_ACCEPTED") for body in current_comments
            ) and not any(
                body.startswith(("## API_FAILED", "## API_BLOCKED"))
                for body in current_comments
            ):
                errors.append("this API Issue is already accepted or running")
            duplicate = _duplicate_reason(
                os.getenv("GITHUB_REPOSITORY", ""),
                issue_number,
                packet,
                fingerprint,
            )
            if duplicate:
                errors.append(duplicate)

    accepted = not errors and packet is not None and plan is not None and fingerprint is not None
    reason = "validated independent API ticket" if accepted else "; ".join(errors)
    status = _status(
        accepted=accepted,
        reason=reason,
        packet=packet,
        issue_number=issue_number,
        fingerprint=fingerprint,
        request_count=len(plan["requests"]) if isinstance(plan, Mapping) else 0,
    )
    (output_dir / "ticket-status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Do not copy rejected or untrusted Issue bodies into Artifacts.
    if accepted and packet is not None:
        (output_dir / "ticket.json").write_text(
            json.dumps(packet, ensure_ascii=False, indent=2, allow_nan=False),
            encoding="utf-8",
        )
    if plan is not None:
        (output_dir / "request-plan.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False),
            encoding="utf-8",
        )
    for name in ("accepted", "reason", "task_id", "ticket_sha256", "request_count"):
        value = status.get(name, "")
        _write_output(name, str(value).lower() if isinstance(value, bool) else value)
    selected_secret = ""
    required_secret_count = 0
    if isinstance(plan, Mapping):
        selected_secret = str(plan.get("required_secret_environment_variable") or "")
        required_secret_count = len(plan.get("required_secret_environment_variables") or [])
    _write_output("required_secret_environment_variable", selected_secret)
    _write_output("required_secret_count", required_secret_count)
    return 0 if accepted else 2


def render(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    status = _load_json(output_dir / "ticket-status.json")
    heading = {"accepted": "API_ACCEPTED", "rejected": "API_REJECTED"}[args.phase]
    print(f"## {heading}")
    print()
    print(f"- Task ID: `{status.get('task_id') or 'unknown'}`")
    print(f"- Accepted: `{str(bool(status.get('accepted'))).lower()}`")
    print(f"- Request count: `{status.get('request_count') or 0}`")
    print(f"- Ticket SHA256: `{status.get('ticket_sha256') or 'none'}`")
    print("- Model calls: `0`")
    print("- Arbitrary URLs: `forbidden`")
    print(f"- Run: `{args.run_url}`")
    if args.phase == "rejected":
        print(f"- Reason: `{status.get('reason') or 'unknown'}`")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--event-path", required=True)
    prepare_parser.add_argument("--output-dir", default="api-artifacts")
    prepare_parser.set_defaults(func=prepare)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--phase", choices=["accepted", "rejected"], required=True)
    render_parser.add_argument("--output-dir", default="api-artifacts")
    render_parser.add_argument("--run-url", default="")
    render_parser.set_defaults(func=render)
    return root


if __name__ == "__main__":
    arguments = parser().parse_args()
    raise SystemExit(arguments.func(arguments))
