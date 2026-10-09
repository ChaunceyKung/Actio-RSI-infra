# Codex 执行 Prompt：Phase 1C2C1 通道审计与单 seat 候选谱系

请在 Actio-RSI-infra 实施 **Phase 1C2C1**：局部扩展 reasoning/text 通道的可核验范围，完成一个受限 scaffold 候选的“提案→校验→本机配对执行→独立准入决策→完整谱系”闭环。复用已通过的 DSH/Concordia/SQLite 和12张任务卡；本轮为离线及 loopback 工程演练，不运行新的 provider pilot。完成验证后提交、推送任务分支及 **main**，核对远端 SHA。不要只再交付规划，也不要为了展示晋升而制造收益。

项目：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
GitHub：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
建议分支：`phase1c2c1-channel-audit-and-candidate-lineage`。
审阅基线：`e2e6691ef9bae5f61bccaaa97528e0478bd9a666`；C2C0 冻结实现：`2e5f77b69b98f85c61df87e18d7e3ffad28e8cba`。

从包含本 Prompt 的最新 origin/main 开始，记录真实 HEAD、祖先关系和工作树，保护用户修改。读取 AGENTS.md、`docs/reviews/phase1c2c0_review_and_c2c1_plan.md`、同目录 `phase1c2c0_review_evidence.json`；C2C0 的 CONTRACT/RESULTS/GATES/CLI、manifest、failure-review、preregistration、任务/oracle/来源；以及 `docs/planning/08_evolution_architecture.md` 和 `17_reuse_extraction_plan.md` 中 C02/C03。相对路径均以项目根目录为基准。

## 0. 当前授权、范围和硬停止点

用户持续要求每轮完成并验证后推送 GitHub **main**。普通推送，无分叉优先快进；有并发更新先读取整合，不覆盖他人工作、不 force push。首次实现/任务执行合同冻结与最终结果分别发布；无需重复询问发布授权。

TokenKey 无金额上限授权继续有效，不能再引入 USD1/零金额门槛或“首次真实调用重新批准”的旧规则。但本轮实验目标通过本地确定性 fixture 验证，**不新增真实模型、provider API 或目录请求**，不进行 key 可用性探测。这是任务范围，非金额限制；后续需要 live 时沿用已有授权并独立冻结计划。

保留 C2C0 全部原件：sent/usage=15，admitted=14，not_run=33，unknown=0；累计真实生成尝试=91，目录 GET=1另计。禁止重发 ep-07/A、续跑其 B、补齐旧 pilot、重置旧 claim 或将历史 provider 输出解释为新候选实验。

本轮不新增 task family、模型、自由多轮协商、跨 episode 学习、LLM proposer、live judge、真人标签、训练、生产激活或演化晋升。只开放 **mutation seat=prompt_scaffold，actor slot=A**；这里“seat”是可变组件，不是同时放开两个 actor。

成功不要求 candidate 战胜 baseline；一次完整、可复核的 insufficient_evidence 或 reject 同样是有效工程交付。停止于 C2C1，不自动进入 C2C2。

## 1. 复用栈和不可变历史

