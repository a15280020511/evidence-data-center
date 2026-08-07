# 中国大陆司法公开实践定时自迭代

## 目标

把既有中国大陆政法—司法—纪检监察全景矩阵、公开侦查技术矩阵和案例能力账本连接成定时学习闭环：

`定时发现 → 一手官方来源复核 → 高层证据/技术能力抽取 → 稳定 capability_id 映射 → 去重 → 支持/冲突检查 → 账本增量 → 验证工作流 → 审计 PR → 合并 → 下一轮继续验证`

## 频率

- 每天 UTC 03:20（北京时间 11:20）运行；
- UTC 周日自动使用 weekly profile，增加公安院校、刑事技术标准、司法鉴定与检察技术科研等源头侧查询；
- 单轮搜索、页面读取和自动吸收数量均有限额；不并发轰炸中国大陆官方站点。

## 自动吸收条件

只有同时满足以下条件的案件观察才能自动写入候选分支：

1. URL 属于固定的一手官方公开来源白名单；
2. 页面可公开读取，不登录、不绕过 CAPTCHA/WAF；
3. 能确认发布日期；
4. 页面具有案件/审查/侦查/裁判等实践信号；
5. 只映射到已经治理通过的高层 capability_id；
6. 不出现需要人工判断的证据冲突、排除、程序违法等信号；
7. 不出现秘密系统、秘密实施参数、目标选择、侦查规避、反取证或操作战术内容；
8. 不删除或覆盖既有案件观察。

自动新观察初始只能是 `PRIMARY_OBSERVED`；自动流程最高只能升到 `CORROBORATED_PRACTICE`。`STRONGLY_CORROBORATED` 必须额外确认现行规范/标准与教育科研源头证据。

## 新技术与冲突

自动系统不会因为一个新名词直接创造新的侦查能力类别。未映射的新技术、冲突案例、证据排除、程序争议或敏感内容只进入 Review Artifact / Issue，等待治理复核。历史观察不因冲突而删除。

## 自动合并

当账本有安全的新增观察时，定时任务创建独立 automation 分支和审计 PR，并显式 `workflow_dispatch` 下列验证：

- PRC Investigative Technology Learning Validate
- prc-legal-investigative-validate
- Validate PRC Mainland Compliance Policy
- Full Repository Line Audit
- Evidence Quality Validate
- Validate Governance 4.x Intelligence Topology
- Validate API Center
- Validate GPTs Intelligence Catalog
- CodeQL Security Analysis

全部成功后，使用普通 `gh pr merge` 合并，不使用 `--admin`，不绕过分支保护。任何验证失败时 PR 保留，不自动进入 `main`。

## 安全边界

系统只用于公开、合法、可验证的司法实践与防御性法律/证据研究。禁止自动登录、验证码/WAF绕过、隐藏 API 逆向、代理/身份轮换、秘密内部系统收集、秘密侦控参数、目标选择、侦查规避、反取证、证据销毁和个人定向监控。
