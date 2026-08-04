# 计算中心纯数值基准库生产合同

> **本目录位于情报中心，但只保存表结构、数值化规则和导出验证代码。私有 Hugging Face Dataset 的存储网关、凭据、入库和转交全部属于治理仓库。**

机器角色见 `library-role.json`：

```text
beneficiary_center=a15280020511/compute-simulation-center
data_producer=a15280020511/evidence-data-center
storage_gateway_owner=a15280020511/decision-system-governance
intelligence_center_direct_dataset_write_allowed=false
compute_center_direct_dataset_access_allowed=false
```

## 正确链路

```text
网页 GPTs
→ 治理仓库
→ 情报中心采集公开信息
→ 清洗、编码、单位统一、范围和质量校验
→ 纯数值 Parquet
→ 情报中心发布不可变 GitHub Actions Artifact
→ 治理仓库核验 Manifest、SHA、Schema、类型、空值和来源
→ 治理仓库写入私有 compute-numeric-baselines
→ 治理仓库按任务构建转交包
→ 断网计算中心
```

## 情报中心允许做的事

- 读取公开数据源；
- 清洗、去重和标准化；
- 将地区、行业、实体、事件、单位和方法编码为整数 ID；
- 生成纯数值 Parquet；
- 生成治理入库 Manifest；
- 上传不可变 Artifact；
- 发布来源、Run、Artifact、文件 SHA 和行数回执。

## 情报中心禁止做的事

- 配置或使用私有基准库 `HF_TOKEN`；
- 直接读取、写入或初始化 `compute-numeric-baselines`；
- 直接向计算中心传送数据；
- 把网页正文、PDF、摘要、知识库、知识图谱、控制 JSON 或 Secret 写入 Dataset；
- 让 GPTs 直接控制本仓库。

## 纯数值规则

导出的每个 Parquet 必须满足：

1. 所有列均为整数或浮点数；
2. Schema 字段不可为空；
3. 数据不得含 `null`；
4. 文件名必须与受管表 ID 一致；
5. 使用 ZSTD 压缩；
6. 来源以数值 `provenance_id` 和数值指纹保存；
7. 不确定性使用上下界、置信度和分布参数；
8. 控制元数据只进入治理 Artifact 的 `manifest.json`，不得上传到 Hugging Face。

## 覆盖范围

当前控制面覆盖 29 个计算 operation、185 个托管模式和 31 类纯数值表，包括统计、优化、时间序列、计量、因果、贝叶斯、金融、商业、GIS、交通、能源、系统动力学、Agent、博弈、政策、网络传播和危机预警。

- `operation-data-matrix.json`：计算 operation 与数值表需求；
- `numeric-table-registry.json`：表名、列名和数值类型；
- `build_governance_baseline_export.py`：生成治理入库 Artifact 和 Manifest。

## 存储所有权

私有 Dataset `compute-numeric-baselines` 的唯一运行入口位于：

```text
a15280020511/decision-system-governance/compute-baseline-gateway/
```

情报中心只负责生产，不负责存储；计算中心只负责使用，不负责联网取数；治理仓库负责验证、入库、转交和审计。
