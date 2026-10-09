# Codex 执行 Prompt：Phase 1C2C0 任务集与独立评估准入

请在 Actio-RSI-infra 实施 **Phase 1C2C0**：修复分层分母，明确有限超时合同，从已经查验的开源资产提取第二个任务 family，完成独立确定性评估与离线区分度准入，再运行一个预注册的有限 solver 工程 pilot。验证后提交、推送任务分支及 **main**，核对远端 SHA。请完成可运行交付，不要只再写一轮准备文档。

项目：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
仓库：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
建议任务分支：`phase1c2c0-task-suite-and-evaluation-admission`。
审阅基线：`e89d8b370c6cc53de21f651b49e7b2626eb1a559`；C2B2 冻结实现：`80d13896a790cb341ecf923f41330b967591b210`。

从包含本 Prompt 的最新 origin/main 开始，记录实际 HEAD 和祖先关系，先保护已有修改。阅读 AGENTS.md、`docs/reviews/phase1c2b2_review_and_c2c0_plan.md`、同目录 `phase1c2b2_review_evidence.json`，以及 C2B2 的 CONTRACT/RESULTS/GATES/CLI、manifest、preregistration、failure-review。相对路径均相对于上述项目根目录。

## 0. 已授权范围与本轮完成定义

用户已指定 TokenKey `https://api.tokenkey.dev/v1`，并要求“不设置预算上限，以推进项目为准”。本 Prompt 所需的凭据读取和有限 solver 工程 pilot 沿用已有授权，**无需再次询问同一真实调用或金额批准**。使用显式 uncapped 策略，不能用 0、巨大整数或没有语义的 null 冒充无上限；仍保留逐请求长度、期限、一次性 claim、usage/unknown 账本、清理及阶段停止条件。

本轮目标是任务资产和评估基础设施准入，仍是 engineering pilot。没有真人标签就报告 0；人工编写的真值表是测试 oracle，不是真人行为标注或专家效度校准。live judge、训练、自动候选生成/晋升、部署、完整恢复和正式研究不在本轮。

完成目标：

1. 分层统计与独立离线 reader 正确，C2B2 追加纠正表可复核；
2. scheduling 和 finite multi-item bargaining 两个 family 在现有真实 DSH/Concordia 栈工作；
3. 两个 family 的 oracle、指标区分度、可见性、计划完整性通过本地准入；
4. 在先发布冻结实现/预注册的条件下，执行新 pilot 或按预注册停止，完整报告全部分母；
5. 发布验证过的实现、证据、结果和复现入口到 main。

不要把 C2B2 的 STOPPED 当作必须“补齐 64 次”的失败。旧 unknown=1、not_run=10 与原 claim 保持原样；禁止重发 `ep-26/B`、重置 claim、回填旧批次或混合新旧合同。

## 1. 固定基础与版本边界

