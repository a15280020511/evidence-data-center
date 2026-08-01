# Agent Toolbelt AI 股票研究与代理工具

正式票据前缀：

```text
[api-agent-toolbelt]
```

正式凭据：

```text
GitHub Repository Secret: AGENT_TOOLBELT_KEY
```

Provider 固定访问：

```text
https://www.agenttoolbelt.live
```

固定开放 **29 项能力**：

- 1 项本地能力目录；
- 8 项美股研究：投资论点、盈利质量、内部人信号、估值、多空论证、股票比较、护城河和自选股扫描；
- 20 项通用工具：文本提取、Token 计算、Schema 生成、CSV 转 JSON、Markdown 转换、公开网页元数据与摘要、正则、Cron、地址标准化、色板、品牌包、图片元数据清理、会议行动项、提示词优化、文档比较、合同条款提取、模拟 API 响应、依赖漏洞审计和上下文打包。

安全边界：

- 每个票据最多一次上游请求；
- 仅允许固定 `/api/tools/<allowlisted-tool>` 路径；
- 不开放 Watchlist 创建、更新、删除、提醒或任何其他写接口；
- 不开放交易、下单、Webhook、任意工具名、任意主机或客户端凭据；
- URL 工具只接受公开 HTTPS 地址，拒绝本机、私网、保留地址字面量和带账号密码的 URL；
- 票据只允许公开、非个人数据。合同、会议记录和其他文本不得包含个人信息或机密材料；
- 股票研究输出属于第三方自动化分析，不构成投资建议；合同分析不构成法律意见；
- 上游调用会消耗免费额度或产生费用，API 中心不会自动循环或后台监控。

Agent Toolbelt 官方 API 使用 Bearer Key。未配置 `AGENT_TOOLBELT_KEY` 时，本地能力目录仍可读取，但真实上游调用会返回结构化缺失凭据错误。
