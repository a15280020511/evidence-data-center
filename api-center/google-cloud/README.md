# BigQuery 与 Earth Engine 托管数据能力

本目录为 API 中心提供两个独立的 Google 托管数据能力：

- Google BigQuery：动态目录浏览和受费用上限保护的只读 GoogleSQL；
- Google Earth Engine：官方 STAC 数据目录、完整算法目录和受控只读 `value:compute`。

它们不经过 KrakenD 普通连接器，也不改变原有 `[api]` GET 取数链。正式入口是标题以 `[api-gcp]` 开头的 Issue，由独立工作流执行。

## GPTs 能力目录

GPTs 应先读取：

1. `provider-catalog.json`：两个提供方的全部操作、参数、限制和替代关系；
2. 上级 `api-catalog.json`：普通连接器和托管提供方统一目录；
3. 本文件：认证、费用和安全规则。

“开放全部功能目录”表示 GPTs 可以看到和选择：

- BigQuery 数据集、表、视图、字段、例程和模型目录；
- Earth Engine 官方 STAC 数据集目录；
- Earth Engine 当前账户可见的完整算法目录。

它不表示允许任意写入。执行边界固定为只读。

## 必需配置

GitHub Repository Secret：

```text
GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON
```

Secret 值是完整的 Google Cloud 服务账号 JSON。不得把内容写入 Issue、代码、日志或 Artifact。

对应 Google Cloud 项目必须：

- 已启用 BigQuery API；
- 已启用并注册 Earth Engine API；
- 允许服务账号创建 BigQuery 查询作业；
- 允许服务账号执行 Earth Engine 计算；
- 已配置有效的计费项目和配额。

可选 GitHub Repository Variable：

```text
BIGQUERY_ALLOWED_PUBLIC_PROJECTS
```

值为逗号分隔的额外公共项目ID。默认只允许：

```text
bigquery-public-data,gdelt-bq
```

## BigQuery 安全与费用规则

`query-readonly` 固定执行以下步骤：

```text
验证单条 SELECT/WITH
→ 检查所有表都使用完整反引号项目名
→ 检查项目白名单
→ dry-run 估算扫描量
→ 超过 maximum_bytes_billed 立即终止
→ 执行只读查询
→ 限制返回行数和响应大小
```

禁止：

- DDL、DML和多语句脚本；
- 导出、加载、远程函数和外部查询；
- 写表、修改数据集、创建模型；
- 查询未列入白名单的项目；
- 使用用户个人或受监管数据。

默认扫描上限为 1 GB，硬上限为 10 GB；默认返回1000行，硬上限5000行。实际费用和免费额度由 Google Cloud 账户、区域、缓存和当前定价决定。

## Earth Engine 安全规则

目录操作开放官方 STAC 数据目录和算法目录。计算操作只允许返回 JSON 值的 `value:compute` 表达式。

禁止：

- Export、上传和下载任务；
- 创建、删除、复制、重命名或修改资产；
- 用户私有资产；
- 非 `earthengine-public` 的项目资产；
- 外部URL和云存储桶；
- 视频、缩略图和Map ID任务。

表达式限制：最多20000字符、500个节点、30层深度。结果超过票据响应上限时终止。

## 票据示例

### 浏览BigQuery公共项目

```json
{
  "task_id": "gcp-bigquery-catalog-0001",
  "provider": "bigquery",
  "operation": "catalog-projects",
  "objective": "查看可供GPTs选择的BigQuery公共项目",
  "parameters": {},
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false
  },
  "acceptance": {
    "timeout_seconds": 30,
    "max_response_bytes": 500000
  }
}
```

### 搜索Earth Engine数据集

```json
{
  "task_id": "gcp-ee-worldpop-catalog-0001",
  "provider": "earth-engine",
  "operation": "catalog-dataset-search",
  "objective": "查找WorldPop人口数据集",
  "parameters": {
    "search": "WorldPop",
    "max_results": 20
  },
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false
  },
  "acceptance": {
    "timeout_seconds": 30,
    "max_response_bytes": 500000
  }
}
```

## 被替代的旧连接器

接入完成后删除以下普通连接器，避免重复维护：

- `gdelt-doc-articles`：改由 BigQuery `gdelt-bq.gdeltv2` 查询；
- `nasa-black-marble-granules`：改由 Earth Engine 夜间灯光目录和计算；
- `worldpop-population-stats`：改由 Earth Engine WorldPop目录和区域统计计算。

地图路线、地理编码、POI、实时天气、世界银行、DBnomics、Wikidata和OSM继续保留，因为它们不是BigQuery或Earth Engine的等价替代品。
