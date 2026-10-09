# Phase 1C2C0 审阅与 Phase 1C2C1 行动方案

日期：2026-10-09（Asia/Shanghai）。审阅基线：`e2e6691ef9bae5f61bccaaa97528e0478bd9a666`；C2C0 冻结实现：`2e5f77b69b98f85c61df87e18d7e3ffad28e8cba`。

**建议进入 C2C1：单 seat 候选、独立准入与谱系的离线演练，并局部扩展 reasoning/text 通道审计。** 现有任务和指标可以支撑工程演练；本轮 provider 协议范围不足，不需要通过补跑 C2C0 才允许做候选基础设施。新阶段不以完成另一轮真实模型矩阵为目标，也不以虚拟候选分数代替能力证据。

[完整执行 Prompt](../prompts/phase1c2c1_channel_audit_and_candidate_lineage.md) · [审阅证据](phase1c2c0_review_evidence.json)。本轮仅审阅、离线验证和规划，产品代码未改，新增模型请求为 0。

## 1. 已验证的事实

| 内容 | 本轮复核结果 | 限制 |
|---|---|---|
| manifest 来源 | 37 个 artifact、52 个产品文件、4 个入口、86 个工具/测试文件匹配 | 同时核对 Git 和工作区；明确区分既有 CRLF/LF 字节，不改原 hash |
| 原始及源码归档 | 7 个 raw + 8 个 source ZIP；3,420 个成员，157,934,730 未压缩 bytes 匹配 | 检查归档及逐成员 hash，没有重新封存历史 |
| 安装与冻结 | 当前安装 52 个产品文件匹配；冻结后产品源码未变 | 发布早于 intent 由本地记录支持，不是独立签名时间戳 |
| 已发表验收 | 27 项测试记录与文件来源绑定一致，1 次失败验收保留 | 未重跑全部 27 项；交付路径脚本失败也保留 |
| 实际增量复跑 | 4 项纯离线测试通过 | 穷举生产/oracle 对照、手算边界、分层缺失/任务失败、C2B2 纠正；未启动 Worker |
| reader | 当前固定 reader 重算与原报告完全一致 | audit guard 禁止网络、子进程、runtime import、key/env 和文件写入 |
| 账本 | 86 个数据库文件 hash 匹配；43 个 Ledger 只读重算，字节未变 | live 与 rehearsal 分开，旧 rehearsal 的 unknown 不与 live 混算 |
| 清理 | 78 个具名 Job 无活动进程，35 个登记端口无监听 | 35 个服务 join 为历史记录核对 |

完整计划 24 episodes / 48 seats；启动 8，完整结束 7，未启动 16。attempted/sent/response/terminal/usage=15，文本 admitted=14，not_run=33，unknown=0。已启动子账本 registered=16，与 attempted=15 不同：第 8 个 episode 的 B 已注册但未发送；完整计划仍包含其余未启动单位。

**“7 个完整 pair”指 episode 内 A/B 行动对；跨 route 配对 block 仅 3 个完整、9 个缺失。** 下一阶段 candidate/control 又是新的配对轴，不能把 actor pair、route pair 与 candidate arm pair 混用。

reported input/output tokens=6,171/121，3 条 raw cost，币种/单位及 billed cost 仍未知。累计真实生成尝试保持 91，历史目录 GET 1 次另计。当前 report 中 family×route 的 format assigned=12、joint assigned=6；feasibility 分层加回完整计划。C2B2 纠正值仍为两 route 各 feasible 8/7/1、infeasible 8/6/2（assigned/defined/missing）。

本轮复核脚本曾因仅比较工作区 hash 报告 GATES/RESULTS 不匹配；固定 Git blob 与 manifest 匹配，差异仅换行。另一次使用了错误的 Ledger 列假设；实际为 body JSON，按已声明 schema 只读重算后通过。均是审阅脚本问题，未改产品或历史数据库。

## 2. C1R1：停止由审计合同能力范围导致

位置：[stream_audit.py](../../src/actio/stream_audit.py) 的 `single-choice-text-audit.v1`。原合同只允许 `delta.role/content`、单个 index=0 的 text block；这是先前刻意限定的范围。

`ep-07/H5/gpt-5.6/A` 的 HTTP 200 SSE 包含 `reasoning_content`。官方 adapter 输出 reasoning block index=0 和 text block index=1；两块在流内生命周期有重叠，不能假定一块完全关闭后才会打开另一块。本次不展示其推理正文，只对已有字节做比较，确认：

- raw content = adapter text deltas = adapter text block end = native answer；
- raw reasoning_content = adapter reasoning deltas = reasoning block end；
- 终态和 usage 已取得，账务 settled；原 v1 审计拒绝，无该 episode world effect 或 domain receipt。

因此本条样本支持“存在未支持的独立通道”，没有发现它的行动文本矛盾。但它**仍未按原合同准入**，不得将 admitted 14 改为 15、补写 domain receipt、续跑 B 或回填 not_run。

下一版应把两种通道独立核验，只将 content 的最终行动传给世界/B/memory/任务指标；reasoning 不成为公开行动、候选训练语料或推理质量分数。复用官方 translator，新增有界审计 profile；明确 block index、生命周期、文本与终态/usage 顺序。工具调用、额外模态及未声明字段继续 fail closed，而不是“忽略所有未知字段”。

