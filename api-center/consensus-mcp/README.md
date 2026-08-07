# Consensus MCP

情报中心通过 Consensus 官方 Streamable HTTP MCP Server 检索同行评审论文。

## 官方端点

`https://mcp.consensus.app/mcp`

## 默认费用模式

- GitHub Actions 默认使用 **anonymous-free**，不需要 Secret。
- 官方当前文档：匿名模式每次最多 3 篇论文，月搜索次数不限。
- Consensus Free 账号在支持交互式 OAuth 的 MCP 客户端中为每次最多 10 篇、每月 30 次。
- 本 Provider 不尝试在 GitHub Actions 中持久化交互式 OAuth 登录。
- `CONSENSUS_MCP_BEARER_TOKEN` 仅作为可选企业/API Key Bearer 模式；不自动购买、不自动升级。

## 安全边界

- 只允许固定 `search` MCP 工具。
- 允许 `initialize`、`notifications/initialized`、`tools/list`、`tools/call` 协议步骤。
- 禁止任意 JSON-RPC 方法、任意工具名、写操作、网页抓取、付费 API 自动启用。
- 查询内容发送给 Consensus；返回内容仅保存公开学术论文元数据和摘要类结果。
- 所有请求均为 HTTPS，拒绝重定向，响应大小和超时均有上限。

## Issue 票据示例

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

## 验证

```bash
python api-center/consensus-mcp/consensus_mcp_task.py canary \
  --output consensus-mcp-canary.json
```

Canary 会真实执行 `initialize -> tools/list`，并以匿名免费模式调用一次 `search`。
