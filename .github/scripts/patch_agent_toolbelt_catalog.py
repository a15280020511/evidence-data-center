#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def insert_after(text: str, anchor: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    if anchor not in text:
        raise RuntimeError(f"missing insertion anchor: {anchor!r}")
    return text.replace(anchor, anchor + addition, 1)


def replace_exact(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"missing replacement anchor: {old!r}")
    return text.replace(old, new, 1)


path = "api-center/build_catalog.py"
text = read(path)
text = insert_after(
    text,
    '    HERE / "web-retrieval/provider-catalog.json",\n',
    '    HERE / "agent-toolbelt/provider-catalog.json",\n',
)
write(path, text)

path = "api-center/tests/test_api_catalog.py"
text = read(path)
text = insert_after(text, '    "alphafeed": 10,\n', '    "agent-toolbelt": 29,\n')
text = replace_exact(
    text,
    '        self.assertEqual(catalog["managed_provider_count"], 29)\n',
    '        self.assertEqual(catalog["managed_provider_count"], 30)\n',
)
text = replace_exact(
    text,
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 29)\n',
    '        self.assertEqual(catalog["enabled_managed_provider_count"], 30)\n',
)
text = replace_exact(
    text,
    '        self.assertEqual(catalog["managed_operation_count"], 339)\n',
    '        self.assertEqual(catalog["managed_operation_count"], 368)\n',
)
text = insert_after(
    text,
    '            "alphafeed": "ALPHAFEED_API_KEY",\n',
    '            "agent-toolbelt": "AGENT_TOOLBELT_KEY",\n',
)
agent_assertions = '''
        agent_toolbelt = providers["agent-toolbelt"]
        self.assertEqual(
            agent_toolbelt["ticket_prefix"],
            "[api-agent-toolbelt]",
        )
        self.assertEqual(
            agent_toolbelt["required_secret_environment_variable_name"],
            "AGENT_TOOLBELT_KEY",
        )
        self.assertEqual(len(agent_toolbelt["operations"]), 29)
        self.assertEqual(
            agent_toolbelt["limits"]["fixed_api_host"],
            "www.agenttoolbelt.live",
        )
        self.assertFalse(
            agent_toolbelt["limits"]["arbitrary_tool_names_allowed"]
        )
        self.assertFalse(agent_toolbelt["limits"]["watchlist_crud_allowed"])
        self.assertFalse(agent_toolbelt["limits"]["write_operations_allowed"])
        self.assertFalse(
            agent_toolbelt["limits"]["trading_or_order_execution_allowed"]
        )

'''
anchor = '''        self.assertEqual(
            providers["tushare"]["ticket_prefix"],
'''
if agent_assertions.strip() not in text:
    if anchor not in text:
        raise RuntimeError("missing Agent Toolbelt test insertion anchor")
    text = text.replace(anchor, agent_assertions + anchor, 1)
write(path, text)

path = "api-center/tests/test_capability_maximization.py"
text = read(path)
text = replace_exact(
    text,
    '''        self.assertEqual(
            sum(len(row["operations"]) for row in providers.values()),
            339,
        )
''',
    '''        self.assertEqual(
            sum(len(row["operations"]) for row in providers.values()),
            368,
        )
''',
)
text = insert_after(text, '            "alphafeed": 10,\n', '            "agent-toolbelt": 29,\n')
write(path, text)

path = "api-center/README.md"
text = read(path)
section = '''

## Agent Toolbelt

```text
Ticket prefix: [api-agent-toolbelt]
Repository Secret: AGENT_TOOLBELT_KEY
Fixed origin: https://www.agenttoolbelt.live
```

Agent Toolbelt exposes 29 bounded operations in the API catalog: one local
capability catalog, eight US-stock research operations, and twenty utility
operations. The integration forbids arbitrary tool names, Watchlist CRUD,
background monitoring, trading, orders, redirects, client-supplied
credentials, and non-public/private-network URL targets. Upstream calls may
consume quota or incur provider charges.
'''
if "## Agent Toolbelt" not in text:
    text = text.rstrip() + section
write(path, text)

path = "api-center/SECRET_ISOLATION_POLICY.md"
text = read(path)
section = '''

## Agent Toolbelt

```text
Repository Secret: AGENT_TOOLBELT_KEY
```

The key is injected only into the dedicated Agent Toolbelt GitHub Actions job
as a Bearer token. It is never accepted from tickets, written to the unified
catalog, printed in comments, or persisted in artifacts. Failure messages are
redacted before diagnostics are written.
'''
if "## Agent Toolbelt" not in text:
    text = text.rstrip() + section
write(path, text)

subprocess.run(
    ["python", "api-center/build_catalog_market_search.py"],
    cwd=ROOT,
    check=True,
)
