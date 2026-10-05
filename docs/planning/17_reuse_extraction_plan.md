# 17 · 二开拆解包与必要自研

本轮只定义未来文件与修改边界，不创建任何下述实现。所有A/B/C来自[02](02_reuse_decision_matrix.md)，固定SHA/source/许可来自[15](15_evidence_registry.md)。只有三个C包；Meta-Harness、DGM、ACE不为凑复用数量强行复制。预估LOC是规划区间、含必要胶水，不是已写代码或精确承诺。

## C01 · DSH 官方 SDK 生命周期窄扩展

来源 `deepseek-ai/deepseek-harness@5badb15009ae1756c3afe0ae0cef1faafc290ccc`（E001–E005）。入口：`python/sdk/src/deepseek_harness/{client.py,api.py,models.py}`，`packages/sdk/server/src/server.ts::HarnessSdkJsonRpcServer.handleRequest/getOrCreateSession/createSession`，`packages/sdk/protocol/src/types.ts`；底层 `packages/core/session/src/index.ts::SessionStore.fork`、`fork.ts::buildForkSeed`，`packages/core/agent-loop/src/agent.ts::ReactLoopAgent`，JSONL persistence service。

现状server只有三个request方法：`initialize`、`session/prompt`、`shutdown`。session由prompt时getOrCreate创建，不存在独立已发布的完整resume API。A单独不足以满足Actio生命周期；B只读native日志可做观察但无法稳定调用内部cancel/fork/resume，直接绕过SDK会增加第二套私有bridge，所以选窄C而非新网络RPC。

| 拆解维度 | 方案 |
|---|---|
| 输入/输出 | native session ID、seq、expected lease/cursor、command ID→receipt/status/events/child ID；Actio DTO只在RuntimePort转换，不塞入全部领域模型 |
| 最小依赖闭包 | Python SDK client/models/errors、现有stdio protocol/server、ctx.agents/session/persistence、Cordis lifecycle、matching runtime wheel/Node/native sidecars；profile/plugin加载是运行依赖；模型/工具凭据运行时注入，不复制 |
| 保留 | 原transport、launch args、通知分发、错误通道、原生session存储/锁、model/tool loop、平台runtime打包方式 |
| 删除/不纳入 | 新HTTP服务、自写Pythonloop、私有_launch_args部署依赖、Raven host/registry |
| 替换/封装 | RuntimePort将run/spec映射session/profile；显式dsh_home与worker pin；bounded ingestion而非无界消息累积 |
| 扩展 | 能力协商；cancel/status；open-existing/resume；fork-at-seq；event catch-up与durable cursor/receipt查询。若上游最新release已有等价public方法则转A/B移除patch |
| 未来落点 | Actio `adapters/runtime/dsh.py`、`domain/runtime.py`、`workers/supervisor.py`；patch来源清单 `third_party/dsh/patches/`（未来）。优先向上游提补丁，发布时单独patch artifact hash |
| tests | 保留 `python/sdk/tests/test_client.py`、`test_runtime_resolution.py`、server `tests/server.spec.ts`、protocol `tests/transport.spec.ts`；现成真实wheel/model smoke需凭据时单列 |
| contract/fault验证 | cancel前后unknown tool效果、重复receipt、EOF/kill、中文路径、seq gap、profile污染、锁未释放、queue压测；Python/TS版本不匹配必须拒绝 |
| 规模/owner | 预计触及6–10个SDK/protocol文件、300–900 LOC，1–2人周；依据已有三方法dispatcher与内部seam，未实测。I负责；5日探针决定是否仍为窄补丁 |
| 升级/退出 | 每次上游版本diff+合同suite；不改loop主体；若必须重写存储/大范围改loop或超预算，退出到Strands Python（ADR02/03），不无限fork |
| License | MIT根及Cordis适用notice保留；修改标记/上游SHA清单；wheel依赖闭包/第三方NOTICE单列B01。商业托管仍须核sidecar/model/tool条款，不把MIT扩张到全部依赖 |

## C02 · Raven 配对诊断与结果适配

