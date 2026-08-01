#!/usr/bin/env python3
"""Apply BaoStock hard quota and serial-connection policy to generated contracts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "api-center/baostock/provider-catalog.json"
README = ROOT / "api-center/baostock/README.md"
POLICY = ROOT / "api-center/baostock/quota-policy.json"


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    provider = catalog["providers"][0]
    provider["execution_policy"] = (
        "每张票据只允许一次登录、一次白名单查询和一次登出；所有生产票据使用仓库级全局串行并发组，"
        "禁止并发连接。每个上海自然日最多预占 50000 次上游查询，第 50000 次后立即激活当天本地黑名单；"
        "配额台账异常时失败关闭，禁止访问 BaoStock。"
    )
    limits = provider["limits"]
    limits.update(
        {
            "daily_request_limit": int(policy["daily_request_limit"]),
            "daily_quota_timezone": str(policy["timezone"]),
            "max_parallel_connections": int(policy["max_parallel_connections"]),
            "global_serial_connection_required": True,
            "concurrency_group": str(policy["concurrency_group"]),
            "local_blacklist_at_daily_limit": True,
            "quota_ledger_fail_closed": True,
            "quota_ledger_issue_number": int(policy["ledger_issue_number"]),
            "catalog_operations_consume_quota": False,
        }
    )
    CATALOG.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    text = README.read_text(encoding="utf-8")
    heading = "## 生产配额与串行连接"
    if heading not in text:
        text += (
            "\n\n## 生产配额与串行连接\n\n"
            "BaoStock 生产访问采用 `Asia/Shanghai` 自然日计数，每日最多 `50,000` 次上游查询，"
            "并通过固定并发组 `api-baostock-global-single-connection` 保证全局最多一个活动连接。"
            "第 50,000 次请求允许完成并立即激活当天本地黑名单，后续请求在登录前拒绝；次日自动重置。"
            "配额台账读取、解析或更新失败时执行失败关闭。详细规则见 `QUOTA.md` 和 `quota-policy.json`。\n"
        )
        README.write_text(text, encoding="utf-8")

    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
