# IMF SDMX 3.0

通过 IMF 当前官方 SDMX 3.0 API 读取全球宏观、财政、贸易、价格、货币金融与国际收支统计。

## 配置

```text
GitHub Actions Secret: IMF_API_KEY
```

该值应为 IMF Developer Portal 签发的 API 订阅密钥。

## 执行边界

- 票据前缀：`[intel-imf]`
- 固定主机：`api.imf.org`
- 密钥仅通过 `Ocp-Apim-Subscription-Key` 后端请求头发送。
- 每票据一次 GET，不自动翻页或重试。
- 不允许任意 URL、SDMX 资源类型、请求头或写操作。
- HTTP 状态与 Content-Type 在正文解析前记录，HTML 拒绝页不会再被误报成普通 JSON 错误。
