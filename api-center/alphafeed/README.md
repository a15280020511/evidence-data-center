# AlphaFeed 中国与全球证券行情

正式票据前缀和独立 Repository Secret：

```text
[api-alphafeed]
ALPHAFEED_API_KEY
```

Provider 使用官方 `alphafeed==0.1.4` Python SDK，固定开放 10 项操作，覆盖：

- 实时行情；
- 单只与批量 K 线；
- 单只与批量日内分时；
- A 股五档盘口；
- 单只与批量标的信息；
- 复权因子；
- 本地能力目录。

每张票据只执行一个固定 SDK 方法；证券代码、标的池、周期、复权方式、批量数量和响应体积均受限制。API Key 仅由 GitHub Actions 后端注入，不进入 Issue、日志、目录或 Artifact。禁止任意 SDK 方法、WebSocket、交易、下单和写操作。
