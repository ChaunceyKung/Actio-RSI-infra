# 13 · Architecture Decision Records

状态均是规划决定，非已实现系统。AFP=accepted-for-planning，P=provisional。每项列上下文、候选、证据、决策、代价、可逆性与复核触发条件。

| ADR | 上下文 / 候选与证据 | 决策 / 状态 | 代价 / 可逆性 / 复核触发 |
|---|---|---|---|
| ADR01 Independent Root | Raven root fork含host/registry/routing/DAG，但世界/心智/准入owner不同；独立Python可复用模块（E007–E011） | 独立Control，F Raven root、C局部gate/archive；AFP，R10/B02 | 要写薄域调度；RuntimePort可换backend；仅当未来root提供域契约且能消除双owner才重评 |
| ADR02 Python Control / TS Worker | 实验生态偏Python，DSH TS实现广；全TS会迁移实验栈，自写Python loop重复（E001/E015/E016） | 首选Python+DSH TS；P，R01/B03 | 跨进程故障/编码成本；备选Strands Python保持control，改变worker语言须显式ADR；5日探针无可行生命周期seam触发 |
| ADR03 Official SDK vs RPC | DSH已有stdio，但public lifecycle不完整（E001–E003） | A SDK+B adapter+C01窄补丁；不新建HTTP bridge；P | alpha升级维护；补丁超2人周/需重写loop则退出；真正多机需求再论证网络RPC |
| ADR04 Environment Separation | Concordia GM、AgentSociety batch、OASIS platform差异（E017–E020） | environment唯一world/clock owner，B adapter；AFP，R05 | optional caps使client必须处理unsupported；可加adapter不能私改world；第二结构映射失败重开contract |
| ADR05 Canonical Event | 原生日志只覆盖runtime，OTel单parent/queue投影不足（E003/E029） | canonical事实+cursor映射+outbox，原生日志保留；AFP，R03 | 多一层映射/迁移；source ref可重建；原生提供完整durable域事件时减少映射，不立即双写 |
| ADR06 AgentSpec/Genome | runtime config不表达稳定persona与受限演化，候选可能改规则（E008/E013/E036） | immutable Spec+allowlisted Genome；AFP，R16 | schema版本治理；新seat显式扩大，不原地破坏兼容；Persona或权限变异需求需研究批准 |
| ADR07 Memory Ownership | Letta当前local真实但闭包深；Graphiti非自动branch隔离（E012–E014/E021） | 自有contract+SQLite；Letta D，Graphiti B可选；AFP/P，R04 | 自写域投影/namespace；backend可替换；检索ROI不足不引graph，持久化量超界再迁SQL服务 |
| ADR08 Harness-first | prompt/skills/policy/plugin/loop均影响agent，权重训练不是首期必需（E004/E008/E010/E023） | L0/L1/L2一等模型，MVP只开低耦合seat；AFP | 一开始有额外mutation规则；逐seat可开关；隔离与eval充分才开放L2 |
| ADR09 External Training | R-Zero/verl/VerlTool是GPU/数据/模型体系，非控制面（E038–E040） | L3外部dataset/evidence/job/model artifact接口；AFP，R15 | 跨系统provenance；可接多个trainer；需要权重收益实验时单独立项不改owner |
| ADR10 Independent Gate | Raven promoted不强制2σ，小样本inf、archive banking含义不同（E008/E009） | 四态独立admission、冻结test/eval/预算；C02诊断；AFP | 校准/统计成本；rule改版开新campaign；出现judge drift/holdout泄漏即暂停准入 |
| ADR11 Strong Attribution | fork/log replay不捕获世界，LLM attribution非干预（E002/E018/E029/E033） | canonical多父provenance+manifest+cluster experiment；P，R08 | 中途branch首期限制；可降为起点重执行/描述性报告；freeze不完整禁止强因果宣称 |
| ADR12 Viewer and License | Phoenix ELv2，Langfuse MIT带EE排除且多服务（E024/E025） | Langfuse社区主选P，Phoenix内部备选P；R13 | 运维/许可闭包；viewer完全可换/延期；对外托管或使用EE需重审，不能据根MIT覆盖EE |
| ADR13 State and Version Recovery | native lock、world/memory/tool效果独立（E003/E018–E020） | pin run、lease fence、pending reconcile；rollback三域分开；AFP | 恢复可能needs_reconcile而非自动成功；只在完整manifest边界resume；出现旧worker争写/未知效果即停dispatch |

主要取舍不是“复用占比”，而是每个状态谁写、可否验证恢复、补丁是否比适配更贵。R01/R05/R06/R07/R09/R13的P状态必须由B任务证据更新，不能由文档提交自动转生产可用。
