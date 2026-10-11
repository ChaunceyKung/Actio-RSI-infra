# 迁移与验收状态

R7–R10 已完成，**工程验收 PASS**。同一最终 wheel 的全部34 suite、164个唯一方法已通过；原ready超时和隔离复核明确保留。起点 fetch 后安全快进到 `8ab5b5afe6e07029ad499bc462f194a5d03de7c2`，没有 reset 或覆盖并发提交。

| 阶段 | 落地 |
|---|---|
| R7 | Clock port、当前 profile revision、半开报价窗口、system expired rejection、固定 UTC 跨 IPC；旧 quote 不变 |
| R8 | tasks.core 共用原语、唯一 registry dispatcher、无任务 SCC；555 完整 JSON 向量不变 |
| R9 | profiles.registry policy 与纯 validators；Ledger 不导入根 budget；interfaces.budget 装配；preflight 用例独立 |
| R10 | 同连接 StoreOperations/Connection、SQL/migration 资源、runtime/environment/transport adapters、evidence readers、application 编排和 interfaces wiring |

根实现从 54 个降至 0，SCC 从 23/7/3/2/2 降至 0。架构工具原字节保留；边界回归额外禁止 application 导入 runtime/DB adapter，禁止 evidence 导入 writer/application，禁止 profile validators 反向依赖。

当前私有 import 已迁移，历史 scripts 不批量重写。四 console scripts、登记 module/child IPC 和公开 reader 的 facade 保留；移除的私有根模块及新 owner 见 compatibility.json / migration-map.json。历史脚本需要原固定 reader 环境，不承诺它们能直接导入新私有 API。

原 163 个测试方法全部保留，新增一个 Clock 边界方法，共 164。全部 34 suite 已在同一最终 wheel 上通过；开发安装不拼接。新工程证据在 validation/refactor_modularity/completion，旧冻结和失败收据保留。

历史 1,048 文件、SQL 资源字节、quote/pins、19 claims、C4 缺失后缀、已有 decisions 与未来计划不变。新证据不能变更 C4=INCOMPLETE、C1=infrastructure_failure、activation=false、研究 UNESTABLISHED。
