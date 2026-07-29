# Evidence & Data Center 本地运行手册

## 正式入口

Issue 前缀：`[api]`、`[api-akshare]`、`[api-dc]`、`[api-gcp]`、`[api-aifin]`

## 本仓库工作流

- `.github/workflows/aifin-api-ticket.yml`
- `.github/workflows/akshare-api-ticket.yml`
- `.github/workflows/akshare-provider-validate.yml`
- `.github/workflows/api-catalog-validate.yml`
- `.github/workflows/api-center-image.yml`
- `.github/workflows/api-center-validate.yml`
- `.github/workflows/api-ticket.yml`
- `.github/workflows/data-commons-api-ticket.yml`
- `.github/workflows/data-commons-provider-validate.yml`
- `.github/workflows/google-cloud-api-ticket.yml`
- `.github/workflows/google-cloud-provider-validate.yml`

## 运行纪律

1. 只接受本中心票据，不接受另外两个中心的业务任务。
2. 结果必须以业务完成状态、正文、Artifact、Manifest 和 SHA 为准，不能只看 Workflow success。
3. Secret 只在本仓库或本仓库 Environment 中重新配置，不从旧仓库复制值。
4. 依赖升级先经本仓库 CI；禁止跨仓库复用业务运行工作流。
5. 迁移验收完成前，旧仓库入口仅作为回滚源，不与新入口同时承接同一正式任务。
