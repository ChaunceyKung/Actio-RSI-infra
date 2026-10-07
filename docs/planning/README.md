# Actio RSI Infra · 源码证据驱动的规划

**定位：Infrastructure for Persistent, Social and Self-Evolving Agents。原则：Reuse implementations, own abstractions。**

2026-10-05 的规划推荐：独立 Python Control Plane，经 RuntimePort 与官方 Python SDK 运行 DSH TS Worker；两条 vertical slice 共用身份、运行时、事件、记忆、评估和版本体系。以 Concordia 为第一真实 simulator adapter；SQLite + 不可变内容文件作为初期权威存储；受控拆取 Raven 配对诊断和语义档案选择逻辑。Langfuse 社区能力作为可替换 viewer，部署与许可闭包未验证前保持 provisional。

2026-10-05 的交付范围是实施规划，**没有实现 Actio 产品 runtime、adapter、service 或演化引擎**。当时 DSH SDK 客户端 29 项、Raven gate/scoring 37 项通过；Meta-Harness controller 因缺 Harbor 阻塞；真实 wheel/MCP 未运行。2026-10-07 新增范围受限的 [Phase 1A 实际验证](../validation/phase1a/README.md)，原日期与 E001–E042 测试事实保留，新结果独立登记，不将旧 fake-client 结果充当 runtime 准入。

## 九项选择

| 问题 | 当前选择与推翻条件 |
|---|---|
| Root | 独立 Python，拒绝 Raven root fork；host/DAG/routing 的状态模型不能直接成为社会实验控制面 |
| DSH 粒度 | A 官方 SDK + B worker/profile/policy adapter；C01 按 G0/G1 拆分，不嵌入或重写 loop。只有 G0 经公开配置/窄plugin/最小补丁仍不可行才触发 Strands，5 日是预算估算 |
| 单一 harness | Phase1A 在固定 Windows/offline 配置下实际验证：social external Entity 与 assistant 共用同一 DSH adapter；无第二 solver loop；live与产品化仍独立gate |
| Memory | 自有领域 contract，SQLite + immutable files；Graphiti 可选关系投影。Letta 作为机制参考，不并列拥有同一 agent 的 memory/session |
| Evolution | C02 Raven paired/scoring 诊断，C03 archive descriptor/selector；准入判定与可靠 lineage 必须改变。Meta/DGM 仅 D |
| 环境 | Concordia B 主选；AgentSociety v2 设计验证要求 pending、batch barrier、逻辑时钟；OASIS ManualAction 补充兼容 |
| Viewer | Langfuse 社区 B 主选 provisional；内部 Phoenix B 备选，遵守 ELv2 托管限制；都不是权威存储 |
| 语言边界 | Python 持有身份/策略/域状态/实验与准入，TS 持有原生 session/loop/plugin/model/tool invocation；世界/时钟归环境 |
| 自研核心 | 五项：领域身份心智；边界与状态协调；事实与检查点；独立评估准入谱系；干预与归因实验。映射 [17](17_reuse_extraction_plan.md) |

## 阅读顺序与单一事实来源

1. 快速决策：[一页 build/buy/reuse](19_build_buy_reuse_map.md) → [定位](00_project_positioning.md) → [选型矩阵](02_reuse_decision_matrix.md)。
2. 核验选型：[源码审计](01_reference_codebase_audit.md) → [证据](15_evidence_registry.md) → [能力矩阵](16_capability_and_maturity_checklist.md) → [实际验证](18_validation_log.md)。
3. 看落地：[架构](03_target_architecture.md) → [领域模型](04_core_domain_model.md) → [接口](10_interface_specification.md) → [拆解包](17_reuse_extraction_plan.md)。
4. 专题：[运行与事件](05_runtime_and_event_model.md)、[环境](06_environment_and_simulator_integration.md)、[记忆心智](07_memory_and_social_mind.md)、[演化](08_evolution_architecture.md)、[观测归因](09_observability_and_attribution.md)。
5. 开工入口：[路线](11_mvp_roadmap.md) → [Backlog](12_implementation_backlog.md) → [ADR](13_architecture_decisions.md) → [风险问题](14_open_questions_and_risks.md)。

证据以 15 为准，覆盖以 16 为准，选型以 02 为准，contract 以 10 为准，任务验收以 12 为准。`accepted-for-planning` 仅表示采用此方向编排工作；`provisional` 表示有明确阻断探针；都不是生产认证。

入口顺序修订为 B01a 主路径准入→B02a 草案→B03 与必要 B05/B07/B08 探针→B02b 证据冻结。下一最小 slice 及禁止依赖的能力以 [Phase 1A 结论](../validation/phase1a/06_go_no_go_and_next_slice.md) 为准，本轮不自动进入产品实施。
