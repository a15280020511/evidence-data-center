#!/usr/bin/env python3
"""Register the fixed Miaoxiang MCP provider in deterministic API-center contracts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, path: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one occurrence, found {count}: {old!r}")
    return text.replace(old, new, 1)


def update_catalog_generator() -> None:
    path = "api-center/build_catalog_market_search.py"
    text = read(path)
    text = replace_once(
        text,
        'QWEATHER_CATALOG = HERE / "qweather/provider-catalog.json"\n',
        'QWEATHER_CATALOG = HERE / "qweather/provider-catalog.json"\n'
        'MIAOXIANG_MCP_CATALOG = HERE / "miaoxiang-mcp/provider-catalog.json"\n',
        path,
    )
    text = replace_once(
        text,
        '    "qweather": 18,\n',
        '    "qweather": 18,\n    "miaoxiang-mcp": 13,\n',
        path,
    )
    text = replace_once(
        text,
        '    QWEATHER_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n',
        '    QWEATHER_CATALOG,\n    MIAOXIANG_MCP_CATALOG,\n    KNOWLEDGE_TOOLS_CATALOG,\n',
        path,
    )
    text = replace_once(
        text,
        '        "qweather/provider-catalog.json",\n        "knowledge-tools/provider-catalog.json",\n',
        '        "qweather/provider-catalog.json",\n'
        '        "miaoxiang-mcp/provider-catalog.json",\n'
        '        "knowledge-tools/provider-catalog.json",\n',
        path,
    )
    write(path, text)


def update_catalog_tests() -> None:
    path = "api-center/tests/test_api_catalog.py"
    text = read(path)
    text = replace_once(
        text,
        '    "miaoxiang": 4,\n',
        '    "miaoxiang": 4,\n    "miaoxiang-mcp": 13,\n',
        path,
    )
    text = replace_once(
        text,
        '        self.assertEqual(catalog["managed_provider_count"], 21)\n'
        '        self.assertEqual(catalog["enabled_managed_provider_count"], 21)\n'
        '        self.assertEqual(catalog["managed_operation_count"], 213)\n',
        '        self.assertEqual(catalog["managed_provider_count"], 22)\n'
        '        self.assertEqual(catalog["enabled_managed_provider_count"], 22)\n'
        '        self.assertEqual(catalog["managed_operation_count"], 226)\n',
        path,
    )
    text = replace_once(
        text,
        '            "miaoxiang": "MX_APIKEY",\n',
        '            "miaoxiang": "MX_APIKEY",\n'
        '            "miaoxiang-mcp": "EM_API_KEY",\n',
        path,
    )
    marker = (
        '        self.assertFalse(providers["qweather"]["limits"]["redirects_allowed"])\n\n'
    )
    addition = marker + (
        '        self.assertEqual(providers["miaoxiang-mcp"]["ticket_prefix"], "[api-mx-mcp]")\n'
        '        self.assertEqual(providers["miaoxiang-mcp"]["required_secret_environment_variable_name"], "EM_API_KEY")\n'
        '        self.assertEqual(providers["miaoxiang-mcp"]["official_endpoint"], "https://mxapi.eastmoney.com/mxds/mcp")\n'
        '        self.assertEqual(providers["miaoxiang-mcp"]["mcp_protocol_version"], "2025-11-25")\n'
        '        self.assertEqual(providers["miaoxiang-mcp"]["limits"]["fixed_mcp_tool_count"], 11)\n'
        '        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["arbitrary_jsonrpc_methods_allowed"])\n'
        '        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["arbitrary_mcp_tool_names_allowed"])\n'
        '        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["write_operations_allowed"])\n'
        '        self.assertFalse(providers["miaoxiang-mcp"]["limits"]["trading_or_order_execution_allowed"])\n\n'
    )
    text = replace_once(text, marker, addition, path)
    text = replace_once(
        text,
        '            "qweather/provider-catalog.json",\n'
        '            "knowledge-tools/provider-catalog.json",\n',
        '            "qweather/provider-catalog.json",\n'
        '            "miaoxiang-mcp/provider-catalog.json",\n'
        '            "knowledge-tools/provider-catalog.json",\n',
        path,
    )
    write(path, text)


def update_capability_tests() -> None:
    path = "api-center/tests/test_capability_maximization.py"
    text = read(path)
    text = replace_once(
        text,
        '            213,\n',
        '            226,\n',
        path,
    )
    text = replace_once(
        text,
        '            "miaoxiang": 4,\n',
        '            "miaoxiang": 4,\n            "miaoxiang-mcp": 13,\n',
        path,
    )
    marker = (
        '        self.assertFalse(qw_provider["limits"]["write_operations_allowed"])\n\n'
    )
    addition = marker + (
        '        miaoxiang_mcp = json.loads(\n'
        '            (ROOT / "miaoxiang-mcp/provider-catalog.json").read_text(encoding="utf-8")\n'
        '        )\n'
        '        mcp_provider = miaoxiang_mcp["providers"][0]\n'
        '        self.assertEqual(mcp_provider["required_secret_environment_variable"], "EM_API_KEY")\n'
        '        self.assertEqual(mcp_provider["official_endpoint"], "https://mxapi.eastmoney.com/mxds/mcp")\n'
        '        self.assertEqual(mcp_provider["mcp_protocol_version"], "2025-11-25")\n'
        '        self.assertEqual(mcp_provider["limits"]["fixed_mcp_tool_count"], 11)\n'
        '        self.assertFalse(mcp_provider["limits"]["arbitrary_jsonrpc_methods_allowed"])\n'
        '        self.assertFalse(mcp_provider["limits"]["arbitrary_mcp_tool_names_allowed"])\n'
        '        self.assertFalse(mcp_provider["limits"]["resources_allowed"])\n'
        '        self.assertFalse(mcp_provider["limits"]["prompts_allowed"])\n'
        '        self.assertFalse(mcp_provider["limits"]["write_operations_allowed"])\n'
        '        self.assertFalse(mcp_provider["limits"]["trading_or_order_execution_allowed"])\n\n'
    )
    text = replace_once(text, marker, addition, path)
    write(path, text)


def update_readme() -> None:
    path = "api-center/README.md"
    text = read(path)
    old_block = '''新增托管提供方分别使用：

```text
TUSHARE_API_TOKEN
EODHD_API_TOKEN
WOLFRAM_ALPHA_APP_ID
LLAMA_CLOUD_API_KEY
```
'''
    new_block = '''新增托管提供方分别使用：

```text
TUSHARE_API_TOKEN
EODHD_API_TOKEN
WOLFRAM_ALPHA_APP_ID
LLAMA_CLOUD_API_KEY
MX_APIKEY
EM_API_KEY
```
'''
    text = replace_once(text, old_block, new_block, path)
    section = '''\n\n## 东方财富妙想 MCP\n\n`api-center/miaoxiang-mcp/` 使用东方财富官方 Streamable HTTP MCP Server：\n\n```text\nhttps://mxapi.eastmoney.com/mxds/mcp\n```\n\n正式票据前缀和独立 Secret：\n\n```text\n[api-mx-mcp]\nEM_API_KEY\n```\n\nMCP 协议固定为 `2025-11-25`，鉴权只通过后端 `em_api_key` 请求头注入。当前固定开放 11 个上游只读工具，覆盖 A股、港股、美股、基金、债券、指数板块、宏观经济、新闻研报、公告披露和证券筛选；连同本地能力目录与 `tools/list`，总计 13 项操作。禁止任意 JSON-RPC 方法、任意 MCP 工具名、Resources、Prompts、自选股修改、模拟交易和真实交易。\n\n原有 `api-center/miaoxiang/` 是 Skills REST Provider，使用 `MX_APIKEY`（`mkt_` 类型）；MCP Provider 使用 `EM_API_KEY`（`em_` 类型）。两类密钥必须独立保存，不能互换。\n'''
    if "## 东方财富妙想 MCP" not in text:
        text += section
    write(path, text)


def update_dependabot() -> None:
    path = ".github/dependabot.yml"
    directories = [
        "/api-center",
        "/api-center/akshare",
        "/api-center/google-cloud",
        "/api-center/data-commons",
        "/api-center/qweather",
        "/api-center/miaoxiang-mcp",
    ]
    lines = [
        "version: 2",
        "updates:",
        '  - package-ecosystem: "github-actions"',
        '    directory: "/"',
        "    schedule:",
        '      interval: "weekly"',
        "    open-pull-requests-limit: 5",
    ]
    for directory in directories:
        lines.extend(
            [
                '  - package-ecosystem: "pip"',
                f'    directory: "{directory}"',
                "    schedule:",
                '      interval: "weekly"',
                "    open-pull-requests-limit: 5",
            ]
        )
    write(path, "\n".join(lines) + "\n")


def main() -> int:
    update_catalog_generator()
    update_catalog_tests()
    update_capability_tests()
    update_readme()
    update_dependabot()
    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