来源 `EverMind-AI/Raven@3632e6040c7038a60ec418ce39ccae185c72c19f`（E008）。主模块：`evolver/orchestrator/gates/paired.py::paired_lift/PairedResult`（105行），`evolver/orchestrator/scoring.py::TaskEval/EvalFn`（226行）。参考而非整包复制：`gates/pipeline.py`、`strategies.py::PairedTwoSigmaGate`、`policy.py::CandidateOutcome/DecisionContext`。

原始import闭包：paired→scoring→`analysis/stability_bucket.py::TaskStability`（183行）和`scheduler/anchor_selection.py::AnchorSelection`（236行）；anchor又依赖stability，均以stdlib为主；HarnessNode为type-only引用。若连同strategy复制，会拉screen/policy/tree/judge等更大闭包。目标只保留统计纯函数/结果结构与明确所需TaskEval字段，替换类型边界切断benchmark与调度依赖；无需model client、CLI、后台服务、git或Docker。

| 动作 | 具体范围 |
|---|---|
| 保留 | 同task配对差值、均值/SE诊断、原始per-unit结果、现有测试向量；明确旧promoted/credited意义供兼容验证 |
| 删除 | 自动基于mean-only晋升、missing→0作为所有失败通用处理、n=1/zero variance→inf作为强证据、直接bench runner依赖 |
| 替换 | Actio EvalUnitResult区分task失败/infra/invalid，frozen split+cluster ID；统计方法由独立policy选择；not-enough-evidence显式返回 |
| 封装/扩展 | `PairedDiagnostics`输入validated matched units，输出effect/N/CI/assumptions；AdmissionPort独立处理最小Δ、硬约束、多重比较/holdout，不用上游promoted字段控制生产 |
| 未来文件 | `evaluation/reuse/raven_paired.py`（带来源）、`evaluation/results.py`、`evolution/admission.py`。最后两者属K4，不能误称全部为Raven代码 |
| tests | 移植 `tests/test_evolver_gates.py`/`test_evolver_scoring.py`中纯诊断fixtures；保留旧行为兼容测试并新增Actio不同预期：n1、zero variance、missing、infra contamination、paired mismatch、cluster dependence、阈值与budget |
| 规模 | 约150–350 LOC适配/诊断，独立gate约200–400 LOC规划；0.5–1.5人周，E+R维护。根据105+226行源与可切断type边界估算，实际实现再修正 |
| 升级/退出 | upstream evolver计划退役；固定来源快照，不追整个root。季度/相关安全修复时diff；若类型切断仍复杂则标准统计库+保留test vectors，Raven降D |
| License | Apache2，保留root LICENSE及适用NOTICES，标记修改与origin SHA；未复制nanobot/UI也需记录scope而非丢全部notice。无本包专属商业托管禁令，第三方条款独立核 |

“bench-neutral”不等于统计前提适用。上游TaskEval docstring关于infra排除与实际pipeline行为存在差异；以实现/测试为准。37项通过只证明上游行为复现，不证明Actio admission正确。

## C03 · Raven 语义档案 selector

同一Raven SHA（E009）。`evolver/orchestrator/archive.py` 388行，入口 `GsmeArchive.consider/eligible_elites`、`CellElite`、descriptor及touched-path helpers。输入为candidate descriptor、parent lineage、valid eval summary、changed/deleted paths；输出是elite/重组建议，**不是production admission**。

原始闭包：archive→`gates/policy.py`（245行）→scoring/fisher/anchor；archive→`tree/node.py`（705行）→`judge/schema.py`（PatchWhere/PatchWhy）；其余json/dataclasses/pathlib/typing。直接复制archive会导入大量无关node/judge定义。源码只见stdlib类与上述模块链，不把整root/pydantic/model backend强行纳入；tree/loop更外围git/bench/config/sealed链不复制。

