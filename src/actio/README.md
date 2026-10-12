# Actio 源码模块导航

这是模块化单体的产品包。当前代码基线为 `9e4db32`；evidence 五组已落地，整轮回归仍 INCOMPLETE。根入口收拢尚未实施，见[下一轮计划](../../docs/reviews/root_entrypoints_r15_r18_review.md)。

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
| [interfaces](interfaces/) | CLI/IPC解析、用例接线、Store与ports装配 | [cli](interfaces/cli.py)、[wiring](interfaces/wiring.py) |

输入沿“冻结 → 执行 → 行动认证/环境效果 → 持久化 → 核验/测量 → 追加决策”流动。模块之间的调用图与import依赖图不同；完整流程见[三条关键流程](../../docs/architecture/FLOWS.md)，I/O与状态边界见[模块卡片](../../docs/architecture/MODULES.md)。

**当前根文件为何多：** 19个旧命令/import薄层、`__init__`/`__main__`、3个JSON数据文件。`pins`与`_vendor`存固定支持内容。根文件数量不能代替依赖边界检查，但现有公开入口确实需要收拢。

**已确定的下一轮方向：** 删除旧根薄层，统一`actio`命令，内部协议与子进程入口分入interfaces，JSON/pins归resources，根层只保留init/main/本README。用户已允许接口迁移；旧命令及历史材料用固定旧版本复现。该目标目前尚未实施，不应把拟议命令直接作为当前使用方法。

返回[项目README](../../README.md) · [系统一页图](../../docs/architecture/README.md) · [R15–R18执行Prompt](../../docs/prompts/refactor_public_entrypoints_r15_r18.md)。
