# 情报中心控制拓扑

## 唯一控制路径

```text
网页 GPTs
  → a15280020511/decision-system-governance
  → 本仓库 Issue 票据与受控工作流
  → Artifact、摘要与可信终态回到治理仓库
  → 网页 GPTs 读取治理回执
```

网页 GPTs 不得直接控制本仓库。`a15280020511/decision-system-governance` 是唯一外部控制器和唯一跨仓库中继。

## 允许

- 由治理仓库创建符合本中心 Schema 的任务 Issue。
- 本中心按固定 Provider、固定主机、固定 HTTP 方法和有界参数访问外部公开或已授权数据源。
- 本中心生成不可变 Artifact、摘要、来源、时间戳、内容哈希和终态评论。
- 治理仓库按任务读取本中心可信终态并向网页 GPTs 返回回执。
- 免认证、只读的公共 Hugging Face Provider 继续作为普通外部数据源使用。

## 禁止

- 网页 GPTs 直接创建或控制本中心业务任务。
- 本中心直接调用计算中心或专家中心。
- 任一业务中心读取另一业务中心的运行目录、Secret、环境、缓存或 Artifact。
- 业务中心间共享工作流、共享业务 Secret、`repository_dispatch` 或运行时仓库导入。
- 本中心持有或使用私有 Hugging Face 基准库存储 Token。
- 任意 URL、任意代码、任意依赖、自动翻页、无限重试或非受控写操作。

## 网络边界

情报中心必须联网获取现实数据，但网络权限仅限 Provider 目录声明的外部来源。它不允许访问计算中心、专家中心或私有 Hugging Face 基准库。网络可用不等于跨中心通信可用。

## 存储边界

私有 Hugging Face 基准库存储归 `a15280020511/decision-system-governance` 所有。情报中心可以产生供治理仓库接收的数据包，但不得直接写入该私有存储。计算中心和专家中心也不得直接访问该存储。

## 版本合同

权威机器合同为 `governance-compatibility.json`。当前兼容治理版本为 `>=4.1.0,<5.0.0`；任何改变控制器、跨仓库中继、中心直连、私有存储或网络边界的变更必须先通过 `Validate Governance 4.x Intelligence Topology`。