沿用 Windows x64、Python 3.12、短路径运行目录、官方 DSH SDK/runtime `0.1.5rc1`，exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`，Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。保持 Python Control Plane → 官方 Python SDK → DSH TS loop → 真实 Concordia Sequential；SQLite 继续持有领域事实、账务和计划关联。

复用官方 `@deepseek-ai/dsh-llm-pi-ai`、`actio-tokenkey` Chat Completions 路由、serializer/translator、无 retry profile、最终 fetch gate、raw→adapter→native 文本检查、Ledger、归档和只读 reader。不重新检查已证实插件是否存在、不再扫描整个模型目录、不建设网关、不用 Python OpenAI SDK 取代 solver。

优先读现有 `src/actio/` 下 pilot、pilot_contract、pilot_measurement、task_v2、task_contract、scenarios、stream_audit、gateway、gateway_contract、transport、transport_contract、budget、terminal、verify，以及 `plugins/transport.mjs`、对应 tests 和 scripts。按现有边界扩展，不建立平行的第二套事实权威或执行器。

以明确的新配置/任务/测量/预注册版本和 C2C0 执行模式分派；具体版本号在实现时依据仓库当前注册表确定并冻结。旧 v6/task v2 的允许值、超时和 reader 解释不放宽。新运行不能继续标为 C2B2。增加新的阶段授权入口及独立 claim namespace，绑定完整计划、源码/任务/metric hash，跨输出目录仍只能领取一次。

## 2. 首先完成两项有证据的前置修正

### C0R1：从完整计划计算分层分母

`pilot_measurement.analyze_pilot` 先过滤 `metrics=None`，导致 `joint_by_feasibility` 漏掉未启动 episode。冻结任务已经可以确定其 feasibility。

新版本在运行前给每个 planned episode 绑定 family、case、role、route、feasibility 等 evaluator-only 分组。即使未启动也不能消失。每项指标明确单位（seat/episode/pair）、适用条件、真值及缺失原因；建议输出：

- `assigned = eligible + not_applicable`；
- `eligible = defined + missing`；
- 对布尔指标 `defined = true + false`；
- 不适用、未启动、前驱行动无效、原始文本不可信和基础设施 unknown 分开；未观察到不填 false/0。

指标 eligibility 应尽可能由冻结合同决定。对于依赖合法 A proposal 的 B local 指标，预先规定前驱无效时的 not_applicable/不可评估理由，并另报 A 行为错误及未运行 B，不能借此隐藏失败。每层汇总可回到完整计划；未完成模型配对 block 不删除、不补零。

在新验证目录写 C2B2 append-only sidecar，绑定原文件 hash、固定旧 reader SHA、新复核 reader SHA 和 metric 版本。旧报告/manifest/产物不改；旧 reader 重算仍应与旧报告一致，新 sidecar 明确纠正范围。必须复现以下 episode 级表：

| route | feasible | assigned | defined | missing |
|---|---|---:|---:|---:|
| gpt-5.6 | true | 8 | 7 | 1 |
| gpt-5.6 | false | 8 | 6 | 2 |
| claude-sonnet-4-6 | true | 8 | 7 | 1 |
| claude-sonnet-4-6 | false | 8 | 6 | 2 |

新增必要行为测试覆盖整层未启动、单 seat unknown、无完整 pair、合法任务失败、全部 not_run；不能只给这四个数写硬编码测试。

### C0R2：有限超时、可解释失败与停止语义

旧官方 idle=30s 从首 headers 前就可能生效，覆盖 headers=45s 的等待预算。本次失败有 native TIMEOUT，没有 HTTP 响应；29,276ms fetch 层时长不意味着 native 30s 记录错误。

新合同默认考虑 headers=60s、idle=60s、total=90s；ready=30s、RPC=5s、result=115s、drain=5s、close=5s、Worker=165s 沿用前必须验证起算点、包含关系和有效上界。若组合不成立，在首次新 live 前按本地证据调整并说明；不要无限延长，也不要宣称 60s 能保证供应商成功。

记录每层起点/期限、触发来源、native failure code、HTTP status/headers 是否实际观察到、部分正文事实、账务 state、文本/行动准入结果。保留 broad 历史 protocol_error 兼容字段，但根因 timeout、文本不一致、语法行为错误、domain 结果分开。unknown 不能改成供应商未接收或免费。

用 loopback 验证：headers 延迟越过旧 30s 但在新期限内、headers 前 timeout、首 token 后停顿、持续心跳但无完成时 total 到期、终态附近取消与 Worker 回收。可用短期限测试逻辑；至少一次真实固定 runtime 验证新生产期限确实传递并能容纳 >30s 的响应，不用新增真实模型调用诊断期限。其他层到期仍优先服从，记录哪一层生效。保持 fail closed、一次发送和有限清理，不恢复已知不支持的 semantic cancel。

## 3. 有来源的窄复用，不导入整套研究栈

资产根：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase`。

**Concordia：** `15_concordia/repo`，固定 commit `b71d202750e23444ce1bf28d9f114bcd88aa41db`，Apache-2.0。

- `examples/games/haggling/simulation.py`：HagglingPayoff 和有限价格；
- `examples/games/haggling/haggling_logic_test.py`：接受/拒绝、盈利、零收益、亏损测试；
- `examples/games/haggling_multi_item/simulation.py`：parse_item_and_price、MultiItemHagglingPayoff、选项生成；
- `examples/games/haggling_multi_item/haggling_multi_item_logic_test.py`：多物品算术、未知物品、缺参与者、价格选项；
- `examples/games/haggling/sequential_bargain_payoff.py`：真实公开 offer 后才构造响应者观察的参考；
- `examples/games/pub_coordination/pub_coordination_logic_test.py`：公共限制、偏好与协调测试参考。

