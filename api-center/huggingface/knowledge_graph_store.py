#!/usr/bin/env python3
"""Build and synchronize a public-metadata global knowledge graph on Hugging Face."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlsplit

import pyarrow as pa
import pyarrow.parquet as pq
import requests
from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

HERE = Path(__file__).resolve().parent
API_CENTER = HERE.parent
REPO_ROOT = API_CENTER.parent
CONTROL = HERE / "global-knowledge-graph"
CONTRACT = CONTROL / "graph-store-contract.json"
PLAN = CONTROL / "source-harvest-plan.json"
REGISTRY = API_CENTER / "global-knowledge-registry"
INDEX = REGISTRY / "registry-index.json"
GRAPH = REGISTRY / "graph-contract.json"
REMOTE = "knowledge-graph/v1"
HF_TOKEN_ENV = "HF_TOKEN"
HF_REPO_ENV = "HF_GLOBAL_KNOWLEDGE_GRAPH_DATASET_REPO"
USER_AGENT = "evidence-data-center-global-knowledge-graph/1.1"

NODE_SCHEMA = pa.schema([
    pa.field(name, pa.string(), nullable=False)
    for name in (
        "kg_id", "node_type", "name", "source_id", "source_record_id",
        "canonical_ids_json", "provenance_url", "retrieved_at", "valid_from",
        "valid_to", "license", "rights", "content_hash", "language",
        "jurisdiction", "payload_json", "snapshot_date",
    )
])
EDGE_SCHEMA = pa.schema([
    pa.field("edge_id", pa.string(), nullable=False),
    pa.field("edge_type", pa.string(), nullable=False),
    pa.field("source_kg_id", pa.string(), nullable=False),
    pa.field("target_kg_id", pa.string(), nullable=False),
    pa.field("source_id", pa.string(), nullable=False),
    pa.field("provenance_url", pa.string(), nullable=False),
    pa.field("retrieved_at", pa.string(), nullable=False),
    pa.field("valid_from", pa.string(), nullable=False),
    pa.field("valid_to", pa.string(), nullable=False),
    pa.field("confidence", pa.float64(), nullable=False),
    pa.field("evidence_hash", pa.string(), nullable=False),
    pa.field("payload_json", pa.string(), nullable=False),
    pa.field("snapshot_date", pa.string(), nullable=False),
])
STATE_SCHEMA = pa.schema([
    pa.field("source_id", pa.string(), nullable=False),
    pa.field("status", pa.string(), nullable=False),
    pa.field("last_attempt_at", pa.string(), nullable=False),
    pa.field("last_success_at", pa.string(), nullable=False),
    pa.field("cursor", pa.string(), nullable=False),
    pa.field("record_count", pa.int64(), nullable=False),
    pa.field("content_hash", pa.string(), nullable=False),
    pa.field("error", pa.string(), nullable=False),
])


class GraphError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cjson(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    raw = value if isinstance(value, str) else cjson(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def clean(value: Any, limit: int = 2000) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def source_kg(source_id: str) -> str:
    return f"kg:source:{source_id}"


def node_kg(node_type: str, source_id: str, record_id: str) -> str:
    return f"kg:{node_type.lower()}:{digest(source_id + chr(31) + record_id)[:32]}"


def node(
    node_type: str,
    name: str,
    source_id: str,
    record_id: str,
    url: str,
    license_text: str,
    payload: Mapping[str, Any],
    canonical: Mapping[str, Any],
    retrieved: str | None = None,
    kg_id: str | None = None,
    jurisdiction: str = "",
) -> dict[str, Any]:
    retrieved = retrieved or now()
    row = {
        "kg_id": kg_id or node_kg(node_type, source_id, record_id),
        "node_type": node_type,
        "name": clean(name, 1000) or record_id,
        "source_id": source_id,
        "source_record_id": record_id,
        "canonical_ids_json": cjson(canonical),
        "provenance_url": clean(url),
        "retrieved_at": retrieved,
        "valid_from": "",
        "valid_to": "",
        "license": clean(license_text, 1000),
        "rights": clean(license_text),
        "content_hash": "",
        "language": "",
        "jurisdiction": clean(jurisdiction, 120),
        "payload_json": cjson(payload),
        "snapshot_date": retrieved[:10],
    }
    stable = {k: v for k, v in row.items() if k not in {"retrieved_at", "snapshot_date", "content_hash"}}
    row["content_hash"] = digest(stable)
    return row


def edge(
    edge_type: str,
    source_node: str,
    target_node: str,
    source_id: str,
    url: str,
    retrieved: str | None = None,
) -> dict[str, Any]:
    retrieved = retrieved or now()
    evidence = {
        "type": edge_type,
        "source": source_node,
        "target": target_node,
        "source_id": source_id,
        "url": url,
    }
    ev_hash = digest(evidence)
    return {
        "edge_id": f"kg:edge:{ev_hash[:32]}",
        "edge_type": edge_type,
        "source_kg_id": source_node,
        "target_kg_id": target_node,
        "source_id": source_id,
        "provenance_url": clean(url),
        "retrieved_at": retrieved,
        "valid_from": "",
        "valid_to": "",
        "confidence": 1.0,
        "evidence_hash": ev_hash,
        "payload_json": "{}",
        "snapshot_date": retrieved[:10],
    }


def state(source_id: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "status": "never",
        "last_attempt_at": "",
        "last_success_at": "",
        "cursor": "",
        "record_count": 0,
        "content_hash": "",
        "error": "",
    }


def registry_rows(index: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in index["category_files"]:
        raw = str(item["path"])
        if not raw.startswith("api-center/global-knowledge-registry/"):
            raise GraphError("registry path escaped control root")
        payload = load(REPO_ROOT / raw)
        source_rows = payload.get("sources")
        if not isinstance(source_rows, list):
            raise GraphError(f"registry category has no sources: {raw}")
        if len(source_rows) != payload["source_count"] or payload["source_count"] != item["source_count"]:
            raise GraphError(f"invalid registry category {raw}")
        rows.extend(source_rows)
    ids = [str(row.get("source_id") or "") for row in rows]
    if len(rows) != index["source_count"] or "" in ids or len(ids) != len(set(ids)):
        raise GraphError("registry source count or IDs are invalid")
    return rows


def seed_nodes(index: Mapping[str, Any]) -> list[dict[str, Any]]:
    retrieved = now()
    result: list[dict[str, Any]] = []
    default_rights = (
        "Source-specific terms apply; registry inclusion does not grant content reuse rights."
    )
    for row in registry_rows(index):
        source_id = str(row["source_id"])
        regions = row.get("regions") or []
        license_text = (
            row.get("license_note")
            or row.get("license_policy")
            or row.get("license")
            or default_rights
        )
        canonical = row.get("canonical_ids") or []
        result.append(
            node(
                "Source",
                str(row.get("name") or source_id),
                source_id,
                source_id,
                str(row.get("official_url") or row.get("api_url") or ""),
                str(license_text),
                row,
                {"registry_source_id": [source_id], "canonical_families": canonical},
                retrieved,
                source_kg(source_id),
                str(regions[0]) if regions else "",
            )
        )
    return result


def validate() -> dict[str, Any]:
    contract, plan, index, graph = load(CONTRACT), load(PLAN), load(INDEX), load(GRAPH)
    if contract.get("schema_version") != "hf-global-knowledge-graph-store-v1":
        raise GraphError("invalid store contract")
    if contract.get("status") != "production-control":
        raise GraphError("store contract is not production-control")
    policy = contract["payload_policy"]
    if not policy["public_metadata_only"] or not policy["open_or_source_declared_reusable_only"]:
        raise GraphError("public metadata policy disabled")
    for key in (
        "patient_level_data_allowed",
        "personal_profiling_allowed",
        "paywall_bypass_allowed",
        "restricted_data_copying_allowed",
        "secrets_in_payload_allowed",
    ):
        if policy[key]:
            raise GraphError(f"forbidden policy enabled: {key}")
    governance = contract["governance"]
    if governance["direct_center_to_center_calls_allowed"] or governance["write_operations_to_upstreams_allowed"]:
        raise GraphError("forbidden connection or upstream write enabled")

    active = plan["active_sources"]
    if len(active) != 5 or len({row["source_id"] for row in active}) != 5:
        raise GraphError("five unique backbone sources required")
    for row in active:
        parsed = urlsplit(row["endpoint"])
        if parsed.scheme != "https" or not parsed.netloc or row["credential_mode"] != "none":
            raise GraphError(f"invalid active source {row['source_id']}")

    if index["source_count"] != 249 or index["category_file_count"] != 14:
        raise GraphError("registry count changed unexpectedly")
    if len(index["category_files"]) != 14:
        raise GraphError("registry category file count mismatch")
    if len(graph["node_types"]) != 32 or len(graph["edge_types"]) != 31:
        raise GraphError("graph contract count changed unexpectedly")
    if not {"Source", "Collection", "Standard", "Dataset"} <= set(graph["node_types"]):
        raise GraphError("graph contract lacks required node types")
    if "REGISTERED_IN" not in graph["edge_types"]:
        raise GraphError("graph contract lacks REGISTERED_IN")

    seeds = seed_nodes(index)
    if len(seeds) != 249 or len({row["kg_id"] for row in seeds}) != 249:
        raise GraphError("seed graph is invalid")
    return {
        "contract": contract,
        "plan": plan,
        "index": index,
        "graph": graph,
        "seeds": seeds,
        "contract_sha256": digest(contract),
        "plan_sha256": digest(plan),
        "registry_sha256": digest(index),
        "graph_sha256": digest(graph),
    }


def to_table(rows: list[Mapping[str, Any]], schema: pa.Schema) -> pa.Table:
    if rows:
        return pa.Table.from_pylist(rows, schema=schema)
    return pa.Table.from_arrays([pa.array([], type=f.type) for f in schema], schema=schema)


def write_parquet(path: Path, rows: list[Mapping[str, Any]], schema: pa.Schema) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = to_table(rows, schema)
    pq.write_table(value, path, compression="zstd", use_dictionary=False)
    return {
        "rows": value.num_rows,
        "columns": value.num_columns,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def read_parquet(path: Path, schema: pa.Schema) -> list[dict[str, Any]]:
    if pq.read_schema(path) != schema:
        raise GraphError(f"schema mismatch: {path.name}")
    value = pq.read_table(path)
    if any(column.null_count for column in value.columns):
        raise GraphError(f"null values: {path.name}")
    return value.to_pylist()


def merge(
    old: list[Mapping[str, Any]],
    new: list[Mapping[str, Any]],
    key: str,
) -> list[dict[str, Any]]:
    rows = {str(row[key]): dict(row) for row in old}
    rows.update({str(row[key]): dict(row) for row in new})
    if "" in rows:
        raise GraphError(f"empty {key}")
    return [rows[item] for item in sorted(rows)]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def first_text(elem: ET.Element, names: set[str]) -> str:
    for child in elem.iter():
        if local_name(child.tag) in names and child.text and child.text.strip():
            return child.text.strip()
    return ""


def registered_edge(
    source: Mapping[str, Any],
    child: Mapping[str, Any],
    url: str,
    retrieved: str,
) -> dict[str, Any]:
    return edge(
        str(source["edge_type"]),
        str(child["kg_id"]),
        source_kg(str(source["source_id"])),
        str(source["source_id"]),
        url,
        retrieved,
    )


def parse_re3data(raw: bytes, src: Mapping[str, Any], at: str):
    root = ET.fromstring(raw)
    records = [elem for elem in root.iter() if local_name(elem.tag) == "repository"]
    nodes, edges = [], []
    for item in records[: int(src["max_records"])]:
        rid = first_text(item, {"id", "repositoryid", "repositoryidentifier"})
        name = first_text(item, {"name", "repositoryname", "title"})
        if not rid:
            continue
        url = first_text(item, {"link", "repositoryurl", "url"}) or f"https://www.re3data.org/repository/{rid}"
        child = node(
            "Collection", name or rid, str(src["source_id"]), rid, url,
            str(src["license"]), {"name": name}, {"re3data": [rid]}, at,
        )
        nodes.append(child)
        edges.append(registered_edge(src, child, url, at))
    return nodes, edges, ""


def parse_ols(raw: bytes, src: Mapping[str, Any], at: str):
    records = (json.loads(raw).get("_embedded") or {}).get("ontologies") or []
    nodes, edges = [], []
    for item in records[: int(src["max_records"])]:
        cfg = item.get("config") or {}
        rid = str(item.get("ontologyId") or cfg.get("id") or "")
        if not rid:
            continue
        url = f"https://www.ebi.ac.uk/ols4/ontologies/{rid}"
        child = node(
            "Collection", str(cfg.get("title") or rid), str(src["source_id"]), rid,
            url, str(src["license"]), item, {"ontology_id": [rid]}, at,
        )
        nodes.append(child)
        edges.append(registered_edge(src, child, url, at))
    return nodes, edges, ""


def parse_obo(raw: bytes, src: Mapping[str, Any], at: str):
    data = json.loads(raw)
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = data.get("@graph") or data.get("ontologies") or data.get("data") or []
    else:
        records = []
    nodes, edges = [], []
    for item in records[: int(src["max_records"])]:
        rid = str(item.get("id") or item.get("ontology") or item.get("prefix") or "")
        if not rid:
            continue
        url = str(item.get("homepage") or item.get("@id") or f"https://obofoundry.org/ontology/{rid}.html")
        child = node(
            "Collection", str(item.get("title") or item.get("label") or rid),
            str(src["source_id"]), rid, url, str(item.get("license") or src["license"]),
            item, {"obo_prefix": [rid]}, at,
        )
        nodes.append(child)
        edges.append(registered_edge(src, child, url, at))
    return nodes, edges, ""


def parse_optimade(raw: bytes, src: Mapping[str, Any], at: str):
    nodes, edges = [], []
    for item in (json.loads(raw).get("data") or [])[: int(src["max_records"])]:
        attrs = item.get("attributes") or {}
        rid = str(item.get("id") or "")
        if not rid:
            continue
        url = str(attrs.get("base_url") or attrs.get("base_url_stable") or "https://providers.optimade.org/")
        child = node(
            "Source", str(attrs.get("name") or rid), str(src["source_id"]), rid,
            url, str(src["license"]), item, {"optimade_provider": [rid]}, at,
        )
        nodes.append(child)
        edges.append(registered_edge(src, child, url, at))
    return nodes, edges, ""


def parse_fairsharing(raw: bytes, src: Mapping[str, Any], at: str):
    root = ET.fromstring(raw)
    nodes, edges, cursor = [], [], ""
    records = [elem for elem in root.iter() if local_name(elem.tag) == "record"]
    for record in records[: int(src["max_records"])]:
        header = next((elem for elem in record if local_name(elem.tag) == "header"), None)
        metadata = next((elem for elem in record if local_name(elem.tag) == "metadata"), None)
        if header is None or metadata is None:
            continue
        rid = first_text(header, {"identifier"})
        if not rid:
            continue
        titles = [
            elem.text.strip() for elem in metadata.iter()
            if local_name(elem.tag) == "title" and elem.text
        ]
        types = [
            elem.text.strip().lower() for elem in metadata.iter()
            if local_name(elem.tag) == "type" and elem.text
        ]
        node_type = (
            "Standard" if any("standard" in item for item in types)
            else "Dataset" if any(word in item for item in types for word in ("database", "repository", "dataset"))
            else "Source"
        )
        suffix = rid.rsplit(":", 1)[-1]
        url = f"https://fairsharing.org/{suffix}" if suffix.isdigit() else "https://fairsharing.org/"
        child = node(
            node_type, titles[0] if titles else rid, str(src["source_id"]), rid,
            url, str(src["license"]), {"titles": titles, "types": types},
            {"fairsharing_oai": [rid]}, at,
        )
        nodes.append(child)
        edges.append(registered_edge(src, child, url, at))
    for elem in root.iter():
        if local_name(elem.tag) == "resumptiontoken" and elem.text:
            cursor = elem.text.strip()
            break
    return nodes, edges, cursor


PARSERS = {
    "re3data": parse_re3data,
    "ols": parse_ols,
    "obo-foundry": parse_obo,
    "optimade-providers": parse_optimade,
    "fairsharing-oai": parse_fairsharing,
}


def get(url: str, timeout: int, max_bytes: int) -> tuple[bytes, str, int]:
    original = urlsplit(url)
    with requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        timeout=timeout,
        allow_redirects=True,
        stream=True,
    ) as response:
        final = urlsplit(response.url)
        if final.scheme != "https" or final.hostname != original.hostname:
            raise GraphError("redirect escaped fixed host")
        response.raise_for_status()
        chunks, total = [], 0
        for block in response.iter_content(65536):
            if not block:
                continue
            total += len(block)
            if total > max_bytes:
                raise GraphError("response too large")
            chunks.append(block)
        return b"".join(chunks), response.url, response.status_code


def harvest(
    src: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
    limits: Mapping[str, Any],
):
    sid, attempted = str(src["source_id"]), now()
    current = dict(previous or state(sid))
    current.update({"source_id": sid, "status": "failed", "last_attempt_at": attempted, "error": ""})
    receipt: dict[str, Any] = {
        "source_id": sid, "status": "FAILED", "network_used": False,
        "request_count": 0, "records": 0,
    }
    try:
        url = str(src["endpoint"])
        if sid == "fairsharing-oai" and current.get("cursor"):
            url = (
                "https://api.fairsharing.org/oai?verb=ListRecords&resumptionToken="
                + quote(str(current["cursor"]), safe="")
            )
        raw, final, status = get(
            url, int(limits["timeout_seconds"]), int(limits["max_response_bytes"])
        )
        nodes, edges, cursor = PARSERS[sid](raw, src, attempted)
        if not nodes:
            raise GraphError("no usable records")
        current.update({
            "status": "success", "last_success_at": attempted, "cursor": cursor,
            "record_count": len(nodes),
            "content_hash": digest([item["content_hash"] for item in nodes]),
            "error": "",
        })
        receipt.update({
            "status": "PASS", "network_used": True, "request_count": 1,
            "records": len(nodes), "edges": len(edges), "http_status": status,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(), "final_url": final,
        })
        return nodes, edges, current, receipt
    except Exception as exc:
        current["error"] = clean(f"{type(exc).__name__}: {exc}", 1500)
        if sid == "fairsharing-oai":
            current["cursor"] = ""
        receipt["error"] = current["error"]
        return [], [], current, receipt


def bootstrap(output: Path) -> dict[str, Any]:
    control = validate()
    source_states = [state(item["source_id"]) for item in control["plan"]["active_sources"]]
    files = {
        "nodes": write_parquet(output / "nodes.parquet", control["seeds"], NODE_SCHEMA),
        "edges": write_parquet(output / "edges.parquet", [], EDGE_SCHEMA),
        "states": write_parquet(output / "source-state.parquet", source_states, STATE_SCHEMA),
    }
    receipt = {
        "status": "GLOBAL_KNOWLEDGE_GRAPH_BOOTSTRAP_VALIDATED",
        "registered_source_node_count": 249, "edge_count": 0,
        "active_backbone_source_count": 5, "node_type_count": 32,
        "edge_type_count": 31, "files": files, "public_metadata_only": True,
        "full_text_copied": False, "patient_level_data_included": False,
        "secret_values_exposed": False, "network_used": False, "model_calls": 0,
    }
    dump(output / "validation-receipt.json", receipt)
    return receipt


def existing(repo: str, token: str, output: Path):
    api = HfApi()
    visible = set(api.list_repo_files(repo_id=repo, repo_type="dataset", token=token))
    result = []
    for name, schema in (
        ("nodes", NODE_SCHEMA), ("edges", EDGE_SCHEMA), ("source-state", STATE_SCHEMA),
    ):
        remote = f"{REMOTE}/{name}.parquet"
        if remote not in visible:
            result.append([])
            continue
        local = hf_hub_download(
            repo_id=repo, repo_type="dataset", filename=remote,
            token=token, force_download=True,
        )
        copied = output / f"existing-{name}.parquet"
        copied.write_bytes(Path(local).read_bytes())
        result.append(read_parquet(copied, schema))
    return result


def sync(output: Path) -> dict[str, Any]:
    control = validate()
    token = os.getenv(HF_TOKEN_ENV, "").strip()
    if not token:
        raise GraphError("HF_TOKEN is not configured")
    api = HfApi()
    owner = str((api.whoami(token=token) or {}).get("name") or "")
    configured = os.getenv(HF_REPO_ENV, "").strip()
    repo = configured or f"{owner}/global-knowledge-graph"
    if not owner or "/" not in repo:
        raise GraphError("invalid Hugging Face Dataset repository")

    api.create_repo(
        repo_id=repo, repo_type="dataset", private=False, exist_ok=True, token=token,
    )
    info = api.repo_info(repo_id=repo, repo_type="dataset", token=token)
    if bool(getattr(info, "private", False)):
        raise GraphError("knowledge graph Dataset must be public")

    old_nodes, old_edges, old_states = existing(repo, token, output)
    state_map = {row["source_id"]: row for row in old_states}
    new_nodes = list(control["seeds"])
    new_edges, new_states, receipts = [], [], []
    for src in control["plan"]["active_sources"]:
        new_nodes.append(node(
            "Source", src["name"], src["source_id"], src["source_id"],
            src["endpoint"].split("?")[0], src["license"], src,
            {"backbone_source_id": [src["source_id"]]},
            kg_id=source_kg(src["source_id"]),
        ))
        nodes, edges, source_state, receipt = harvest(
            src, state_map.get(src["source_id"]), control["contract"]["limits"]
        )
        new_nodes.extend(nodes)
        new_edges.extend(edges)
        new_states.append(source_state)
        receipts.append(receipt)

    successes = sum(item["status"] == "PASS" for item in receipts)
    minimum = int(control["plan"]["schedule_policy"]["minimum_successful_sources"])
    if successes < minimum:
        raise GraphError(f"only {successes} backbone sources succeeded")

    nodes = merge(old_nodes, new_nodes, "kg_id")
    edges = merge(old_edges, new_edges, "edge_id")
    states = merge(old_states, new_states, "source_id")
    data_dir = output / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    node_meta = write_parquet(data_dir / "nodes.parquet", nodes, NODE_SCHEMA)
    edge_meta = write_parquet(data_dir / "edges.parquet", edges, EDGE_SCHEMA)
    state_meta = write_parquet(data_dir / "source-state.parquet", states, STATE_SCHEMA)
    manifest = {
        "schema_version": "global-public-metadata-knowledge-graph-manifest-v1",
        "generated_at": now(), "repository": repo, "node_count": len(nodes),
        "edge_count": len(edges), "source_state_count": len(states),
        "registered_source_node_count": 249, "successful_source_count": successes,
        "failed_source_count": len(receipts) - successes,
        "source_receipts": receipts,
        "files": {"nodes": node_meta, "edges": edge_meta, "states": state_meta},
        "public_metadata_only": True, "full_text_copied": False,
        "patient_level_data_included": False, "secret_values_exposed": False,
        "model_calls": 0,
    }
    dump(data_dir / "manifest.json", manifest)
    readme = f"""---
