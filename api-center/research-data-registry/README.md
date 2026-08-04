# re3data 科研数据仓库目录

本模块提供 re3data.org 官方版本4.0接口的固定只读访问，用于发现全球科研数据仓库及其访问、许可、学科、API、认证和持久标识信息。

## 操作

```text
catalog-capabilities
re3data-repositories
re3data-repository
```

- `re3data-repositories`：一次读取官方仓库索引，不自动分页；
- `re3data-repository`：按固定 `r3d...` 标识读取单条完整XML记录。

## 边界

- 无需API Key；
- 固定 `www.re3data.org` HTTPS主机和v40路径；
- 每张票据一次请求；
- 不允许任意URL、重定向、自动重试、自动分页或写操作；
- 上游返回XML，结果保留原始XML及哈希；
- 合并后真实票据通过前标记为待生产验收。

re3data数据库条目按其官方说明开放复用；使用结果时保留来源和访问时间。
