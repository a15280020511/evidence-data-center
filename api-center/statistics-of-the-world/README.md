# Statistics of the World 全球统计

受限只读接入 `https://statisticsoftheworld.com`，用于国家、宏观指标、历史时间序列、国家排名、跨国比较和高频统计序列。

## 凭据

```text
Repository Secret: SOTW_API_KEY
```

该 Secret 为可选项。未配置时使用官方匿名免费访问；配置后仅在后端通过 `X-API-Key` 请求头发送。Issue、目录、日志和 Artifact 均不得包含 Key 值。

> 用户在聊天或工单中粘贴过的 Key 应视为已暴露，先在上游控制台轮换，再写入 GitHub Repository Secret。

## 固定能力

共 11 项：

- `catalog-capabilities`
- `list-countries`
- `get-country`
- `list-indicators`
- `get-indicator`
- `get-history`
- `get-rankings`
- `search-indicators`
- `compare-countries`
- `list-series`
- `get-series`

## 治理边界

- 每张票最多一次固定 HTTPS GET。
- 仅允许 `statisticsoftheworld.com` 的固定 `/api/v1`、`/api/v2` 路径。
- 禁止任意 URL、路径、请求头、客户端凭据、重定向和自动分页。
- 禁止 `/api/v1/series/bulk` 全量下载和 `/api/chat` 自然语言接口。
- 禁止写操作、后台轮询和个人数据。
- 响应体、超时、排名数量、比较国家数量均受限。
- 聚合结果必须保留原始来源、年份、单位和许可信息；不得将本服务作为唯一权威证据源。

## 免费与稳定性定位

官方当前文档显示匿名和免费开发者层均为每日 1,000 次请求，付费 API Pro 为每日 50,000 次。该服务由独立运营者维护，免费政策、端点和覆盖范围可能调整，因此在情报中心中按“次级聚合源”使用，并保留 World Bank、IMF、WHO 等原始来源作为替代和复核路径。
