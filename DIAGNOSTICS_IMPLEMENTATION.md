# 统一日志与自动诊断实现

## 运行层

仓库保留 GitHub Actions 原始 Run、Job、Step 和完整日志。新增的 `Workflow Diagnostic Sweep` 每 30 分钟扫描近期运行，并对非成功运行执行：

1. 获取 Run、Job、Step、Attempt、SHA、触发者和耗时；
2. 下载完整工作流日志；
3. 对 Authorization、Cookie、Token、API Key、SendKey、密码和 URL 查询凭据脱敏；
4. 抽取关键错误行；
5. 识别权限、Secret、限流、超时、网络、依赖、Schema、Artifact、模型 Provider、测试、资源耗尽和运行时异常；
6. 生成失败指纹、重试建议和失败 Step 定位；
7. 输出带 SHA-256 Manifest 的诊断包并生成 GitHub Artifact；
8. 对诊断压缩包生成 GitHub Artifact Attestation。

成功运行保留元数据、Job/Step 时长和状态；失败、取消、超时和启动失败运行额外保留脱敏日志。

## 与现有情报中心诊断的关系

现有 `api-diagnostics.json`、`api-audit.json`、`api-console.log`、网关日志和 Artifact Manifest 继续作为业务层权威证据。新诊断器提供跨全部工作流的一致外层索引和故障分类，不替代 API 业务状态，也不以 HTTP 200 或 Workflow success 代替 `API_COMPLETED` 等业务结论。

## 诊断包读取顺序

```text
summary.md
→ diagnostic-index.json
→ runs/<run_id>/failure.json
→ runs/<run_id>/key-lines.jsonl
→ runs/<run_id>/jobs.jsonl
→ runs/<run_id>/redacted-logs/
→ manifest.json
→ GitHub Artifact Attestation
```

## 错误处置

- `secret_or_auth`：修复 Secret 名称、权限或 Token 范围后再运行；
- `rate_limit_or_quota`：有界退避，禁止无限重试；
- `timeout_or_cancellation`：检查阶段耗时和上游卡点；
- `network_dns_tls`：有限重试并保留端点和 HTTP 状态，不记录凭据；
- `dependency_install`：锁定依赖或修复冲突；
- `schema_or_input`：修复输入，不原样重试；
- `artifact_or_attestation`：核对路径、Manifest、SHA-256、来源 Run 和 Attestation；
- `provider_or_model`：记录 Provider、模型 ID、HTTP/业务错误码和有限恢复结果；
- `unknown`：以完整脱敏日志和失败 Step 为依据人工定位，不伪造根因。

禁止写入完整环境变量、Authorization、Cookie、API Key、Token、SendKey、密码、个人隐私数据或原始敏感响应正文。
