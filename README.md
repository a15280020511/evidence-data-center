# Evidence & Data Center

本仓库是正式独立的数据证据中心；拆仓来源和固定提交仅记录在迁移证据文件中，不参与日常运行。

正式对外名称：`情报中心`（Intelligence Center）。技术目录 `api-center/` 作为兼容路径继续保留，不代表对外名称。

## 职责

外部结构化数据、地图、天气、金融、经济、新闻、人口、遥感、版本冻结与数据溯源。

## 机器权威目录

`api-center/api-catalog.json`

## 治理 4.x 唯一入口

- 网页 GPTs 不得直接控制本仓库，只能向 `a15280020511/decision-system-governance` 提交治理票据并读取治理回执。
- `a15280020511/decision-system-governance` 是唯一外部控制器和唯一跨仓库中继。
- 本仓库不得直接调用计算中心或专家中心，也不得读取其运行目录、Artifact 或 Secret。
- 情报采集允许按 Provider 白名单访问外部数据源；该网络权限不构成跨中心通信权限。
- 私有 Hugging Face 基准库存储归治理仓库所有；本仓库只保留免认证、只读的公共 Hugging Face Provider。

## 隔离边界

- 本仓库只运行本中心任务。
- 禁止中心间直接调用、运行时导入、Artifact 互取和共享业务 Secret。
- 原业务目录 `api-center/` 暂时保留，避免迁移与路径重构同时发生。
- 迁移源仓库只作为回滚与审计来源，不是治理仓库，也不是运行时依赖。

## 迁移证据

查看 `MIGRATION_MANIFEST.json`、`MIGRATION_PROVENANCE.json`、`MIGRATION.md`、`CONTROL_TOPOLOGY.md` 和 `governance-compatibility.json`。

## V3 data quality controls

Connector status is classified as PRODUCTION / DEGRADED / BLOCKED / RETIRED. Formal outputs require immutable snapshot metadata and a source-comparison report; correlated sources may not be naively averaged.

### WHO GHO OData

情报中心新增免密、只读的 WHO Global Health Observatory OData Provider，固定开放 8 项受控操作并保留官方接口迁移监测。

## 证据标准化能力层

`api-center/evidence-standardization/` 提供8项零密钥本地能力：目录读取、证据记录规范化、内容指纹与近重复、来源谱系DAG、时间版本差异、STIX 2.1离线结构校验、GPTs传输清单和来源质量画像。该层不采集外部数据、不访问网络、不读取票据文件路径、不处理个人数据，也不执行模型调用。

仓库根目录 `CENTER_CAPABILITY_OWNERSHIP.json` 是计算中心与情报中心的权威工具归属合同。