| 动作 | 范围 |
|---|---|
| 保留 | WHERE×WHY descriptor、同cell优胜建议、已尝试pair过滤、同file冲突跳过、多父来源的选择信息 |
| 删除 | `save/_load` best-effort JSON、坏文件空表成功、只有promoted才记完整parent的假设；不复制loop/CLI/backend/model/bench |
| 替换 | `CandidateOutcome/HarnessNode/AppliedPatch`投影为Actio immutable DTO；所有candidate/status写canonical lineage；selector纯读snapshot返回建议 |
| 扩展 | taxonomy_version、seat/schema兼容、namespace隔离、all-outcome lineage；banking、champion、admission三个状态分开；field-level seat冲突优先于粗文件冲突 |
| 未来文件 | `evolution/reuse/raven_archive_selector.py`、`evolution/archive_projection.py`；`storage/lineage.py`归K4。selector不持SQLite连接，不自己写active pointer |
| tests | 本次搜索未找到直接覆盖GsmeArchive/eligible_elites的专门上游tests；不能虚称已通过。可保留gates/scoring输入fixture；未来必须新增超过vanilla但未晋升、重组多父/重叠、重复pair、坏snapshot、写失败、failed候选保存等行为测试 |
| 规模/owner | 预计保留100–220行selector，100–250行转换/投影，0.5–1人周；依据388行源删去JSON与metadata authority。I负责存储，E负责selector |
| 升级/退出 | 与C02固定退役前快照；descriptor改版显式迁移。MVP可移除selector改SQL parent query，lineage/evidence不丢；无需另一完整外环 |
| License | Apache2、适用NOTICES、修改标记、原始SHA/source清单；未来再分发独立核依赖，托管不自动授权model/data |

## 为什么其余只D

Meta-Harness onboarding能直接成为检查清单，但experimental controller必须拉Harbor/BaseAgent/benchmark command、且timeout混reward；为了结果envelope抽取反而比少量Actio glue更大。DGM outer/self_improve_step携SWE日志、Docker与POSIX cp，parent selection假设不合社会实验。ACE playbook工具当前ADD为主，完整CRUD仍TODO；没有必要把字符串bullet格式变成Memory contract依赖。三者机制吸收进K4，既不复制也不声称模块已集成。

## 所有 E 项归入五个自有核心

| 核心 / 未来模块建议 | 为什么A/B不足、复用什么实现 | Backlog / 可验收边界 |
|---|---|---|
| K1 `domain/agent_spec.py`、`domain/persona.py`、`domain/mind.py`、`memory/contracts.py` | DSH config/Letta memory/Graphiti fact都不表达稳定身份、observer双时间、Genome权限；复用SQL与runtime context能力 | B02/B06；身份不静默覆盖、branch隔离、CAS迁移 |
| K2 `control/runs.py`、`workers/supervisor.py`、`adapters/runtime/dsh.py`、`adapters/environment/concordia.py` | 无现有root同时满足单world/single-memory owner及双slice；复用SDK、loop、Engine/Entity而非写第二loop | B03/B05/B07/B08；lease/reconcile、同合同 |
| K3 `experience/events.py`、`storage/event_store.py`、`experience/checkpoints.py`、`observability/otel_projection.py` | native journal不含完整域事实，OTel不能多父权威存储；复用SQLite/文件/journal/OTel SDK | B04/B12/B13；去重/缺失/完整manifest、可重建投影 |
| K4 `evaluation/contracts.py`、`evolution/candidates.py`、`evolution/admission.py`、`evolution/versions.py`、`storage/lineage.py` | Raven判定/可靠性不足，Meta/DGM闭包大；复用C02/C03及SOTOPIA评委，独立规则/权限必需 | B09–B11/B17；四态、冻结test、完整失败谱系/版本切换 |
| K5 `experiments/design.py`、`experiments/interventions.py`、`experiments/attribution.py` | viewer/DAG/LLM attribution没有实验识别；复用runtime fork、环境可选快照与标准统计工具 | B12/B15；cluster设计、freeze验证、受控差异/因果边界 |

这些路径只用于划分未来责任，不保证每个文件最终都存在；wrapper/extension也归五核心，不偷偷另增自研训练器/数据库/前端。A/B配置与test harness的实施范围必须先由B01/B02冻结。
