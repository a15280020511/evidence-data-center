# 联合国 UN Comtrade API

该托管 Provider 固定访问联合国统计司官方端点：

```text
https://comtradeapi.un.org
```

不允许票据覆盖或替换该主机。

正式票据前缀与独立 Repository Secret：

```text
[intel-un-comtrade]
UN_COMTRADE_API_KEY
```

## 能力

固定开放 10 项只读操作：

1. `catalog-capabilities`：读取本地安全能力目录；
2. `preview-trade`：无需密钥预览贸易数据，最多 500 条；
3. `final-trade`：使用 Subscription Key 读取正式货物或服务贸易数据；
4. `tariffline-trade`：读取货物关税行数据；
5. `data-availability`：查询数据集可用性和发布日期；
6. `live-updates`：读取最近发布和修订进度；
7. `metadata`：读取数据集说明、脚注和发布元数据；
8. `trade-balance`：读取货物贸易差额工具结果；
9. `reporters-reference`：读取报告国家和地区代码；
10. `partners-reference`：读取伙伴国家和地区代码。

覆盖货物与服务、年度与月度、HS/SITC/BEC/EBOPS 等上游支持的分类，并支持报告方、伙伴方、商品、流向、第二伙伴、运输方式和海关程序等受约束筛选。

## 免费账户边界

UN Comtrade 免费基础账户可在 Developer Portal 申请 Subscription Key。官方当前说明包括：

- 免费账户 API 调用上限为每日 500 次；
- 无密钥 Preview 每次最多 500 条；
- 免费登录账户正式数据接口可达到每次 100,000 条。

情报中心不会使用上游最大值，而是将正式数据、关税行和贸易差额硬限制为每次最多 5,000 条，以降低超时、配额耗尽和证据包过大的风险。

## 安全边界

- 固定主机 `comtradeapi.un.org`；
- 每张票据只发送一次 GET；
- 不自动重试、不自动翻页；
- 最多 12 个时期、5 个报告方、20 个商品代码和 10 个伙伴；
- 最大响应体 20 MB；
- 禁止 Bulk API、Async API、文件下载和后台递归抓取；
- 禁止任意 URL、主机、路径、请求头和客户端提供密钥；
- `UN_COMTRADE_API_KEY` 仅由 GitHub Actions 后端注入查询参数；
- 响应在写入 Snapshot、Diagnostics 和 Artifact 前递归清除 Subscription Key。

## 票据示例

```json
{
  "task_id": "un-comtrade-china-energy-imports-001",
  "provider": "un-comtrade",
  "operation": "final-trade",
  "objective": "读取中国从全球进口HS27能源产品的年度贸易数据",
  "parameters": {
    "type_code": "C",
    "frequency": "A",
    "classification": "HS",
    "periods": [2023, 2024],
    "reporter_codes": [156],
    "commodity_codes": ["27"],
    "flow_codes": ["M"],
    "partner_codes": [0],
    "max_records": 5000,
    "include_descriptions": true
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

Subscription Key 需在 UN Comtrade Developer Portal 的 Free APIs 产品中申请后，配置到仓库 Secret `UN_COMTRADE_API_KEY`。
