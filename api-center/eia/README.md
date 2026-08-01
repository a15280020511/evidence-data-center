# 美国能源信息署 EIA API v2

该托管 Provider 固定访问美国能源信息署官方只读端点：

```text
https://api.eia.gov/v2
```

正式票据前缀与独立 Repository Secret：

```text
[intel-eia]
EIA_API_KEY
```

## 能力

固定开放 6 项操作：

1. `catalog-capabilities`：本地安全能力目录；
2. `api-root`：发现当前顶级数据路线；
3. `route-metadata`：读取任意受约束 EIA 层级路线的子路线、频率、Facet、数据列和时间范围；
4. `facet-values`：读取某个 Facet 的可用过滤值；
5. `route-data`：按数据列、频率、时间、Facet、排序、offset 和 length 读取结构化能源数据；
6. `series-by-id`：通过 API v2 兼容路线读取单一历史 Series ID。

层级路线设计使同一连接器可以覆盖电力、石油、天然气、煤炭、核能、可再生能源、国际能源、州级能源和短期能源展望等当前及未来公开数据树，无需为每个数据集硬编码新端点。

## 安全边界

- 固定主机 `api.eia.gov` 和 `/v2` 前缀；
- 路线最多 8 段，禁止 `..`、`data`、`facet` 注入和路径穿越；
- 每票据只发一次 GET，不自动重试或翻页；
- JSON 每次最多 5000 行；
- 最多 20 个数据列、12 个 Facet、100 个 Facet 值和 4 个排序规则；
- 禁止 XML、批量文件下载、任意 URL、任意请求头、后台递归抓取和写入；
- `EIA_API_KEY` 只在后端查询参数中注入。

EIA 的调试回显可能包含请求参数，包括 API Key。执行器会递归清除密钥后才写入 `response.json`、Snapshot、Diagnostics 和 Artifact，原始响应不会落盘。

## 票据示例

```json
{
  "task_id": "eia-electricity-retail-sales-001",
  "provider": "eia",
  "operation": "route-data",
  "objective": "读取美国住宅用电月度零售价格",
  "parameters": {
    "route": "electricity/retail-sales",
    "data": ["price"],
    "frequency": "monthly",
    "facets": {
      "sectorid": ["RES"],
      "stateid": ["US"]
    },
    "sort": [{"column": "period", "direction": "desc"}],
    "length": 24
  },
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false
  },
  "acceptance": {
    "timeout_seconds": 30,
    "max_response_bytes": 10000000
  }
}
```

API Key 需在 EIA Open Data 注册页面免费申请后配置到仓库 Secret `EIA_API_KEY`。
