from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "prc-attributable-legal-risk-registry.json"
POLICY_FILES = (
    ROOT / "jurisdiction-scope-policy.json",
    ROOT / "prc-source-channel-policy.json",
    ROOT / "source-server-footprint-policy.json",
    REGISTRY_PATH,
)

BLOCKING_BOOLEAN_KEYS = {
    "contains_personal_data",
    "personal_data",
    "important_data",
    "restricted_geospatial_data",
    "commercial_secret",
    "state_secret",
    "nonpublic_data",
    "private_message_collection",
    "individual_profiling",
    "captcha_bypass",
    "waf_bypass",
    "rate_limit_bypass",
    "proxy_rotation",
    "origin_rotation",
    "credential_rotation",
    "write_operations",
    "trading",
    "account_control",
    "external_distribution",
    "raw_data_resale",
}

REVIEW_VALUES = {
    "unknown",
    "unclear",
    "external",
    "public_release",
    "resale",
    "commercial_service",
    "important_data",
    "restricted_geospatial",
    "personal_data",
    "commercial_secret",
    "nonpublic",
}

LOCAL_OPERATION_PREFIXES = (
    "catalog-",
    "quota-",
    "local-",
    "health-",
    "capabilities",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_output(key: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"{key}={value}\n")


def _walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, path + (str(key),))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, path + (str(index),))
    else:
        yield path, value


def _ticket_operation(ticket: dict[str, Any]) -> str:
    candidates: list[str] = []
    for path, value in _walk(ticket):
        if not isinstance(value, str):
            continue
        key = path[-1].lower() if path else ""
        if key in {"operation", "operation_id", "tool", "tool_name", "action"}:
            candidates.append(value.strip())
    return candidates[0] if candidates else "unknown"


def _is_local_operation(operation: str) -> bool:
    normalized = operation.strip().lower()
    return normalized == "local" or normalized.startswith(LOCAL_OPERATION_PREFIXES)


def _identify_ticket_provider(ticket: dict[str, Any], allowed: list[str]) -> str | None:
    allowed_lower = {item.lower(): item for item in allowed}
    matches: set[str] = set()
    for path, value in _walk(ticket):
        if not isinstance(value, str):
            continue
        key = path[-1].lower() if path else ""
        normalized = value.strip().lower()
        if key in {"provider", "provider_id", "connector", "connector_id", "source", "source_id"}:
            if normalized in allowed_lower:
                matches.add(allowed_lower[normalized])
        elif normalized in allowed_lower:
            matches.add(allowed_lower[normalized])
    if len(matches) == 1:
        return next(iter(matches))
    return None


def _ticket_risk_findings(ticket: dict[str, Any]) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    review: list[str] = []
    for path, value in _walk(ticket):
        key = path[-1].lower() if path else ""
        dotted = ".".join(path)
        if key in BLOCKING_BOOLEAN_KEYS and value is True:
            blocking.append(f"{dotted}=true")
        if key in {"distribution_scope", "data_classification", "authorization_status", "license_scope"}:
            normalized = str(value).strip().lower()
            if normalized in REVIEW_VALUES:
                review.append(f"{dotted}={normalized}")
    return sorted(set(blocking)), sorted(set(review))


def _validate_registry(registry: dict[str, Any]) -> None:
    assert registry.get("schema_version") == "prc-attributable-legal-risk-registry-v1"
    assert registry.get("status") == "production-control"
    assert registry.get("unknown_classification_action") == "REVIEW_REQUIRED"
    controls = registry.get("global_required_controls", [])
    assert len(controls) >= 10
    providers = registry.get("providers", {})
    workflows = registry.get("workflows", {})
    assert providers and workflows
    for provider_id, provider in providers.items():
        assert provider.get("prc_nexus") is True, provider_id
        assert provider.get("identity_attributable") is True, provider_id
        assert provider.get("identity_signals"), provider_id
        assert provider.get("trace_records"), provider_id
        assert provider.get("material_risk_triggers"), provider_id
        assert provider.get("authorization_basis"), provider_id
        assert provider.get("data_scope"), provider_id
        assert provider.get("channel_tier") in {"GREEN_DIRECT", "YELLOW_CONTROLLED", "ORANGE_DEDICATED"}, provider_id
        assert provider.get("automatic_decision") == "ALLOW_WITH_CONTROLS", provider_id
    for workflow_id, workflow in workflows.items():
        assert workflow_id.startswith(".github/workflows/")
        assert workflow.get("ticket_path")
        selection = workflow.get("provider_selection")
        assert selection in {"fixed", "ticket"}
        if selection == "fixed":
            assert workflow.get("provider_id") in providers
        else:
            candidates = workflow.get("provider_ids", [])
            assert candidates and all(item in providers for item in candidates)


