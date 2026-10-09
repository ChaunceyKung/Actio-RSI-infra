# Codex 执行 Prompt：Phase 1C2C2 有限真实候选配对与跨批次评估谱系

请实施 **Phase 1C2C2**：保留C2C1的B0/C1和12张开发卡，扩展同一候选的独立评估批次，正确区分行为失败与技术证据缺失，连接已有TokenKey链路，完成一次先冻结后执行的有限真实baseline/candidate配对。验证后提交、推送任务分支及 **main** 并核对远端SHA。请交付可运行实现、完整证据和实际执行/停止结果，不只写准备文档。

项目：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
仓库：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
建议分支：`phase1c2c2-live-candidate-pairing`。
审阅基线：`6578c742bd5ab3672c97ee002a6559150c70b1fd`，C2C1冻结：`dc15292bc6827593e8321e31acbcf599dd25d772`。

从包含本Prompt的最新origin/main开始，记录实际HEAD、祖先关系、工作树及远端。读取AGENTS.md，`docs/reviews/phase1c2c1_review_and_c2c2_plan.md` 和 `docs/reviews/phase1c2c1_review_evidence.json`，C2C1合同/结果/Gate/CLI/manifest/preregistration/proposals/policy/lineage/delivery，以及已有C2B1–C2C0真实执行合同和C2C0任务/oracle。除另行标明外，相对路径均相对于项目根目录。

## 0. 已授权范围和完成定义

用户已要求项目必要API调用“不设置预算上限，以推进项目为准”，指定TokenKey `https://api.tokenkey.dev/v1` 和本地凭据；本轮有限solver工程试验沿用授权，**不用再次询问同一真实调用或费用批准**。金额策略为明确的C2C2 uncapped，而非0、巨大整数或含糊null。继续保留有限计划、单请求长度/期限、一次性资格、账务和清理。

本轮是单一人工候选的**开发集探索性工程试验**。只允许A的已有scaffold与baseline对照，不创建C2、不调用LLM proposer、不做搜索/训练/live judge/真人标注/部署/生产激活/自动演化晋升。即使候选正差值，也不能宣称能力已准入。

完成条件：

1. 同一个不可变B0/C1能关联C2C1旧local评估和C2C2新live评估，原决策不覆盖；
2. 完整观察的格式/行为错误不误归为infrastructure_failure；每项指标有完整分母；
3. 新版live/rehearsal分派、本机双通道/干预/账务验收通过；
4. 实现与预注册计划先推送任务分支/main，随后运行一次有限live，或按预注册停止；
5. 结果、四态决策、谱系、manifest、CLI和清理完整交付到main。

保留C2C1主矩阵24 episodes/48本机发送/12pairs/delta=0和6份提案原样；C2C0、C2B2的停止、unknown/not_run和claim均不重置、不补跑。历史真实生成尝试91、目录GET1另计。本轮不得为“补齐之前实验”调用模型。

## 1. 固定栈、候选与新版本

