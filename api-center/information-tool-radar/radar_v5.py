#!/usr/bin/env python3
"""GitHub dual-mode discovery for the Information & Tool Radar.

Recent-change queries stay sorted by update time. Broad category discovery uses
GitHub's best-match order so older but semantically relevant projects are not
buried by unrelated newly updated repositories.
"""
from __future__ import annotations

import sys
from typing import Any, Mapping

import radar as base
import radar_v4  # installs prior resilience and truthful coverage gates


def github(config: Mapping[str, Any], runtime: Mapping[str, int]) -> base.AdapterResult:
    result = base.AdapterResult("github", str(config["category"]))
    token = base.os.getenv("GITHUB_TOKEN", "").strip()
    headers = {"X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    query_plan: list[tuple[str, str]] = []
    query_plan.extend((str(query), "recent") for query in list(config.get("queries") or []))
    query_plan.extend(
        (str(query), "best_match")
        for query in list(config.get("best_match_queries") or [])
    )
    result.details["query_modes"] = {
        "recent": sum(mode == "recent" for _, mode in query_plan),
        "best_match": sum(mode == "best_match" for _, mode in query_plan),
    }

    for query, mode in query_plan:
        result.probes += 1
        try:
            params: dict[str, Any] = {
                "q": query,
                "per_page": runtime["max_records"],
            }
            if mode == "recent":
                params.update({"sort": "updated", "order": "desc"})
            url = base.query_url(str(config["endpoint"]), params)
            data = base.request_json(
                url,
                timeout=runtime["timeout"],
                max_bytes=runtime["max_bytes"],
                headers=headers,
            )
            rows = data.get("items") if isinstance(data, Mapping) else []
            if not isinstance(rows, list):
                raise RuntimeError("GitHub items missing")
            result.successful_probes += 1
            for row in rows[: runtime["max_records"]]:
                if isinstance(row, Mapping) and row.get("html_url"):
                    result.candidates.append(base.make_candidate(
                        result.name,
                        result.category,
                        str(row.get("full_name") or row.get("name") or query),
                        str(row["html_url"]),
                        {
                            "query": query,
                            "search_mode": mode,
                            "description": base.bounded_text(row.get("description") or "", 500),
                            "archived": bool(row.get("archived", False)),
                            "updated_at": row.get("updated_at"),
                            "language": row.get("language"),
                            "stars": row.get("stargazers_count"),
                        },
                        status="candidate",
                    ))
        except Exception as exc:
            result.add_error(f"{query} [{mode}]: {type(exc).__name__}: {exc}")
    result.success = result.successful_probes > 0
    return result


base.ADAPTERS["github"] = github


if __name__ == "__main__":
    raise SystemExit(base.main(sys.argv[1:]))
