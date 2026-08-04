# Cloudflare Intelligence Provider

固定接入 Cloudflare Browser Rendering、Radar 和 URL Scanner 只读能力。

## 正式入口

- Issue 前缀：`[intel-cloudflare]`
- Provider：`cloudflare`
- 每张票据最多执行一个固定 Cloudflare API 请求。
- 外部控制入口：仅允许治理仓库派发的正式子 Issue。

## 采集与存储分工

```text
网页 GPTs
→ Decision System Governance
→ Evidence & Data Center / Cloudflare
→ GitHub Actions Artifact + 哈希回执
→ Decision System Governance 核验与后续路由
```

Cloudflare 负责公开网页、Radar 和 URL Scanner 数据采集；GitHub Actions 负责票据校验、串行执行、完整性校验、哈希和审计回执。

普通情报结果不再写入任何私有 Hugging Face Dataset。成功结果只形成受控 GitHub Actions Artifact，默认保留30天，后续由治理仓库按具体任务核验、取回和路由。

## 计算基准数据

只有明确进入数值编译流程的数据，才能在情报中心完成：

1. 清洗和去重；
2. 实体、地区、行业、事件、单位和方法整数编码；
3. 单位统一和范围校验；
4. 纯数值 Parquet 生成；
5. Manifest 和 SHA-256 生成；
6. `compute-baseline-export-*` 不可变 Artifact 发布。

情报中心不得直接写入私有 `compute-numeric-baselines`。治理仓库的 `compute-baseline-gateway` 核验 Artifact 后才可入库。计算中心保持断网，不得直接访问 Cloudflare、情报中心或 Hugging Face。

## 后台配置

情报中心只配置：

- `CLOUDFLARE_API_TOKEN`：Cloudflare Custom Token；
- `CLOUDFLARE_ACCOUNT_ID`：Cloudflare Account ID。

情报中心不得配置：

- 私有 Dataset 写入用途的 `HF_TOKEN`；
- `HF_CLOUDFLARE_DATASET_REPO`；
- `HF_NUMERIC_BASELINE_DATASET_REPO`。

私有计算基准库所需的 `HF_TOKEN` 和目标 Dataset 变量只允许配置在 `a15280020511/decision-system-governance`。

## 安全边界

- 禁止 Cloudflare Global API Key；
- Browser Rendering 只允许公网 HTTPS URL；
- 不接受 Cookie、代理、自定义请求头、浏览器脚本或任意 API 路径；
- URL Scanner 只读取已有扫描，不提交新扫描；
- 普通情报 Artifact 不自动转化为计算基准数据；
- 禁止情报中心和计算中心直接通信；
- 禁止正文、PDF、自然语言材料、知识库和知识图谱进入计算基准 Dataset。
