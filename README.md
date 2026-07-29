# Evidence & Data Center

本仓库由 `a15280020511/test` 在固定提交 `abac3d776340c8c162b8fc0c670167fde94f3baa` 拆分迁入。

## 职责

外部结构化数据、地图、天气、金融、经济、新闻、人口、遥感、版本冻结与数据溯源。

## 机器权威目录

`api-center/api-catalog.json`

## 隔离边界

- 本仓库只运行本中心任务。
- GPTs 是三个业务中心之间唯一的控制与证据中继。
- 禁止中心间直接调用、运行时导入、Artifact 互取和共享业务 Secret。
- 原业务目录 `api-center/` 暂时保留，避免迁移与路径重构同时发生。
- 旧仓库在验收完成前保留为治理记录和回滚源，本次不删除旧内容。

## 迁移证据

查看 `MIGRATION_MANIFEST.json`、`MIGRATION.md` 和 `governance-compatibility.json`。
