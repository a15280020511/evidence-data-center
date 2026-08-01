# Evidence & Data Center

本仓库是正式独立的数据证据中心；拆仓来源和固定提交仅记录在迁移证据文件中，不参与日常运行。

正式对外名称：`情报中心`（Intelligence Center）。技术目录 `api-center/` 作为兼容路径继续保留，不代表对外名称。

## 职责

外部结构化数据、地图、天气、金融、经济、新闻、人口、遥感、版本冻结与数据溯源。

## 机器权威目录

`api-center/api-catalog.json`

## 隔离边界

- 本仓库只运行本中心任务。
- GPTs 是三个业务中心之间唯一的控制与证据中继。
- 禁止中心间直接调用、运行时导入、Artifact 互取和共享业务 Secret。
- 原业务目录 `api-center/` 暂时保留，避免迁移与路径重构同时发生。
- 迁移源仓库只作为回滚与审计来源，不是治理仓库，也不是运行时依赖。

## 迁移证据

查看 `MIGRATION_MANIFEST.json`、`MIGRATION_PROVENANCE.json`、`MIGRATION.md` 和 `governance-compatibility.json`。

## V3 data quality controls

Connector status is classified as PRODUCTION / DEGRADED / BLOCKED / RETIRED. Formal outputs require immutable snapshot metadata and a source-comparison report; correlated sources may not be naively averaged.


### WHO GHO OData

情报中心新增免密、只读的 WHO Global Health Observatory OData Provider，固定开放 8 项受控操作并保留官方接口迁移监测。