Windows x64、Python3.12、隔离短路径、官方DSH SDK/runtime `0.1.5rc1`，exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`；Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。运行仍经Python Control Plane→官方Python SDK→DSH TS loop/pi-ai→真实Concordia Sequential，SQLite持领域事实。

复用C2C1的candidate/scaffold/tasks/双通道/绑定/lineage和C2B1–C2C0的凭据、transport、预算账本、controller、freeze、export、reader。检查 `candidate_contract/campaign/measurement/store/tasks.py`、`candidate_schema.sql`、`channel_audit.py`、`candidate.py`、`pilot.py`、`transport*`、`gateway*`、`budget.py`、`store/database/scenarios/verify.py` 和相关脚本/tests。

冻结既有身份：

- B0 proposal：`84e9ab99465ada9c47cc17334c305a5f493524f042a218d4be4732c054462fe5`；
- C1 proposal：`e381eb3dd58494dde035b7c301331bdc3f5cde8af18c644bf6e7301087a130b2`；
- B0 scaffold：`9b686045d24438d2544378a515d71915dc92b3eda2a59804607f9d88aa69fbb7`；
- C1 scaffold：`1458fb1db9310b9c54a03c72f32f09045293f789a0f93e3ef9e4cad2fad15c95`。

从已发布proposal重新计算验证以上hash，不手工复制新对象改名。C1仍为那三个通用检查词条，不增加隐藏信息、规则、答案或清单内容。保留base identity/spec、B、初始空memory、12卡及生产world/oracle语义。

为C2C2新增明确config/task-input/campaign/evaluation/decision等版本，具体编号按现有注册表确定。旧v8继续local-only，不把其endpoint/授权/允许字段全局放宽。旧proposal静态校验policy与新evaluation policy分开，不因评估policy更新改变proposal hash。

## 2. C2R1：以evaluation为作用域追加评估历史

当前 `campaign_binding`、`decision` 以candidate为单一主键，候选状态decided后不能再bind。这个旧合同不修改解释。新增以 `evaluation_id/campaign_id + candidate_id` 关联的evaluation、事件、binding、decision事实；每次评估有自己的frozen policy/source/dataset/plan与once-only claim。

候选内容身份、parent edge、静态验证结果与每批执行状态分开。不要把旧decided重置validated、删除decision、给相同清单新名字或复制报告假装新实验。新的evaluation可以引用旧candidate；旧evaluating不因新evaluation而自动恢复/重领。明确baseline为参照身份、C1为相对baseline的候选，不能将“对比两臂”的同一获益判定写成两者均获能力提升。

采用最小显式schema扩展和复制迁移（例如v3→新schema）：保留原库/备份/hash和全部旧事件/decision，新事实仍由同一Store owner持有。可将已核验C2C1源库复制为C2C2候选库后迁移；不要把JSON投影提升为第二权威状态。实现只读导出能同时列出同一候选的旧local与新live评估，并绑定旧来源hash/reader。

新evaluation policy版本由Control Plane选择并冻结；candidate只引用静态artifact，不能改dataset、metrics、policy、权限、预算、日志或driver。完整delivery绑定proposal→parent→evaluation plan→每arm run/ledger/native/domain/evidence→measurements→decision；跨批次不能误接C2C1的零差值。

必要验证：重复登记幂等、同evaluation不能重复claim、事务失败不产生半条evaluation/decision、两评估并存且旧decision不变、重开DB等值、坏库拒绝、迁移不改旧库、未知parent不产生有效edge。仅证明登记/迁移持久性，不宣称完整controller recovery。

## 3. C2R2：技术完成、行为错误和指标缺失分别定义

现有 `candidate_measurement` 把joint defined当episode/arm pair完整，`complete=false`直接交给infrastructure_failure。新合同不能照搬：真实模型给出可信但不在ActionSpec中的非空文本时，行为错误已被完整观察，不能作为unknown或基础设施故障。

冻结一张状态/计数表，至少区分：

- planned/attempted/sent/response/usage/unknown/not_run；
- technical evidence complete：响应/原始通道/native/账务、必要领域拒绝证据是否可核验；
- execution resolved：episode已按照任务终止或跳过规则结束，包括A格式无效导致B合法跳过；
- text_verified、format_valid、domain_executable、local_hard_rule、joint/utility等指标，各自适用性；
- arm_pair_execution_resolved 与每个metric的paired_defined/missing/not_applicable，不能只有一个通用pair complete。

可信格式错误记录format=false；A非法则B `not_run_reason=task_predecessor_invalid`，不修答案、不重发A、不伪造B。该episode可为execution resolved，joint/utility依原规则为null，格式/违规指标仍有观察值。B格式错误同理。合法但违反公开/自身hard rule是任务失败，合法拒绝不是失败。对方隐藏状态不作为A应知答案，全知regret只作诊断。

每指标规定 `assigned=eligible+not_applicable`、`eligible=defined+missing`，布尔defined=true+false；完整计划和按family/arm/feasibility分层都能核回。delta只在该指标两臂可比较时定义，否则null并带原因；不因一方格式错误删除整个pair，不把null utility填0。把失败率/缺失覆盖与只在可比较pair上得到的差值一起报告，禁止据选择后的样本单独声称获益。

协议不支持、raw/adapter/native矛盾、无法核验终态、timeout、未知发送等仍与行为错误分开，按预注册停止。对空content或length截断继续按既有双通道支持边界处理，记录确切类别和已知usage，不为使pilot继续临时放宽。任何边界变化必须在首次live前有版本、说明和本地证据。

新增必要本机案例：可信非空非法A、非法B、合法低效用/拒绝/自身约束违反、只有一个arm观察到错误、技术unknown与后续not_run。验证“零技术错误但行为很差”的campaign不会被误称provider infrastructure failure。上述用合成fixture，不作为真实候选表现。

## 4. C2R3：单独的live链路及输入因果边界

增加新live和rehearsal mode、公开plan/preflight/execute/verify入口；仅execute调用凭据resolver和外部网络。旧candidate_loopback维持原限制。逐层检查cfg→task→host→transport→fetch guard→Ledger→raw/native audit→measurement→delivery分派，新报告不沿用external_provider_requests=0或历史固定总数常量。

调用现成TokenKey Chat Completions和官方pi-ai，不用Python OpenAI SDK替代solver、不自建gateway、不升级runtime/换协议。双通道沿用C2C1 profile，只有content进入公开行动、世界、B和memory；reasoning只核验结构/一致性，不回灌solver/proposer、不当质量分、不复制正文进新公开报告。

保持A清单为唯一直接干预。参数、Persona、角色、自身私有状态、任务、option order、model、输出上限和期限跨arm一致。原始run/request/ledger/attempt UUID独立，在外部绑定；只归一化已证明独立且不进入wire的message UUID，不隐藏其他不同。

A在两arm可能输出不同：每个B只看本arm实际公开A行动。正向重算每份B观察/prepared/full-wire与其真实A历史一致；去除允许变化的公开历史后，B自己的信息、指令、权限和scaffold仍一致。A相同则B wire应相同；A不同时不能要求B全文相同，也不能放弃检查B的非历史字段。

本机至少覆盖两种合法A输出→不同B历史/可能不同响应的路径，再覆盖相同A的原不变性，以及改变对方hidden信息时自身允许输入不变。完整task/oracle/feasibility/candidate/arm/pair labels及其隐藏派生hash仍不进入actor提示。不要把fixture预选答案、收益或arm身份放进wire。

## 5. 固定有限live计划

使用原12张卡（两个family，每个6张），原B0/C1，单一TokenKey requested model `gpt-5.6`。同episode两actor使用相同route。选择此route沿用当前candidate serializer及已观察双通道路径，**不是模型排名**；本轮不新增Claude对照、不做全模型目录扫描、key smoke或直接诊断请求。

默认冻结 **12 cards × 2 arms × 1 route × 1 repeat =24 episodes，最多48次真实seat发送**。这限定工程设计而非金额预算。固定seed安排card/family和arm交错顺序，尽量每family有相同baseline-first/candidate-first数量。完整有序计划预先枚举所有seat/episode/pair与版本；不先跑完baseline再跑candidate。

模型参数保持已支持的max_tokens=512、temperature/seed未指定、reasoning不主动请求，所有实际wire参数事先冻结。调度seed不是供应商sampling seed；每卡单次两臂不能消除模型随机性、时间/路由漂移。本轮不以统计显著性为目标，不在结果后重复到有差异。

12张卡都已经用于开发；明确`split=development_exploratory`、`independent_research_units=0`、human_labels=0，不称sealed/held-out/generalization。保留source_template、structural_group、family、card、presentation、repeat、route、arm、evaluation层次。既有local结果和91次真实历史不进入新主要分母。

本轮问题限定为：真实路由是否支持已冻结的输入/双通道/动作/评估链；相同开发任务上的B0/C1实际观察和约束遵守有何差异；缺失与一次性执行是否完整保留。无论差值正、负或0，完整报告；不添加任务/改C1/换模型以寻找好结果。

## 6. 本机验收、发布冻结、真实执行

先完成版本分派、跨评估谱系、行为/技术语义和输入绑定。本机rehearsal复用真实DSH/Concordia、literal loopback/fake credential，覆盖完整计划以及新增分支；已通过的旧慢期限测试不无故重复。若复用原24episode矩阵，必须来自新模式且绑定新evaluation，不能复制旧export改ID。新增差异/错误案例另外标注，不拼进正式live分母。

保持C2C0/C2C1有限期限：ready30、RPC5、headers60、idle60、total90、result115、drain5、close5、Worker165秒及原起点；单次请求，无SDK或transport隐式重试。新通道活动不能延长total。未修改期限传递则沿用原31秒延迟证据，新增模式接线有实际本地验收。

本机plan/preflight/verify保持零副作用，不读key/env、网络、启动Worker或写文件。线上publish检查属于专用execute前置，不伪装成离线preflight。干净安装/来源一致、pip check、公开CLI、旧reader分派完成后，生成完整preregistration，至少冻结：

- B0/C1 proposal/scaffold与静态policy；新evaluation policy/identity和旧谱系来源；
- tasks/oracle/metric/source/runtime/hash、初始spec/memory、允许输入和唯一A干预；
- 全部有序单位/配对/arm顺序seed、route/wire参数、资源期限与端点；
- 指标适用性、behavior/infra/unknown分类、跳过/停止/no-retry规则；
- 仅描述性报告、开发集限制、无晋升；已有91次与本机尝试的排除/累计；
- 本阶段explicit uncapped和用户授权依据、独立claim namespace。

**第一次新live之前，commit并普通push实现及preregistration到任务分支和main，核对两端SHA、clean checkout和已提交计划。** 若不能证实已发布，live不开始；先交付准备成果和真实网络阻塞。不是另向用户索取费用许可。凭据只在发布/本机前置通过后的专用execute内读取。

真实计划执行单并发，A/B各一次。首个完整arm block后只检查证据和清理，不依据得分决定继续；合同不变则属于正式分母。可信行为错误按照第3节继续下个预定episode；首个技术unknown、timeout、协议/文本/route identity问题停止整个campaign，后缀保留not_run，不换模型/route、不修答案、补样或第二次live批次。

若controller中途异常，先封存已发生attempt、原始运行和计划后缀，不能靠finally重算失败导致交付全丢。对无法关联/核验的部分报告明确缺口和infrastructure_failure，不复制另一arm、不声称full recovery。调查默认只读；本轮不为诊断自动增加真实请求。可能失败时同样完成结果/manifest/清理并发布。

## 7. 预先冻结的决策与能力边界

新evaluation policy保留四态，但证据种类必须明确为live_development_exploratory，与local_fixture/policy_fixture分开。结构化decision至少含evaluation_id、candidate、baseline、policy/dataset/report/evidence hashes、技术状态、行为约束结果、分母/缺失、reason、scope和eligible_for_activation=false。

预先冻结优先级：静态不合法reject且不发送；技术证据不完整/协议停止为infrastructure_failure并保留已观察行为事实；技术上完整且C1已准入文本存在任何格式或自身hard-rule违反，按本轮“零已观察违规”的开发约束gate标reject；其余技术完整但只有这12张开发卡单次观察，无论差值正负，能力admission保持insufficient_evidence。合法拒绝、全知最优未达到、联合不可行不属于该hard违规。不同case证据不能相互补写。

此处reject只说明候选未满足本轮开发约束，不是对总体能力的统计结论。可将engineering execution和measurement标PASS，同时candidate decision为reject；反之不能将优秀行为抵消技术证据缺失。baseline按同口径报告行为约束，但不因参照结果得到“晋升”决定。

保留原C2C1 B0/C1的insufficient_evidence历史；新增decision属于新evaluation。不开active pointer、不改Store.agent、不执行CAS激活/回滚。C2C2没有capability pass路径；policy fixture对pass的历史测试不是真实证据，不可挪用。

逐family/arm报告format、本地hard、B响应、joint和toy utility；各metric对应的完整/缺失配对与delta逐项列出，不输出综合score、排名、显著性、推广CI、无限z或成本归一化收益。reasoning token/content不代表思维真实性，完整HTTP响应也不证明上游权重身份。

## 8. 凭据、费用、历史与复用

凭据为ignored/untracked `.local/credentials/token_key.txt`，仅副本缺失时从已授权 `D:\调研\CausalEngine\api_key\token_key.txt` 安全复制，内存注入专用引用。只能发送到 `https://api.tokenkey.dev` 的指定Chat Completions路径；保留重定向/cross-origin限制。不打印key、片段、长度或hash，不放入Prompt/config/trace/Git。

