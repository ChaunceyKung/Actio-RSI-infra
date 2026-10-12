# Actio 0.2 源码导航

模块化单体。用户入口为 `actio` / `python -m actio`，根层仅本 README 和两个包入口。

| 核心模块 | 职责 | 从哪里开始读 |
|---|---|---|
| [contracts](contracts/) | 格式、seal、wire、最小端口 | [json](contracts/json.py)、[ports](contracts/ports.py) |
| [domain](domain/) | 状态、账务、namespace与Clock规则 | [episode](domain/episode.py)、[clock](domain/clock.py) |
| [tasks](tasks/) | 任务、可见输入、行动规则和版本分派 | [registry](tasks/registry.py)、[core](tasks/core.py) |
| [profiles](profiles/) | 模式、期限、准入与用量合同 | [registry](profiles/registry.py)、[validation](profiles/validation.py) |
| [application](application/) | 执行、记忆、导出与决策写用例 | [store](application/store.py)、[transport](application/transport.py) |
| [adapters](adapters/) | persistence、runtime、environment、transport、filesystem五类实现 | [Ledger](adapters/persistence/ledger.py)、[RuntimePort](adapters/runtime/runtime.py) |
| [evidence](evidence/) | audit协议认证、bundles封包、campaigns测量报告、lineage谱系、diagnostics诊断 | [verify](evidence/bundles/verify.py)、[失败观察](evidence/diagnostics/failure_observation.py) |
| [measurement](measurement/) | 独立oracle与诊断指标 | [oracle](measurement/oracle.py) |
| [interfaces](interfaces/) | CLI/IPC解析、用例接线、Store与ports装配 | [cli](interfaces/cli/main.py)、[wiring](interfaces/wiring.py) |

输入沿“冻结 → 执行 → 行动认证/环境效果 → 持久化 → 核验/测量 → 追加决策”流动。模块之间的调用图与import依赖图不同；完整流程见[三条关键流程](../../docs/architecture/FLOWS.md)，I/O与状态边界见[模块卡片](../../docs/architecture/MODULES.md)。每个核心目录的 README 还说明设计思想、典型调用、扩展边界与对应测试：阅读 [contracts](contracts/README.md) 了解数据合同，再看 [domain](domain/README.md) 和 [tasks](tasks/README.md)；需要接入运行能力时看 [adapters](adapters/README.md)，需要核验材料时看 [evidence](evidence/README.md)。

支持目录：`resources/{pricing,trust,pins}` 保存固定 JSON，`_vendor` 保存窄复用与许可。SQL/MJS 仍归 adapters。内部入口为 `interfaces.ipc.budget` 与 `interfaces.workers.{host,mcp_server,eval_worker}`；`interfaces.cli.main` 按显式 argv 延迟路由，wiring/store/export/campaign 保留必要装配。

每个核心目录的 README 提供输入、处理、输出、边界及测试导航。旧 API 已删除，详见[迁移指南](../../docs/architecture/MIGRATION_0_2.md)。验收状态单独维护在[结果](../../docs/validation/refactor_entrypoints/RESULTS.md)，不将历史成绩当作当前安装成绩。
