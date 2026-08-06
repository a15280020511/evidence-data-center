#!/usr/bin/env python3
"""Candidate-only catalog-domain discovery using Wikidata and Wikipedia.

The script never edits the approved domain registry. It queries only official
Wikimedia APIs, records candidate HTTPS domains, and requires a later governance
review before any candidate can become an enabled catalog domain.
"""
from __future__ import annotations

import argparse
import json
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
SOURCE_HOST_SUFFIXES = ("wikipedia.org", "wikidata.org", "wikimedia.org")
USER_AGENT = (
    "evidence-data-center-catalog-domain-discovery/1.0 "
    "(+https://github.com/a15280020511/evidence-data-center)"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def normalize_domain(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("candidate must be an HTTPS domain")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("candidate credentials and ports are forbidden")
    return f"https://{parsed.hostname.casefold()}"


def approved_domain_set(registry: Mapping[str, Any]) -> set[str]:
    output: set[str] = set()
    for item in registry.get("domains") or []:
        if not isinstance(item, Mapping):
            continue
        try:
            output.add(normalize_domain(str(item.get("url") or "")))
        except ValueError:
            continue
    return output


def discovery_config(registry: Mapping[str, Any]) -> Mapping[str, Any]:
    value = registry.get("discovery")
    if not isinstance(value, Mapping):
        raise ValueError("registry discovery configuration missing")
    if value.get("candidate_only") is not True:
        raise ValueError("discovery must be candidate-only")
    if value.get("automatic_promotion") is not False:
        raise ValueError("automatic promotion must be disabled")
    return value


def request_json(url: str, timeout: int, max_bytes: int) -> Mapping[str, Any]:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").casefold()
    if parsed.scheme != "https" or not any(
        host == suffix or host.endswith("." + suffix) for suffix in SOURCE_HOST_SUFFIXES
    ):
        raise ValueError(f"unapproved Wikimedia API host: {host}")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise RuntimeError(f"response exceeded {max_bytes} bytes")
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError("Wikimedia API response was not an object")
    return value


def api_url(endpoint: str, params: Mapping[str, Any]) -> str:
    return endpoint + "?" + urllib.parse.urlencode(params, doseq=True)


def search_wikidata(query: str, language: str, timeout: int, max_bytes: int) -> list[str]:
    data = request_json(
        api_url(
            WIKIDATA_API,
            {
                "action": "wbsearchentities",
                "search": query,
                "language": language,
                "uselang": language,
                "type": "item",
                "limit": 5,
                "format": "json",
            },
        ),
        timeout,
        max_bytes,
    )
    rows = data.get("search")
    if not isinstance(rows, list):
        return []
    return [
        str(row.get("id"))
        for row in rows
        if isinstance(row, Mapping) and str(row.get("id") or "").startswith("Q")
    ]


def fetch_entities(ids: list[str], timeout: int, max_bytes: int) -> Mapping[str, Any]:
    if not ids:
        return {}
    data = request_json(
        api_url(
            WIKIDATA_API,
            {
                "action": "wbgetentities",
                "ids": "|".join(ids[:10]),
                "props": "claims|sitelinks|labels|descriptions",
                "languages": "en|zh",
                "format": "json",
            },
        ),
        timeout,
        max_bytes,
    )
    entities = data.get("entities")
    return entities if isinstance(entities, Mapping) else {}


def claim_urls(entity: Mapping[str, Any]) -> list[str]:
    claims = entity.get("claims")
    p856 = claims.get("P856") if isinstance(claims, Mapping) else []
    output: list[str] = []
    if not isinstance(p856, list):
        return output
    for statement in p856:
        if not isinstance(statement, Mapping):
            continue
        mainsnak = statement.get("mainsnak")
        datavalue = mainsnak.get("datavalue") if isinstance(mainsnak, Mapping) else None
        value = datavalue.get("value") if isinstance(datavalue, Mapping) else None
        if isinstance(value, str):
            output.append(value)
    return output


def sitelink_titles(entity: Mapping[str, Any], languages: list[str]) -> list[tuple[str, str]]:
    sitelinks = entity.get("sitelinks")
    if not isinstance(sitelinks, Mapping):
        return []
    output: list[tuple[str, str]] = []
    for language in languages:
        item = sitelinks.get(f"{language}wiki")
        if isinstance(item, Mapping) and item.get("title"):
            output.append((language, str(item["title"])))
    return output


def wikipedia_external_links(
    language: str,
    title: str,
    timeout: int,
    max_bytes: int,
) -> list[str]:
    endpoint = f"https://{language}.wikipedia.org/w/api.php"
    data = request_json(
        api_url(
            endpoint,
            {
                "action": "query",
                "prop": "extlinks",
                "titles": title,
                "ellimit": "max",
                "format": "json",
                "formatversion": 2,
            },
        ),
        timeout,
        max_bytes,
    )
    pages = data.get("query", {}).get("pages", []) if isinstance(data.get("query"), Mapping) else []
    output: list[str] = []
    if not isinstance(pages, list):
        return output
    for page in pages:
        links = page.get("extlinks") if isinstance(page, Mapping) else []
        if not isinstance(links, list):
            continue
        for link in links:
            if isinstance(link, Mapping) and isinstance(link.get("url"), str):
                output.append(str(link["url"]))
    return output


def candidate_matches(url: str, tokens: list[str], official_claim: bool) -> bool:
    if official_claim:
        return True
    host = (urllib.parse.urlparse(url).hostname or "").casefold()
    compact = host.replace("-", "").replace(".", "")
    return any(
        token.casefold().replace("-", "").replace(".", "") in compact
        for token in tokens
        if token.strip()
    )


def discover(
    registry: Mapping[str, Any],
    timeout: int = 15,
    max_bytes: int = 1_000_000,
) -> dict[str, Any]:
    cfg = discovery_config(registry)
    queries = [str(value).strip() for value in cfg.get("entity_queries") or [] if str(value).strip()]
    languages = [str(value).strip() for value in cfg.get("wikipedia_languages") or ["en"]]
    tokens = [str(value).strip() for value in cfg.get("domain_tokens") or [] if str(value).strip()]
    if not queries or not tokens:
        raise ValueError("entity_queries and domain_tokens are required")

    approved = approved_domain_set(registry)
    entity_ids: list[str] = []
    source_errors: list[str] = []
    successful_queries = 0
    for query in queries:
        try:
            ids = search_wikidata(query, languages[0], timeout, max_bytes)
            successful_queries += 1
            for entity_id in ids:
                if entity_id not in entity_ids:
                    entity_ids.append(entity_id)
        except Exception as exc:
            source_errors.append(f"wikidata search {query}: {type(exc).__name__}: {str(exc)[:180]}")

    entities: Mapping[str, Any] = {}
    if entity_ids:
        try:
            entities = fetch_entities(entity_ids, timeout, max_bytes)
        except Exception as exc:
            source_errors.append(f"wikidata entities: {type(exc).__name__}: {str(exc)[:180]}")

    candidates: dict[str, dict[str, Any]] = {}
    pages_checked: list[dict[str, str]] = []
    for entity_id, raw_entity in entities.items():
        if not isinstance(raw_entity, Mapping):
            continue
        for url in claim_urls(raw_entity):
            try:
                domain = normalize_domain(url)
            except ValueError:
                continue
            if candidate_matches(url, tokens, official_claim=True):
                candidates.setdefault(
                    domain,
                    {
                        "candidate_domain": domain,
                        "status": "already-approved" if domain in approved else "unapproved-candidate",
                        "sources": [],
                    },
                )["sources"].append(
                    {"type": "wikidata-P856", "entity_id": entity_id, "source_url": url}
                )

        for language, title in sitelink_titles(raw_entity, languages):
            pages_checked.append({"language": language, "title": title, "entity_id": entity_id})
            try:
                links = wikipedia_external_links(language, title, timeout, max_bytes)
            except Exception as exc:
                source_errors.append(
                    f"wikipedia {language}:{title}: {type(exc).__name__}: {str(exc)[:180]}"
                )
                continue
            for url in links:
                if not candidate_matches(url, tokens, official_claim=False):
                    continue
                try:
                    domain = normalize_domain(url)
                except ValueError:
                    continue
                candidates.setdefault(
                    domain,
                    {
                        "candidate_domain": domain,
                        "status": "already-approved" if domain in approved else "unapproved-candidate",
                        "sources": [],
                    },
                )["sources"].append(
                    {
                        "type": "wikipedia-external-link",
                        "language": language,
                        "page_title": title,
                        "entity_id": entity_id,
                        "source_url": url,
                    }
                )

    rows = sorted(candidates.values(), key=lambda item: item["candidate_domain"])
    new_rows = [row for row in rows if row["status"] == "unapproved-candidate"]
    if successful_queries == 0:
        status = "unavailable"
    elif source_errors:
        status = "degraded"
    else:
        status = "pass"

    return {
        "schema_version": "catalog-domain-discovery-report-v1",
        "generated_at": utc_now(),
        "status": status,
        "mode": "candidate-only",
        "registry_mutated": False,
        "automatic_promotion": False,
        "entity_queries": queries,
        "entity_ids": entity_ids,
        "wikipedia_pages_checked": pages_checked,
        "approved_domains": sorted(approved),
        "candidates": rows,
        "new_candidates": new_rows,
        "manual_review_required": bool(new_rows),
        "source_errors": source_errors,
        "promotion_requirements": [
            "independent identity and provenance verification",
            "HTTPS and TLS validation",
            "search-page contract validation",
            "security and legal review",
            "pull request approval",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--max-bytes", type=int, default=1_000_000)
    parser.add_argument("--enforce-policy", action="store_true")
    args = parser.parse_args()
    try:
        report = discover(
            load_json(args.registry),
            timeout=min(max(args.timeout, 5), 30),
            max_bytes=min(max(args.max_bytes, 100_000), 2_000_000),
        )
    except Exception as exc:
        report = {
            "schema_version": "catalog-domain-discovery-report-v1",
            "generated_at": utc_now(),
            "status": "fail",
            "mode": "candidate-only",
            "registry_mutated": False,
            "automatic_promotion": False,
            "policy_errors": [f"{type(exc).__name__}: {exc}"],
        }
    save_json(args.output, report)
    print(
        json.dumps(
            {
                "status": report.get("status"),
                "candidate_count": len(report.get("candidates") or []),
                "new_candidate_count": len(report.get("new_candidates") or []),
                "manual_review_required": report.get("manual_review_required", False),
            },
            ensure_ascii=False,
        )
    )
    if args.enforce_policy and (
        report.get("mode") != "candidate-only"
        or report.get("registry_mutated") is not False
        or report.get("automatic_promotion") is not False
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
