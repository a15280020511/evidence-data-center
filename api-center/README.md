# 独立情报中心

情报中心是三个业务中心中的受控取数层。它与专家研判中心、计算推演中心不共享依赖、任务状态、运行目录或业务逻辑，也不能直接调用它们。自定义 GPTs 是唯一使用中心和唯一跨中心中继；普通网页 GPT + GitHub 插件是维修中心。

## 最大安全只读策略

情报中心执行 `maximum-safe-readonly`：在固定官方后端、固定只读能力、参数白名单、请求与响应上限、Secret 隔离和证据回执不变的前提下，最大化暴露已接入上游的高价值公共数据能力。

统一能力规模不在本文硬编码，以以下确定性生成文件为准：

- `api-catalog.json`：机器可读完整能力目录；
- `api-catalog.md`：人类和 GPTs 可读目录；
- `connector-manifest.json`：普通连接器底层注册表；
- `connectors/*.connector.json`：单连接器完整声明合同；
- 各托管提供方的 `provider-catalog.json`：固定操作和参数 Schema。

目录公开能力名称、用途、固定端点、方法、参数白名单、响应合同、地域、新鲜度、成本等级、限制、Secret 环境变量名称和 SHA-256；绝不公开 Secret 值、Authorization、Cookie、私有凭据、预签名下载地址或用户个人数据。

目录由以下命令确定性生成：

```text
python api-center/build_config.py
python api-center/build_catalog_market_search.py
```

新增或修改能力时，必须同步提交生成后的 `api-catalog.json` 和 `api-catalog.md`，并通过 Git diff 确定性校验。

## Secret 隔离

一个外部 API 服务对应一个独立 Repository Secret。不得把多家 API 的 Key、Token 或 AppID 拼接到 JSON、文本或总 Secret 中。

普通连接器当前使用：

```text
AMAP_API_KEY
BAIDU_MAP_API_KEY
NEWSAPI_API_KEY
```

新增托管提供方分别使用：

```text
TUSHARE_API_TOKEN
EODHD_API_TOKEN
ALPHA_VANTAGE_API_KEY
ALPHAFEED_API_KEY
XWEATHER_CLIENT_SECRET
WOLFRAM_ALPHA_APP_ID
LLAMA_CLOUD_API_KEY
MX_APIKEY
EM_API_KEY
```

以上凭据不与其他金融、搜索、计算知识或文档解析服务复用。Secret 只能在后端注入，不能进入仓库、Issue、日志或 Artifact。完整规则见 `SECRET_ISOLATION_POLICY.md`。

## 普通只读连接器

普通 `[api]` 票据仅允许调用 `connector-manifest.json` 中已启用的固定 GET 连接器和白名单参数。典型能力包括：

- 高德和百度地图的地理编码、POI、路线、距离、天气与路况；
- Open-Meteo 天气、气候、海洋、洪水、空气质量和历史数据；
- 世界银行、DBnomics、Wikidata、OpenStreetMap；
- NewsAPI 的 Everything、Top Headlines 和 Sources。

正式票据未配置远程网关时，可以在 GitHub Actions 中启动临时回环 KrakenD 网关；所需 Secret 只写入本次 Runner 临时环境文件，并在任务结束前删除。

## 托管提供方


托管提供方共同遵守：

```text
固定票据前缀
固定 Provider ID
固定只读操作目录
每个操作独立参数 Schema
固定官方 HTTPS 主机
后端凭据注入
请求、超时、分页和响应体积上限
结构化 Snapshot、Diagnostics 和 Artifact
禁止任意 URL、任意请求头、任意代码、交易和业务数据写回
```

部分上游以固定 POST 协议实现只读取数或只读源转换。该协议不等于开放写操作：请求体必须由白名单参数构造，不能指定任意 URL、Webhook、回调、存储目标或用户自定义请求头。


## BaoStock 中国证券免费数据

`api-center/baostock/` 通过官方 `baostock==0.9.3` Python 客户端提供免密、只读的中国证券数据。正式票据前缀为 `[api-baostock]`，无需 Repository Secret。固定开放 20 项能力，覆盖交易日历、全部证券、证券基础、历史 K 线、复权因子、行业、三类主要指数成分、六类财务能力指标、业绩快报/预告、存款利率和 Shibor。每张票据只允许一次登录、一次白名单查询和一次登出，禁止任意函数、任意主机、代码执行、交易、下单和写入。