license: other
pretty_name: Global Public Metadata Knowledge Graph
tags:
- knowledge-graph
- metadata
- provenance
---

# Global Public Metadata Knowledge Graph

Public metadata only. Full text, patient-level data, restricted content,
credentials and personal profiles are excluded.

- Nodes: {len(nodes)}
- Edges: {len(edges)}
- Successful backbone sources: {successes}
- Snapshot: {manifest['generated_at']}
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    operations = [
        CommitOperationAdd(path_in_repo=f"{REMOTE}/{name}", path_or_fileobj=path)
        for name, path in (
            ("nodes.parquet", data_dir / "nodes.parquet"),
            ("edges.parquet", data_dir / "edges.parquet"),
            ("source-state.parquet", data_dir / "source-state.parquet"),
            ("manifest.json", data_dir / "manifest.json"),
        )
    ]
    operations.append(CommitOperationAdd(
        path_in_repo="README.md", path_or_fileobj=output / "README.md"
    ))
    commit = api.create_commit(
        repo_id=repo, repo_type="dataset", operations=operations,
        commit_message=f"Refresh public metadata graph {manifest['generated_at']}",
        token=token,
    )
    receipt = {
        **manifest, "status": "GLOBAL_KNOWLEDGE_GRAPH_SYNCHRONIZED",
        "commit_oid": str(getattr(commit, "oid", "") or ""),
        "network_used": True,
        "upstream_request_count": sum(item["request_count"] for item in receipts),
        "data_preserved_on_sync": True,
    }
    dump(output / "sync-receipt.json", receipt)
    return receipt


