#!/usr/bin/env python3
"""One-shot deterministic integration patch for TickFlow and SerpAPI."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"expected text not found in {path}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    replace_once(
        "api-center/build_catalog.py",
        '    HERE / "web-retrieval/provider-catalog.json",\n)',
        '    HERE / "web-retrieval/provider-catalog.json",\n    HERE / "market-search/provider-catalog.json",\n)',
    )
    replace_once(
        "api-center/build_catalog.py",
        '            "yuandian/readonly-apis.snapshot.json",\n            "catalog-metadata.json",',
        '            "yuandian/readonly-apis.snapshot.json",\n            "market-search/provider-catalog.json",\n            "catalog-metadata.json",',
    )

    test_catalog = "api-center/tests/test_api_catalog.py"
    for old, new in (
        ('self.assertEqual(catalog["managed_provider_count"], 13)', 'self.assertEqual(catalog["managed_provider_count"], 15)'),
        ('self.assertEqual(catalog["enabled_managed_provider_count"], 13)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 15)'),
        ('self.assertEqual(catalog["managed_operation_count"], 114)', 'self.assertEqual(catalog["managed_operation_count"], 123)'),
        ('self.assertEqual(catalog["exposed_parameter_count"], 714)', 'self.assertEqual(catalog["exposed_parameter_count"], 746)'),
        ('                "jina-reader", "exa", "tavily", "firecrawl",\n', '                "jina-reader", "exa", "tavily", "firecrawl", "tickflow", "serpapi",\n'),
        ('            "firecrawl": 4,\n', '            "firecrawl": 4,\n            "tickflow": 5,\n            "serpapi": 4,\n'),
        ('        self.assertEqual(providers["firecrawl"]["required_secret_environment_variable_name"], "FIRECRAWL_API_KEY")\n', '        self.assertEqual(providers["firecrawl"]["required_secret_environment_variable_name"], "FIRECRAWL_API_KEY")\n        self.assertEqual(providers["tickflow"]["required_secret_environment_variable_name"], "TICKFLOW_API_KEY")\n        self.assertEqual(providers["serpapi"]["required_secret_environment_variable_name"], "SERPAPI_API_KEY")\n        self.assertEqual(providers["tickflow"]["ticket_prefix"], "[api-tickflow]")\n        self.assertEqual(providers["serpapi"]["ticket_prefix"], "[api-serpapi]")\n'),
    ):
        replace_once(test_catalog, old, new)

    capability = "api-center/tests/test_capability_maximization.py"
    replace_once(capability, 'self.assertEqual(sum(len(row["operations"]) for row in providers.values()), 114)', 'self.assertEqual(sum(len(row["operations"]) for row in providers.values()), 123)')
    replace_once(
        capability,
        '        self.assertEqual(len(providers["firecrawl"]["operations"]), 4)\n',
        '        self.assertEqual(len(providers["firecrawl"]["operations"]), 4)\n        self.assertEqual(len(providers["tickflow"]["operations"]), 5)\n        self.assertEqual(len(providers["serpapi"]["operations"]), 4)\n',
    )
    replace_once(
        capability,
        '        self.assertFalse(firecrawl_limits["async_crawl_allowed"])\n',
        '        self.assertFalse(firecrawl_limits["async_crawl_allowed"])\n\n        market = json.loads((ROOT / "market-search/provider-catalog.json").read_text(encoding="utf-8"))\n        market_providers = {row["provider_id"]: row for row in market["providers"]}\n        self.assertFalse(market_providers["tickflow"]["limits"]["write_or_trade_allowed"])\n        self.assertFalse(market_providers["tickflow"]["limits"]["websocket_allowed"])\n        self.assertFalse(market_providers["serpapi"]["limits"]["async_allowed"])\n        self.assertFalse(market_providers["serpapi"]["limits"]["html_output_allowed"])\n        self.assertFalse(market_providers["serpapi"]["limits"]["arbitrary_engine_allowed"])\n',
    )

    workflow = ".github/workflows/api-catalog-validate.yml"
    for old, new in (
        ("          web_providers = load_json('api-center/web-retrieval/provider-catalog.json')\n", "          web_providers = load_json('api-center/web-retrieval/provider-catalog.json')\n          market_providers = load_json('api-center/market-search/provider-catalog.json')\n"),
        ("          assert catalog['managed_provider_count'] == 13\n", "          assert catalog['managed_provider_count'] == 15\n"),
        ("          assert catalog['enabled_managed_provider_count'] == 13\n", "          assert catalog['enabled_managed_provider_count'] == 15\n"),
        ("              'jina-reader', 'exa', 'tavily', 'firecrawl'\n", "              'jina-reader', 'exa', 'tavily', 'firecrawl', 'tickflow', 'serpapi'\n"),
        ("          assert sum(len(row['operations']) for row in catalog['managed_providers']) == 114\n", "          assert sum(len(row['operations']) for row in catalog['managed_providers']) == 123\n"),
        ("          assert catalog['exposed_parameter_count'] == 714\n", "          assert catalog['exposed_parameter_count'] == 746\n"),
        ("          assert web_map['firecrawl']['required_secret_environment_variable'] == 'FIRECRAWL_API_KEY'\n", "          assert web_map['firecrawl']['required_secret_environment_variable'] == 'FIRECRAWL_API_KEY'\n          assert market_providers['secret_values_exposed'] is False\n          market_map = {row['provider_id']: row for row in market_providers['providers']}\n          assert set(market_map) == {'tickflow', 'serpapi'}\n          assert market_map['tickflow']['required_secret_environment_variable'] == 'TICKFLOW_API_KEY'\n          assert market_map['serpapi']['required_secret_environment_variable'] == 'SERPAPI_API_KEY'\n          assert len(market_map['tickflow']['operations']) == 5\n          assert len(market_map['serpapi']['operations']) == 4\n"),
        ("              'managed_providers': 13,\n              'managed_operations': 114,\n", "              'managed_providers': 15,\n              'managed_operations': 123,\n"),
        ("            api-center/web-retrieval/context-ticket.schema.json\n", "            api-center/web-retrieval/context-ticket.schema.json\n            api-center/market-search/provider-catalog.json\n            api-center/market-search/ticket.schema.json\n"),
    ):
        replace_once(workflow, old, new)

    subprocess.run(["python", "api-center/build_catalog.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "py_compile", "api-center/market-search/market_search_task.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "unittest", "discover", "-s", "api-center/market-search/tests", "-v"], cwd=ROOT, check=True)
    subprocess.run(["python", "-m", "unittest", "discover", "-s", "api-center/tests", "-v"], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
