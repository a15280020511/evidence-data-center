# 目录域名发现与合法书籍读取

## 域名发现

`catalog_domain_discovery.py`通过Wikidata实体搜索、Wikidata `P856`网站声明和Wikipedia外部链接寻找候选域名。

发现结果只进入候选报告：

- 不修改`catalog-domains.json`；
- 不自动启用新域名；
- 不跟随旧域名跳转到未知域名；
- 每个候选保留Wikidata实体、Wikipedia页面、语言和来源链接；
- 新域名必须经过身份来源、TLS、页面结构、安全与法律复核，并通过PR更新允许名单。

Wikipedia/Wikidata可能滞后、缺失或被错误编辑，所以它们只属于线索源，不是信任根。

## 合法书籍读取

`lawful_book_reader.py`只允许以下权利基础：

- `public-domain`：公版书；
- `open-license`：明确开放许可；
- `user-provided`：用户已合法持有并明确授权处理的本地文件。

远程下载仅限`lawful-book-sources.json`中的批准来源。目前包括Project Gutenberg、Standard Ebooks和Wikisource相关域名。

支持格式：

- EPUB；
- HTML/XHTML；
- TXT。

输出包括：

- 书籍元数据；
- 目录条目；
- 章节标题和有界摘录；
- 有上限的正文文本；
- 下载字节数、截断状态和权利依据。

默认不保留原始书籍文件。手动工作流可对公版或开放许可来源选择将下载文件放入短期GitHub Actions Artifact。

## 明确禁止

- 不从Anna's Archive下载书籍；
- 不进入Anna书籍详情或下载链接；
- 不绕过验证码、反自动化、访问控制、限流或付费墙；
- 不允许未知域名；
- 不允许以用户填写的声明覆盖域名允许名单；
- 不把候选域名自动提升为生产域名；
- 不处理来源或授权状态不明确的远程书籍。
