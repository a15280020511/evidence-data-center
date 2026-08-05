# 全球来源自动发现控制面

该目录把现有全球开放 API、机构数据、专业数据、文献、知识库和网页读取能力收敛为一个每日自动发现入口，不替代已有的固定 Provider。

## 覆盖范围

关键词矩阵覆盖全球地区与主要语言，以及政府、监管机构、国际组织、智库、大学、研究所、实验室、图书馆、档案馆、基金会、协会、标准组织、交易所和公共事业单位；行业覆盖宏观、金融、商业、贸易、海关、税收、就业、人口、医疗、教育、农业、能源、环境、气象、海洋、卫星、空间地理、交通、航运、航空、物流、通信、网络安全、AI、半导体、制造、地产、矿业、零售、旅游、法律、政策、安全、灾害、社会行为与发展等。

发现对象包括 REST/OpenAPI/GraphQL、远程 MCP、CKAN、Socrata、ArcGIS REST、STAC、SPARQL、SDMX、OAI-PMH、RSS/Atom、批量下载和可公开读取网页。

## 自动接入边界

“自动接入”指进入 `registry.json` 的固定 URL 只读注册表，并可通过 `[intel-discovered-source]` 票据执行一次有界 GET。只有同时满足以下条件的来源才会自动接入：

- HTTPS，且不是本地地址、私网地址或带凭据 URL；
- 无需 Key，固定 URL，只读；
- 机构域名可信；
- 条款没有明确禁止自动访问；
- 有界健康探测通过；
- 来源类型在允许名单内。

发现到的本地 MCP 包、npm/pip/Docker 命令、未知二进制、写接口、付费/授权接口不会自动执行。远程 MCP 也必须是可信域名上的 HTTPS 只读入口。

## 搜索引擎

每天轮换关键词组合并使用：

1. APIs.guru 公共 OpenAPI 目录；
2. GitHub Code Search；
3. Tavily（配置 `TAVILY_API_KEY` 时）；
4. Exa（配置 `EXA_API_KEY` 时）。

系统同时读取 World Bank 国家目录，把各国家和地区名称加入轮换轴。轮换游标保证覆盖面逐日扩展，而不是每天重复相同关键词。全互联网不可能一次穷尽，因此系统采用持续扩展、去重和复核模式。

## 通知

高价值且明确需要 Key 的来源只进入候选区，不自动启用。工作流优先使用 Repository Secret `SERVERCHAN_SENDKEY`；兼容 `SERVERCHAN_KEY` 或 `SCKEY`。Server酱未配置或推送失败时，自动创建或更新 `[source-discovery-key]` GitHub Issue，避免静默遗漏。

## 每日时间

GitHub Actions cron 为 `30 1 * * *`，即每天韩国时间 10:30（UTC 01:30）。GitHub 对计划任务可能存在平台级延迟。
