# Consensus（免费交互式学术来源）

Consensus 继续作为学术论文检索来源使用，但不再作为情报中心内需要凭证的自动化 API/MCP Provider。

## 当前策略

- **不要求 API Key**。
- **不要求 GitHub Secret**。
- 不再使用 `CONSENSUS_MCP_REFRESH_TOKEN`、`CONSENSUS_MCP_BEARER_TOKEN` 或任何 refresh-token bridge。
- 不在 GitHub Actions 中做无人值守 OAuth 登录。
- 不抓取 Consensus 网页。
- 不自动启用或购买 Consensus 付费 API。
- 需要论文证据时，优先通过当前支持 Consensus 的交互式客户端（例如 ChatGPT 中可用的 Consensus 研究连接器/MCP）使用其免费访问能力。

## 为什么不在 GitHub Actions 里裸连免费 MCP

2026-08-07 的真实验证显示，直接从无凭证 GitHub Actions 向 `https://mcp.consensus.app/mcp` 发起 MCP `initialize` 会返回 HTTP 401。Consensus 的免费使用路径可以由支持交互式 OAuth 的客户端完成，但这不等于 GitHub Actions 可以匿名、无凭证自动调用。

因此本仓库不伪造“匿名自动可用”能力，也不再要求仓库所有者配置 OAuth/Secret。

## 使用方式

当任务需要同行评审论文、系统综述、RCT、观察性研究或其他学术证据时：

```text
用户问题
  ↓
网页 GPT / 支持 Consensus 的交互式客户端
  ↓
Consensus 免费检索
  ↓
论文元数据 / 摘要 / DOI / 研究结论
  ↓
作为外部学术证据进入后续分析
```

该路径不需要在 `evidence-data-center` 仓库保存任何 Consensus 凭证。

## 边界

Consensus 目前属于**外部免费交互式学术来源**，不是治理仓可无人值守派发的 GitHub API Center Provider。因此，只有实际取得的论文结果及其可验证引用才可作为证据；不能把“Consensus 可用”本身当成已完成的 GitHub 数据采集任务。
