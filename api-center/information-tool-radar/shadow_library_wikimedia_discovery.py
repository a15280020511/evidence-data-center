#!/usr/bin/env python3
"""Discover shadow-library projects and transient website candidates via Wikimedia only.

The persistent registry contains names/aliases and Wikimedia page titles, never
shadow-library domains. Runtime domains are resolved through Wikipedia pageprops
and Wikidata P856 and are intended only for an in-process metadata adapter. CLI
reports deliberately redact the actual domains and never persist them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SCHEMA = "shadow-library-wikimedia-registry-v1"
USER_AGENT = "evidence-data-center-shadow-wikimedia-discovery/1.0"

JsonGetter = Callable[[str, Mapping[str, str], int], Mapping[str, Any]]


def load_registry(path: Path) -> Mapping[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("registry must be an object")
    return data


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != SCHEMA:
        errors.append(f"schema_version must be {SCHEMA}")
    policy = registry.get("policy")
    if not isinstance(policy, Mapping):
        return errors + ["policy missing"]
    required_true = (
        "wikipedia_wikidata_only_for_domain_discovery",
        "discard_runtime_domains_after_run",
        "metadata_only",
    )
    required_false = (
        "persist_shadow_domains",
        "detail_pages_allowed",
        "download_links_allowed",
        "file_retrieval_allowed",
        "ipfs_magnet_md5_resolution_allowed",
        "access_control_bypass_allowed",
        "captcha_bypass_allowed",
        "paywall_bypass_allowed",
    )
    for key in required_true:
        if policy.get(key) is not True:
            errors.append(f"policy.{key} must be true")
    for key in required_false:
        if policy.get(key) is not False:
            errors.append(f"policy.{key} must be false")
    wikimedia = registry.get("wikimedia")
    if not isinstance(wikimedia, Mapping):
        errors.append("wikimedia missing")
    else:
        for key in ("wikipedia_api", "wikidata_api"):
            value = str(wikimedia.get(key) or "")
            if not value.startswith("https://"):
                errors.append(f"wikimedia.{key} must be https")
        if wikimedia.get("website_property") != "P856":
            errors.append("wikimedia.website_property must be P856")
    seeds = registry.get("reviewed_seeds")
    if not isinstance(seeds, list) or not seeds:
        errors.append("reviewed_seeds must be non-empty")
        return errors
    seen: set[str] = set()
    for index, raw in enumerate(seeds):
        if not isinstance(raw, Mapping):
            errors.append(f"reviewed_seeds[{index}] invalid")
            continue
        source_id = str(raw.get("id") or "")
        if not source_id:
            errors.append(f"reviewed_seeds[{index}].id missing")
            continue
        if source_id in seen:
            errors.append(f"duplicate id: {source_id}")
        seen.add(source_id)
        titles = raw.get("wikipedia_titles")
        if not isinstance(titles, list) or not any(str(x).strip() for x in titles):
            errors.append(f"{source_id}.wikipedia_titles missing")
        lowered = json.dumps(raw, ensure_ascii=False).casefold()
        for marker in ("http://", "https://", "ipfs://", "magnet:", "/md5/"):
            if marker in lowered:
                errors.append(f"{source_id}: persisted locator forbidden: {marker}")
    return errors


def http_json(url: str, params: Mapping[str, str], timeout: int) -> Mapping[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{url}?{query}",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(2_000_000)
    data = json.loads(payload.decode("utf-8", errors="replace"))
    if not isinstance(data, Mapping):
        raise ValueError("Wikimedia response must be an object")
    return data


def wikipedia_item_id(
    api: str,
    title: str,
    *,
    timeout: int,
    getter: JsonGetter,
) -> str | None:
    data = getter(
        api,
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "pageprops",
            "redirects": "1",
            "titles": title,
        },
        timeout,
    )
    pages = ((data.get("query") or {}).get("pages") or [])
    for page in pages:
        if not isinstance(page, Mapping):
            continue
        item = ((page.get("pageprops") or {}).get("wikibase_item"))
        if item:
            return str(item)
    return None


def wikidata_websites(
    api: str,
    item_id: str,
    *,
    timeout: int,
    getter: JsonGetter,
) -> list[str]:
    data = getter(
        api,
        {
            "action": "wbgetentities",
            "format": "json",
            "ids": item_id,
            "props": "claims",
        },
        timeout,
    )
    entity = ((data.get("entities") or {}).get(item_id) or {})
    claims = (entity.get("claims") or {}).get("P856") or []
    output: list[str] = []
    for claim in claims:
        if not isinstance(claim, Mapping):
            continue
        value = (((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value"))
        if isinstance(value, str) and value.startswith("https://"):
            parsed = urllib.parse.urlparse(value)
            if not parsed.hostname:
                continue
            root = f"https://{parsed.hostname.casefold()}"
            if root not in output:
                output.append(root)
    return output


def resolve_seed_runtime_domains(
    registry: Mapping[str, Any],
    seed: Mapping[str, Any],
    *,
    timeout: int = 15,
    getter: JsonGetter = http_json,
) -> list[str]:
    """Return ephemeral domain candidates for an in-process metadata adapter only."""
    errors = validate_registry(registry)
    if errors:
        raise ValueError("; ".join(errors))
    wikimedia = registry["wikimedia"]
    domains: list[str] = []
    for title in seed.get("wikipedia_titles") or []:
        item_id = wikipedia_item_id(
            str(wikimedia["wikipedia_api"]),
            str(title),
            timeout=timeout,
            getter=getter,
        )
        if not item_id:
            continue
        for domain in wikidata_websites(
            str(wikimedia["wikidata_api"]),
            item_id,
            timeout=timeout,
            getter=getter,
        ):
            if domain not in domains:
                domains.append(domain)
    return domains


def _fingerprint(domains: Sequence[str]) -> str | None:
    if not domains:
        return None
    material = "\n".join(sorted(domains)).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def redacted_report(
    registry: Mapping[str, Any],
    *,
    selected_ids: set[str] | None = None,
    timeout: int = 15,
    getter: JsonGetter = http_json,
) -> dict[str, Any]:
    errors = validate_registry(registry)
    if errors:
        return {"schema_version": SCHEMA, "status": "fail", "errors": errors}
    rows: list[dict[str, Any]] = []
    for seed in registry.get("reviewed_seeds") or []:
        source_id = str(seed.get("id"))
        if selected_ids and source_id not in selected_ids:
            continue
        try:
            domains = resolve_seed_runtime_domains(
                registry, seed, timeout=timeout, getter=getter
            )
            status = "resolved" if domains else "no-current-p856-domain"
            error = None
        except Exception as exc:
            domains = []
            status = "wikimedia-unavailable"
            error = f"{type(exc).__name__}: {str(exc)[:240]}"
        rows.append(
            {
                "id": source_id,
                "name": seed.get("name"),
                "lifecycle": seed.get("lifecycle"),
                "metadata_adapter": seed.get("metadata_adapter"),
                "status": status,
                "runtime_domain_candidate_count": len(domains),
                "runtime_domain_fingerprint": _fingerprint(domains),
                "runtime_domains_redacted": True,
                "runtime_domains_persisted": False,
                "error": error,
            }
        )
    return {
        "schema_version": SCHEMA,
        "status": "pass",
        "source_count": len(rows),
        "resolved_source_count": sum(r["status"] == "resolved" for r in rows),
        "sources": rows,
        "safety": {
            "discovery_via_wikipedia_wikidata_only": True,
            "shadow_domains_persisted": False,
            "shadow_domains_exposed_in_report": False,
            "shadow_detail_pages_followed": False,
            "shadow_download_links_followed": False,
            "shadow_files_retrieved": False,
            "access_controls_bypassed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args()
    report = redacted_report(
        load_registry(args.registry),
        selected_ids=set(args.source) or None,
        timeout=min(max(args.timeout, 5), 30),
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "status": report.get("status"),
        "source_count": report.get("source_count", 0),
        "resolved_source_count": report.get("resolved_source_count", 0),
        "shadow_domains_persisted": (report.get("safety") or {}).get("shadow_domains_persisted"),
    }, ensure_ascii=False))
    if args.enforce and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