显式uncapped只解除金额上限，不解除单请求长度/期限、阶段结束、账本与一次发送。计数分历史91、新live实际attempted/sent/response/usage/unknown、loopback、未发送资格；若执行满48，累计139，仅在实际发送证据支持时填139，不能预填。

raw cost原Decimal与币种未知标记保留；无可信报价不估USD，无账单不说已对账，unknown不补0。费用/upstream identity待证限制相关结论，不阻断本轮工程。无需重复网站/全模型/账单猜测端点；不充值、改账户限制或登录管理后台。

不新增框架。DSH固定源 `5badb15009ae1756c3afe0ae0cef1faafc290ccc` 的pi-ai stream和Raven固定源 `3632e6040c7038a60ec418ce39ccae185c72c19f` 的paired/archive继续作为已有窄复用依据；本地分别在 `codebase/01_deepseek-harness/repo`、`codebase/02_Raven/repo`（相对agentic_evolution_infrastructure根）。沿用来源/许可/NOTICE，禁止missing→0、mean-only promoted、JSON best-effort权威持久化或完整root fork。

历史C2C1由固定reader `6578c742bd5ab3672c97ee002a6559150c70b1fd`，C2C0由 `e2e6691ef9bae5f61bccaaa97528e0478bd9a666`，其余按既有受信完整SHA注册表。旧v8仍能拒绝provider origin、旧报告精确重现；原产物不修改/重新封存，新增解释写sidecar。artifact不得指定执行任意源码/插件。