沿用 Windows x64、Python 3.12、隔离短路径、官方 DSH SDK/runtime `0.1.5rc1`，exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`，Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。

维持 Python Control Plane → 官方 Python SDK → DSH TS loop → 真实 Concordia Sequential；复用官方 pi-ai translator、最终 fetch gate、Ledger、一次性资格、事实/receipt、归档、独立 oracle 和只读核验。不要搭第二套 runtime、网关、domain owner 或 JSON 权威档案。

优先读：`stream_audit.py`、`transport.py`、`transport_campaign.py`、`gateway_contract.py`、`budget.py`、`pilot_measurement.py`、`suite_contract.py`、`suite_tasks.py`、`suite_oracle.py`、`suite_measurement.py`、`pilot.py`、`scenarios.py`、`store.py`、`database.py`、`schema.sql`、`evaluation.py` 的 seal/publish，以及相应 tests/scripts。

新通道、新 scaffold/config/任务绑定、新 candidate/campaign/decision/lineage 导出均显式版本化；版本号依注册表确定并冻结。旧 v7/task v3/pure-text audit v1 解释不变。当前 implementation hash 会随新文件改变；历史证据必须用固定历史 source/reader 核验，不用新 reader 重新封存旧合同。

## 2. C1R1：版本化 reasoning/text 审计，生产转换继续用官方实现

已核对的来源：

- 本地 `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\01_deepseek-harness\repo`；
- GitHub `deepseek-ai/deepseek-harness@5badb15009ae1756c3afe0ae0cef1faafc290ccc`；
- `packages/llm/llm-pi-ai/src/stream.ts::toStreamChunks`；
- `packages/llm/llm-pi-ai/tests/convert.spec.ts` 中 thinking/text 映射测试；根 LICENSE。

源码明确区分 reasoning/text blocks；C2C0 固定 binary 也实际输出这两类。源码参考与 binary 观测分别记证据，`binary_source_mapping=unproven` 仍成立。不修改官方 translator，不为取最终答案重写 solver。

新增 bounded audit profile（命名可如 `single-choice-dual-channel-audit.v2`），在明确的新 C2C1 配置中选择。保留旧 v1 函数/版本或显式分派，不能因允许新字段而追认历史合同。

最低支持范围：单 choice、可选 reasoning_content、最终 content 行动、文本类型、已支持 finish/usage/DONE 与有限 UTF-8 SSE。原有 identity/重复键/字节、event、chunk、输出和期限边界继续有效。明确 null/空增量与字段类型策略；非空 reasoning 占用同一总体资源上界，不能无限丢弃后绕过审计限制。

分别核验：

1. raw `delta.content` → adapter text deltas → 对应 text block end → native 最终行动；
2. raw `delta.reasoning_content` → adapter reasoning deltas → 对应 reasoning block end；
3. adapter/native reasoning 记录的可用结构证据；如某层不保留该通道，明确覆盖边界，不能声称端到端不存在的证据已验证；
4. 唯一 stream identity、终态/usage 顺序与账务口径继续独立一致。

**不能把 block index 写死为0，也不能假设两种 block 不会同时打开。** 已有 C2C0 样本先打开 reasoning index=0，再打开 text index=1，随后分别 block-end。用按 index/type 的有限状态跟踪，冻结本版支持的块数/顺序/终止规则；不按“第一个块”取行动。只支持查验过的组合，额外 channel、tool/refusal/audio 等仍为明确 unsupported，不能通用忽略未知字段。

只有最终 content 行动进入世界、B 的公开观察、memory 和任务指标。reasoning 不是行动、正确答案、解释真实性或推理质量证据；不把它自动送给下一 actor、candidate proposer 或训练集，不要求模型额外暴露推理内容。用户可见报告以结构/核验结论为主，不复制推理正文。

测试用合成短 reasoning/text fixture，覆盖 text-only、reasoning+text、空 channel、交错块生命周期、分片边界、无最终 content、length 截断、各层文本不一致与未支持类型的拒绝。记录真实官方 DSH runtime 的 block/answer 行为；这些是本机协议验收，不冒称新的 provider 兼容已验证。

给 C2C0 历史失败追加只读 compatibility sidecar：原 source hash/reader SHA、原 rejected verdict、新 profile 核验结果与局限。本轮 review 已确认该记录 raw content 与 adapter/native answer 一致、reasoning 与 adapter 一致。新 sidecar 不能改旧 admitted=14、原停止点、domain receipt/world 或账务，不继续执行历史 episode。

## 3. C1R2：失败与删失语义

当前 `suite_measurement.failure_facts` 将 audit rejection 统一称 `text_integrity`，并令所有 root cause 对应 `censored=true`。新版本分开：unsupported_protocol/channel、content_mismatch、incomplete_stream、timeout、accounting_unknown、syntax_invalid、task_rule_violation；未知原因保留 unknown，不能靠错误字符串猜未观察到的事实。

保留 HTTP/headers/finish 实际观察、native code、deadline trigger、text admission、domain 状态、Ledger 状态。按具体时钟报告 observed/missing/right-censored：完整 HTTP/终态的耗时可以 observed，而行动指标因协议拒绝仍 missing。不能仅因为任务未准入就删失已完整观察的响应耗时，也不能从 HTTP200 推断真实上游身份或实际收费。

复用 C2C0 60/60/90 秒内层和115/165秒外层有限期限；若没有改期限传递，无需再次运行整套31秒慢测。新增通道活动不能无限续期 total deadline。保留无自动 retry、失败停止、Job 回收、usage 和 unknown 分离。

## 4. C1R3：唯一可变 scaffold 与不可变身份

定义有版本的 `ScaffoldArtifact` 和 `CandidateProposal`。本轮唯一可改字段例如 `/scaffold/checklist`：UTF-8 字符串数组，1..6项，每项非空且不超过160字符、整体不超过1024 UTF-8 bytes；baseline 明确允许空清单。限制值在合同中冻结，拒绝额外字段、未知路径和任意可执行内容。这里是数据校验，不宣称字符串长度等于完整语义安全认证。

只变 actor A 的 subordinate 行动检查清单；身份/Persona、自己的初始约束、B 的 scaffold、provider/model/profile、工具/权限、账务/期限、任务卡、可见性、oracle/evaluator、准入 policy、日志和隐藏数据均不可由 candidate 修改。候选不能提供 Python/TS、文件路径加载器、网络地址或自定义 evaluator。

candidate 不覆盖 `Store.agent` 的 immutable spec。保持稳定 actor identity 与基线 spec；scaffold 作为独立不可变版本，由 run manifest 显式绑定 `base_spec_hash + scaffold_hash + actor_slot + rendered_input_hash`。如必须改现有 schema，采用已有迁移/备份机制，不静默更新旧 agent.spec、不重写历史 run。领域状态继续由 Python Store 持有。

合法清单应是跨卡通用规则，例如检查公共允许范围、只用自己的约束、输出一个精确选项；不得写入 H5/S4 等测试卡答案、对手私有值或全知分组。初始合法 candidate 由实施者人工编写并明确来源，不调用模型生成候选，不循环搜索。

本轮至少记录：

- B0：冻结 baseline，空 scaffold；
- C1：B0 的单父合法 checklist candidate；
- 静态负例：越界字段、长度超限、不存在/不匹配的 parent，各自显式标 synthetic fixture，验证拒绝和留档。

每份提案保留原始规范化内容、hash、parent 引用、mutation seat/actor slot、diff、来源、验证结果和事件。无效 parent 可以保留在原始 rejected proposal 中，不能伪造 canonical parent edge 或违反外键。拒绝的候选也不能从谱系查询中消失。

## 5. 候选登记、决策和谱系的领域存储

复用 Store 的事务与 immutable content，必要时新增最小 candidate、candidate_event、lineage_edge、campaign_binding、decision 结构。不可变事实与可重建索引区分清楚；导出 JSON 是投影，不成为第二权威数据库。

基本状态流：proposed → validated/rejected → evaluating → decided；不支持自动重新领取 evaluating 任务。每次 transition/decision 有独立记录及 policy hash，不通过覆盖一个 JSON 丢失旧状态。单父 B0→C1 即可，多父/重组只保留将来 schema 扩展点，不做搜索或 selector 系统。

必须持久绑定：proposal/parent/baseline/candidate hash、单一 seat diff、任务/oracle/policy/source/运行 pins、初始 memory/spec、campaign和全部 arm 单位、run/request/ledger/evidence refs、逐单位诊断、四态结果及原因、缺失和清理。candidate identity、统计分组与答案不进入 actor wire。

复用并查验：

- `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\02_Raven\repo`；
- `EverMind-AI/Raven@3632e6040c7038a60ec418ce39ccae185c72c19f`；
- `evolver/orchestrator/gates/paired.py`、`tests/test_evolver_gates.py`；
- `evolver/orchestrator/archive.py` 的 descriptor/parent/changed-fields 思路。

按 C02 窄复用 per-unit 差值与字段/测试向量，缺失显式表示；不能照搬 missing→0、mean-only `promoted` 或 n=1/zero variance→infinity。C03 只作 WHERE/WHY/parent 元数据参考，本轮无需复制完整 selector；禁止 JSON save 失败吞掉、坏档案清空成功或只留 winners。提取代码保留 Apache-2.0/适用 NOTICE、来源 SHA 与修改说明；若仅参考公式/测试，明确 reference，不宣称整模块已集成。

## 6. 候选配对合同：冻结的是干预，不是好成绩

不要把 C2C0 的 route comparison 偷换成 candidate/control。新配对键至少包含 card、task/oracle hash、固定 route label、初始状态 hash、mutation seat/actor slot、repeat、baseline/candidate版本；arm 是该配对内的 baseline 或 candidate。

本轮冻结 **12 cards × 2 arms × 1个固定 loopback route label × 1 repeat =24 episodes，最多48次本机 solver HTTP发送**。使用已支持的 gpt-5.6 标签作为 serializer fixture 即可；它不代表调用真实 GPT。两 actor 仍同一固定 label。case 顺序和 arm 先后由冻结 seed 交错，baseline/candidate 不共享动态 memory或世界状态。

A 的 allowed scaffold 是唯一直接干预。B 的配置不变，但 B 必须看到各 arm 实际 A 公开行动；A 行动变化带来的 B 输入变化是下游结果，不能强制替换成另一 arm 的 A 行动。baseline/candidate 运行分别使用独立 Store/run/claim/账本，保留规范化 identity 的可比性和执行身份的唯一性。

**主矩阵两 arm 使用相同的冻结 fixture 响应规则，预期指标 delta=0。** 不根据 candidate 名称/arm 选择更好的答案。loopback 只让真实 DSH/Concordia执行可控协议和任务行为；它不解释 scaffold 意义，不证明自然语言清单有效。fixture 规则及可能读取的字段事先冻结，不能把 oracle/答案放进 actor messages来冒充 solver 解题。

独立的小型合成 decision fixtures覆盖正/负差值、格式/硬规则失败、缺失/不完整、协议错误和方差边界；明确 `evidence_kind=policy_fixture`，不得混入主矩阵或真实候选收益。无需每个 policy fixture 都启动 Worker；纯函数足以验证时用纯函数。

沿用完整计划：每个 seat/episode/arm pair 即使未启动、前驱无效或基础设施失败也有位置和原因。pair assigned=12；两 arm均可评估才是 complete arm pair，缺失不删除/补0。actor A/B pair 与 arm pair 分列，禁止把48条消息当作48个独立样本。全部12张卡已用于开发，`independent_research_units=0`，不能变成 held-out/sealed final test。

## 7. 独立准入 policy 与激活阻断

区分三类结果：static candidate validity、工程执行/证据 validity、能力 admission。proposer artifact 不得自带可执行 policy、阈值或替换 evaluator；由 Control Plane 加载冻结的受信版本，candidate只能引用其hash。

四态 decision 保留 `pass/reject/insufficient_evidence/infrastructure_failure`，同时必须有 scope/evidence_kind、逐项原因、来源和 `eligible_for_activation`。明确优先级：

1. 候选越界/父绑定错误等已确认静态不合法 → reject；
2. 运行/证据不完整导致不能可靠评估 → infrastructure_failure，完整保留缺失；
3. 静态合法且工程证据完整，但只有 fixture/已用开发卡/无独立真实收益证据 → capability decision 为 insufficient_evidence；
4. policy 的 pass 分支可以用显式 synthetic fixture 做单元验收，但该记录必须限定 policy_fixture，`eligible_for_activation=false`，不能变成 C1 的能力准入。

可以报告候选接口及本机闭环 engineering PASS。**本轮所有真实登记候选的生产 activation=false；主矩阵不支持 capability pass。** 不创建/更新生产 active version pointer，不修改现有 agent/spec。可封存 inactive候选版本/decision，后续阶段再实现有证据的激活 CAS。

按 family 分开显示格式、本地 hard rule、共同结果、toy utility、缺失和协议状态；不合成为跨 family 排名，不计算显著性/推广 CI、无限 z 或成本归一化结论。全知 upper bound/regret不能成为 actor 应知道对手私有值的惩罚。不要从一两个好例子选 winner；本轮没有选优搜索。

## 8. 核验与持久性：验证真实行为，不只构造对象

冻结候选、policy、schema、配置/通道、任务/metric和本机矩阵前完成纯测试。将通过的实现及机器可读执行计划 commit 并普通 push 任务分支和 main，核对 SHA；这次提前冻结证明合同固定，不把它包装成正式研究预注册。随后运行本机矩阵，终稿再发布结果。发现实现缺陷则保留失败、明确新版本与受影响重跑，不悄悄换合同合并样本。

必要验收包括：

- 双通道 raw/adapter/native检查、旧 v1不放宽、C2C0兼容 sidecar与失败分类；
- candidate单字段及长度/parent校验、不可变内容hash、重复提交幂等、所有被拒提案留档；
- baseline/candidate的实际prepared/full-wire差异仅限 A 清单；固定 A输出时B wire不因candidate metadata改变；改变对方hidden信息时自身允许视图/wire保持不变；
- 真实DSH/Concordia完整24-episode主矩阵，receipt/world/evaluator绑定到各自arm，而不是把baseline报告复制后改candidate_id；
- 双通道仅content进入公开观察、领域事实及memory；reasoning不被当行动或记忆；
- 完整计划/配对/分层分母、对比指标与四态policy独立重算；
- 事务内登记与事件原子性；注入写失败后不产生半条proposal/decision/edge；重开DB原事实仍在，不能把损坏档案当空库成功；
- 重复/中断任务不会自动重执行，错误parent/循环edge不能变成有效谱系；失败/unknown保留不授予重试；
- 新导出由只读 verifier核验，禁止网络、key/env、子进程、Worker、写入；不执行导出指定的任意源码或插件；
- 必要迁移/旧库只读兼容、pip check、源码与安装一致、实际公开CLI及具名Job/服务/端口清理。

候选DB登记/导出恢复不等于完整 controller恢复；继续报告 `full_controller_recovery=unsupported`。本轮验证原子性可用最小故障点，不要重建分布式恢复系统。

无需因为文档变化反复跑全量suite；只对新增/受影响行为运行必要测试，失败及修复证据留存。构建、runtime矩阵、清理串行；不并行启动旧历史测试Worker。

历史固定 reader沿用既有完整SHA注册表，尤其C2C0=`e2e6691ef9bae5f61bccaaa97528e0478bd9a666`、C2B2=`e89d8b370c6cc53de21f651b49e7b2626eb1a559`。旧reader仍重现原报告，新解释只写sidecar；旧C0/C1/C2A.1/C2B0/C2B1按受影响分派做回归，不为确认旧key或插件再次发请求。

## 9. 执行与发布保护

本轮runtime只接明确literal loopback与fake credential，禁止provider origin；真实key只在必要的发布前本地精确秘密扫描中读取，不输出任何key/片段/长度/hash，不进入Actor/trace/Git。已有TokenKey副本继续ignored/untracked，不复制或重新发给服务。

一次seat请求、有限输出/总期限、独立claim、任务失误和基础设施失败分离。主矩阵基础设施/证据异常按冻结规则停止并保留未运行，随后本地修复有独立版本；不自动换供应商或进入真实pilot验证。运行目录用短路径、具名Job；只清理当前拥有的进程/服务，不杀所有Python/Node或依靠复用PID。

源于历史文件的reasoning内容和账户数据不用复制进新公共报告；必要原件继续按既有受控归档管理，公开元数据/合成fixture/核验结果即可。Git阶段只stage本轮安全文件，精确凭据和敏感内容检查后发布；不提交venv、binary或大raw日志。无需无目的扫描全部node_modules。

## 10. 交付和main要求

交付 `docs/validation/phase1c2c1/`：

- CONTRACT/RESULTS/GATES/CLI、当前README入口；
- 通道profile与兼容sidecar、失败/时延观察分类；
- candidate/baseline/seat/parent合同与提案清单、来源及静态拒绝记录；
- 冻结本机campaign/全部arm单位、实际运行证据与独立诊断；
- policy/四态决策、明确scope和不可激活状态；
- canonical lineage导出和只读核验、DB持久性/必要迁移证据；
- DSH/Raven复用映射、许可、source hash、干净安装/历史回归/清理、evidence_manifest；
- C2C2建议，但不执行下一阶段。

Gate至少分别报告 `channel_audit`、`candidate_contract`、`paired_execution`、`lineage_durability`、`offline_verification`、`provider_compatibility`、`capability_admission`、`production_activation`。本机兼容不提升provider稳定性证据等级；真实模型请求0、human_labels=0、independent_research_units=0。费用/账单/upstream identity仍UNVERIFIED，binary source映射和完整恢复限制不变。

最后检查diff/凭据/产物hash/CLI，commit → 普通push任务分支 → 安全合入main → 普通push origin/main → 核对远端SHA与本地一致、工作树状态。推送失败保留本地提交并报告具体原因，不强推、不把未发布说成已发布。

最终中文报告说明完成的候选闭环、旧协议停止的准确解释、新通道审计覆盖、实际local运行/失败/not_run/unknown、四态decision及为何不激活、历史91次生成尝试保持不变、清理、main提交和结果/manifest/CLI链接。**停止于C2C1；不因fixture PASS自动生成新候选、激活版本或调用真实模型。**
