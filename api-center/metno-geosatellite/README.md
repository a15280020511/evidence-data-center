# MET Norway Geosatellite 1.4

受控、免密、只读的地球同步气象卫星影像提供方。

- 票据前缀：`[intel-metno-geosatellite]`
- 固定主机：`api.met.no`
- Secret：无
- 操作：能力目录、静态 PNG、欧洲 MP4/WebM 动画、按区域过滤的可用影像清单
- 约束：每票据一次请求、单并发、不自动重试、不自动翻页、不允许无过滤全目录、不开放已移除的 `small` 图
- 请求身份：固定 `User-Agent`，包含仓库联系地址
- 许可：CC BY 4.0；对外使用时应注明 MET Norway 来源
