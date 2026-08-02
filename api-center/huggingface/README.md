# Hugging Face Hub 公共情报 Provider

固定读取 Hugging Face Hub 的公开模型、数据集、Spaces 与仓库元数据，用于模型市场、数据源、开源生态和安全状态调查。

## 正式入口

```text
Issue 前缀：[intel-huggingface]
Provider：huggingface-hub
Repository Secret：不需要
```

## 开放能力

- 模型搜索、模型详情、模型安全扫描状态；
- 数据集搜索与数据集详情；
- Space 搜索与详情，但不调用 Space；
- 模型、数据集、Space 的非递归目录、分支/标签和指定路径元数据。

## 安全边界

只允许公开仓库，客户端固定 `token=False`，不读取用户私有仓库，不使用 `HF_TOKEN` 或其他登录状态。禁止模型推理、Inference Providers、训练、Jobs、Space 调用、文件下载、仓库克隆、自动翻页、递归全仓扫描、权限审批、上传、Commit 和任何写操作。

每张票据最多执行一个固定 Hub 方法；搜索最多 50 项，目录最多 100 项，路径查询最多 20 项。依赖固定为 `huggingface_hub==1.24.0`。
