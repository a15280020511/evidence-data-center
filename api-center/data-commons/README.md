# Google Data Commons 托管 Provider

该 Provider 使用 Repository Secret：

```text
GOOGLE_DATA_COMMONS_API_KEY
```

密钥只由后端通过 `X-API-Key` 注入，不写入 Issue、日志或 Artifact。

## 为什么保留

Data Commons 不是普通数据目录，也不是 BigQuery 或 Earth Engine 的重复入口。它负责：

- 地名、地区和统计指标的实体解析；
- 统一知识图谱节点及属性读取；
- 跨来源统计变量的语义对齐；
- 按地点、指标和时间读取统一观测序列。

Google Cloud Provider 中的 BigQuery 负责表级目录和 SQL 查询，Earth Engine 负责空间栅格、遥感目录和受控计算。两者都不能替代 Data Commons 的实体解析、统计变量语义和图关系能力。

Google 曾在 BigQuery Analytics Hub 发布 Data Commons 表，但官方已说明该表不再更新并可能下线，因此不得把该镜像作为删除本 Provider 的依据。

## 允许操作

```text
catalog-capabilities
resolve-place
resolve-indicator
node-properties
observations
```

## 安全边界

- 禁止任意 URL、SPARQL、自然语言生成接口、MCP、写操作和个人数据查询；
- 每张票据最多执行一次只读请求；
- 不允许将 BigQuery、Earth Engine 与 Data Commons 静默互相降级；
- 上游停用或配额耗尽时显式失败，不伪造数据。
