# Wind AIFin Market 托管适配器

正式票据前缀：`[api-aifin]`。

开放模式为 **maximum-safe-readonly**：

- 四个固定 MCP 服务：`stock_data`、`financial_docs`、`economic_data`、`analytics_data`；
- `catalog-all-tools` 实时读取四类服务的完整安全只读工具目录和输入 Schema；
- `invoke-readonly-tool` 只允许调用实时 `tools/list` 中存在、通过只读名称检查且参数通过上游 JSON Schema 的工具；
- 最近一次受控发现快照登记 15 个只读工具，见 `readonly-tools.snapshot.json`；
- 原有行情、新闻、经济和分析快捷操作继续兼容。

禁止任意端点、URL、请求头、Secret 值、代码、文件、写入、交易和下单。
