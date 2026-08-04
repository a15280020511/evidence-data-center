# 全球知识源注册表与知识图谱骨干

该目录是情报中心的**知识发现与身份解析层**，不是“把所有网页全文复制进仓库”。

## 已完成

- 将全球跨学科文献库、图书馆、档案馆、数据仓库、政府数据库、专业科学数据库、行业资料库、术语本体和知识图谱纳入统一注册表。
- 区分 `existing-active`、`backbone-candidate`、`catalog-only`、`conditional-free`、`application-required`、`web-only`、`deferred`。
- 为每个来源保存领域、地区、访问协议、凭证方式、费用类别、许可证说明、中国覆盖度、规范标识符和现有 Provider 映射。
- 建立跨库知识图谱节点、边、身份消歧、时态、来源和权利合同。
- 保存宽关键词矩阵，后续发现不再只围绕“免费 API/MCP”搜索。

## 关键原则

1. 注册来源不等于允许全量抓取或复制全文。
2. 元数据、开放全文、批量数据、受控数据和商业授权必须分层处理。
3. 优先接入 re3data、OpenDOAR、FAIRsharing、BARTOC、OLS、OPTIMADE 等上位目录，再由它们持续发现下游专业库。
4. 已有 Provider 不重复安装；新增直接连接器必须经过固定主机、单次只读请求、许可和生产验收。
5. 患者级、个人级、受控基因组和敏感司法数据不得进入普通公共知识图谱。
6. GPTs 是唯一跨中心转交方。

## 验证

```bash
python api-center/global-knowledge-registry/validate_global_knowledge_registry.py
```