上述两套议价模块的 27 个未修改上游测试已经实际通过；来源与 GitHub hash 在本轮 review JSON。先核对指定版本/文件即可，不重新做全仓资产审计。提取或窄适配时保留许可证、来源 SHA、上游/本地对应表与修改理由；只对新增适配运行必要测试。

必须改变的语义：

1. 上游 `re.match` 改为有限域精确匹配，尾随文本、未知物品、越界价格不能偷偷解析成合法 offer；
2. seat/role 从冻结合同绑定，不能按行动子串猜买卖方；
3. 缺失、未准入、未知不能转换为拒绝或零收益；拒绝的 0 是完整合法 pair 的结果；
4. 显式验证物品/价格域，不能用未知物品估值/成本默认 0 计算正收益；
5. 使用小整数实验效用，币种标签是 toy coins，绝不混作 TokenKey USD；
6. 独立 oracle 不得调用生产 payoff、GM task_result 或同一函数的包装。

SOTOPIA `18_sotopia/repo@a0aaafb440e570e5e61b7c44a44e5e417c545383` 的 `sotopia/database/persistent_profile.py` 仅作来源/目标/可见性元数据参考。本轮不导入完整 evaluator/Redis 或新的真实人物数据；新合成卡明确标记 Actio 编写、机制源自何处。Raven `02_Raven/repo@3632e6040c7038a60ec418ce39ccae185c72c19f` 的 `evolver/orchestrator/gates/paired.py` 仅保留后续配对设计参考，不复制缺失填 0、零标准误无限 z 或均值提升即晋升。

## 4. 两个有限任务 family：保持两 seat / 两行动

每 episode 重置初始身份/spec/memory；仍为确定性 GM + 真实 Concordia Engine。A 只生成一次实际 proposal，B 只回应实际 A 公开 proposal，不预填答案、不隐式新增规划/总结请求。先冻结任务语义、动作域和完整真值，再调用模型。

### Family S：受限排期与偏好

扩展已有 scheduling，使用三个公开时段、公共开放/关闭条件、各自私有 availability 和小整数偏好效用。A 提议一个时段，B accept/decline。

- hard feasibility：公开开放且在相应 actor 自己的 availability 中；
- B 的 local rule：对公开合法且自己可用的提议接受，否则拒绝；软偏好不偷偷变成未声明的否决条件；
- 软偏好只在 hard 条件满足后的效用维度评分；joint feasibility、可实现效用上界属于 evaluator 全知诊断，不是 actor 已知答案；
- 冻结完整 pair 的成功/拒绝/约束违反、实际世界结果与效用规则。公开禁止或自己不可用的 proposal 即使格式正确，也应可记录为行为失误。

至少 6 张覆盖卡分别覆盖：唯一公共可行交集；多个交集且偏好不同；A 自己偏好但 B 不可用；公共关闭的诱人时段；双方各自可用但无公共交集；有交集但双方局部偏好/联合效用存在取舍。参数不要只做时段换名；若仍存在结构对称，明示同组。

### Family H：有限多物品议价

A 固定为 buyer/proposer，B 为 seller/responder。默认两个公开物品、整数价格 1..5 的有限 catalog；公共交易限制可裁掉合法交易集合，完整语法域/规则在合同中明确。A 私有 item values 和预算，B 私有 item costs。A 输出精确 item/price offer，B accept/reject。

- buyer local hard rule：已知物品/价格，符合公共限制，价格不超过自己预算和估值；
- seller local rule：符合公共条件且价格不低于自己该物品成本时 accept，否则 reject；本版本将零利润边界明确为 accept；
- 完整合法且接受的 pair：buyer utility=value-price，seller utility=price-cost；合法拒绝则双方 0；
- 不完整/语法非法/证据不可信的 pair，其收益是 null，并保留具体原因；不要把未知当拒绝；
- `joint_feasible` 是允许域中存在双方非负收益的 offer；另报严格正总剩余是否可能，别把零利润边界与正收益混为一类；
- A 不知道 B 成本，不能因未选择全知最优价格就判“违反自己约束”。全知 regret/Pareto/总剩余只作单列描述，不能称为可知最优决策的错误率。

