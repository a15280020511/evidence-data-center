# FAOSTAT

通过 FAO 官方 FAOSTAT API 读取农业、粮食安全、贸易、价格、投入与排放统计。

- Repository Variable：`FAOSTAT_USERNAME`
- Actions Secret：`FAOSTAT_PASSWORD`
- 票据前缀：`[intel-faostat]`
- 每票据最多一次登录 POST 与一次业务 GET，JWT 不落盘。
