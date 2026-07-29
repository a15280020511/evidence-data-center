# 独立外部 API 接入中心

API 接入中心是三个业务中心中的受控取数层。它与专家团中心、计算中心不共享依赖、任务状态、运行目录或业务逻辑，也不能直接调用它们。自定义 GPTs 是唯一使用中心和唯一跨中心中继；普通网页 GPT + GitHub 插件是维修中心。

## GPTs 能力目录

GPTs 使用 API 中心前应先读取：

- `api-catalog.json`：机器可读完整能力目录；
- `api-catalog.md`：人类和 GPTs 可读目录；
- `connector-manifest.json`：底层注册表；
- `connectors/*.connector.json`：单连接器完整声明合同。

目录公开：

- 能力名称、用途和分类；
- 启用状态；
- 固定端点和方法；
- 输入参数白名单与示例；
- 返回字段和业务响应合同；
- 地域、新鲜度、成本等级和限制；
- 熔断、限流和SSRF策略；
- Secret环境变量名称；
- 连接器SHA-256。

目录绝不公开：

- Secret值；
- Authorization或Cookie；
- 私有部署凭据；
- 用户个人数据。

目录由以下命令确定性生成：

```text
python api-center/build_catalog.py
```

新增或修改连接器时，必须同步更新 `catalog-metadata.json`，重新生成目录，并通过 Git diff 校验。

## BigQuery、Earth Engine 与 AKShare 托管能力

BigQuery、Earth Engine和AKShare不伪装成普通KrakenD GET连接器。它们使用独立的
`google-cloud/provider-catalog.json`完整功能目录和`[api-gcp]`正式票据：

```text
GPTs读取统一api-catalog.json
→ 按需读取google-cloud/provider-catalog.json
→ 选择BigQuery目录/只读查询或Earth Engine目录/只读值计算
→ GitHub独立工作流执行并生成Artifact
```

托管目录开放数据集、表、字段、例程、模型、STAC数据集和Earth Engine算法信息；
执行仍严格只读，并受公共项目、扫描量、返回行数、表达式复杂度和资产权限限制。
认证Secret名称为`GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON`，值不进入目录或Artifact。

被BigQuery或Earth Engine等价替代的GDELT、NASA夜间灯光元数据和WorldPop普通连接器已删除，
避免重复维护。地图、路线、POI、天气和其他独立数据源继续保留。

## NewsAPI 新闻能力

NewsAPI作为普通只读连接器接入，开放官方三项能力：

- `newsapi-everything`：按关键词、时间、语言、来源和域名检索文章元数据；
- `newsapi-top-headlines`：按国家、类别、来源或关键词读取头条；
- `newsapi-sources`：读取可用于Top Headlines的来源目录。

三项能力共享后端Secret环境变量名：

```text
NEWSAPI_API_KEY
```

密钥通过后端`X-Api-Key`请求头注入，GPTs和正式票据不能提交、读取或覆盖密钥。使用GitHub Actions临时网关时，应将它加入现有Repository Secret `API_CENTER_SECRETS_JSON`，例如：

```json
{
  "AMAP_API_KEY": "已有高德密钥",
  "TIANDITU_API_KEY": "已有天地图密钥",
  "NEWSAPI_API_KEY": "NewsAPI密钥",
  "BAIDU_MAP_API_KEY": "百度地图开放平台服务端AK"
}
```

不要删除JSON中仍在使用的其他键，也不要把真实密钥写入仓库、Issue或Artifact。

NewsAPI只返回标题、来源、URL、摘要和受限正文片段，不提供完整文章正文。套餐限制、延迟、历史范围、请求配额和生产使用许可由NewsAPI账户决定；GPTs必须把返回内容作为新闻线索，并打开原始文章进行来源与日期核验。

## 正式数据任务

创建标题以 `[api]` 开头的 Issue，正文必须符合 `api-ticket.schema.json`。GitHub Actions 将：

```text
校验票据与去重
→ 从当前connector-manifest动态读取连接器
→ 仅允许启用的GET连接器和白名单参数
→ 选择远程认证网关或临时本地网关
→ 采集并检查HTTP状态、业务状态和非空数据
→ 生成结构化证据、Manifest和Issue回退正文
```

正式输出：

- `api-snapshot.json`
- `api-audit.json`
- `api-diagnostics.json`
- `api-console.log`
- `api-summary.md`
- `artifact-manifest.json`

