# OpenSky Network Provider

OpenSky Network 已作为受限、只读的托管 Provider 接入情报中心。

## 凭据

- GitHub Actions Secret: `OPEN_SKY_CLIENT_SECRET`
- GitHub Actions Repository Variable: `OPEN_SKY_CLIENT_ID`

两个值来自 OpenSky 账户页创建的 OAuth2 API Client。最新状态查询可在未配置凭据时匿名运行；历史状态、本人接收器、航班、机场到离港和航迹需要 OAuth2。

## 票据入口

Issue 标题必须以 `[intel-opensky]` 开头，正文使用 `ticket.schema.json`。

## 能力

- `states-current`
- `states-recent`
- `states-own`
- `flights-interval`
- `flights-aircraft`
- `airport-arrivals`
- `airport-departures`
- `track-aircraft`
- `catalog-capabilities`

## 固定边界

- 不允许无过滤全球状态查询。
- 状态边界框最大 400 平方度，或最多 20 个 ICAO24。
- 最近状态仅限过去 1 小时。
- 全网航班区间最多 2 小时；单机及机场航班最多 2 天。
- 航迹仅限实时或过去 30 天。
- 每票最多一次 OAuth POST 和一次业务 GET；无重试、无自动翻页。
- 不接入 Trino、MinIO、批量下载、持续轮询或写操作。
- OAuth token 和 client secret 不写入 Artifact。

OpenSky 明确说明该实时 API 面向研究和非商业用途，并可能阻断部分云服务商出口 IP。使用数据时应遵守其条款与引用要求。

## 航空器型号与注册信息补全

OpenSky 状态向量本身不保证返回注册号、制造商或具体机型。情报中心同时接入 `hexdb-aviation`：将 OpenSky 返回的 `icao24` 交给 `aircraft-by-icao24`，可补全注册号、制造商、ICAO 机型代码、具体机型、登记所有人和运营方代码；呼号可进一步补全推定航线和机场信息。该补全数据为第三方众包性质，必须保留来源和不确定性说明。
