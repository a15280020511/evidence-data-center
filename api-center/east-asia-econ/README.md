# East Asia Econ managed provider

固定官方主机：`https://data-api.eastasiaecon.com`

Repository Secret：

```text
EAST_ASIA_ECON_API_KEY
```

API Key 由 East Asia Econ 账户的 API Keys 页面生成，官方 Key 以 `eae_` 开头。搜索、序列元数据和数据库统计无需密钥；序列数据与用量查询需要密钥。

## 票据入口

Issue 标题必须以 `[api-east-asia-econ]` 开头，正文必须符合 `ticket.schema.json`。

开放操作：

- `catalog-capabilities`
- `search-series`
- `series-info`
- `database-stats`
- `series-data`
- `usage`

## 安全边界

- 只允许固定 HTTPS GET 端点；
- 禁止任意 URL、Host、Path、Header 和用户提供 API Key；
- 每张票据最多一次上游请求；
- 禁止重试序列下载，避免重复消耗月度额度；
- 禁止个人数据、写入、交易和账户修改；
- Secret 值不得进入目录、Issue、日志、诊断或 Artifact。
