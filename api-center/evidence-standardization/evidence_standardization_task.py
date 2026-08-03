#!/usr/bin/env python3
"""Local, bounded evidence normalization and provenance provider."""
from __future__ import annotations

import difflib
import hashlib
import json
import math
import re
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from managed_provider_runtime import finish_execution, load_json, provider_row, run_cli, utc_now, validate_ticket  # noqa: E402

SCHEMA_PATH = HERE / "ticket.schema.json"
CATALOG_PATH = HERE / "provider-catalog.json"
MAX_RECORDS = 1000
MAX_CONTENT_CHARS = 200_000
MAX_GRAPH_NODES = 5000
MAX_GRAPH_EDGES = 20_000
MAX_PAIRWISE = 100_000
STIX_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}--[0-9a-fA-F-]{36}$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must be an array")
    return value


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _bounded_text(value: Any, name: str, maximum: int = MAX_CONTENT_CHARS, allow_empty: bool = False) -> str:
    text = str(value or "")
    if not allow_empty and not text.strip():
        raise ValueError(f"{name} must not be empty")
    if len(text) > maximum:
        raise ValueError(f"{name} exceeds {maximum} characters")
    return text


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalize_space(text: str) -> str:
    return "\n".join(" ".join(line.split()) for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip())


def _canonical_url(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    parsed = urlsplit(text)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("source_url must be a public HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ValueError("source_url credentials are prohibited")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("local source_url is prohibited")
    port = parsed.port
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, ""))


def _parse_time(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_evidence_records(parameters: Mapping[str, Any]) -> dict[str, Any]:
    records = _sequence(parameters.get("records"), "parameters.records")
    if not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError(f"records must contain 1 to {MAX_RECORDS} rows")
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(records):
        row = _mapping(raw, f"records[{index}]")
        source_id = _bounded_text(row.get("source_id"), f"records[{index}].source_id", 160).strip()
        content = _normalize_space(_bounded_text(row.get("content"), f"records[{index}].content"))
        title = _normalize_space(_bounded_text(row.get("title", ""), f"records[{index}].title", 1000, allow_empty=True))
        retrieved_at = _parse_time(row.get("retrieved_at"), f"records[{index}].retrieved_at")
        published_at = None
        if row.get("published_at") not in (None, ""):
            published_at = _parse_time(row.get("published_at"), f"records[{index}].published_at")
        source_url = _canonical_url(row.get("source_url"))
        metadata = row.get("metadata") or {}
        if not isinstance(metadata, Mapping) or len(metadata) > 50:
            raise ValueError("record metadata must be an object with at most 50 fields")
        payload = {
            "source_id": source_id,
            "source_url": source_url,
            "retrieved_at": retrieved_at,
            "published_at": published_at,
            "title": title,
            "content": content,
            "metadata": dict(metadata),
        }
        content_sha = _sha(content.encode("utf-8"))
        payload["content_sha256"] = content_sha
        payload["record_id"] = f"evidence-{_sha(_canonical_json({'source_id': source_id, 'source_url': source_url, 'retrieved_at': retrieved_at, 'content_sha256': content_sha}))[:24]}"
        normalized.append(payload)
    return {"record_count": len(normalized), "records": normalized, "schema": "normalized-evidence-record-v1"}


def _simhash(text: str) -> int:
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())[:50_000]
    if not tokens:
        return 0
    weights = [0] * 64
    for token in tokens:
        value = int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")
        for bit in range(64):
            weights[bit] += 1 if value & (1 << bit) else -1
    result = 0
    for bit, weight in enumerate(weights):
        if weight >= 0:
            result |= 1 << bit
    return result


def content_fingerprint(parameters: Mapping[str, Any]) -> dict[str, Any]:
    texts = _sequence(parameters.get("texts"), "parameters.texts")
    if not 1 <= len(texts) <= MAX_RECORDS:
        raise ValueError(f"texts must contain 1 to {MAX_RECORDS} rows")
    threshold = int(parameters.get("near_duplicate_hamming_threshold", 3))
    if not 0 <= threshold <= 16:
        raise ValueError("near_duplicate_hamming_threshold must be between 0 and 16")
    rows = []
    for index, value in enumerate(texts):
        text = _normalize_space(_bounded_text(value, f"texts[{index}]"))
        rows.append({"index": index, "sha256": _sha(text.encode("utf-8")), "simhash64": f"{_simhash(text):016x}", "characters": len(text)})
    exact: dict[str, list[int]] = {}
    for row in rows:
        exact.setdefault(row["sha256"], []).append(row["index"])
    exact_groups = [indices for indices in exact.values() if len(indices) > 1]
    near = []
    comparisons = 0
    for left in range(len(rows)):
        left_hash = int(rows[left]["simhash64"], 16)
        for right in range(left + 1, len(rows)):
            comparisons += 1
            if comparisons > MAX_PAIRWISE:
                raise ValueError("pairwise fingerprint comparisons exceed governed limit")
            distance = (left_hash ^ int(rows[right]["simhash64"], 16)).bit_count()
            if distance <= threshold and rows[left]["sha256"] != rows[right]["sha256"]:
                near.append({"left": left, "right": right, "hamming_distance": distance})
    return {"rows": rows, "exact_duplicate_groups": exact_groups, "near_duplicate_pairs": near, "comparisons": comparisons, "threshold": threshold}


