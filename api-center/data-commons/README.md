# Google Data Commons 托管提供方

Data Commons 是 API 中心的独立只读托管提供方，使用 `[api-dc]` Issue 票据。它与 BigQuery、Earth Engine、计算中心和专家团中心均不直接通信；GPTs 是唯一控制者和证据中继。

## Secret

Repository Secret 名称：

```text
GOOGLE_DATA_COMMONS_API_KEY
```

Secret 值不得写入仓库、Issue、评论或 Artifact。

## 固定操作

- `catalog-capabilities`：读取本地能力和中国起步目录，不需要 API Key；
- `resolve-place`：地点名称解析为 DCID；
- `resolve-indicator`：指标描述解析为统计变量或主题 DCID；
- `node-properties`：读取节点属性和关系；
- `observations`：读取最新、指定日期或完整时间序列观测，并保留 facet 来源。

只允许官方 REST V2 的 `/resolve`、`/node` 和 `/observation`。禁止 SPARQL、自然语言 API、任意 URL、写操作和个人数据。

## 示例票据

```json
{
  "task_id": "dc-fuzhou-population-20260729",
  "provider": "data-commons",
  "operation": "resolve-place",
  "objective": "解析福州市的Data Commons地点DCID",
  "parameters": {
    "nodes_json": "[\"Fuzhou, Fujian, China\"]"
  },
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false
  },
  "acceptance": {
    "timeout_seconds": 30,
    "max_response_bytes": 500000
  }
}
```

取得地点和指标 DCID 后，再创建新的 `observations` 票据。不要把同名候选自动当作正确地点，也不要把不同 facet 来源的数值无说明混合。

## 中国数据边界

Data Commons 对中国国家、省级和部分城市指标有价值，但不同指标、年份和行政层级覆盖不一致。关键政策、投资或商业结论必须与国家统计局、地方统计年鉴或原始国际机构交叉核验。
