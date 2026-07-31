# 独立外部 API 接入中心

API 接入中心是三个业务中心中的受控取数层。它与专家研判中心、计算推演中心不共享依赖、任务状态、运行目录或业务逻辑，也不能直接调用它们。自定义 GPTs 是唯一使用中心和唯一跨中心中继；普通网页 GPT + GitHub 插件是维修中心。

## 最大安全只读策略

API 中心执行 `maximum-safe-readonly`：在固定官方后端、固定只读能力、参数白名单、请求与响应上限、Secret 隔离和证据回执不变的前提下，最大化暴露已接入上游的高价值公共数据能力。

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
WOLFRAM_ALPHA_APP_ID
LLAMA_CLOUD_API_KEY
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

API 中心拒绝：

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

API 中心不能直接调用计算推演中心或专家研判中心。允许的业务协作是：

```text
API 中心产生 Snapshot
→ GPTs 读取正文、Manifest 和 SHA
→ GPTs 按任务需要选择计算或专家中心
→ GPTs 创建新的正式票据
```

调用顺序由 GPTs 组合，但必须满足治理仓库冻结合同中的输入依赖、证据和循环限制；业务运行时不得跨仓库直接读取或调用其他中心。
