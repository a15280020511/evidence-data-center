# WHO GHO OData 全球卫生数据

正式票据前缀：

```text
[intel-who-gho]
```

固定官方兼容端点：

```text
https://ghoapi.azureedge.net/api
```

无需 API Key 或 Repository Secret。

固定开放 8 项能力：本地能力目录、维度目录、维度值、指标目录、指标搜索、指标观测值、国家目录和地区目录。指标数据可按国家或 WHO 地区、年份范围、性别和分页读取。

安全边界：每张票据最多一次 GET；不自动跟随 `@odata.nextLink`；不接受任意 `$filter`、`$select`、`$expand`、函数、URL、主机、路径、请求头或写操作；不允许整库下载。

迁移提示：WHO 官方页面说明当前 GHO OData 接口计划在 2025 年底前后迁移至 World Health Data Hub 的新 OData 实现。2026 年 8 月接入时兼容端点仍可响应，但必须保留迁移监测，未来仅在验证新官方端点和字段映射后切换。
