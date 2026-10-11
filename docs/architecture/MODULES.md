# 模块与关键流程

| Owner | 职责与边界 |
|---|---|
| contracts | canonical、seal、受限 JSON、endpoint、wire 和最小 ports；无 I/O |
| domain | namespace、candidate 决策、账务聚合、episode 状态规则、角色配置、ClockSpec |
| tasks.core / registry | 共享 sealed/require/visibility；唯一版本 dispatcher。family 模块不反向导入 dispatcher/application |
| measurement | 独立 oracle、任务诊断和稳健性定义；不调用生产裁决冒充 oracle |
| profiles.registry / validation | schema/profile、caps、reservation、wire、usage、terminal key、mode 选择；纯 validators 与构造/身份读取分离 |
| evidence | export/verify、stream/channel audit、terminal 检查、history trust、候选/评估谱系、task/transport diagnostic reader |
| application | StoreOperations、memory、candidate/evaluation 写用例、episode/terminal、campaign、migration 和诊断编排 |
| adapters.persistence | SQL 资源、连接/WAL/只读/事务、数据库创建/复制迁移、单一 Ledger |
| adapters.runtime | 官方 DSH host/Worker、Windows Job supervisor、MCP、native journal/facts、受限 eval 子进程、cleanup |
| adapters.environment | Concordia engine 和 final source |
| adapters.transport | TransportPort、官方 TS plugin、fixture server 和 responses |
| adapters.filesystem | 文件 hash、身份闭包、受控 artifact/publication/credential 接入 |
| interfaces | 参数、可信 profile 选择、ports/Store/Ledger 装配、stdout/退出码；根文件仅登记入口或薄 shim |

## Episode

interfaces → application StoreOperations 冻结输入并取得资格 → EpisodePorts 提供 runtime/environment/transport → 官方 TS Worker 通过 `python -m actio.budget` 原子 reserve/sending → loopback fixture → evidence 认证输入、回执、通道和 usage → Concordia/任务裁决 → 同一 Store 事务记录 world/memory effect → 导出 → finally 回收 Job/服务。

A 先执行，B 使用实际 A 的公开行动；A 技术失败则 B 保持 not_run。unknown 不归零、不恢复发送资格。领域库与发送库各自负责原有事务，不宣称跨库原子提交。

## 离线核验和候选评估

文件读取 → evidence 校验封包、来源和事实 → 独立 measurement 计算指标 → 返回核验结果。持久化 decision 的流程单独位于 application，Store 注入单个连接。artifact 不提供可执行 reader；历史 reader 只由固定 Git SHA 选择。

## C5 诊断

interfaces.transport_diagnostics → application.diagnostic_runtime → DiagnosticPorts → 官方 Worker 与 GatewayStub 的显式 response_policy → 九场景原 attempt/usage/unknown → cleanup → evidence.failure_observation。runtime 编排依赖纯 reader，reader 不反向导入 runtime。

新可移址诊断包 `transport-diagnostic-package.v2-refactor` 用有序 path/hash 列表保存扩大的源码清单，保持原 128-field、depth、node 和 byte 限制；受控条目的新 reader 仅对与当前代码完整清单严格相等的映射采用既有 items 上限；其它字典仍限 128 字段，并保留全局 nodes/depth/bytes 限制。旧包和历史 reader 不改。Clock 和新源码身份不会合并入旧实验分母。

不支持完整 controller 恢复、原生 resume/fork、训练、部署、自动激活。SDK/Concordia/依赖版本未升级。