def provenance_lineage(parameters: Mapping[str, Any]) -> dict[str, Any]:
    nodes_raw = _sequence(parameters.get("nodes"), "parameters.nodes")
    edges_raw = _sequence(parameters.get("edges"), "parameters.edges")
    if not 1 <= len(nodes_raw) <= MAX_GRAPH_NODES or len(edges_raw) > MAX_GRAPH_EDGES:
        raise ValueError("lineage graph exceeds governed limits")
    nodes: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(nodes_raw):
        row = _mapping(raw, f"nodes[{index}]")
        node_id = _bounded_text(row.get("id"), f"nodes[{index}].id", 160).strip()
        if node_id in nodes:
            raise ValueError(f"duplicate lineage node: {node_id}")
        nodes[node_id] = row
    outgoing = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for index, raw in enumerate(edges_raw):
        row = _mapping(raw, f"edges[{index}]")
        source = str(row.get("source") or "")
        target = str(row.get("target") or "")
        if source not in nodes or target not in nodes or source == target:
            raise ValueError("lineage edge references missing node or self-loop")
        outgoing[source].append(target)
        indegree[target] += 1
    queue = deque(sorted(node for node, count in indegree.items() if count == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for target in sorted(outgoing[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    cycles = len(order) != len(nodes)
    roots = sorted(node for node in nodes if all(node not in targets for targets in outgoing.values()))
    leaves = sorted(node for node, targets in outgoing.items() if not targets)
    return {"node_count": len(nodes), "edge_count": len(edges_raw), "acyclic": not cycles, "topological_order": order if not cycles else [], "roots": roots, "leaves": leaves, "status": "PASS" if not cycles else "FAIL"}


def timeline_version_diff(parameters: Mapping[str, Any]) -> dict[str, Any]:
    versions = _sequence(parameters.get("versions"), "parameters.versions")
    if not 2 <= len(versions) <= 200:
        raise ValueError("versions must contain 2 to 200 rows")
    rows = []
    for index, raw in enumerate(versions):
        row = _mapping(raw, f"versions[{index}]")
        timestamp = _parse_time(row.get("timestamp"), f"versions[{index}].timestamp")
        content = _normalize_space(_bounded_text(row.get("content"), f"versions[{index}].content"))
        rows.append({"timestamp": timestamp, "content": content, "sha256": _sha(content.encode("utf-8"))})
    rows.sort(key=lambda item: item["timestamp"])
    changes = []
    for previous, current in zip(rows, rows[1:]):
        before = previous["content"].splitlines()
        after = current["content"].splitlines()
        diff = list(difflib.ndiff(before, after))
        changes.append({"from": previous["timestamp"], "to": current["timestamp"], "changed": previous["sha256"] != current["sha256"], "added_lines": sum(line.startswith("+ ") for line in diff), "removed_lines": sum(line.startswith("- ") for line in diff), "from_sha256": previous["sha256"], "to_sha256": current["sha256"]})
    return {"version_count": len(rows), "versions": [{key: value for key, value in row.items() if key != "content"} for row in rows], "changes": changes}


def stix_bundle_validate(parameters: Mapping[str, Any]) -> dict[str, Any]:
    bundle = _mapping(parameters.get("bundle"), "parameters.bundle")
    if bundle.get("type") != "bundle" or not STIX_ID_RE.fullmatch(str(bundle.get("id") or "")):
        raise ValueError("bundle must be a STIX 2.1 bundle with a valid id")
    objects = _sequence(bundle.get("objects"), "bundle.objects")
    if len(objects) > MAX_RECORDS:
        raise ValueError("STIX bundle exceeds governed object limit")
    ids: set[str] = set()
    types: dict[str, int] = {}
    references: list[tuple[str, str, str]] = []
    errors: list[str] = []
    for index, raw in enumerate(objects):
        row = _mapping(raw, f"bundle.objects[{index}]")
        object_id = str(row.get("id") or "")
        object_type = str(row.get("type") or "")
        if not object_type or not STIX_ID_RE.fullmatch(object_id) or not object_id.startswith(object_type + "--"):
            errors.append(f"invalid object identity at index {index}")
            continue
        if object_id in ids:
            errors.append(f"duplicate object id: {object_id}")
        ids.add(object_id)
        types[object_type] = types.get(object_type, 0) + 1
        for key, value in row.items():
            if key.endswith("_ref") and isinstance(value, str):
                references.append((object_id, key, value))
            elif key.endswith("_refs") and isinstance(value, list):
                references.extend((object_id, key, str(item)) for item in value)
    unresolved = [{"source": source, "field": field, "target": target} for source, field, target in references if target not in ids]
    return {"object_count": len(objects), "type_counts": dict(sorted(types.items())), "duplicate_or_schema_errors": errors, "unresolved_internal_references": unresolved, "status": "PASS" if not errors and not unresolved else "FAIL", "network_used": False, "taxii_called": False}


def transfer_package_manifest(parameters: Mapping[str, Any]) -> dict[str, Any]:
    files = _sequence(parameters.get("files"), "parameters.files")
    if not 1 <= len(files) <= MAX_RECORDS:
        raise ValueError("files must contain 1 to 1000 rows")
    rows = []
    names = set()
    for index, raw in enumerate(files):
        row = _mapping(raw, f"files[{index}]")
        name = str(row.get("name") or "")
        if not SAFE_NAME_RE.fullmatch(name) or ".." in Path(name).parts or name in names:
            raise ValueError("manifest file name is unsafe or duplicated")
        names.add(name)
        size = int(row.get("bytes", -1))
        digest = str(row.get("sha256") or "").lower()
        if size < 0 or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("manifest bytes or sha256 is invalid")
        classification = str(row.get("classification") or "public")
        personal = row.get("contains_personal_data", False)
        if classification != "public" or personal is not False:
            raise ValueError("only public, non-personal evidence may enter this transfer contract")
        rows.append({"name": name, "bytes": size, "sha256": digest, "classification": classification, "contains_personal_data": False})
    rows.sort(key=lambda item: item["name"])
    return {"schema_version": "gpts-evidence-transfer-manifest-v1", "file_count": len(rows), "total_bytes": sum(row["bytes"] for row in rows), "files": rows, "manifest_sha256": _sha(_canonical_json(rows)), "secret_values_exposed": False}


def source_quality_profile(parameters: Mapping[str, Any]) -> dict[str, Any]:
    sources = _sequence(parameters.get("sources"), "parameters.sources")
    if not 1 <= len(sources) <= MAX_RECORDS:
        raise ValueError("sources must contain 1 to 1000 rows")
    weights = {"authority": 0.25, "directness": 0.25, "recency": 0.15, "corroboration": 0.2, "method_transparency": 0.15}
    rows = []
    for index, raw in enumerate(sources):
        row = _mapping(raw, f"sources[{index}]")
        source_id = _bounded_text(row.get("source_id"), f"sources[{index}].source_id", 160).strip()
        dimensions = {}
        for name in weights:
            value = float(row.get(name, -1))
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
            dimensions[name] = value
        score = sum(dimensions[name] * weight for name, weight in weights.items())
        label = "HIGH" if score >= 0.8 else "MEDIUM" if score >= 0.6 else "LOW"
        rows.append({"source_id": source_id, **dimensions, "quality_score": score, "quality_label": label})
    return {"weights": weights, "sources": rows, "high_quality_count": sum(row["quality_label"] == "HIGH" for row in rows), "decision_rule": "source quality informs weighting but does not establish truth"}


OPERATIONS = {
    "normalize-evidence-records": normalize_evidence_records,
    "content-fingerprint": content_fingerprint,
    "provenance-lineage": provenance_lineage,
    "timeline-version-diff": timeline_version_diff,
    "stix-bundle-validate": stix_bundle_validate,
    "transfer-package-manifest": transfer_package_manifest,
    "source-quality-profile": source_quality_profile,
}


def execute(ticket_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    ticket = load_json(ticket_path)
    validate_ticket(ticket, schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH)
    operation = str(ticket["operation"])
    parameters = dict(ticket.get("parameters") or {})
    started_at, started_perf = utc_now(), time.perf_counter()
    status = "INTEL_EVIDENCE_STANDARDIZATION_FAILED"
    failure: Mapping[str, Any] | None = None
    snapshot: Mapping[str, Any] | None = None
    metadata = {"upstream_called": False, "network_used": False, "credential_mode": "none", "secret_environment_variable": "", "requests_per_ticket_max": 0, "automatic_retry": False, "secret_values_exposed": False, "operation": operation}
    try:
        if operation == "catalog-capabilities":
            snapshot = {"provider": provider_row(CATALOG_PATH)}
        else:
            handler = OPERATIONS.get(operation)
            if handler is None:
                raise ValueError(f"unsupported operation: {operation}")
            snapshot = {"provider": "evidence-standardization", "operation": operation, "data": handler(parameters)}
        status = "INTEL_EVIDENCE_STANDARDIZATION_COMPLETED"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)[:2000]}
    return finish_execution(ticket=ticket, output_dir=output_dir, status=status, snapshot=snapshot, metadata=metadata, failure=failure, started_at=started_at, started_perf=started_perf, schema_prefix="evidence-standardization")


if __name__ == "__main__":
    raise SystemExit(run_cli(execute=execute, ticket_prefix="[intel-evidence-standardize]", schema_path=SCHEMA_PATH, catalog_path=CATALOG_PATH, status_schema="evidence-standardization-ticket-status-v1", display_name="Evidence Standardization"))
