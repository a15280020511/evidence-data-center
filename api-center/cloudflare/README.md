# Cloudflare Intelligence Provider

固定接入 Cloudflare Browser Rendering、Radar 和 URL Scanner 只读能力。

## 正式入口

- Issue 前缀：`[intel-cloudflare]`
- Provider：`cloudflare`
- 每张票据最多执行一个固定 Cloudflare API 请求。

## 后台配置

- `CLOUDFLARE_API_TOKEN`：Cloudflare Custom Token。建议仅授予 `Browser Rendering - Edit`、`Radar - Read`、`URL Scanner - Read`。
- `CLOUDFLARE_ACCOUNT_ID`：32 位 Cloudflare Account ID。

禁止使用 Global API Key。Browser Rendering 仅允许公网 HTTPS URL，不接受 Cookie、代理、自定义请求头、浏览器脚本或任意 API 路径。URL Scanner 只读取已有扫描，不提交新扫描。
