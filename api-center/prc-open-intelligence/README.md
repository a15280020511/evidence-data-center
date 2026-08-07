# 中国大陆开放情报免费稳定层

本模块只接纳能够满足情报中心 `maximum-safe-readonly` 准入标准的中国大陆公开情报能力。

## 生产启用

当前只有两个新增 Provider 进入生产暴露：

1. `china-check`：第三方无认证 MCP 企业基础登记查询。其免费托管能力不被视为永久 SLA，因此状态为 `PROVISIONAL_SAFE_READONLY`；每日健康检查失败、收费策略变化、401/403/429、WAF/CAPTCHA 或合同漂移时立即停用，不自动切换身份、代理或付费路径。
2. `sinofacts`：GitHub 发布的 CC BY 4.0 中国科技/出海企业公开事实快照。保留来源、验证时间和署名要求，不调用其付费验证层，不做全库再分发。

两者均：

- 不需要 API Key 或 GitHub Secret；
- 不允许自动付费或付费升级；
- 不允许 Cookie、代理轮换、验证码破解、指纹规避；
- 不允许任意 URL、写操作、无限分页；
- 仅处理公开、非个人数据；
- 失败必须形成结构化回执。

## 为什么其他工具没有全部直接装进生产

`prc-tool-registry.json` 保存所有已审计候选及生命周期状态。长期稳定不等于把第三方代码全部复制进仓库，而是：官方源优先、能力去重、可替换、健康检查、许可证复审和失败降级。

- `ccgp-monitor`：保留为解析/评分参考；中国政府采购网官方公开源已经在情报中心的一手来源计划中，因此不再建立重复爬虫依赖。
- `GeneralNewsExtractor`：GPL-3.0 的可选正文解析候选，保持为可分离组件；现有网页读取仍是默认路径。
- `RSSHub`：AGPL-3.0，自托管才可能获得可控稳定性；公共实例不作为生产 SLA。
- `TrendRadar`：保留监控架构和来源发现思路，与现有 Information Tool Radar 重叠，不重复部署。
- `HanLP`：Apache-2.0 代码可用，但模型资产需要单独许可证和可复现审计，因此先作为受控候选。
- `CNInfoHedgeCrawler`：只保留巨潮公告/PDF/SQLite 的解析思路；TLS 指纹规避能力永久排除。
- `LawRefBook/Laws`：未发现明确仓库许可证，保持 `QUARANTINED`，法律事实回到官方国家法律法规数据库等一手源。
- `OpenSanctions`：代码虽开源，但商业使用其数据不符合“永久免费生产数据源”门槛，保持 `REJECTED`；需要制裁信息时优先官方制裁清单。
- `weiboSpider`：登录态和用户级字段风险较高，只允许受控、聚合化品牌/事件研究候选。
- `MediaCrawler`、`DrissionPage`、`pywencai`、公共代理池：不满足当前生产准入要求，保持拒绝状态。

## 正式治理入口

本模块不提供独立 Issue 执行入口。网页 GPT 与其他上层调用者必须继续使用治理仓既有 `intelligence` 路由；治理仓会创建标准 `[api]` 子 Issue，由情报中心通用 API Center 校验后进入 `local-prc-open` 本地只读模式。

允许的 4 个固定连接器：

- `prc-china-check-company-search`
- `prc-china-check-company-snapshot`
- `prc-sinofacts-company-search`
- `prc-sinofacts-company-profile`

示例子票据（由治理仓生成 `task_id` 后派发）：

```json
{
  "task_id": "gov-123-intelligence",
  "objective": "核验公开企业基础登记信息",
  "data_policy": {"classification": "public", "contains_personal_data": false},
  "requests": [
    {
      "request_id": "company-1",
      "connector_id": "prc-china-check-company-search",
      "parameters": {"query": "示例公司", "language": "zh"}
    }
  ],
  "acceptance": {"require_all": true, "minimum_successful_requests": 1}
}
```

PRC 本地连接器不得与普通网关连接器混装在同一张 `[api]` 票据中；它们不启动 KrakenD 网关、不读取 Repository Secret，也不允许在上游拒绝后改用代理、身份或付费服务。
## 稳定性机制

```text
准入审计
→ 固定只读合同
→ 零 Key / 零自动付费门
→ 单元测试
→ 每日 live health
→ 许可证/维护/价格复审
→ 401/403/429/WAF/CAPTCHA 硬停止
→ 上游变化则 DISABLED/QUARANTINED
→ 由官方公开源或其他已批准源在新的独立任务中补证
```

这里的“长期免费”含义是：**系统绝不因为免费入口失效而自动转为收费路径**。第三方服务是否永远存在无法由本仓库保证；本仓库保证的是持续监测、可替换、无隐性付费和可审计降级。
