# 02 · 复用决策矩阵（权威表）

A Direct Reuse；B Adapter；C Extract/Secondary Development；D Design Reference；E Self-developed；F Reject。按能力/用途判定。`accepted-for-planning`（AFP）不是集成通过；`provisional`（P）必须过 gate；`blocked`（X）不可进入确定交付。证据见 [15](15_evidence_registry.md)，能力状态见 [16](16_capability_and_maturity_checklist.md)。

| ID / Capability | 主选 / 粒度 / 状态 | Evidence | integration / 缺口 | 备选 / 退出条件 | 验收 |
|---|---|---|---|---|---|
| R01 Shared Runtime | DSH 官方 SDK A + TS worker/profile B；Phase1A 条件准入，非 production | E001–E005；[Phase1A](../validation/phase1a/README.md) | Windows 固定 wheel、独立短路径 home、静态 policy guard、有界 supervisor；完整 resume/cancel/fork/cursor 为 G1 | Strands Python 仅在 G0 确认不可行且窄配置/plugin/patch 无解时同合同比较；网络/预算缺失不是退出 | B03/B05 与共享 assistant/Concordia adapter |
| R02 Tools/plugins | DSH/Cordis A、MCP client2 A、域 plugin B/P | E004/E006/E026 | permission/effect ledger、事件、deadline；HTTP OAuth 后置 | Strands tools/hooks B；只在 runtime 退出时整体切换 | B08，不重复外部写效果 |
| R03 Facts/storage | SQLite A、canonical E/K3、OTel SDK A+B/P | E003/E029/E042 | cursor、去重、hash、事务、outbox；不自研 DB 引擎 | 容量实测不够才迁 Postgres | B04/B13 |
| R04 Mind/memory | 自有 contract E/K1 + SQLite A/AFP；Graphiti B/P、P2 | E012–E014/E021 | M0–M6、主观性/双时间、CAS、consolidation；Graphiti 强制 namespace | Letta D；完整 Letta 作第二 owner F/AFP（此用途） | B06/B16 |
| R05 Environment | Concordia B/P；AgentSociety B/P2；OASIS B/P2 | E017–E020 | Entity.observe/act、GM 结果映射；pending/barrier 可选；snapshot 诚实声明 | Concordia seam 不成立则重评 AgentSociety，不自建完整 simulator | B07/B15 |
| R06 Eval/gate | Raven paired/scoring C02/P；独立 admission E/K4/AFP | E008/E010/E036 | 四态、缺失/infra、样本单位、阈值/多重比较；禁直用 promoted | 标准统计库+最小诊断（K4），保留 test vectors，不引完整外环 | B09/B10 |
| R07 Archive/lineage | Raven descriptor/selector C03/P；canonical lineage E/K4/AFP | E009/E011/E037 | selector 与入库分离、保存失败；移除 best-effort JSON authority | 普通 SQL parent query，selector 可移除 | B11 |
| R08 Replay/attribution | DSH fork A/B；manifest/experiment E/K3/K5/P | E002/E018–E020/E029/E033 | 全域 capture、I/O 匹配、冻结/重执行、干预 | episode 起点重执行；不支持的中途 branch 明确拒绝 | B12 |
| R09 Social evaluator | SOTOPIA EpisodeLLMEvaluator B/P | E022；Phase1A P5 controlled envelope | identity 映射、[]/错维度→invalid_measurement；worker故障另分 infrastructure_failure；真实 evaluator 未运行 | 确定性约束+人工 rubric；LLM 分数 exploratory | B09 pilot 后另 gate |
| R10 Control root | 独立 Python E/K2/AFP；Raven root F/AFP | E007–E009 | 域调度/lease，不重写模型 loop；避免 host 争权 | 无另一 root 直接解决 mind/world owner；优先缩范围 | B02/B04 |
| R11 Search/context | Meta、DGM、ACE、ADAS、AgentSquare、AFlow、ALSO、RSIHub、autoharness、OpenEvolve D/AFP | E010/E011/E023/E030–E037/E041 | 冻结评估、历史、seat 机制；提案仅 structured delta | P2 重评 RSIHub；不复制执行/权限闭包 | B10/B17 |
| R12 Sandbox | 结构化 seat allowlist+预算 E/K4；上游 sandbox A/B/P | E005/E010/E011/E030 | MVP 不执行候选代码；L2 Linux 隔离另 gate | Native Windows 不满足隔离则 L2 blocked，继续 L1 | B10/B14 |
| R13 Viewer | Langfuse 社区 B/P；Phoenix 内部 B/P | E024/E025/E029 | OTel projection + score/dataset refs；资源/EE 闭包审核 | 可延期 viewer；Phoenix 未许可对外托管 F | B13 |
| R14 Interop | MCP A/B；A2A/ACP D/P2、AFP | E026–E029 | spec/SDK/artifact 分开；域 API 独立 | 多机确需时才论证网络 RPC | B08/B17 |
| R15 External training | L3 port E/K4/AFP；R-Zero/verl/VerlTool D | E038–E040 | dataset/evidence→job→model artifact→独立准入 | 无 GPU/凭据不阻断 MVP | B17 |
| R16 Spec/Genome | immutable spec/受限变异 E/K1/AFP | E008/E013/E036 | schema、allowlist、CAS；禁变 evaluator/权限/预算 | runtime config 只作执行投影，无可直接替代的社会域模型 | B02/B10 |

## P0 排除与风险

硬排除针对采用范围：许可不兼容或不明且需复制/发布；仅营销材料却当依赖；必需服务不可用且无替代；核心 seam 仅占位；无法消除多重权威；无法记录核心输入输出。当前排除 Raven/Letta 整体作为第二 owner、未许可 Phoenix 商业托管、普通 exec 执行任意候选；不是否定这些项目所有用途。

可缓解风险包括 SDK gap、Windows UTF-8、wheel 差异、Concordia partial checkpoint、Langfuse 开销、judge 偏差，各有 gate/降级；不能据此重写全部基础设施。每个 C 的包与每个 E 的必要性集中于 [17](17_reuse_extraction_plan.md)。

买/用服务：未来可能采购模型 API 或已有托管观测；本轮不调用、不开户。价格、数据与合同是实施输入，费用按 [11](11_mvp_roadmap.md) 参数化。代码可用不等于免费运行。
