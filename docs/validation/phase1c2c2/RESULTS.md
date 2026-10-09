# C2C2 结果

冻结提交 `3bef7e15b0eb21beeb10888eb508056592b977b0`。计划 `05ec305c272dcf3a5c4173ff58a1c2bc224d91a7f5bb5f399b692bdcbcc96707`。
远端核验 2026-10-09T15:02:56.353Z → intent 2026-10-09T15:02:57.289Z；这是本机记录，不是独立签名时标。

技术工程：**PASS**。C1 本轮决策：**insufficient_evidence**；B0 为参照，未授予晋升决定。能力没有 pass 路径，activation=false。

| 计数 | 实际值 |
|---|---|
| planned_episodes | 24 |
| observed_episodes | 24 |
| not_run_episodes | 0 |
| technical_complete_episodes | 24 |
| execution_resolved_episodes | 24 |
| assigned | 48 |
| sent | 48 |
| response | 48 |
| terminal | 48 |
| admitted | 48 |
| not_run | 0 |
| protocol_error | 0 |
| attempted | 48 |
| usage_responses | 48 |
| unknown | 0 |
| task_predecessor_invalid | 0 |

本轮实际外部生成发送 48；历史 91 与目录 GET 1 排除于新分母；累计真实生成尝试 139。未进行 smoke、目录扫描、诊断或第二 live 批次。
开发/验收本机发送 149、usage 147、unknown 2，单列而不拼入 live。

| 指标配对 | assigned | defined | missing | not_applicable |
|---|---|---|---|---|
| format_A | 12 | 12 | 0 | 0 |
| local_hard_A | 12 | 12 | 0 | 0 |
| format_B | 12 | 12 | 0 | 0 |
| local_hard_B | 12 | 12 | 0 | 0 |
| b_response_rule | 12 | 12 | 0 | 0 |
| joint | 12 | 12 | 0 | 0 |
| utility_A | 12 | 12 | 0 | 0 |
| utility_B | 12 | 12 | 0 | 0 |
| pareto | 12 | 12 | 0 | 0 |
| regret | 12 | 12 | 0 | 0 |
| text_verified_A | 12 | 12 | 0 | 0 |
| domain_executable_A | 12 | 12 | 0 | 0 |
| text_verified_B | 12 | 12 | 0 | 0 |
| domain_executable_B | 12 | 12 | 0 | 0 |

本次所有逐卡指标 delta 均为 0。这里只描述本轮观测，不证明候选等效、无效或可泛化。

| family | arm | format A/B true/defined | hard A/B true/defined | joint true/defined |
|---|---|---|---|---|
| scheduling | baseline | 6/6 / 6/6 | 6/6 / 6/6 | 3/6 |
| scheduling | candidate | 6/6 / 6/6 | 6/6 / 6/6 | 3/6 |
| bargaining | baseline | 6/6 / 6/6 | 6/6 / 6/6 | 2/6 |
| bargaining | candidate | 6/6 / 6/6 | 6/6 / 6/6 | 2/6 |

arm pair 执行完成 12/12；与每个指标能否比较分开。各卡原值/delta/null/原因、全部 seat、family/arm/feasibility 分层见 [report](samples/report.json) 和 [bindings](bindings.json)。
C1 已观察约束违反 0 项；B0 参照诊断 0 项。任一方格式错误不删除整对；缺失效用不补 0。

三个前置边界：schema 4 新 evaluation 追加历史，保留旧 candidate decided/decision；技术完成与行为/指标适用性分离；v9 独立 live/rehearsal 接线，旧 v8 仍 local-only。每份 B 输入按本臂实际 A 正向重算，非历史字段及 hidden 反事实保持允许边界。
同一 B0/C1 仍链接 C2C1 原 local 评估及本轮 live 评估。原六份提案/decision、24/48/12/零差值、C2C0/C2B2 的停止与 claim 保留。源库/hash/备份、迁移、两评估事件、重开等值和固定历史 reader 均有证据。

这 12 卡均已用于开发，单 route、单次两臂没有消除模型随机性或时间漂移。split=development_exploratory，independent_research_units=0，human_labels=0。无整体排名、显著性、推广 CI、候选能力获益或泛化结论。
费用保留原 Decimal 文本；币种/单位、可信报价、账单和上游权重身份未核实，不估 USD、不声称对账。reasoning 仅用于协议一致性核验，正文在 controlled raw archive，不进入公开报告/actor/memory。

清理：197 个本轮具名 Job 均 inactive/reaped，8 个本机服务 join，8 个记录端口无监听，authorized/reserved/sending=0。unknown 可保留，不重领。
完整 controlled delivery 已在禁止 key/env/network/process/runtime import/write 的 guard 下独立重算。公共报告为该完整导出的投影；其本地路径、hash 与固定 reader 见 [controlled delivery](controlled-delivery.json)，不把脱敏投影冒充原始可核验协议证据。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [预注册](preregistration.json) · [谱系](samples/lineage.json) · [决策](samples/decision.json) · [manifest](evidence_manifest.json)

停止于 C2C2；binary_source_mapping=unproven，full_controller_recovery=unsupported。