6 张覆盖卡覆盖：单物品可行而另一物品亏损；双方可行且剩余不同；buyer 自己偏好的物品 seller 成本较高；零利润接受边界；双方没有可行交易；公共交易限制或 buyer 预算改变可行 offer 集。为每张卡验证小有限域真值。

行动域可以包含格式合法但违反任务规则的选择，以测量真实行为；不要根据对方私有状态缩减 actor 选项来透露答案。未知物品、域外值、尾随解释属于语法/域错误，不进入领域状态。已知域中的任务约束违反应记录为 task outcome：冻结 GM 是拒绝该世界变化还是产生违反约束的模拟结果；不能静默纠正成好行动或将其统统升级为供应商 unknown。

### 共同的信息边界

actor 只接收公共规则/行动域、自己的状态/目标、实际公开历史。双方完整任务、对方私有值、oracle、正确答案、feasibility/group labels 及其派生 hash 都留在 Control Plane/evaluator。

ActionSpec、system/user messages、工具描述、提示、headers、ID、option order 均纳入实际 prepared/full-wire 检查：固定某 actor 的自身和公共信息，改变对方隐藏字段，其 wire 应不变（预先固定独立随机审计 ID）。B 检查还要固定实际 A 公开行动。有限选项及编号只能来自允许视图，不靠全知排序/筛选暗示正确答案；外部任务和源码绑定继续保留。

## 5. 独立评估准入：先证明指标能识别差异

生产 runner 只产生事实；只读 evaluator 由冻结 task、可信原始/native 行动和完整计划重算。不得读取领域 success 作为正确率，不调用 LLM judge，不共享生产 payoff 核心计算函数。

对每张卡穷举小行动域及 B 响应，用独立算术/集合实现交叉检查。另写清楚可手算的真值表，覆盖零边界、无交集、公共禁止、软偏好取舍、拒绝、部分 pair、非法值。声明 oracle 的独立范围：代码路径/公式独立复核，仍非独立人类研究评判。

指标至少分开：

- 传输/文本证据完整性、语法/行动域合法性、各 actor 本地 hard rule；
- 可评估完整 pair 的共同结果、效用、联合可行性及全知上界；
- 完整计划覆盖、attempt/sent/response/usage/unknown/not_run；
- route/时延/账务元数据，时延仅作有删失标记的描述。

**避免按成功准入选择样本。** 文本证据可信但内容格式错误，应保留为 format=false 和行为错误；即使不能产生 domain receipt，也不能从格式分母删除。文本不可信才属于不可评估/缺失。保持“原始文本可核验”“格式可解析”“domain 可执行”“语义目标满足”四个条件的区别。为每种条件/分母建立测试，报告覆盖率；不得只在 admitted 的合法回答中宣称格式正确率 100%。

离线至少使用固定的：第一选项策略、总是接受策略、总是拒绝策略，以及遵守自身信息规则的确定性策略。它们只生成本地 fixture action，不作为真实模型结果或真人标签。每 family 的准入要求：

1. 至少一个已知 hard-rule 违反能被正确识别；
2. 至少一组格式合法且满足 hard rule 的行动能体现软效用差异；
3. 正确接受与正确拒绝均有真值案例；不可行任务不被统一解释为 actor 无能；
4. 未知/缺失/非法不冒充 0 收益或有效样本；
5. 生产状态/结果与独立 oracle 在约定范围一致，全部有限真值验收通过。

这是预先要求的 metric sensitivity，不要求 GPT 或 Claude 在 live 中一定得不同分或失败。若两条 route 都满分，照实报告；不得看到结果后加难度、挑卡或扩样直到有差异。本轮不合成跨 family 总排名分，不做显著性检验、推广性 CI 或 cost-normalized ranking。

## 6. 本机准入与冻结新计划

先完成新合同、修复、任务包、oracle、可见性和 offline reader。再用 loopback fixture、真实 DSH/Concordia 跑 **12 张卡 × 2 条路由 =24 episodes 的本地矩阵**，B 使用真实 A 输出；加针对新增规则/失败分母的必要负例。fixture 支持两条 route label 不等于供应商已验证。

