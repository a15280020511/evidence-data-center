# API Secret 隔离策略

## 规则

普通 `[api]` 工作流执行以下强制策略：

1. 一个外部 API 服务对应一个独立 Repository Secret。
2. 不允许把多家 API 的 Key、Token 或 AppID 拼接进 JSON、文本、列表或总 Secret。
3. 单个普通 `[api]` 票据最多引用一个需要密钥的上游 API 服务。
4. 同一家 API 的多个只读端点可以共享该服务自己的凭据，例如 NewsAPI 的 Everything、Top Headlines 和 Sources 共用 `NEWSAPI_API_KEY`，Wolfram|Alpha 的三种结果接口共用 `WOLFRAM_ALPHA_APP_ID`。
5. 无密钥公共 API 可以与一个有密钥 API 同票据执行，因为它们不会引入第二个凭据。
6. 需要同时调用两家有密钥 API 时，必须拆成两个独立票据，由 GPTs 在上层汇总结果。
7. 托管提供方同样坚持一服务一凭据；Tushare 只读取 `TUSHARE_API_TOKEN`，Wolfram|Alpha 只读取 `WOLFRAM_ALPHA_APP_ID`，LlamaParse 只读取 `LLAMA_CLOUD_API_KEY`。
8. Secret 只能由对应 GitHub Actions 工作流注入固定官方主机；客户端不得在票据中提供、覆盖或回显凭据。
9. Authorization、Cookie、预签名下载 URL、临时访问 URL 和 Secret 值不得进入 Issue、日志、Artifact 或能力目录。

## Google 例外


## 当前独立 API Secret

```text
AMAP_API_KEY
BAIDU_MAP_API_KEY
NEWSAPI_API_KEY
TUSHARE_API_TOKEN
ALPHA_VANTAGE_API_KEY
ALPHAFEED_API_KEY
XWEATHER_CLIENT_SECRET
WOLFRAM_ALPHA_APP_ID
LLAMA_CLOUD_API_KEY
```

每个 Secret 必须在 GitHub Repository Secrets 中分别创建、轮换和撤销。Secret 值不得进入仓库、Issue、日志或 Artifact。

Wolfram|Alpha 的 AppID 仅允许作为 `appid` 查询参数注入三个固定官方端点。LlamaParse Key 仅允许作为 Bearer 凭据注入 NA 或 EU 官方 Parse v2 主机；解析结果中的预签名下载地址必须删除后才能写入 Artifact。

天地图提供方已删除；`TIANDITU_API_KEY` 不再被任何工作流或代码读取。仓库设置中残留的旧 Secret 需由仓库所有者在 GitHub Settings 中手动删除。

Alpha Vantage Key 仅允许作为 `apikey` 查询参数注入 `https://www.alphavantage.co/query`；客户端不得覆盖 `function` 白名单或传入自己的密钥。

AlphaFeed Key 仅允许由 `api-center/alphafeed/` 的固定工作流注入官方 `alphafeed==0.1.4` SDK；客户端不得提交或覆盖 Key，不开放任意 SDK 方法、WebSocket、交易或下单。Overture Maps、OECD 和 World Bank 均为无密钥只读数据源。

Xweather 的公开 Client ID 作为 GitHub Repository Variable `XWEATHER_CLIENT_ID` 注入，唯一敏感凭据为 Repository Secret `XWEATHER_CLIENT_SECRET`。两者只发送至 `https://data.api.xweather.com` 的固定白名单 GET 端点，不写入仓库、Issue、日志或 Artifact。

## Agent Toolbelt

```text
Repository Secret: AGENT_TOOLBELT_KEY
GAPUP_API_KEY
```

The key is injected only into the dedicated Agent Toolbelt GitHub Actions job
as a Bearer token. It is never accepted from tickets, written to the unified
catalog, printed in comments, or persisted in artifacts. Failure messages are
redacted before diagnostics are written.


## Gapup MCP

```text
Repository Secret: GAPUP_API_KEY
```

该Key只允许作为 `x-api-key` 请求头发送至 `https://mcp.gapup.io/mcp`。客户端不得提交或覆盖Key。情报中心不保存钱包、不生成x402付款证明、不自动支付，也不把Key、Authorization或支付信息写入Issue、日志、目录或Artifact。

### Mediastack

```text
MEDIASTACK_API_KEY
```

仅由 Mediastack 票据工作流注入为后端 `access_key` 查询参数；不得出现在 Issue、目录、日志、Artifact、请求元数据或客户端参数中。

### Statistics of the World

```text
SOTW_API_KEY
```

该 Secret 为可选项，仅允许在 GitHub Actions 后端通过 `X-API-Key` 请求头注入。不得出现在 Issue、PR、目录、日志、测试夹具、Artifact、请求元数据或错误详情中。未配置时仅使用官方匿名免费层。聊天或工单中曾粘贴的 Key 必须先轮换再写入 Repository Secret。
