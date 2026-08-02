# FRED 官方经济数据 Provider

通过圣路易斯联邦储备银行官方 FRED API v1 读取 FRED 与 ALFRED 经济数据。

## 正式入口

- Issue 前缀：`[intel-fred]`
- Provider：`fred`
- 固定主机：`api.stlouisfed.org`
- 独立 Repository Secret：`FRED_API_KEY`

## 安全边界

- 每张票据最多一次 HTTPS GET；
- 强制 `file_type=json`；
- 只允许目录内固定只读路径与参数；
- 不自动重试、不自动翻页、不跟随重定向；
- 单次最多 1,000 条，观测值默认最多 1,000 条；
- 不开放 FRED API v2 批量发布下载、Maps shape 文件、任意 URL、任意路径、任意请求头或写操作；
- API Key 仅由 GitHub Actions 后端注入，不进入 Issue、日志、Snapshot 或 Artifact。

当前开放 25 项能力，覆盖分类、发布、数据序列、观测值、修订日期、来源与标签。FRED API 所有 Web Service 请求均要求 32 位小写字母数字 API Key。
