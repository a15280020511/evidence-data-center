# Consensus MCP

情报中心已加入 Consensus 官方 Streamable HTTP MCP Provider，用于检索同行评审论文；不抓取 Consensus 网页。

## 官方端点

`https://mcp.consensus.app/mcp`

## 免费账号怎么使用

Consensus 官方 Free 账号在支持交互式 OAuth 的 MCP 客户端中可使用免费 MCP。官方当前文档给出的 Free 配额是每次最多 10 篇、每月 30 次 MCP 搜索。

这与 GitHub Actions 的服务器端调用必须区分：2026-08-07 的真实 GitHub Actions 探测显示，直接向官方 MCP 发送无 Token 的 `initialize` 返回 HTTP 401。随后标准 OAuth 元数据发现成功，并确认：

- Authorization Code：支持
- Dynamic Client Registration：存在
- Client Credentials：不支持

因此，Free 账号可以通过 ChatGPT、Claude、Codex 等支持浏览器 OAuth 的客户端登录使用；但 GitHub Actions 不能靠 `client_credentials` 无人值守换取你的 Free 账号 Token。

## 当前情报中心状态

- Provider/协议层：**已接入**
- 固定只读工具：`search`
- OAuth 元数据发现：**可用**
- 无凭证裸连：**HTTP 401，按真实结果 fail-closed**
- GitHub Actions 自动论文搜索：**需要 OAuth 凭证桥或 Consensus 接受的 Bearer Token 后才能启用**
- 付费 API：**不会自动购买或启用**

`CONSENSUS_MCP_BEARER_TOKEN` 仅作为可选 Bearer Secret 接口。普通 Free 账号本身并不会给出一个可直接粘贴到 GitHub Actions 的永久 API Key。

## 安全边界

- 只允许固定 `search` MCP 工具。
- 允许 `initialize`、`notifications/initialized`、`tools/list`、`tools/call` 协议步骤。
- 禁止任意 JSON-RPC 方法、任意工具名、写操作、网页抓取、付费 API 自动启用。
- 查询内容会发送给 Consensus；返回内容只作为学术检索证据处理。
- HTTPS 固定主机；拒绝重定向；响应大小和超时有上限。
- OAuth/Bearer 凭证不得写入仓库、日志或 Artifact。

## 票据示例

Issue 标题：`[api-consensus-mcp] research`

```json
{
  "task_id": "consensus-demo-001",
  "provider": "consensus-mcp",
  "operation": "search",
  "objective": "检索因果推断领域的高质量同行评审研究",
  "parameters": {
    "query": "causal inference",
    "exclude_preprints": true
  },
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false
  },
  "acceptance": {
    "timeout_seconds": 30,
    "max_response_bytes": 1500000,
    "max_rows": 3
  }
}
```

如果没有有效 OAuth Bearer，该远程票据会失败关闭，不会降级成网页抓取。

## 验证

OAuth 元数据：

```bash
python api-center/consensus-mcp/oauth_probe.py \
  --output consensus-mcp-oauth-probe.json
```

远程 MCP Canary：

```bash
python api-center/consensus-mcp/consensus_mcp_task.py canary \
  --output consensus-mcp-canary.json
```

CI 会分别记录“协议/OAuth 是否可发现”和“是否存在可用 Bearer 并真正完成 search”，不会把 OAuth 可发现误报成论文搜索成功。
