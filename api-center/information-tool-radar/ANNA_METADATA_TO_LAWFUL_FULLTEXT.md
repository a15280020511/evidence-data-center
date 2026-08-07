# Anna 书目线索到合法全文

## 结论

情报中心不直接处理 Anna's Archive 的详情页、下载按钮、镜像下载链或文件地址。解决“找到书但无法读取全文”的生产方案是：

```text
Anna 公开搜索页的可见书名元数据
→ 标题清洗、去重和相似度匹配
→ Project Gutenberg / Standard Ebooks / 英文与中文 Wikisource
→ 仅保留官方声明的可读位置
→ lawful_book_reader 下载、解析目录和正文
```

入口：`catalog_lawful_resolver.py`。

## 为什么这样处理

Anna 的公开搜索结果可作为书目线索，但可见书目记录不能证明对应文件具有下载授权。情报中心已有的 Anna 适配器因此保持 `metadata-only`：

- 每次从 Wikimedia 临时解析当前搜索域名；
- 只读取公开搜索结果中的可见标题；
- 不打开详情页；
- 不跟随下载链接；
- 不保存域名；
- 不处理验证码、403、429 或访问控制。

新增解析器把这些标题线索交给已有的公版书搜索器，并只接受以下可读位置声明：

- Project Gutenberg 官方 OPDS 的 acquisition 链接；
- Wikisource 官方页面；
- 未来新增来源必须先进入固定来源注册表和测试门禁。

## 查找合法全文链接

```bash
python api-center/information-tool-radar/catalog_lawful_resolver.py \
  --catalog-registry api-center/information-tool-radar/catalog-domains.json \
  --public-registry api-center/information-tool-radar/public-book-search-sources.json \
  --reader-registry api-center/information-tool-radar/lawful-book-sources.json \
  --query "Alice in Wonderland" \
  --output catalog-lawful-report.json \
  --enforce
```

主要输出：

- `catalog_candidate_titles`：Anna 公开搜索得到的标题线索；
- `lawful_searches`：每个标题在批准来源中的查询回执；
- `matches`：标题相似度达到门槛且具有官方可读位置的结果；
- `selected_match`：排序最高的合法全文候选；
- `safety`：明确记录未进入 Anna 详情页、未跟随 Anna 下载链、未从 Anna 获取文件。

Anna 临时域名解析失败时，程序会直接使用用户原始书名查询合法来源，不会把失败转化为访问控制规避。

## 下载并读取第一个合法候选

只有提供明确权利说明时才启用读取器：

```bash
python api-center/information-tool-radar/catalog_lawful_resolver.py \
  --catalog-registry api-center/information-tool-radar/catalog-domains.json \
  --public-registry api-center/information-tool-radar/public-book-search-sources.json \
  --reader-registry api-center/information-tool-radar/lawful-book-sources.json \
  --query "Alice in Wonderland" \
  --read-first \
  --rights-note "Provider-declared public-domain or open-license edition." \
  --output catalog-lawful-reader-report.json \
  --enforce
```

`--read-first`只会把排序最高的批准来源 URL 交给`lawful_book_reader.py`。读取器仍会再次检查：HTTPS、允许域名、权利基础、格式、重定向、文件大小和内容长度。

## 明确不支持

以下能力不属于该方案：

- 解析或生成 Anna 下载直链；
- 访问 Anna 详情页抓取 MD5、下载节点或镜像地址；
- 绕过验证码、登录、付费、403、429、WAF 或下载限制；
- 用代理、换域名、换账号或第三方包装器规避限制；
- 将 Anna 可见书目记录自动视为下载授权。

## 测试

确定性测试：

```bash
cd api-center/information-tool-radar
python test_catalog_lawful_resolver.py
```

CI：`.github/workflows/catalog-lawful-resolver-quality.yml`。

门禁覆盖：

- Anna 元数据桥接；
- 标题清洗和相似度排序；
- 非批准及 Anna 链接剔除；
- Anna 不可用时的原始书名回退；
- 权利说明门禁；
- 向合法读取器交接下载和全文解析。
