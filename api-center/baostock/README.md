# BaoStock managed provider

- Ticket prefix: `[api-baostock]`
- Provider ID: `baostock`
- Credentials: none
- Package: `baostock==0.9.3`
- Policy: one login, one allowlisted read-only query, one logout per ticket
- Output: structured Snapshot, Diagnostics, Manifest and GitHub Actions Artifact

This integration does not expose arbitrary BaoStock functions, arbitrary hosts, Python code, trading, order execution or write operations.


## 生产配额与串行连接

BaoStock 生产访问采用 `Asia/Shanghai` 自然日计数，每日最多 `50,000` 次上游查询，并通过固定并发组 `api-baostock-global-single-connection` 保证全局最多一个活动连接。第 50,000 次请求允许完成并立即激活当天本地黑名单，后续请求在登录前拒绝；次日自动重置。配额台账读取、解析或更新失败时执行失败关闭。详细规则见 `QUOTA.md` 和 `quota-policy.json`。
