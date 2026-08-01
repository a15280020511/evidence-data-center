# Agent Toolbelt 通用代理工具

正式票据前缀：

```text
[api-agent-toolbelt]
```

正式凭据：

```text
GitHub Repository Secret: AGENT_TOOLBELT_KEY
```

Provider固定访问：

```text
https://www.agenttoolbelt.live
```

固定开放 **21项能力**：

- 1项本地能力目录；
- 20项通用工具：Schema生成、文本提取、Token计算、CSV转JSON、Markdown转换、公开网页元数据、正则生成、Cron生成、美国地址标准化、色板、文档比较、合同条款提取、提示词优化、会议行动项、图片元数据清理、品牌包、模拟API响应、依赖漏洞审计、网页摘要和上下文打包。

明确删除并禁止以下8项仅限美股的研究工具：

```text
stock-thesis
earnings-analysis
insider-signal
valuation-snapshot
bear-vs-bull
compare-stocks
moat-analysis
watchlist-scan
```

这些操作不再出现在Provider目录、票据Schema或统一API目录中；提交对应票据会在本地校验阶段被拒绝，不会消耗Agent Toolbelt额度。

安全边界：

- 每个票据最多一次上游请求；
- 仅允许固定 `/api/tools/<allowlisted-tool>` 路径；
- 不开放任何股票研究、Watchlist创建/更新/删除/提醒或其他写接口；
- 不开放交易、下单、Webhook、任意工具名、任意主机或客户端凭据；
- URL工具只接受公开HTTPS地址，拒绝本机、私网、保留地址字面量和带账号密码的URL；
- 票据只允许公开、非个人数据；合同、会议记录和其他文本不得包含个人信息或机密材料；
- 合同分析不构成法律意见；
- 上游调用会消耗免费额度或产生费用，API中心不会自动循环或后台监控。

Agent Toolbelt官方API使用Bearer Key。未配置 `AGENT_TOOLBELT_KEY` 时，本地能力目录仍可读取，但真实上游调用会返回结构化缺失凭据错误。
