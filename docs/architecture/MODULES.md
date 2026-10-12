# 模块卡片

与[系统一页图](README.md)、[关键流程](FLOWS.md)共同描述 `9e4db32` 的实际实现。下表处理链用于定位代码，不表示新增接口或服务。R11–R14完整验收仍INCOMPLETE；后续[根入口迁移](../reviews/root_entrypoints_r15_r18_review.md)尚未实施。细节优先维护在代码与测试中。

## 规则与定义

| 模块 | 输入 → 内部处理 → 输出 | 当前入口 | 关键边界 |
|---|---|---|---|
| contracts | JSON/wire/端口数据 → 受限解析、规范化与 seal → 校验值或合同错误 | [json.py](../../src/actio/contracts/json.py)、[ports.py](../../src/actio/contracts/ports.py) | 最底层格式与接口，不依赖运行实现 |
| domain | 状态、角色、账务项、时钟规格 → 领域约束/聚合 → 状态或决策值 | [episode.py](../../src/actio/domain/episode.py)、[clock.py](../../src/actio/domain/clock.py) | 规则与 I/O 分开；不能用 lease 超时自动授权接管 |
| tasks | 任务版本、卡片、actor、行动 → registry 选择 family → 可见输入、行动空间与任务结果 | [registry.py](../../src/actio/tasks/registry.py)、[core.py](../../src/actio/tasks/core.py) | family 不反向依赖 dispatcher，私有信息不进入对方输入 |
| measurement | 卡片、行动/缺失 → 独立 oracle 与诊断计算 → 指标单元与原因 | [oracle.py](../../src/actio/measurement/oracle.py)、[diagnostic.py](../../src/actio/measurement/diagnostic.py) | 不拿生产裁决作为独立 oracle，无 Worker 或账本写入 |
| profiles | 配置/模式 → registry、纯 validators、必要的身份构造 → caps、wire、usage、期限等规则 | [registry.py](../../src/actio/profiles/registry.py)、[validation.py](../../src/actio/profiles/validation.py) | 验证与构造不同，旧版本允许域不随新 profile 扩张 |

## 用例、证据与入口

| 模块 | 输入 → 内部处理 → 输出 | 当前入口 | 关键边界 |
|---|---|---|---|
| application | 命令、冻结输入、注入 ports/Store → claim、执行、认证、效果与导出编排 → run、证据包、追加 decision | [store.py](../../src/actio/application/store.py)、[transport.py](../../src/actio/application/transport.py)、[export.py](../../src/actio/application/export.py) | 运行依赖经 ports 注入；StoreOperations/memory 等仍含 SQL，保持原事务边界 |
| evidence | 封存材料、固定信任表 → 结构/输入/协议/账务认证、报告与谱系检查 → 核验结果、计数、缺失、决策依据 | [verify.py](../../src/actio/evidence/bundles/verify.py)、[evaluation_measurement.py](../../src/actio/evidence/campaigns/evaluation_measurement.py)、[failure_observation.py](../../src/actio/evidence/diagnostics/failure_observation.py) | 只读 reader 不启动 runtime、不写领域数据库；文件 I/O 不等于纯函数 |
| interfaces | CLI/IPC 参数 → 可信选择、参数检查、装配与调用 → stdout、退出码或用例结果 | [cli.py](../../src/actio/interfaces/cli.py)、[wiring.py](../../src/actio/interfaces/wiring.py)、[store.py](../../src/actio/interfaces/store.py)、[budget.py](../../src/actio/interfaces/budget.py) | composition 是实现接线位置；根兼容入口委托到这里或登记 owner |

## 外部能力适配

| 模块 | 输入 → 内部处理 → 输出 | 当前入口 | 关键边界 |
|---|---|---|---|
| adapters.persistence | DB 路径与操作 → 连接、WAL、只读、事务、迁移/快照 → 原 Store/Ledger 状态 | [store.py](../../src/actio/adapters/persistence/store.py)、[ledger.py](../../src/actio/adapters/persistence/ledger.py) | 每个权威的连接与事务保持，不另建第二 Ledger |
| adapters.runtime | 冻结 task/运行规格 → 官方 SDK/Worker、Job、事实与清理 → 原生回执、事实、退出证据 | [runtime.py](../../src/actio/adapters/runtime/runtime.py)、[supervisor.py](../../src/actio/adapters/runtime/supervisor.py) | 原生 session/journal 仍归 DSH，不宣称完整恢复 |
| adapters.environment | Store/run、任务与 runtime factory → Concordia Sequential 推进 → 环境效果及行动来源 | [concordia.py](../../src/actio/adapters/environment/concordia.py) | 按各版本任务顺序与可见性运行，引擎不是评价者模型 |
| adapters.transport | 配置、任务、Ledger 引用 → TransportPort、TS guard、协议记录 → raw/adapter/native 材料 | [transport.py](../../src/actio/adapters/transport/transport.py)、[fixture.py](../../src/actio/adapters/transport/fixture.py) | 本机 fixture 是可安装能力，不导入 tests；unknown 不冒充 usage=0 |
| adapters.filesystem | 受控路径与文件 → hash、身份闭包、读写与秘密接入 → 资源/身份/导出材料 | [目录](../../src/actio/adapters/filesystem/) | 真实凭据只在已授权执行路径内存注入，本轮重构不读取 |

## 修改某个能力时看哪里

| 要修改的能力 | 主要位置 | 现有测试入口示例 |
|---|---|---|
| 任务、可见性和 oracle | tasks + measurement | [test_suite.py](../../tests/test_suite.py)、[test_task_diagnostics.py](../../tests/test_task_diagnostics.py) |
| profile / Clock / 发送合同 | profiles + domain + interfaces.budget + Ledger | [test_readiness_config.py](../../tests/test_readiness_config.py)、[test_budget.py](../../tests/test_budget.py) |
| run、memory、快照及并发 | application + persistence | [test_reliability.py](../../tests/test_reliability.py)、[test_entry_concurrency.py](../../tests/test_entry_concurrency.py) |
| 协议准入与失败诊断 | evidence + transport/runtime | [test_failure_observation.py](../../tests/test_failure_observation.py)、[test_transport.py](../../tests/test_transport.py) |
| 候选与 evaluation 历史 | domain + application + evidence | [test_evaluation_candidate.py](../../tests/test_evaluation_candidate.py)、[test_evaluation_candidate_runtime.py](../../tests/test_evaluation_candidate_runtime.py) |
| 依赖方向、wheel 与入口 | interfaces + packaging + architecture tools | [test_modularity.py](../../tests/test_modularity.py)、[维护 runner](../../tools/refactor/validate.py) |

表中是导航，测试名称不能直接判断是否会启动 Worker。完整分组与套件顺序以 `tools/refactor/validate.py` 为准；尤其 `suite_evidence` 消费同轮 `suite_runtime` 产物。离线使用和验收命令见[工程 CLI](../validation/refactor_modularity/CLI.md)。

## Evidence groups

`evidence.audit` authenticates streams, channels, transport contracts and accounting. `evidence.bundles` reads sealed task and evaluation packages. `evidence.campaigns` computes campaign measurements and registries. `evidence.lineage` tracks candidate and evaluation history. `evidence.diagnostics` contains failure observations, fixtures, schedules and task/transport diagnostics. The groups form a one-way dependency projection; the root `failure_observation` module is a registered compatibility reader only.