def _policy_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in POLICY_FILES:
        if not path.is_file():
            raise FileNotFoundError(f"missing policy file: {path.name}")
        hashes[path.name] = _sha256_file(path)
    return hashes


def _preflight(workflow_id: str, ticket_path: Path, output_dir: Path) -> int:
    registry = _load_json(REGISTRY_PATH)
    _validate_registry(registry)
    workflow = registry.get("workflows", {}).get(workflow_id)
    ticket_exists = ticket_path.is_file()
    ticket: dict[str, Any] = _load_json(ticket_path) if ticket_exists else {}
    ticket_sha256 = _sha256_bytes(_canonical_bytes(ticket)) if ticket_exists else None
    operation = _ticket_operation(ticket)

    decision = "REVIEW_REQUIRED"
    reason_codes: list[str] = []
    provider_id: str | None = None
    provider: dict[str, Any] = {}
    blocking_findings: list[str] = []
    review_findings: list[str] = []

    if workflow is None:
        reason_codes.append("WORKFLOW_NOT_REGISTERED")
    elif not ticket_exists:
        reason_codes.append("PREPARED_TICKET_MISSING")
    else:
        if workflow.get("provider_selection") == "fixed":
            provider_id = str(workflow.get("provider_id"))
        else:
            provider_id = _identify_ticket_provider(ticket, list(workflow.get("provider_ids", [])))
            if provider_id is None:
                reason_codes.append("PROVIDER_IDENTITY_NOT_UNAMBIGUOUS")

        if provider_id:
            provider = registry.get("providers", {}).get(provider_id, {})
            if not provider:
                reason_codes.append("PROVIDER_NOT_REGISTERED")
            else:
                blocking_findings, review_findings = _ticket_risk_findings(ticket)
                if _is_local_operation(operation):
                    decision = "NOT_APPLICABLE"
                    reason_codes.append("LOCAL_OPERATION_NO_UPSTREAM_COLLECTION")
                elif blocking_findings:
                    decision = "BLOCK"
                    reason_codes.append("BLOCKING_DATA_OR_CAPABILITY_DECLARED")
                elif review_findings:
                    decision = "REVIEW_REQUIRED"
                    reason_codes.append("LEGAL_OR_LICENSE_SCOPE_REQUIRES_REVIEW")
                elif not provider.get("authorization_basis"):
                    decision = "REVIEW_REQUIRED"
                    reason_codes.append("AUTHORIZATION_BASIS_MISSING")
                else:
                    decision = str(provider.get("automatic_decision", "REVIEW_REQUIRED"))
                    reason_codes.extend(
                        [
                            "PRC_NEXUS_CONFIRMED",
                            "USER_IDENTITY_ATTRIBUTION_CONFIRMED",
                            "PROVIDER_TRACE_RECORDS_CONFIRMED",
                            "MATERIAL_LEGAL_OR_ACCOUNT_RISK_AUDITED",
                            "FIXED_READONLY_AUTHORIZED_PATH_REQUIRED",
                        ]
                    )

    accepted = decision in set(registry.get("approved_decisions", []))
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    audit = {
        "schema_version": "prc-attributable-legal-risk-audit-v1",
        "audit_id": _sha256_bytes(
            _canonical_bytes(
                {
                    "workflow_id": workflow_id,
                    "ticket_sha256": ticket_sha256,
                    "provider_id": provider_id,
                    "policy_hashes": _policy_hashes(),
                }
            )
        )[:24],
        "audited_at": now,
        "auditor": "repository-policy-engine",
        "workflow_id": workflow_id,
        "provider_id": provider_id,
        "ticket_path": str(ticket_path),
        "ticket_sha256": ticket_sha256,
        "operation": operation,
        "jurisdiction_profile": "PRC_STRICT" if provider else "UNRESOLVED",
        "prc_nexus": provider.get("prc_nexus") if provider else None,
        "identity_attribution_state": "ATTRIBUTABLE" if provider.get("identity_attributable") else "UNRESOLVED",
        "identity_signals": provider.get("identity_signals", []),
        "trace_records": provider.get("trace_records", []),
        "material_risk_state": "AUDITED" if provider else "UNRESOLVED",
        "material_risk_triggers": provider.get("material_risk_triggers", []),
        "authorization_basis": provider.get("authorization_basis"),
        "data_scope": provider.get("data_scope", []),
        "channel_tier": provider.get("channel_tier"),
        "distribution_scope": "INTERNAL_ONLY_UNLESS_SEPARATELY_REVIEWED",
        "blocking_findings": blocking_findings,
        "review_findings": review_findings,
        "required_controls": registry.get("global_required_controls", []),
        "decision": decision,
        "accepted": accepted,
        "reason_codes": sorted(set(reason_codes)),
        "policy_hashes": _policy_hashes(),
        "secret_or_real_name_values_recorded": False,
        "zero_risk_guarantee": False,
    }
    audit_path = output_dir / "prc-legal-risk-audit.json"
    _write_json(audit_path, audit)

    _write_output("accepted", "true" if accepted else "false")
    _write_output("decision", decision)
    _write_output("status", "PRC_LEGAL_RISK_AUDIT_PASSED" if accepted else "PRC_LEGAL_RISK_AUDIT_BLOCKED")
    _write_output("audit_path", str(audit_path))
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    return 0 if accepted else 2


