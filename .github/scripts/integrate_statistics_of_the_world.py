#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "api-center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"expected text missing in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


api_test = API / "tests/test_api_catalog.py"
replace_once(api_test, '    "mediastack": 5,\n    "wolfram-alpha": 4,', '    "mediastack": 5,\n    "statistics-of-the-world": 11,\n    "wolfram-alpha": 4,')
replace_once(api_test, 'self.assertEqual(catalog["managed_provider_count"], 33)', 'self.assertEqual(catalog["managed_provider_count"], 34)')
replace_once(api_test, 'self.assertEqual(catalog["enabled_managed_provider_count"], 33)', 'self.assertEqual(catalog["enabled_managed_provider_count"], 34)')
replace_once(api_test, 'self.assertEqual(catalog["managed_operation_count"], 582)', 'self.assertEqual(catalog["managed_operation_count"], 593)')

cap_test = API / "tests/test_capability_maximization.py"
replace_once(cap_test, '            582,\n', '            593,\n')
replace_once(cap_test, '            "mediastack": 5,\n            "wolfram-alpha": 4,', '            "mediastack": 5,\n            "statistics-of-the-world": 11,\n            "wolfram-alpha": 4,')

append_once(
    API / "README.md",
    "## Statistics of the World 全球统计",
    """
## Statistics of the World 全球统计

- Provider：`statistics-of-the-world`
- 工单前缀：`[intel-sotw]`
- 可选 Repository Secret：`SOTW_API_KEY`
- 11 个固定只读操作，覆盖国家、指标、历史、排名、搜索、国家比较和高频序列。
- 禁止全量 bulk、自然语言 chat、任意路径、自动分页和写操作。
- 定位为次级聚合证据源，重要结论应回查 IMF、World Bank、WHO、FRED、ECB 或 UN 原始来源。
""",
)

append_once(
    API / "SECRET_ISOLATION_POLICY.md",
    "### Statistics of the World",
    """
### Statistics of the World

```text
SOTW_API_KEY
```

该 Secret 为可选项，仅允许在 GitHub Actions 后端通过 `X-API-Key` 请求头注入。不得出现在 Issue、PR、目录、日志、测试夹具、Artifact、请求元数据或错误详情中。未配置时仅使用官方匿名免费层。聊天或工单中曾粘贴的 Key 必须先轮换再写入 Repository Secret。
""",
)

append_once(
    API / "CAPABILITY_MAXIMIZATION.md",
    "### Statistics of the World 全球统计",
    """
### Statistics of the World 全球统计

安全开放 11 个固定只读操作：国家目录与详情、指标目录与横截面、历史、排名、指标搜索、2 至 10 国比较、高频序列目录与单序列读取。每票仅一次请求；禁止批量全库下载、自然语言聊天、任意 URL/路径/请求头、客户端凭据、自动分页、后台轮询和写操作。
""",
)

subprocess.run(
    ["python", str(API / "build_catalog_market_search.py")],
    cwd=ROOT,
    check=True,
)

print("Statistics of the World integration complete")
