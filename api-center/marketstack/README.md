# Marketstack Provider

Ticket prefix: `[intel-marketstack]`

Repository Secret:

```text
MARKETSTACK_ACCESS_KEY
```

固定上游：`https://api.marketstack.com/v2`

本 Provider 只开放 Marketstack 免费计划可用的只读能力：

- `catalog-capabilities`
- `eod-latest`
- `eod-history`
- `eod-by-date`
- `dividends`
- `splits`
- `tickers-list`
- `ticker-info`
- `exchanges-list`
- `currencies-list`
- `timezones-list`

默认安全边界：

- 每张票据只发送一次 HTTPS GET 请求，不自动重试，避免重复消耗月度额度。
- 每张票据最多 5 个证券代码；Marketstack 会按证券代码计费请求数。
- 历史日期跨度最多 366 天，与免费计划的一年历史范围一致。
- `limit` 最大 100，禁止自动翻页和批量下载。
- API Key 仅由 GitHub Actions 后端注入，不得写入 Issue、目录、日志或 Artifact。
- 不开放盘中、实时轮询、WebSocket、债券、ETF、商品、企业基本面、EDGAR、交易或写入能力。

Marketstack 免费计划当前公开额度为每月 100 次请求，提供 EOD、最多一年历史、拆股与分红、证券和交易所目录、币种及时区数据。上游计划和配额可能变化，执行结果以账户实际权限为准。
