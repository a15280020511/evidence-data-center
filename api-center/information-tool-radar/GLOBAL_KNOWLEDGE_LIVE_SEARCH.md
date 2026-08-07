# 全球知识源统一实时搜索

## 目的

`global_knowledge_search.py` 把已经进入 `global-knowledge-sources.json` 的一部分高价值官方/公开源升级为可直接调用的统一只读搜索入口。它只搜索和归一化元数据，不下载检索结果文件，也不把外部链接自动视为授权全文。

当前首批实时适配器共 10 个：

- Open Library
- Google Books
- Crossref
- DataCite
- Europe PMC
- Semantic Scholar
- Zenodo
- arXiv
- dblp
- Library of Congress

这些适配器统一输出：`source_id`、标题、作者、年份、标识符、目录页和来源自身声明的访问状态。DOI、ISBN、Open Library ID、arXiv ID、PMID/PMCID 等可用于后续跨库去重和实体解析。

## 边界

搜索层固定执行以下约束：

- 只调用代码白名单中的官方/公开 HTTPS endpoint；
- 单源串行、有界结果、有界响应体和超时；
- 401、403、429 作为来源侧硬停止，不换域名、代理或身份规避；
- 不获取搜索结果指向的 PDF/EPUB/附件；
- provider 声明的 Open Access、Full View、public scan 等状态只作为元数据返回；
- 真正读取全文仍必须经过条目级权利检查和已有 lawful reader；
- 影子图书馆不在 `LIVE_SOURCE_IDS` 中，无法通过该模块发起实时网络搜索，更不能变成下载源。

## 全量搜索

```bash
python api-center/information-tool-radar/global_knowledge_search.py \
  --registry api-center/information-tool-radar/global-knowledge-sources.json \
  --query "causal inference" \
  --limit 5 \
  --output global-knowledge-search.json \
  --enforce
```

默认依次查询 10 个已实现实时适配器。单个来源失败会在 `sources` 中保留失败原因，不隐藏故障；只要仍有其他来源成功，报告可继续返回有效结果。

## 指定来源

```bash
python api-center/information-tool-radar/global_knowledge_search.py \
  --registry api-center/information-tool-radar/global-knowledge-sources.json \
  --query "福州 城市交通" \
  --source crossref \
  --source datacite \
  --source open-library \
  --limit 5 \
  --output selected-knowledge-search.json
```

不在白名单的来源会直接 `blocked`。影子库即使存在于上层注册表，也不能作为 `--source` 传入本模块。

## 结果中的访问声明

不同来源可能返回：

- Open Library：`public_scan`、Internet Archive 标识；
- Google Books：`viewability`、`public_domain`、`web_reader_link`；
- Crossref / DataCite：许可证和 DOI 元数据；
- Europe PMC：`is_open_access`、PMC 收录状态；
- Semantic Scholar：来源声明的 OA PDF URL 与状态；
- Zenodo：访问级别和许可证；
- arXiv：记录 ID 与提交时间；
- Library of Congress：在线格式与权利字段。

这些字段只是来源声明。统一搜索器不会自动跟随或下载文件。后续全文读取必须由独立权利门禁判断 public domain、open license、Full View/Open Access 或用户自身授权。

## Key 来源

需要 Key 或机构权限的来源仍留在 `global-knowledge-sources.json`，由 `global_knowledge_registry.py` 报告 Key 缺失/可用状态。例如 OpenAlex、Europeana、DPLA、Trove、CORE、NASA ADS。它们不应因为 Key 尚未配置而被伪装为已接通实时适配器。

## 测试

确定性测试：

```bash
cd api-center/information-tool-radar
python test_global_knowledge_search.py
```

CI：`.github/workflows/global-knowledge-live-search-quality.yml`

CI 包含两层：

1. 10 个解析器的固定 fixture 测试和影子库隔离测试；
2. Open Library、Crossref、Europe PMC 的小规模真实联网 Canary，每源最多 1 条结果，要求至少 2/3 来源成功，并确认没有获取结果文件或调用影子库。

这种门禁将“代码能解析”与“真实公网目前可调用”分开验证，同时避免单个公共服务短时故障阻断整个情报中心。
