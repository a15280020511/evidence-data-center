# 东方财富妙想 MCP Provider

独立的只读 MCP Provider，固定连接东方财富官方服务：

- MCP Server：`mx-ds-mcp`
- URL：`https://mxapi.eastmoney.com/mxds/mcp`
- 传输：`StreamableHttp`
- MCP 协议：`2025-11-25`
- 独立 Secret：`EM_API_KEY`
- 鉴权请求头：`em_api_key`
- 票据前缀：`[api-mx-mcp]`

只开放实际探测并固定登记的 11 个只读工具。禁止任意 MCP 工具名、任意 JSON-RPC 方法、任意 URL/Host/Header、自选股修改、模拟交易和真实交易。

原有 `miaoxiang` Provider 是 Skills REST 接口，使用 `MX_APIKEY`（`mkt_` 类型）；本目录是 MCP 接口，使用 `EM_API_KEY`（`em_` 类型），两类密钥不得混用。
