#!/usr/bin/env python3
"""Coverage-balanced entrypoint for global source discovery."""
from __future__ import annotations

import math
import sys
from typing import Any, Mapping

import global_source_discovery_v2 as runtime


def stride_for(length: int, preferred: int) -> int:
    if length <= 1:
        return 1
    for candidate in (preferred, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53):
        candidate %= length
        if candidate and math.gcd(candidate, length) == 1:
            return candidate
    return 1


def balanced_query_set(
    config: Mapping[str, Any],
    cursor: int,
    limit: int,
    regions: list[str],
) -> tuple[list[str], int]:
    axes = [
        list(config.get("protocol_keywords") or []),
        list(config.get("institution_keywords") or []),
        list(config.get("sector_keywords") or []),
        list(config.get("publication_keywords") or []),
        list(regions or []),
    ]
    if not all(axes):
        return [], cursor
    strides = [stride_for(len(axis), preferred) for axis, preferred in zip(axes, (5, 7, 11, 13, 17))]
    offsets = [0, 3, 7, 11, 19]
    queries: list[str] = []
    for offset in range(limit):
        index = cursor + offset
        values = [
            axis[(index * stride + base + index // max(1, len(axis))) % len(axis)]
            for axis, stride, base in zip(axes, strides, offsets)
        ]
        protocol, institution, sector, publication, region = values
        queries.append(f'"{protocol}" "{sector}" ({institution} OR "{publication}") "{region}"')
    return queries, cursor + limit


runtime.query_set = balanced_query_set


if __name__ == "__main__":
    raise SystemExit(runtime.main(sys.argv[1:]))
