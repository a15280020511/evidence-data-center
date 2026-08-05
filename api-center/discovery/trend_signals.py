#!/usr/bin/env python3
"""Collect bounded Google Trends signals for query expansion.

Google Trends is an auxiliary discovery signal only. It must never override
coverage gaps, official registries, licensing, security or free-mode gates.
The collector uses the official Trending Now RSS export, fails closed, and
writes an empty but valid result when feeds are unavailable.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

UA = "evidence-data-center-trend-signals/1"
NUMBER_RE = re.compile(r"([0-9][0-9,.]*)")
ASCII_WORD_RE = re.compile(r"^[a-z0-9][a-z0-9 +#./-]*$", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, Mapping) else {}


def save_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalized_text(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def marker_matches(blob: str, marker: str) -> bool:
    """Match ASCII markers on token boundaries and non-ASCII phrases literally."""
    marker = normalized_text(marker).casefold()
    if not marker:
        return False
    if ASCII_WORD_RE.fullmatch(marker):
        pattern = rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])"
        return re.search(pattern, blob, flags=re.I) is not None
    return marker in blob


def matching_markers(blob: str, markers: list[str]) -> list[str]:
    return [marker for marker in markers if marker_matches(blob, marker)]


def approx_volume(item_text: str) -> int:
    match = NUMBER_RE.search(item_text.replace(" ", " "))
    if not match:
        return 0
    try:
        number = float(match.group(1).replace(",", ""))
    except ValueError:
        return 0
    lowered = item_text.casefold()
    if "million" in lowered or "m+" in lowered:
        number *= 1_000_000
    elif "thousand" in lowered or "k+" in lowered:
        number *= 1_000
    return int(number)


def fetch_feed(url: str, max_bytes: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/rss+xml, application/xml, text/xml", "User-Agent": UA},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise RuntimeError("trend feed exceeds maximum size")
        return data


def iter_items(xml_bytes: bytes) -> Iterable[tuple[str, str]]:
    root = ET.fromstring(xml_bytes)
    for item in root.findall(".//item"):
        title_node = item.find("title")
        title = normalized_text(title_node.text if title_node is not None else "")
        item_text = normalized_text(" ".join(text for text in item.itertext() if text))
        if title:
            yield title, item_text


def collect(config: Mapping[str, Any]) -> dict[str, Any]:
    trend_cfg = config.get("google_trends") if isinstance(config.get("google_trends"), Mapping) else {}
    enabled = bool(trend_cfg.get("enabled", False))
    result: dict[str, Any] = {
        "schema_version": "trend-signals-v1",
        "generated_at": utc_now(),
        "source": "google-trends-trending-now-rss",
        "enabled": enabled,
        "terms": [],
        "errors": [],
        "feeds_checked": 0,
        "feeds_succeeded": 0,
        "policy": "auxiliary-low-weight-only",
    }
    if not enabled:
        return result

    geos = [str(value).upper() for value in trend_cfg.get("rss_geos") or []][:20]
    template = str(trend_cfg.get("rss_url_template") or "https://trends.google.com/trending/rss?geo={geo}")
    max_bytes = min(int(trend_cfg.get("max_feed_bytes") or 1_000_000), 2_000_000)
    max_terms = min(int(trend_cfg.get("max_terms_per_run") or 20), 50)
    markers = [str(value).casefold() for value in trend_cfg.get("relevance_markers") or []]
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []

    for geo in geos:
        result["feeds_checked"] += 1
        try:
            xml_bytes = fetch_feed(template.format(geo=geo), max_bytes=max_bytes)
            result["feeds_succeeded"] += 1
            for title, item_text in iter_items(xml_bytes):
                blob = f"{title} {item_text}".casefold()
                matched = matching_markers(blob, markers)
                if markers and not matched:
                    continue
                key = title.casefold()
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "term": title[:160],
                        "geo": geo,
                        "approx_volume": approx_volume(item_text),
                        "matched_markers": matched[:8],
                    }
                )
        except Exception as exc:  # fail closed; trends are non-critical
            result["errors"].append(f"{geo}: {type(exc).__name__}: {str(exc)[:180]}")

    rows.sort(key=lambda row: (-int(row.get("approx_volume") or 0), str(row.get("term") or "").casefold()))
    result["terms"] = rows[:max_terms]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = collect(load_json(args.config))
    save_json(args.output, result)
    print(json.dumps({
        "enabled": result["enabled"],
        "feeds_checked": result["feeds_checked"],
        "feeds_succeeded": result["feeds_succeeded"],
        "terms": len(result["terms"]),
        "errors": len(result["errors"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
