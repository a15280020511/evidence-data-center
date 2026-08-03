# Hugging Face 领域基准资料库

该目录定义情报中心私有 Hugging Face Dataset 中的领域基准资料控制面。真实数据文件存储在 Hugging Face；GitHub 保存需求、Schema、目录生成器、同步器和验收代码。

## 中心边界

- Hugging Face 连接只属于情报中心；
- 计算中心不持有 `HF_TOKEN`、仓库地址或数据库凭证；
- 计算中心保持 `network=deny`；
- GPTs 是唯一跨中心中介，只转交不可变文件、版本、SHA256和适用范围；
- 禁止情报中心与计算中心直接调用。

## 存储目标

优先使用 Repository Variable `HF_DOMAIN_BENCHMARK_DATASET_REPO`；未设置时复用 `HF_CLOUDFLARE_DATASET_REPO`；两者均未设置时使用已认证账户下的 `cloudflare-intelligence-archive`。

远端固定根目录：

```text
domain-benchmarks/v1/control/
```

## 八个领域

- commercial-footfall
- finance-investment
- public-policy
- social-behavior
- information-diffusion
- crisis-warning
- resource-optimization
- china-real-world

## 十二类全局资产库

- sample-library
- factor-library
- domain-rule-snapshot-library
- baseline-library
- metric-threshold-library
- outcome-feedback-library
- ontology-crosswalk-library
- regime-event-library
- source-catalog-library
- data-dictionary-library
- license-provenance-library
- benchmark-manifest-library

## 每个领域的十二类待采集目录

- sources
- snapshots
- variable-dictionaries
- factors
- rule-snapshots
- baselines
- metric-thresholds
- regime-events
- crosswalks
- outcome-feedback
- licenses-provenance
- manifests

这些目录初始化为 `data-pending`。目录存在不代表真实数据、因子、规则或阈值已经具备。

## 入库要求

后续采集资料必须包含：

- 来源机构与原始引用；
- 时间和地理范围；
- 变量字典、单位和编码；
- 许可、归属、再分发和商业使用条件；
- 点时数据和发布时间滞后；
- 文件大小、媒体类型和SHA256；
- 已知缺失、偏差、修订和适用限制；
- 训练、校准、封存测试和影子反馈划分；
- 简单基线、指标、阈值和对抗测试；
- 不包含密钥和未经批准的个人数据。

## 同步入口

仓库所有者可创建以下前缀 Issue 执行真实同步并取得回执：

```text
[sync-hf-domain-benchmark]
```

同步失败会留下结构化失败回执并使工作流失败。