def _render(audit_path: Path) -> int:
    audit = _load_json(audit_path)
    accepted = bool(audit.get("accepted"))
    heading = "## 中国大陆实名可追溯采集法律风险审计通过" if accepted else "## 中国大陆实名可追溯采集已阻断"
    print(heading)
    print()
    print(f"- 决策：`{audit.get('decision')}`")
    print(f"- Provider：`{audit.get('provider_id') or 'UNRESOLVED'}`")
    print(f"- 操作：`{audit.get('operation')}`")
    print(f"- 身份关联：`{audit.get('identity_attribution_state')}`")
    print(f"- 渠道等级：`{audit.get('channel_tier') or 'UNRESOLVED'}`")
    print(f"- 审计编号：`{audit.get('audit_id')}`")
    print(f"- 原因码：`{', '.join(audit.get('reason_codes', [])) or 'NONE'}`")
    print()
    if accepted:
        print("仅允许固定、只读、已授权、有限量的内部采集；不得对外发布、转售或处理个人信息、重要数据、受限测绘、商业秘密和非公开数据。")
    else:
        print("未通过审计前不会注入上游密钥，也不会发起采集请求。")
    return 0


def _validate() -> int:
    registry = _load_json(REGISTRY_PATH)
    _validate_registry(registry)
    _policy_hashes()
    print(
        json.dumps(
            {
                "status": "PASS",
                "providers": len(registry.get("providers", {})),
                "workflows": len(registry.get("workflows", {})),
                "unknown_action": registry.get("unknown_classification_action"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--workflow-id", required=True)
    preflight.add_argument("--ticket", required=True)
    preflight.add_argument("--output-dir", required=True)

    render = subparsers.add_parser("render")
    render.add_argument("--audit", required=True)

    subparsers.add_parser("validate")
    args = parser.parse_args()

    try:
        if args.command == "preflight":
            return _preflight(args.workflow_id, Path(args.ticket), Path(args.output_dir))
        if args.command == "render":
            return _render(Path(args.audit))
        return _validate()
    except Exception as exc:  # fail closed and avoid secret-bearing tracebacks
        _write_output("accepted", "false")
        _write_output("decision", "REVIEW_REQUIRED")
        _write_output("status", "PRC_LEGAL_RISK_AUDIT_ERROR")
        print(f"PRC legal-risk audit failed closed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
