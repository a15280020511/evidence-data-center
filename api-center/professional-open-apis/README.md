# 全球专业行业开放 API

本模块把现有聚合层未覆盖或不能替代的专业数据能力封装为固定、只读、单请求操作。

## 首批行业能力

- 政府开放数据：data.gov.uk CKAN；
- 化学、药物与材料：PubChem PUG REST；
- 水文与环境传感器：USGS Water Services；
- 海洋生物与渔业：WoRMS；
- 高校、图书馆和科研权威实体：IdRef、Sudoc；
- 官方统计：英国 ONS；
- 农业与食品文献：FAO AGRIS Open Data Set。

## 安全和稳定边界

- 每张票据最多一个上游请求；
- 固定官方主机和固定路径；
- 禁止任意 URL、任意请求头、自动翻页、自动重试、重定向和写操作；
- 不接收个人数据或画像任务；
- 上游响应、时间和结果规模受限；
- 只有真实 GitHub Actions 验收通过后才从 `production_pending_live_acceptance` 升级为生产来源。

## Data Commons 与 FAO 状态

Data Commons 使用仓库 Secret `GOOGLE_DATA_COMMONS_API_KEY`，与 BigQuery、Earth Engine 分工不同。2026-08-05 的新真实票据再次完成地点解析，因此当前可正常使用。

FAOSTAT 必须区分三条链路：

1. 旧 `fenixservices` REST 路径已经在真实执行中返回上游错误，不能算生产可用；
2. 2026 年新的 FAOSTAT Developer Portal/API 采用账号或令牌鉴权，仓库尚未配置生产凭据；
3. 官方批量下载继续可免 Key 使用，AGRIS 开放数据索引也采用免 Key 的批量采集方式。

因此，当前可用的是 FAO/FAOSTAT 官方批量数据路径，而不是尚未配置认证的新交互式 FAOSTAT API。
