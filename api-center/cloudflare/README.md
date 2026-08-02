# Cloudflare Intelligence Provider

固定接入 Cloudflare Browser Rendering、Radar 和 URL Scanner 只读能力。

## 正式入口

- Issue 前缀：`[intel-cloudflare]`
- Provider：`cloudflare`
- 每张票据最多执行一个固定 Cloudflare API 请求。

## 采集与存储分工

```text
Cloudflare
└─ 负责网页、Radar 和 URL Scanner 数据采集

GitHub Actions
└─ 负责票据校验、串行执行、完整性校验、哈希与审计回执

Hugging Face Private Dataset Repo
└─ 负责采集结果的长期、版本化、追加式存储
```

Hugging Face 在此处是数据湖式证据仓库，不作为低延迟事务数据库。每次成功采集会写入独立目录，包含原始响应或二进制文件、`ticket.json`、`diagnostics.json`、`manifest.json` 和 `archive-record.json`。目录按 UTC 年/月/日、操作、任务和 GitHub Run 分区；重复内容由 Git/LFS 内容寻址存储复用底层对象。

只归档满足以下条件的结果：

- Cloudflare 执行状态为 `INTEL_CLOUDFLARE_COMPLETED`；
- 数据分类为 `public`；
- `contains_personal_data=false`；
- 本地 Manifest 文件大小与 SHA-256 全部一致；
- Secret 泄露标记全部为 `false`；
- Hugging Face 目标仓库确认为私有 Dataset Repo。

归档失败时任务按失败关闭，但 GitHub Artifact 仍保留30天作为恢复证据。

## 后台配置

- `CLOUDFLARE_API_TOKEN`：Cloudflare Custom Token。建议仅授予 `Browser Rendering - Edit`、`Radar - Read`、`URL Scanner - Read`。
- `CLOUDFLARE_ACCOUNT_ID`：32 位 Cloudflare Account ID。
- `HF_TOKEN`：Hugging Face Fine-grained Token，用于私有 Dataset Repo 创建和写入。
- `HF_CLOUDFLARE_DATASET_REPO`：可选 Repository Variable，格式为 `owner/name`。未配置时自动使用 `<HF账户>/cloudflare-intelligence-archive`。

禁止使用 Cloudflare Global API Key。Browser Rendering 仅允许公网 HTTPS URL，不接受 Cookie、代理、自定义请求头、浏览器脚本或任意 API 路径。URL Scanner 只读取已有扫描，不提交新扫描。

Hugging Face 归档层不改变 Cloudflare Provider 的只读边界；写入只发生在情报中心自己的私有归档仓库。归档流程不上传 Secret、不写入私有或个人数据、不执行模型推理。
