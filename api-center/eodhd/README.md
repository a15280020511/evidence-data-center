# EODHD 全球金融市场数据

- Provider：`eodhd`
- 票据前缀：`[api-eodhd]`
- Repository Secret：`EODHD_API_TOKEN`
- 协议：固定 `GET https://eodhd.com/api/...`，后端注入 `api_token`。
- 当前开放 25 项固定只读操作。
- 禁止任意 URL、任意路径、任意请求头、WebSocket、交易、下单、账户修改和写入。

每张正式票据生成 Snapshot、Diagnostics、Manifest、摘要与 GitHub Actions Artifact；上游套餐、调用额度和数据范围由 EODHD 账户决定。
