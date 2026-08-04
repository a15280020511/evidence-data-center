# 全球公共元数据知识图谱存储

该目录把情报中心的全球知识源注册表转化为可持久化、可增量更新的知识图谱。

## 分工

- GitHub：来源注册、图谱合同、抓取计划、代码、验证和审计回执。
- Hugging Face Dataset：公开元数据节点、关系、来源状态和版本化快照。
- 原始来源：全文、附件、大体量文件和受控数据继续留在来源端。
- GPTs：唯一跨中心转交方。

## 当前骨干采集源

1. re3data：全球科研数据仓库目录。
2. EMBL-EBI OLS4：跨学科生命科学本体。
3. OBO Foundry：生物医学本体注册表。
4. OPTIMADE Providers：材料数据库联邦目录。
5. FAIRsharing OAI-PMH：数据库、标准和政策元数据。

OpenDOAR 需要有效 API Key 后再启用；BARTOC 正在重建，暂不伪装为稳定 API。

## 数据文件

```text
knowledge-graph/v1/nodes.parquet
knowledge-graph/v1/edges.parquet
knowledge-graph/v1/source-state.parquet
knowledge-graph/v1/manifest.json
README.md
```

节点按 `kg_id` 去重，关系按 `edge_id` 去重，来源状态按 `source_id` 去重。每次同步覆盖当前快照，但 Hugging Face 提交历史保留所有版本。

## 安全边界

- 仅保存公开元数据及来源明确允许公开的字段。
- 默认只保存原文链接，不复制全文。
- 禁止患者级数据、个人画像、受控基因组、付费墙绕过和密钥进入 Dataset。
- 上游全部只读；每个来源每轮最多一个请求，不自动重试。
- 同步失败不会删除已有节点；至少三个骨干来源成功才发布新快照。

## 本地验证

```bash
python api-center/huggingface/knowledge_graph_store.py validate \
  --output-dir global-knowledge-graph-validation
python -m unittest api-center/huggingface/tests/test_knowledge_graph_store.py -v
```

## 同步入口

合并到 `main` 后，工作流会使用：

```text
HF_TOKEN
HF_GLOBAL_KNOWLEDGE_GRAPH_DATASET_REPO（可选）
```

默认 Dataset 名称为当前 Hugging Face 用户下的 `global-knowledge-graph`，并保持公开。