## Tushare Pro 中国金融数据

`api-center/tushare/` 使用官方 HTTPS JSON API：

```text
POST https://api.tushare.pro
```

正式票据前缀：

```text
[api-tushare]
```

独立 Repository Secret：

```text
TUSHARE_API_TOKEN
```

当前固定开放 20 项操作，其中一项为本地能力目录，19 项为上游只读数据：

- 交易日历和股票基础信息；
- A 股日线、周线、月线、复权因子和每日估值指标；
- 个股资金流、融资融券汇总和龙虎榜；
- 利润表、资产负债表、现金流量表和财务指标；
- 指数基础信息和指数日线；
- 基金基础信息和基金净值；
- 沪深港通持股明细。

执行器只允许目录中登记的 `api_name`，Token 仅在 HTTPS POST JSON 中注入。每张票据最多一次正常请求和一次瞬态故障重试。实际可用接口、频率和历史范围由 Tushare 账户积分及权限决定；权限不足会返回结构化 `TUSHARE_PERMISSION_DENIED`，不会伪造空数据。

## EODHD 全球金融市场数据

`api-center/eodhd/` 使用固定官方 HTTPS GET 接口，票据前缀和独立 Secret 为：

```text
[api-eodhd]
EODHD_API_TOKEN
```

开放 25 项只读操作，覆盖全球交易所和证券目录、历史与实时行情、基本面、公司行动、技术指标、新闻情绪、股票筛选、企业日历、宏观事件以及交易时段和节假日。上游套餐决定实际数据范围与额度；情报中心不开放 WebSocket、交易、下单、账户操作、任意 URL 或任意请求头。

## Alpha Vantage 全球金融与宏观数据

`api-center/alpha-vantage/` 使用固定官方 HTTPS GET 端点，票据前缀和独立 Secret 为：

```text
[api-alpha-vantage]
ALPHA_VANTAGE_API_KEY
```

固定开放 66 项只读操作，覆盖全球股票、指数、期权、基本面、公司行动、新闻情绪、外汇、数字资产、商品、美国宏观经济和技术指标。每张票据最多一次上游请求，Provider 全局串行，不自动重试，以保护官方免费密钥每日 25 次的标准额度。部分函数、实时或延迟市场数据以及完整历史范围需要 Alpha Vantage 付费权限；权限或额度不足会返回结构化诊断，不会伪造空数据。

## World Bank 世界银行开放数据

World Bank 已通过 9 个普通只读连接器接入，无需 API Key，覆盖指标目录、指标元数据、国家/地区、收入等级、贷款类型、主题、数据源、指标观测值和 JSON-stat 输出。本次不重复建设第二套 Provider，只强化统一目录和回归验收。

## Overture Maps 全球开放地图数据

`api-center/overture-maps/` 使用 Overture 官方 STAC 目录、匿名对象存储和固定 Python 客户端：

```text
[api-overture]
```

无需 Repository Secret。固定开放 7 项只读操作，覆盖发布版本、要素类型、城市级边界框计数与有限 GeoJSON 提取、GERS 查询。禁止全量全球下载、任意对象存储路径、任意 URL 和写操作。

## OECD Data Explorer SDMX

`api-center/oecd/` 固定访问 OECD 官方免费 SDMX REST API：

```text
[api-oecd]
https://sdmx.oecd.org/public/rest/v1
```

无需 Repository Secret。固定开放 6 项只读操作，覆盖数据流、数据结构、代码表和按维度键/时间范围取数；每张票据最多一次上游请求。

## AlphaFeed 中国与全球证券行情

`api-center/alphafeed/` 使用官方 Python SDK，正式票据前缀和独立 Secret 为：

```text
[api-alphafeed]
ALPHAFEED_API_KEY
```

固定开放 10 项只读操作，覆盖 A股、ETF、美股、港股实时行情、K线、分时、盘口、标的信息和复权因子。禁止任意 SDK 方法、WebSocket、交易、下单和写操作。

## Xweather 全球专业天气数据

`api-center/xweather/` 固定访问 Xweather Weather API：

```text
[api-xweather]
Repository Variable: XWEATHER_CLIENT_ID
Repository Secret:   XWEATHER_CLIENT_SECRET
```

固定开放 10 项核心只读能力，覆盖地点解析、实时观测、插值天气条件、最长 15 日预报、官方天气预警、空气质量、日月、月相和历史观测日汇总。部分端点受账户套餐、区域和调用倍率约束；禁止任意 URL、路线批量、Webhook 和写操作。