## 9. 必要验收、交付与main

测试覆盖新增语义与真实接线：跨campaign同候选不可变历史、migration/事务/幂等、行为错误≠技术缺失、按metric配对、动态A→B公开历史、full-wire隐藏不变性、双通道与新模式、一次资格/停止/unknown、offline reader与实际public CLI。构建/本机runtime/live串行，避免争用改变期限；通过后只在新变化或失败时重跑必要范围，不追求重复测试数量。

运行使用独立短路径和具名Job，清理仅当前拥有的Worker/服务；不按泛化进程名或复用PID杀其他工作。记录全部失败与开发尝试、source/argv、Job inactive/reaped、service join、相关端口、活动authorized/reserved/sending。unknown可以保留，活动Worker不能残留。源数据库/归档hash与实际reader一致，公共产物保护凭据、账户隐私和历史reasoning正文。

交付 `docs/validation/phase1c2c2/`：CONTRACT/RESULTS/GATES/CLI、冻结preregistration/完整plan、新evaluation/binding/policy/decision、旧新候选谱系关联、输入干预检查、完整逐seat/episode/metric-pair报告、费用状态、停止/失败/清理、源码/安装与必要历史reader证据、evidence_manifest。README更新当前入口，CLI须实际跑过；完整delivery在无key/env/network/process/runtime/write条件下复核。

Gate分开报告：candidate_static_contract、evaluation_lineage、intervention_integrity、measurement_integrity、live_execution、provider_protocol_observation、candidate_development_constraints、capability_admission、production_activation、billing/upstream_identity。不因为某项PASS覆盖其他缺口。binary_source_mapping=unproven、full_controller_recovery=unsupported不顺带声称解决。

最终精确凭据/敏感内容扫描、git diff --check、仅stage本轮安全文件，commit→普通push任务分支→安全合入main→普通push origin/main→核对远端SHA与本地一致、工作树状态。无分叉快进，有并发先整合验证，不force push；推送失败保留本地提交并说明精确阻塞，不能称已发布。

最终中文报告：三个前置边界如何处理、冻结提交、实际planned/attempted/sent/usage/admitted/not_run/unknown/累计真实次数、每metric配对覆盖与候选结论、旧评估历史保持情况、费用/身份限制、清理、main SHA及结果/manifest/CLI链接。**停止于C2C2**；下一阶段再根据观测决定新任务或候选修改，不自动进入研究、激活或自主演化。