给 C2C0 增加只读兼容性 sidecar，区分旧 verdict 与新 profile 的结构核验结果。此次比较只是单条历史证据分析，新审计和 runtime 集成尚未实施。

## 3. C1R2：失败归类及删失口径需细分

位置：[suite_measurement.py](../../src/actio/suite_measurement.py) 的 `failure_facts`。当前将所有 audit rejection 归为 `text_integrity`，并令任何 root cause 对应 `censored=true`。这在有限 C2C0 合同内用于保守拒绝，但下阶段容易混淆三个不同事实：

1. 不支持的协议字段/通道；
2. 已支持通道内的内容不一致；
3. 传输未完成/超时或原始证据不完整。

本例响应和终态完整，文本未准入不意味着 HTTP 请求耗时观察被截断。新合同按每个时钟/指标标注 observed、missing 或 right-censored；任务指标可以 missing，同时完整响应耗时仍 observed。root cause、文本准入、领域执行、账务和时延观察分别报告，不推断上游实际权重或账单。

## 4. 复用资产与具体界限

| 资产 | 已查验入口 | 下一步复用 | 不采用 |
|---|---|---|---|
| 官方 DSH pi-ai | `deepseek-ai/deepseek-harness@5badb15009ae1756c3afe0ae0cef1faafc290ccc`，`packages/llm/llm-pi-ai/src/stream.ts` 及 `tests/convert.spec.ts` | 已有 thinking→reasoning、text→text block 语义及测试向量 | 不替换生产 translator，不声称该源码与固定 binary 构建映射已证实 |
| Raven paired | `EverMind-AI/Raven@3632e6040c7038a60ec418ce39ccae185c72c19f`，`evolver/orchestrator/gates/paired.py` | 每单位 candidate/control 对照与诊断字段、测试思路 | missing→0、mean-only promoted、n=1/零方差无限 z |
| Raven archive | 同 SHA，`evolver/orchestrator/archive.py` | WHERE/WHY、parent/diff/evidence descriptor 参考 | best-effort JSON 权威存储、只保留赢家、自动重组和整体 root fork |
| 已有 Actio | Store/事务、immutable spec、seal/publish、任务 oracle、run/export/reader | 候选事件和谱系由同一 Python 领域 owner 持有，运行仍用 DSH/Concordia | 另建第二套 runner、JSON 状态权威或覆盖已有 agent spec |

本轮核对了 7 个固定源码/许可文件；3 个 GitHub raw 文件 HTTP 200 且与本地 Git blob 一致。未重新执行 DSH/Raven 全部上游测试；早期 Raven 37 项测试只作历史证据，不能当成本轮适配已验收。

## 5. C2C1 的最小可运行交付

保留两个 family、12 张卡、两 actor、两行动；本轮不再引入新任务、模型或多轮协商。

1. **通道合同**：新审计支持经过验证的 reasoning/text 组合，旧 v1 不变；历史 sidecar 与本地 runtime 测试通过，改正失败/删失分类。
2. **唯一可变 seat**：只让 A 的独立 scaffold artifact 中一段有长度限制的行动检查清单改变；Persona/身份、B、模型/工具/预算/世界/evaluator 不可由候选改动。
3. **候选档案**：一个冻结 baseline、一个人工编写的合法 checklist candidate，及少量静态不合法 fixture；所有提案、失败、decision 和 parent edges 持久化。不做 LLM 搜索或自动生成下一代。
4. **本机配对闭环**：12 cards × baseline/candidate 两 arms × 一条固定 loopback route label =24 episodes/最多48本机发送。每 arm 均真实经过 DSH/Concordia；主要矩阵给两 arm 相同固定响应，预期 delta=0。fixture 不会证明 scaffold 有效。
5. **独立准入与谱系**：候选静态合法、工程流程通过与能力晋升分开。可用带 synthetic 标记的正负 fixture 测试四态 decision；真实候选结论因无真实独立收益证据为 insufficient_evidence，activation=false。
6. **只读导出与持久性**：候选/运行/配对/decision/source 完整绑定；重复请求幂等、事务失败不产生半条谱系、重开数据库不触发重跑。只证明候选登记事务可靠，不扩大成完整 controller 恢复。

本轮新 live 请求不属于设计范围，因此不需要读取或验证真实 key；这不是撤销用户的无金额上限授权。后续确有 live 验证目标时沿用授权并独立冻结新计划，不重复费用询问。C2C1 不重跑旧 pilot，不拿91次历史请求凑 candidate arm 对照。

## 6. 成功与停止边界

C2C1 成功是首次交付可追溯的“提案→静态校验→冻结配对执行→独立决策→完整谱系”工程闭环。候选全部不获能力准入也可以成功；不能为演示晋升而伪造分数、把脚本行为归因于模型，或把12张开发卡改名当 sealed holdout。

Gate 分开报告 channel_audit、candidate_contract、paired_execution、lineage_durability、offline_verification、capability_admission。最后一项仍受真实独立证据限制。真人校准、live judge、研究效度、生产激活与演化晋升均不在本轮。binary_source_mapping=unproven、full_controller_recovery=unsupported 继续保留。

交付后普通推送任务分支及 main，核对 SHA。后续 C2C2 才讨论有限真实 baseline/candidate 工程试验；需要明确新评价数据与实际效用目标，不能直接把离线 dry-run 当作已开始自我改进。
