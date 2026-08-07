# Consensus MCP

情报中心通过 Consensus 官方 Streamable HTTP MCP Provider 检索同行评审论文；不抓取 Consensus 网页，也不会自动启用付费 API。

## 官方端点

`https://mcp.consensus.app/mcp`

## 当前接入状态

- Provider / MCP 协议：**已接入**
- 固定只读工具：`search`
- OAuth Authorization Code：**支持**
- Refresh Token：**支持**
- Dynamic Client Registration：**支持**
- Client Credentials：**不支持**
- 已注册 public client：**已完成**
- PKCE：`S256`
- 回调：`http://127.0.0.1:8765/callback`
- 无凭证裸连：真实 GitHub Actions 探测为 **HTTP 401**
- 纯浏览器 Token Bridge：**不可用**；2026-08-07 实测注册与 token 端点没有可用 CORS
- GitHub Actions Free 账号路径：**本地一次 PKCE 授权 → Repository Secret → runner 内 refresh → 临时 Bearer → MCP**

## 一次性 Free 账号授权

这一步必须在可信电脑上执行，因为 Consensus 的 OAuth 需要浏览器交互，而且回调绑定 `127.0.0.1`。

安装依赖：

```bash
python -m pip install -r api-center/consensus-mcp/requirements.txt
```

执行：

```bash
python api-center/consensus-mcp/oauth_bootstrap.py bootstrap
```

脚本会：

1. 在本机生成 PKCE verifier / challenge 和随机 state；
2. 只监听 `127.0.0.1:8765`；
3. 打开 Consensus 官方 OAuth 授权页；
4. 你用 Free 账号登录并授权 `search`；
5. 本机收到授权码并校验 state；
6. 直接向 Consensus token endpoint 交换 access token + refresh token；
7. 默认保存到：
   `~/.config/evidence-data-center/consensus-oauth-token.json`
8. 本地文件按 0600 权限写入；脚本默认不打印 token。

如浏览器没有自动打开：

```bash
python api-center/consensus-mcp/oauth_bootstrap.py bootstrap --no-browser
```

终端会给出授权 URL，你在同一台电脑浏览器打开即可。

## 写入 GitHub Secret

授权完成后，仅在你自己的电脑上执行：

```bash
python api-center/consensus-mcp/oauth_bootstrap.py show-refresh-token
```

把输出值添加为仓库 Actions Secret：

`CONSENSUS_MCP_REFRESH_TOKEN`

不要把这个值发到 Issue、PR、聊天、日志或普通仓库文件。

如果以后你有 Consensus 接受的现成短期/长期 Bearer，也可以使用：

`CONSENSUS_MCP_BEARER_TOKEN`

现有 Bearer 优先于 refresh-token bridge。

## GitHub Actions 运行方式

有 `CONSENSUS_MCP_REFRESH_TOKEN` 后：

```text
GitHub Secret: refresh token
        ↓
oauth_refresh.py
        ↓
Consensus /oauth/token/
        ↓
短期 access token
        ↓
GITHUB_ENV（当前 runner 内存/临时环境）
        ↓
consensus_mcp_task.py
        ↓
https://mcp.consensus.app/mcp
```

Access token 会先通过 GitHub `add-mask` 隐藏，只写入当前 runner 的 `GITHUB_ENV`，不会进入仓库、Issue 或 Artifact。

### Refresh token 旋转

当前 GitHub 连接器不能安全自动改写 Repository Secret。因此：

- 如果 Consensus 刷新时**不旋转** refresh token：自动调用可以长期工作；
- 如果 Consensus 返回了**新的 refresh token**：`oauth_refresh.py` 会 **fail-closed**，不会把新 token 写进日志或 Artifact；需要重新跑本地 bootstrap 并更新 Secret。

这一点必须用你的真实 Free 账号完成第一次授权后再实测，仓库不会预先假设官方一定采用稳定 refresh token。

## 免费额度

Consensus 官方当前文档对 Free 账号给出的 MCP 配额为：每次最多 10 篇论文、每月 30 次 MCP 搜索。额度由 Consensus 账号套餐控制，不是 GitHub 或 ChatGPT 额度。

## 安全边界

- 只允许固定 `search` MCP 工具；
- 只允许协议必需的 `initialize`、`notifications/initialized`、`tools/list`、`tools/call`；
- 禁止任意 JSON-RPC 方法、任意工具名、写操作、网页抓取、付费 API 自动启用；
- OAuth public client 不包含 client secret；
- access / refresh token 不得进入仓库、Issue、PR、Artifact 或日志；
- 固定 HTTPS 上游，拒绝重定向；响应大小和超时有限制；
- 无有效凭证时 fail-closed，不降级抓 Consensus 网页。

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

CI 会区分：OAuth 元数据可发现、凭证桥是否可用、以及真实 `search` 是否成功，不把 OAuth 元数据成功误报为论文检索成功。