def render(output: Path) -> str:
    path = next((
        item for item in (
            output / "sync-receipt.json",
            output / "validation-receipt.json",
            output / "failure-receipt.json",
        ) if item.exists()
    ), None)
    if path is None:
        raise GraphError("no receipt found")
    row = load(path)
    lines = [
        "## 全球知识图谱存储回执", "",
        f"- Status: `{row.get('status', 'UNKNOWN')}`",
        f"- Nodes: `{row.get('node_count', row.get('registered_source_node_count', 0))}`",
        f"- Edges: `{row.get('edge_count', 0)}`",
        f"- Public metadata only: `{str(bool(row.get('public_metadata_only'))).lower()}`",
        f"- Secret values exposed: `{str(bool(row.get('secret_values_exposed'))).lower()}`",
        f"- Model calls: `{row.get('model_calls', 0)}`",
    ]
    if row.get("repository"):
        lines.extend([
            f"- Hugging Face Dataset: `{row['repository']}`",
            f"- Commit: `{row.get('commit_oid', '')}`",
        ])
    if row.get("error"):
        lines.append(f"- Error: `{row['error']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate", "bootstrap", "sync", "render"])
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    try:
        if args.command in {"validate", "bootstrap"}:
            print(cjson(bootstrap(output)))
        elif args.command == "sync":
            print(cjson(sync(output)))
        else:
            print(render(output), end="")
        return 0
    except Exception as exc:
        failure = {
            "status": "GLOBAL_KNOWLEDGE_GRAPH_FAILED",
            "error": clean(f"{type(exc).__name__}: {exc}", 1600),
            "secret_values_exposed": False,
            "model_calls": 0,
        }
        dump(output / "failure-receipt.json", failure)
        print(failure["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
