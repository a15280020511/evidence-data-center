# 安全边界

- 不提交 Secret 值、令牌、私钥或个人数据。
- 网页 GPTs 不得直接控制本仓库；唯一外部控制器和跨仓库中继是 `a15280020511/decision-system-governance`。
- 不允许计算中心或专家中心读取本仓库运行目录、Environment Secret 或 Artifact，本仓库也不得读取它们的对应资源。
- 不使用 Git submodule、跨仓库运行时 Artifact 下载、业务中心间 `repository_dispatch` 或共享业务 Secret。
- 公共合同只能使用冻结副本、版本和哈希；业务运行时不得跨仓库读取治理文件。
- 情报中心仅可通过固定 Provider、固定主机、固定方法和有界参数访问外部数据源；禁止任意 URL、任意代码和非受控写操作。
- 私有 Hugging Face 基准库存储由治理仓库持有，本仓库不得持有私有存储 Token；免认证只读公共 Hugging Face Provider 可以保留。
- 所有跨中心数据转交必须由治理仓库生成任务级、不可变、带摘要的证据包。
