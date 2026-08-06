# Anna书目到合法全文来源的解决方案

## 目标

解决“在Anna看到书，但不能稳定进入下载链接读取”的实际问题，同时不把情报中心改造成验证码、会员、镜像或受限文件绕过工具。

## 生产流程

```text
Anna公开搜索结果中的书名、作者、ISBN
→ anna_lawful_source_resolver.py
→ Project Gutenberg / Standard Ebooks / English Wikisource / 中文维基文库
→ 版本与标题匹配评分
→ lawful-book-sources.json白名单复核
→ lawful_book_reader.py或lawful_pdf_reader.py读取
```

Anna只提供书目线索。解析器不接受Anna详情页或下载URL，只接受书名、作者和ISBN。

## 匹配与放行

解析器执行：

- Unicode与标点归一化；
- 标题相似度、词集合重合度和作者相似度计算；
- 按匹配分数排序；
- 过滤低分候选；
- 对每个可读位置再次调用现有合法来源注册表；
- 只有HTTPS、已批准主机、已批准格式才能标记为`reader_ready`；
- 未知主机、未知格式和仅有书目页的记录不会交给下载读取器。

真实验收同时检查：至少一个匹配候选、至少一个`reader_ready`位置，以及Anna详情页、下载URL、镜像主机和访问控制绕过计数全部为零。

## 明确不做

- 不访问Anna详情页；
- 不使用Anna下载URL；
- 不解析Anna镜像或外部文件主机；
- 不处理验证码、WAF、登录、会员、等待队列或限流绕过；
- 不把书目匹配视为版权或下载授权证明；
- 不在无合法同版来源时自动降级到Anna下载。

## 结果状态

- `matched-reader-ready`：找到匹配作品，并且至少有一个位置通过现有合法读取器白名单；
- `matched-catalog-only`：找到书目候选，但没有可直接交给读取器的位置；
- `no-lawful-match`：当前已接入来源中没有达到阈值的匹配；
- `policy_blocked`：输入包含URL、Anna下载引用或配置不符合安全合同。

该方案解决的是“如何得到可读取的同一作品合法版本”，不是破解Anna下载链路。