测试选择与增量相符：统计分母、有限语法/角色/收益、negative controls、full-wire 私有反事实、raw/adapter/native 绑定、超时/唯一 claim/unknown、历史分派、公开 CLI、干净安装与 pip check。复用现有 suite，不为文档另写镜像测试；通过后只有新变动或未解决风险才重复大规模检查。构建/本地 runtime/正式 live 串行，避免并发资源争用影响期限。

**新 live 默认计划：2 families × 每 family 6 cards × 2 routes × 1 repeat =24 episodes，最多 48 次 solver 发送。** route 仍为 `gpt-5.6`、`claude-sonnet-4-6`，同 episode 两 seat 同 route，无新模型目录扫描、跨模型对手组合或额外诊断前戏。必要时仅在首次调用前依据未通过的离线条件减少范围并说明；不为某条 route 的成绩调整。

这一数量限制实验设计，不限制金额。每张卡两个 route 构成一个配对 block，12 blocks；固定调度种子并交错路由先后，轮换 family，不能先跑完一个模型才跑另一个。每卡只选一次冻结的 option order，跨卡平衡；不声称本轮识别选项位置因果效应。route label 不等于已验证的上游权重身份。

完整计划在运行前枚举所有 episodes/seats，保存 family/source_template/structural_group/case/presentation/route/block/role 等层次。两个 family 和 12 张自编参数卡不等于独立研究样本，设 `independent_research_units=0`；不创建已在测试中见过的伪 holdout。

机器可读 preregistration 至少冻结：

- 目标、不回答的问题、engineering 状态、来源/许可与任务真值版本；
- task/card/metric/oracle/source hash、初始身份/spec/memory、可见视图构造及外部绑定；
- 路由参数、单回答输出上限、所有期限/起点、一次发送资格；
- 全部单位及顺序/seed/配对、task error 与 infra error 停止规则、not_run 原因；
- 每项指标单位/分母/缺失/不适用/非法/删失定义、描述性报告；
- 76 次历史生成尝试及 1 次目录 GET 的排除/累计规则；用户无金额上限授权与有限阶段范围。

**首次新 live 前，将通过本机验收的实现与 preregistration commit 并普通 push 到任务分支和 main，核对远端 SHA。** 执行器检查 clean checkout、阶段版本、完整计划和已发布冻结 hash 后才读取 key、登记 intent、发送；保留发布检查→intent→send 的证据及其时间证明边界。新阶段 plan/preflight/verify 保持只读零副作用，不读取 key/env、不访问网络、不启动 Worker、不写文件；需要网络的发布状态核验只在专用执行前置层。

如果代码/任务/规则必须变动，先明确 superseding 版本与原因，保留所有旧尝试；不拼接不同合同凑 N。本轮正式冻结后若出现基础设施停止，完成故障只读复核并交付即可，不自动启动第二个 live 批次。

## 7. 执行、停止和费用事实

按完整计划单并发执行。首个配对 block 后只检查基础设施和证据/清理，分数不能决定继续或停；合同未变时该 block 属于正式分母。

- 每 seat 只生成一次；无 retry、自动修格式、额外 judge 或总结请求。
- A 语法无效/合同规定不可继续时，B 标为 task_predecessor_invalid 的 not_run；保留 A 行为失败，继续下一既定 episode。不要为了完成 B 改写 A。
- B 合法拒绝、低效用、hard-rule 违反是任务结果，按冻结域规则记录，不能以“表现不好”停批次。
- 任何基础设施 unknown、超时、原始/原生文本矛盾、配置身份或证据链不一致，立即停止整个有限 pilot，保留当前前缀及后续 not_run；不能自动换 route/模型、重试或补样。
- provider 429/5xx 等也按停止规则处理，记真实观察；没有 status 就为未知，不能猜 HTTP 错误。
- 停止发送后清理受管 Worker/服务，关闭端口，再做只读诊断；不因失败自动增加真实请求。

TokenKey 凭据从忽略的 `.local/credentials/token_key.txt` 内存读取；仅在副本缺失时按用户已指定来源 `D:\调研\CausalEngine\api_key\token_key.txt` 安全复制，保持 ignored/untracked。只注入专用环境/内存，目标仅 `https://api.tokenkey.dev`，保留跨 origin/重定向保护。不打印 key、片段、长度、hash；不得放入配置/trace/Git/Prompt。