## Wolfram|Alpha 计算知识

`api-center/knowledge-tools/` 固定开放四项操作：

```text
catalog-capabilities
full-results
short-answer
llm-result
```

正式票据前缀与独立 Secret：

```text
[api-wolfram]
WOLFRAM_ALPHA_APP_ID
```

执行器只调用 Wolfram|Alpha 官方 Full Results、Short Answers 和 LLM API 固定 GET 端点。输入最长 2,000 字符；单位、语言、位置和上游超时均受 Schema 限制；不开放任意 URL、图片端点、任意请求头或写入能力。

## LlamaParse 文档解析

`api-center/knowledge-tools/` 固定开放三项操作：

```text
catalog-capabilities
parse-public-document
get-job
```

正式票据前缀与独立 Secret：

```text
[api-llamaparse]
LLAMA_CLOUD_API_KEY
```

LlamaParse 仅接受固定白名单公共文档来源，当前包括 GitHub 原始文件、arXiv、CVF、ACL Anthology、NeurIPS Proceedings、SSRN、OpenReview、SEC Archives 和 AnnualReports。禁止普通任意网站、HTTP、IP 地址、localhost、自定义端口、URL 凭据、Webhook 和用户自定义请求头。

解析操作使用官方 Parse v2 创建一次受限作业，再在同一票据中有限轮询；支持 `fast`、`cost_effective`、`agentic`、`agentic_plus` 四个固定 tier，最多 200 页，轮询最长 600 秒。输出会移除 Authorization、密钥以及 `presigned_url`、`download_url`、`signed_url` 等临时下载地址。

## 正式数据任务

普通连接器创建标题以 `[api]` 开头的 Issue；托管提供方使用各自固定前缀。GitHub Actions 将执行：

```text
校验票据与事件发起者
→ 校验 Provider、操作和参数 Schema
→ 后端注入本次唯一外部凭据
→ 执行受限只读请求或只读源转换
→ 检查 HTTP 与上游业务状态
→ 过滤 Secret、临时下载地址和敏感字段
→ 生成 Snapshot、Diagnostics、Manifest 和 Artifact
→ 将可验证摘要写回 Issue
```

所有 API 票据只接受公开、非个人数据。不得在公开 Issue 中提交个人轨迹、账户信息、隐私数据、受监管数据、私有文档 URL 或任何 Secret。

## 安全边界

情报中心拒绝：

- 明文密钥或客户端覆盖后端凭据；
- 未启用连接器或未登记的托管操作；
- 非白名单参数、任意 URL 或任意文档来源；
- 自定义请求头、Cookie、Authorization 和代理地址；
- PUT、PATCH、DELETE 以及未登记的 POST；仅允许 Tushare 固定只读取数 POST 和 LlamaParse 固定解析作业 POST；
- 交易、下单、账户操作和经纪商执行；
- 任意 Python、Shell、Lua、Go 插件或外部代码；
- 私网、保留地址和云元数据地址；
- 私人、受监管或需要访问控制的文档和数据声明。

静态校验不能替代生产出站防火墙、网络策略和上游账户权限管理。

## 与其他中心的关系

情报中心不能直接调用计算推演中心或专家研判中心。允许的业务协作是：

```text
情报中心产生 Snapshot
→ GPTs 读取正文、Manifest 和 SHA
→ GPTs 按任务需要选择计算或专家中心
→ GPTs 创建新的正式票据
```

调用顺序由 GPTs 组合，但必须满足治理仓库冻结合同中的输入依赖、证据和循环限制；业务运行时不得跨仓库直接读取或调用其他中心。

## Google Data Commons

- Provider: `data-commons`
- Ticket prefix: `[api-dc]`
- Secret: `GOOGLE_DATA_COMMONS_API_KEY`
- Authentication: REST V2 `X-API-Key` header
- Fixed read-only operations: 5
- BigQuery and Earth Engine continue to use `GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON`; Data Commons is intentionally isolated.

## 和风天气 QWeather

- Provider: `qweather`
- Ticket prefix: `[api-qweather]`
- Secret: `QWEATHER_API_KEY`
- Fixed Host: `ka6r72kcc3.re.qweatherapi.com`
- Authentication: backend-only `X-QW-Api-Key`
- Fixed read-only operations: 18


## 东方财富妙想 MCP

