# API Secret 隔离策略

## 规则

普通 `[api]` 工作流执行以下强制策略：

1. 一个外部 API 服务对应一个独立 Repository Secret。
2. 不允许把多家 API 的 Key 拼接进 JSON、文本、列表或总 Secret。
3. 单个普通 `[api]` 票据最多引用一个需要密钥的上游 API 服务。
4. 同一家 API 的多个只读端点可以共享该服务自己的 Key，例如 NewsAPI 的 Everything、Top Headlines 和 Sources 共用 `NEWSAPI_API_KEY`。
5. 无密钥公共 API 可以与一个有密钥 API 同票据执行，因为它们不会引入第二个凭据。
6. 需要同时调用两家有密钥 API 时，必须拆成两个独立票据，由 GPTs 在上层汇总结果。
7. 托管提供方同样坚持一服务一凭据；Tushare 只读取 `TUSHARE_API_TOKEN`，不复用其他金融 API 的 Key。

## Google 例外

Google BigQuery、Earth Engine、Data Commons 等能力由独立托管工作流执行，不经过普通 `[api]` 连接器的单密钥限制。Google 凭据可以按 Google 托管架构单独管理或组合管理；不得影响其他 API 的独立 Secret。

## 当前独立 API Secret

```text
AMAP_API_KEY
BAIDU_MAP_API_KEY
NEWSAPI_API_KEY
TUSHARE_API_TOKEN
```

每个 Secret 必须在 GitHub Repository Secrets 中分别创建、轮换和撤销。Secret 值不得进入仓库、Issue、日志或 Artifact。

天地图提供方已删除；`TIANDITU_API_KEY` 不再被任何工作流或代码读取。仓库设置中残留的旧 Secret 需由仓库所有者在 GitHub Settings 中手动删除。
