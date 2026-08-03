# Hugging Face 领域基准库

该目录定义私有 Hugging Face Dataset 中的领域基准控制面。真实数据文件存储在 Hugging Face，GitHub 保存 Schema、需求、同步器和验收代码。

## 存储目标

优先使用 Repository Variable `HF_DOMAIN_BENCHMARK_DATASET_REPO`；未设置时复用 `HF_CLOUDFLARE_DATASET_REPO`；两者均未设置时使用已认证账户下的 `cloudflare-intelligence-archive`。

远端固定根目录：

```text
domain-benchmarks/v1/control/
```

## 已初始化领域

- commercial-footfall
- finance-investment
- public-policy
- social-behavior
- information-diffusion
- crisis-warning
- resource-optimization
- china-real-world

## 必需资产库

- sample-library
- factor-library
- domain-rule-snapshot-library
- baseline-library
- metric-threshold-library
- outcome-feedback-library
- ontology-crosswalk-library
- regime-event-library

## 边界

- Hugging Face 仓库必须是私有 Dataset；
- 证据中心 GitHub Actions 负责联网同步和完整性回执；
- 计算中心保持 `network=deny`；
- 计算中心只接受 GPTs 转交的不可变文件、版本和 SHA256；
- 禁止中心间直接连接；
- 禁止保存密钥和未经批准的个人数据；
- 高风险基准晋升必须具有冻结真实样本、简单基线、样本外验证、对抗测试和影子结果反馈。