API票据只接受公开、非个人数据。不得在公开Issue中提交个人轨迹、账户信息、隐私数据、受监管数据或任何Secret。

## 长期在线网关

GitHub可以验证并构建KrakenD镜像。需要低延迟直接访问时，仓库外平台负责长期运行、HTTPS、入站认证、出站网络策略、Secret、访问日志和回滚。

正式 `[api]` 任务不强制依赖长期部署：未配置远程网关时，可使用GitHub Actions中的临时回环网关。

## 执行模式

1. 同时配置 `API_GATEWAY_BASE_URL` 和 `API_GATEWAY_AUTH_TOKEN`：使用远程HTTPS网关；
2. 未配置远程网关：使用 `API_CENTER_SECRETS_JSON` 启动临时回环网关；
3. 所需配置或Secret缺失：返回 `API_BLOCKED`，不伪造数据。

`API_CENTER_SECRETS_JSON` 是GitHub Actions Repository Secret，内容为环境变量名到值的JSON对象。运行时只提取本次请求所需的键，写入Runner临时目录，并在任务结束前删除。该文件不得进入Artifact。

## 连接器

每个外部数据源是一个 `connectors/*.connector.json` 声明式插头。当前可用能力以 `api-catalog.json` 和 `connector-manifest.json` 为准，不在GPTs提示词中永久硬编码。

启用连接器必须定义：

- 固定公开端点；
- 固定后端主机和路径；
- 输入参数白名单；
- Secret注入环境变量名；
- `response_contract`；
- 固定熔断和可选限流；
- 对应的GPTs目录元数据。

## 新增连接器

1. 复制 `connectors/example.connector.json`；
2. 设置唯一ID、公开端点、后端地址和输入白名单；
3. 使用 `secret_header.env` 或 `secret_query.env` 声明Secret名称，不写入Secret值；
4. 为正式启用的GET连接器增加 `response_contract`；
5. 在 `catalog-metadata.json` 增加显示名称、用途、参数说明、示例和限制；
6. 运行 `python api-center/build_config.py`；
7. 运行 `python api-center/build_catalog.py`；
8. 提交连接器、KrakenD配置、Manifest和目录文件。

## 安全边界

连接器不执行自定义Python、Shell、Lua或Go插件，不允许任意URL。编译器和票据控制面拒绝：

- 明文密钥；
- 客户端传入后端密钥参数；
- 未启用连接器；
- 非白名单参数；
- 正式票据中的POST、PUT、PATCH、DELETE；
- 危险转发头；
- 私网、保留地址和云元数据地址；
- 缺少业务响应合同的正式连接器；
- 私人或受监管数据声明。

静态校验不能阻止DNS重绑定，生产平台仍需出站防火墙或网络策略。

## 与其他中心的关系

API中心不能直接调用计算或专家中心。允许的业务协作是：

```text
API中心产生Snapshot
→ GPTs读取正文、Manifest和SHA
→ GPTs按任务需要选择计算或专家中心
→ GPTs创建新的正式票据
```

调用顺序可以由GPTs自由组合，但必须满足本仓库 `governance-compatibility.json` 与治理仓库冻结合同的输入依赖、证据和循环限制；业务运行时不得跨仓库读取治理仓库。

## AKShare金融公开数据

AKShare使用独立`[api-akshare]`票据和固定函数白名单。它不需要API密钥，但上游网页接口可能变化，因此适配器固定版本、限制行数、输出Artifact并禁止任意函数、URL和交易执行。


## Open-Meteo 与百度地图

Open-Meteo以无密钥普通连接器接入，提供按经纬度读取当前、小时和逐日天气能力。
百度地图以三个后端注入密钥的普通连接器接入：地址转坐标、POI搜索和驾车路线规划。
百度地图密钥环境变量名为`BAIDU_MAP_API_KEY`，实际值只能存入Repository Secret
`API_CENTER_SECRETS_JSON`，不能写入Issue、仓库或Artifact。

## Wind AIFin Market

AIFin Market采用独立托管提供方，不伪装成普通KrakenD GET接口。正式票据前缀为
`[api-aifin]`，只允许固定的MCP服务与工具白名单，使用`WIND_API_KEY`认证。
密钥可配置为独立Repository Secret `WIND_API_KEY`，也可作为同名键放入
`API_CENTER_SECRETS_JSON`。适配器禁止任意server_type、tool_name、URL、交易执行和写操作。