`api-center/miaoxiang-mcp/` 使用东方财富官方 Streamable HTTP MCP Server：

```text
https://mxapi.eastmoney.com/mxds/mcp
```

正式票据前缀和独立 Secret：

```text
[api-mx-mcp]
EM_API_KEY
```

MCP 协议固定为 `2025-11-25`，鉴权只通过后端 `em_api_key` 请求头注入。当前固定开放 11 个上游只读工具，覆盖 A股、港股、美股、基金、债券、指数板块、宏观经济、新闻研报、公告披露和证券筛选；连同本地能力目录与 `tools/list`，总计 13 项操作。禁止任意 JSON-RPC 方法、任意 MCP 工具名、Resources、Prompts、自选股修改、模拟交易和真实交易。

原有 `api-center/miaoxiang/` 是 Skills REST Provider，使用 `MX_APIKEY`（`mkt_` 类型）；MCP Provider 使用 `EM_API_KEY`（`em_` 类型）。两类密钥必须独立保存，不能互换。


## Browserless 托管浏览器 API

`api-center/browserless/` 使用 Browserless Cloud 固定 REST 主机：

```text
https://production-sfo.browserless.io
```

正式票据前缀和独立 Repository Secret：

```text
[api-browserless]
BROWSERLESS_TOKEN
```

固定开放 8 项操作：本地能力目录、JavaScript 渲染 HTML、CSS 选择器结构化抓取、截图、PDF、Lighthouse 性能审计、受限 Web 搜索和站点地图。Search 与 Map 可能要求 Browserless Cloud 套餐。

安全边界禁止 BrowserQL、BaaS/WebSocket、Function、Download、Export、Unblock、任意 JavaScript、Profile、Cookie、Authorization、自定义请求头、代理配置、CAPTCHA 求解和登录态页面。目标只允许公开 HTTPS URL；二进制截图和 PDF 只进入 Artifact。

## WHO GHO OData 全球卫生数据

`api-center/who-gho/` 通过 WHO Global Health Observatory 的公开 OData 兼容端点读取全球卫生指标：

```text
[intel-who-gho]
https://ghoapi.azureedge.net/api
无需 Repository Secret
```

固定开放 8 项只读操作，覆盖维度、维度值、指标目录、指标搜索、国家、地区和按国家/地区、年份、性别筛选的指标观测值。禁止客户端提交任意 OData 表达式、任意 URL、自动翻页和整库下载。WHO 已公告旧 GHO OData 将迁移至 World Health Data Hub 新实现，因此该 Provider 保留迁移监测标记，不把当前兼容端点视为永久合同。

## Mediastack 全球新闻情报

- Provider：`mediastack`
- 票据前缀：`[intel-mediastack]`
- 独立 Secret：`MEDIASTACK_API_KEY`
- 固定开放：最新新闻、关键词检索、历史新闻和来源目录，共5项能力。
- 免费层：官方当前标示每月100次请求，使用延迟新闻；历史数据和商业使用取决于套餐。
- 强制单请求、最多100条、禁止自动翻页、后台监控和文章正文抓取。

## Statistics of the World 全球统计

- Provider：`statistics-of-the-world`
- 工单前缀：`[intel-sotw]`
- 可选 Repository Secret：`SOTW_API_KEY`
- 11 个固定只读操作，覆盖国家、指标、历史、排名、搜索、国家比较和高频序列。
- 禁止全量 bulk、自然语言 chat、任意路径、自动分页和写操作。
- 定位为次级聚合证据源，重要结论应回查 IMF、World Bank、WHO、FRED、ECB 或 UN 原始来源。


## AISstream 全球船舶实时AIS

```text
Provider: aisstream
Ticket prefix: [intel-aisstream]
Repository Secret: AISSTREAM_API_KEY
Operations: 4
Fixed endpoint: wss://stream.aisstream.io/v0/stream
```

只允许短时、有限区域、有限消息数的只读AIS采集。禁止全球无限订阅、后台常驻、流转发、任意WSS端点、客户端密钥、写操作和交易执行。

## 互联网档案馆 Internet Archive

```text
Provider: internet-archive
Ticket prefix: [intel-internet-archive]
Secret: none
Operations: 6
Fixed hosts: archive.org, web.archive.org
```

支持受控馆藏搜索、项目元数据、文件目录、Wayback可用性和有限CDX捕获记录。禁止上传、删除、登录、借阅、文件内容下载、网页正文回放抓取和批量镜像。
