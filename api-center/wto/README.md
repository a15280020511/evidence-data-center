# WTO Timeseries

通过 WTO 官方 Timeseries API 读取国际贸易、关税与市场准入统计。

- Secret：`WTO_API_KEY`
- 票据前缀：`[intel-wto]`
- 每票据一次 GET，不自动翻页或重试，最多 500 条。
