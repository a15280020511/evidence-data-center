# Cloudflare 中国金融商业数值编译器

该模块把公开网页中的中国大陆金融、商业、A股、企业经营、房地产、信贷、地方财政和制造业信息转换为计算中心可直接使用的纯数值数据。

## 数据链路

```text
网页 GPT 创建一张固定票据
→ Cloudflare Browser Run 打开一个公开 HTTPS 页面
→ Browser Run /json 使用 Workers AI 按固定模板提取
→ GitHub Actions 验证固定 JSON Schema
→ GitHub Actions 映射变量、单位、事件和关系代码
→ 生成纯数值 Parquet
→ 串行追加到私有 Hugging Face compute-numeric-baselines
→ 网页 GPT 按任务选择并转交给断网计算中心
```

三个中心禁止互相直连。Cloudflare、GitHub Actions 和 Hugging Face 都属于情报中心的数据处理链；计算中心仍保持 `network=deny`，专家中心不参与数据清洗和入库。

## 固定提取模板

当前注册13个模板：

1. 中国上市公司财务报告；
2. A股公开行情；
3. 公司治理数值；
4. 公司事件；
5. 股权、供应链和经营关系；
6. 企业经营和盈利能力；
7. 零售、电商和平台经济；
8. 房地产和建筑；
9. 银行、信用、保险和财富；
10. 税收、采购和补贴；
11. 地方政府财政；
12. 制造业产能和关键材料；
13. 中小企业、门店和加盟盈利能力。

票据不能提供自定义提示词、自定义JSON Schema、自定义模型或任意Hugging Face路径。每张票据只允许一个URL、一个固定模板、一次Cloudflare请求和一次串行入库。

## 只保存数字

Hugging Face只接收现有数值基准Schema中的：

- `observations`；
- `regime_events`；
- `entity_links`；
- `provenance_index`。

最终列类型只允许整数或浮点数。网页正文、Markdown、HTML、模型解释、买卖建议、目标价、收益保证、个人数据和原始AI响应都不会写入Hugging Face。

模型暂时产生的企业名称、证券代码、统一社会信用代码、项目编号和关系名称只在单次任务内用于生成稳定数值ID，随后丢弃。GitHub中的代码表负责解释 `variable_id`、`unit_id`、`event_type_id` 和 `relation_id`，但代码表不上传到纯数值Dataset。

## Cloudflare免费额度的定位

Cloudflare Browser Run免费版当前适合低频采集和结构化提取，不适合无限批量处理。Workers AI和Browser Run分别按自己的免费额度计量；额度耗尽后任务应失败，不得降低质量、绕过限制或自动切换到付费外部模型。

因此该模块的定位是：

- 处理高价值、需要语义理解的公开网页；
- 标准API、CSV和结构化表格继续优先使用确定性程序；
- 同一页面和结果通过 `provenance_id` 阻止重复入库；
- 所有AI结果必须经过程序验证后才能成为基准数据。

## 票据示例

```json
{
  "task_id": "cn-finance-20260804-001",
  "profile_id": "cn-listed-company-financial-report",
  "url": "https://example.com/public-report",
  "data_policy": {
    "classification": "public",
    "contains_personal_data": false,
    "investment_recommendation_requested": false
  },
  "acceptance": {
    "timeout_seconds": 90,
    "max_response_bytes": 1000000,
    "minimum_confidence": 0.8
  }
}
```

Issue标题前缀：

```text
[compile-cn-numeric]
```

## 重要边界

- 不负责荐股、个性化投资建议或自动交易；
- 不从单一网页生成未来收益承诺；
- 不提取个人账户、个人轨迹、身份证、手机号等数据；
- 不允许任意网页脚本、Cookie、代理、自定义请求头或登录绕过；
- 只能处理公开HTTPS页面；
- 模型置信度低于票据阈值的记录不入库；
- GitHub Actions是最终确定性质量门和唯一入库执行者；
- Cloudflare AI是非权威语义提取器，不能直接决定正式数值。