费用继续区分 raw usage/cost、provider claim、quote、estimated_cost、billed_cost；未知币种/单位不换算 USD，unknown 不填 0。无可信新账单就继承 UNVERIFIED。无需重复无结果的全站/目录/路由调查；若已有明确只读导出，可追加脱敏 sidecar。不给真实账户充值、改限额、登录管理界面或向其他 origin 发送 key。

实际累计分开记历史 76、新 C2C0、loopback 和被拒绝/未发送的 attempt；计划 48 不是实际发送数。有 usage 不等于文本准入、文本准入也不等于实际账单已对账。

## 8. 只读核验、历史保护与清理证据

新导出 verifier 可从冻结计划、证据、源码版本与 oracle 独立重算，在禁止网络、key/env、子进程、Worker/evaluator 运行和写入条件下通过；它是确定性离线评估，不允许启动供应商或完整上游模拟。证明删除未运行行、重复/换 route/混版本/丢 partial pair 会被拒绝，所有 numerator/denominator 可从导出复核。

固定旧 reader：C0=`1e85d8c2`、C1=`af0a88cf`、C2A.1=`b086cba`、C2B0=`f65045a`、C2B1=`1e00535`、C2B2=`e89d8b370c6cc53de21f651b49e7b2626eb1a559`，使用已有受信完整 SHA 注册表解析短名。不要由 artifact 自选执行源码。优先检查历史 hash/分派增量，运行受影响的 reader 回归；不要每修一处就重跑所有历史 Worker 或模型。

C2B2 的旧 reader 必须仍能重现旧报告；新纠正 sidecar 只追加不覆盖。所有历史原件及失败原 hash 保留。binary_source_mapping=unproven、full_controller_recovery=unsupported 不顺带声称解决。

运行用独立短路径、具名 Job 与受管服务。清理按实际所属 Job，不能靠复用 PID 或杀所有 Python/Node。保存本轮全部 local/live 尝试、阶段源码/argv、失败、归档清单、服务 join、Job inactive/reaped、端口和活动 sending 状态。unknown 可继续为 unknown，但不能残留活动 Worker 或挂起 sending。不重复扫描无关 venv/node_modules，不提交大原始日志或真实账户账单。

## 9. 交付、GitHub 和停止点

在 `docs/validation/phase1c2c0/` 交付：

- CONTRACT/RESULTS/GATES/CLI；
- 资产提取/许可与二开映射，12 张合成任务卡、独立真值及区分度结果；
- 不可变 preregistration、完整计划、逐 seat/episode/pair 报告和新分母；
- C2B2 分层纠正 sidecar，新超时生效/失败分类证据；
- 本机矩阵、真实 pilot 全部尝试及 not_run、usage/cost/unknown；
- evidence_manifest、来源与安装一致性、必要历史 reader 回归、清理；
- 下一阶段建议与明确限制。README 更新当前入口，CLI 必须是实际运行过的公开命令。

Gate 分项：`task_suite_admission`、`measurement_admission`、`transport_readiness`、`pilot_execution`、`billing_reconciliation`、`upstream_identity`、`human_calibration`、`judge`、`research_validity`、`evolution_promotion`。根据证据分别 PASS/CONDITIONAL/BLOCKED/UNVERIFIED/STOPPED，不把某一阶段通过扩张成研究或晋升通过。遇到停止也交付完整证据，不重试到 GO。

本地检查通过后，精确凭据/敏感内容检查、git diff --check、只 stage 本轮安全文件，commit → 普通 push 任务分支 → 安全合入 main → 普通 push origin/main → 核对远端 main/任务分支 SHA 与本地一致及工作树状态。无分叉时优先快进；有并发更新先读取、整合、检查，不覆盖他人修改、不 force push。推送失败则明确真实阻塞和本地提交，不能称已发布。

最终中文报告：实现及复用资产、两项前置修正、离线准入/测试、冻结提交、planned/attempted/sent/not_run/usage/unknown/费用、实测覆盖与相关性限制、清理、main 提交与结果/manifest/CLI 链接。**停止于 C2C0**。后续 C2C1 仅建议单 seat 候选/基线/谱系的离线准入演练；本轮不自动进入候选生成、真人校准、judge、研究或演化晋升。
