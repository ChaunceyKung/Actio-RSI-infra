# 19 · 一页 Build / Buy / Reuse

方向：独立Python Control→RuntimePort→官方Python SDK→DSH TS Worker；Concordia首个真实环境；SQLite+immutable artifacts；单seat受控演化。下表是[02](02_reuse_decision_matrix.md)的导航摘要，判定状态与细节以02为准。

| 能力 | 采用资产/成熟度证据 | 方式 | 我们的wrapper/extension | 优先级 / 阻塞 |
|---|---|---|---|---|
| 共享agent执行 | DSH SDK/client/TS loop；client29项通过，真实worker未测 | A+B+C01 | RuntimePort、profile隔离、生命周期小补丁 | P0；E001–E005/B03 |
| plugin/tool/MCP | Cordis lifecycle、DSH MCP client2；静态实现 | A+B | 域hook、permission/effect ledger、语义事件 | P0；E004/E006/E026/B08 |
| 事实与状态 | native JSONL+SQLite；有恢复实现，目标未测 | A+E/K3 | cursor去重、transaction/outbox、manifest | P0；E003/E042/B04/B05 |
| Persona/社会记忆 | SQL后端；Letta/Graphiti作为边界证据 | A+E/K1，Graphiti B/P2 | namespace、双时间、observer、consolidation | P0；E012–E014/E021/B06 |
| 社会环境 | Concordia Engine/Entity/GM；checkpoint部分 | B | visible observation、intent、GM outcome桥接 | P0；E017/E018/B07 |
| 独立社会评价 | SOTOPIA EpisodeLLMEvaluator；异常/身份缺口 | B | result validation、rubric、frozen split | P0；E022/B09 |
| 配对诊断/准入 | Raven paired/scoring；37项测试通过 | C02+E/K4 | 四态、cluster统计、冻结规则/holdout | P0；E008/B10 |
| 档案/谱系 | Raven descriptor/selector；JSON durability不足 | C03+E/K4 | 全候选lineage、transaction、version CAS | P0；E009/B11 |
| branch/干预 | DSH fork+环境partial snapshot | A/B+E/K3/K5 | 全域manifest、起点重执行、实验识别 | P1；E002/E018–E020/B12 |
| 观测viewer | Langfuse社区OTLP/eval/dataset；多服务未部署 | B | 非权威OTel投影、脱敏/outbox | P1；E025/E029/B13；内部Phoenix备选 |
| 外部服务采购 | 模型API/可选托管viewer | Buy仅未来授权 | provider/price/data-use pin、budget | P0输入；本轮无付费调用 |
| 后续环境/训练 | AgentSociety/OASIS；A2A/ACP；外部trainer | B/P2、D、L3port | batch/pending、protocol facade、artifact admission | P2；B15–B17 |

最值得复用的五个模块级资产：① DSH官方Python SDK+TS执行/原生session；② Cordis lifecycle+DSH MCP tools；③ Concordia Engine/Entity/GM seam；④ Raven paired/scoring与archive selector（两个独立C包）；⑤ SOTOPIA EpisodeLLMEvaluator。Viewer/SQLite是基础设施依赖，不是新的领域root。

不直接采用：Raven整体fork作root、完整Letta作第二agent/memory owner、Meta/DGM整个研究执行栈、Phoenix未许可对外托管、把普通subprocess/AST检查当L2沙箱、把session fork或trace links当完整因果分支。

自研只保留五核心：身份心智、边界/状态协调、事实/检查点、独立评估准入谱系、干预归因实验；[17](17_reuse_extraction_plan.md)逐项解释现成实现为何不足。开工顺序B01→B02/B03→B04–B06→B07/B08→B09–B11→B12/B14。三大风险是生命周期/平台闭包、跨owner恢复、评价效度；都有明确降级而非假通过。
