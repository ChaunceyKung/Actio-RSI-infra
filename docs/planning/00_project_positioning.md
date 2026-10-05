# 00 · 项目定位与需求基线

Actio 是持久、社会化、可受控演化 agent 的基础设施。Human/Society Simulation 要求观察可见性、人格一致性、主观信念、关系和社会行为保真；Socially-Minded Assistant 要求持续身份、规划、工具和长期适应。两个目标共享领域内核，通过环境契约表达差异。

初期人口 10–100，未来约 1K。人口不是同时活跃的 worker，也不是模型请求并发；调度、成本与内存预算分别度量。Python 承担实验、领域状态、评价与演化；优先 TS harness worker。Simulator 是外部世界，拥有规则、时钟、可见性和行动裁决。

## 五个核心差异与需求追踪

| 自有核心 | 需求与验收意图 | 证据 → 决策 → ADR → backlog |
|---|---|---|
| K1 身份、Persona、MentalState 与受限 Genome | REQ-MIND：身份不能被候选静默覆盖；belief 有观察者/证据而非世界真相 | E012–E014/E021 → R04/R16 → ADR06/07 → B02/B06 |
| K2 共享 Runtime/Environment 边界及一致性协调 | REQ-RUNTIME/REQ-ENV：同一 runtime 跑 social+assistant，环境唯一裁决，恢复不双写 | E001–E006/E015–E020 → R01/R02/R05 → ADR02/03/04/13 → B03–B08 |
| K3 Canonical Experience/Event/Checkpoint | REQ-EVENT/REQ-REPLAY：输入输出可追踪、重复可去重、丢失可检测，多源 provenance 可重建 | E002/E003/E018/E029 → R03/R08 → ADR05/11/13 → B04/B05/B12 |
| K4 独立评估、准入、版本与谱系 | REQ-EVAL/REQ-EVOLUTION：提案者不能改规则；拒绝/无效结果同样留档 | E008–E011/E022/E023/E036 → R06/R07/R09 → ADR08/10 → B09–B11 |
| K5 Branch/Intervention/Attribution 实验 | REQ-ATTR：冻结条件和识别假设可检查，受控差异与因果主张分级 | E017–E020/E029/E033 → R08 → ADR11 → B12/B15 |

REQ-MEMORY 由 K1/K3 持有，REQ-PROTOCOL 由 K2/K3 接入 MCP/OTel；REQ-TRAIN 仅外部训练 artifact 接口，见 ADR09/B17。完整 SHA 在 [15](15_evidence_registry.md)，不从项目名推断功能。

## 范围与研究边界

首期建设两个最小链路、一个低耦合演化 seat、可靠事实记录与拒绝闭环。不建设完整社会模拟器、百万 agent 平台、训练栈、复杂桌面 UI、工作流编辑器、通用数据库、生产 K8s 或任意自主代码热改。七个逻辑 plane 不拆成七个服务。

研究包括社会指标有效性、身份一致性量表、干预识别和跨场景泛化；工程包括 owner、恢复、namespace、预算和合同兼容。实验指标改善不能替代工程恢复验收，成功启动不能替代社会保真度证据。

L0 是 run 内已授权范围的策略适应；L1 是跨 run 的 policy/prompt 版本演化；L2 是 harness/plugin/loop 组件候选，领域上一等建模，执行上只在后续隔离门槛通过后开放；L3 权重更新仅对接外部训练 job。优先 package/SDK → adapter → 模块抽取 → 窄 fork → 必要自研。

Persona 最小来源支持 synthetic、population_statistics、survey、dataset、generated，携 source_ref、license/consent_ref（适用时）、sampling/calibration/generator_version、population_id 与属性不确定性。MVP 使用自有合成人格，数据可访问不等于可再分发。

完成 MVP 不要求 candidate 战胜 v1。能重现失败、隔离执行、识别证据不足、拒绝违规修改、保留 lineage 并解释恢复边界，同样构成完整演示。
