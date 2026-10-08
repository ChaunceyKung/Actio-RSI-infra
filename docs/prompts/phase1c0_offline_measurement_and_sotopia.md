# Codex 执行 Prompt：Phase 1C0 离线测量准入与 SOTOPIA 最小复用

将本文件交给新的 Codex session 执行。授权范围：先收敛小型合同，再实施本文限定的离线评估工程、测试和文档；完成后 **提交、推送 GitHub 并核对远端 SHA**。不要仅交计划，也不要自行进入付费模型、统计晋升或演化外环。

你是 Actio-RSI Evaluation Infrastructure Engineer。Phase 1B.1 已有持久双场景、场景终态、目标化恢复、旧库副本迁移和离线证据包。现在以真实证据包为输入，建立严谨的测量准入、确定性任务指标、严格结果 envelope 和最小 SOTOPIA parser/schema 复用。

## 0. 仓库、基线与发布授权

仓库：

`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`

GitHub：`https://github.com/ChaunceyKung/Actio-RSI-infra`

产品基线：`bc0c034f997a59161ff79f865ad41098433884b5`，已推送 `phase1b1-reliability-and-evidence-export`。

交接分支：`docs/phase1b1-review-phase1c0-plan`，包含本 Prompt、审阅报告和证据摘要。优先从该分支已推送的最新 HEAD 创建或续用 `phase1c0-offline-measurement`。不要从仍停留旧规划的默认 main 开始，遗漏 Phase 1A/1B/1B.1。

开始时检查 AGENTS.md、branch/HEAD/remote/status、已有修改与 worktree。保留正确后继工作，不 reset/clean 用户文件；需要隔离时显式指定包含产品与交接基线的 ref。参考仓库只读，依赖安装与临时实验使用隔离环境。

每轮完成并验证后推送 GitHub是用户持续授权：提交本轮文件 → 普通 push 当前任务分支到 origin → 用远端 ref 核对本地 HEAD。无需重复询问，不自动 merge main/deploy，不 force push；发生鉴权/网络/并发更新问题，保留成果并说明精确阻塞，不把本地提交称为已推送。

## 1. 读取与继承

先读：

- `docs/reviews/phase1b1_review_and_phase1c0_plan.md`、`phase1b1_review_evidence.json`。
- README、`docs/validation/phase1b1/01_contract.md`、`02_results.md`、`03_gate.md`、`04_bundle_format.md`、manifest 与五个 samples。
- `src/actio/verify.py`、`terminal.py`、`evidence.py`、`scenarios.py`、`runtime.py`、`facts.py`，以及相应 tests。
- 原规划 `08_evolution_architecture.md`、`10_interface_specification.md`、`12_implementation_backlog.md`、SOTOPIA 的 E022/复用定位；按需要补读 owner、memory 和 attribution。
- `probes/phase1a/eval_probe.py`，只理解旧失败分类和 scores 类型漏洞，不直接搬为产品。

已知交付：38 组聚合验收 PASS，22 个产品文件与 15 个相关测试/fixture 文件有匹配 hash，8 份当前 raw archive；干净安装和 CLI smoke 已验证，66 个 Job 清理记录 active=0。五个样例已在本次审阅重新离线核验。不要把工程用例数量当研究样本量。

继续复用官方 DSH SDK/TS loop/native journal、真实 Concordia Engine、SQLite 领域存储及已实现的证据包。保留 Windows x64/Python 3.12/DSH `0.1.5rc1`/固定 Concordia/短根/单活动 run/只读工具/静态最终 guard。原 wheel/exe/source pins 沿用锁文件与 artifact 登记，不默认升级。

**Live 预算为 0。** 不读取偶然存在的 key、不发 provider 请求。SOTOPIA 或 litellm 导入也不能隐式联网拉 metadata/遥测；必要依赖下载属于隔离准备，运行评估阶段须可证明无网络/无模型调用。缺 live 预算不阻断本轮本地工作。

本轮不做：新 agent loop、HTTP 服务、UI、第二存储权威、完整评估平台、Redis 部署、完整 SOTOPIA simulator、Raven candidate 搜索/准入、模型训练、native resume/fork、写效果工具、跨平台扩张、真实 pilot 或模型能力提升宣称。

## 2. 执行顺序与最小产物

先在 `docs/validation/phase1c0/` 写短计划/合同，随后继续实现：

1. C0.0：修复已证实的输入绑定缺口 C0R1，给出 verifier 版本/历史报告处理规则。
2. C0.1：最小不可变 EvalSpec、Evidence admission、EvaluationInput；角色映射和 judge 可见视图。
3. C0.2：源码级 SOTOPIA seam 选择、固定 parser/schema 的真实离线执行、严格 Actio envelope；上游 evaluator 兼容性刻画。
4. C0.3：真实证据的确定性指标；独立合成受控 judge response 的结构验证路径。
5. C0.4：小型冻结 fixture campaign、全量结果/失败登记与去重、验证文档及 GitHub 发布。

依赖通过后在同 session 继续，不停在“可以进一步实现”。只有关键 Gate 不成立才交付具体阻塞，不扩展未授权能力来绕过。

建议使用少量 Python 模块和不可变 JSON/JSONL 产物，评估侧结果独立于原 runtime DB；无必要就不新增核心数据库迁移。所有读取原 bundle 的操作保持只读，不刷新旧 spec/pins，不往旧 native journal 或 memory 回写。

## 3. C0.0：补齐 frozen input → dispatch → native task

审阅已复现：对提交的 social 样例，仅更改 run.input 的 `observations.A` 或 `action_spec.call_to_action`，重算 run input hash、终态 manifest hash 和文件清单 hash，保留 dispatch/native/world 不变；省略可选旧 verification.json 后，当前 verifier 仍输出 consistent/complete/success。

这是包内可见矛盾，应在准入前拒绝，不属于“无签名所以无法证明作者”的外部信任问题。实现以下最小合同：

- 对当前固定场景识别 entity label→真实 agent、调度 step 和冻结 observation policy。
- 检查必要 observations、完整 ActionSpec（call_to_action、output_type、options、tag 等实际合同）、memory 等输入确实来自 frozen manifest，并与 dispatch intent/native prompt 一致。
- 必需字段不能通过删除而跳过验证，不能因 `if field in ...` 就将缺字段当可选成功。
- action 类型/角色/环境不匹配、其他实体私有观察和 GM 全量输入不能被当作合法场景输入。
- 在线场景终态与离线校验使用同一版本化输入规则或有一致性回归，避免重复定义而渐渐分叉。

先核查固定 Concordia Engine 的观察历史：现有 B 输入一条 observation，A 输入两条同值 observation。不要硬编码“每人一次”，也不要修改历史 raw 来符合新检查。当前证据能证明的次数/顺序范围要明确；需要更细来源时在新运行记录新增最小 observation delivery 证据，旧证据不足则诚实标未证。

至少加入两项审阅重算 hash 反例、错角色/缺字段/变 ActionSpec 选项或类型、越权观察，以及原五包的回归。反例应保留 native raw 的不变性，不能仅靠旧 verification.json 比较不相等通过测试。

版本规则：明确 bundle format、verifier implementation/contract 和 stored report 的版本关系。历史报告是当时结果，当前重算是新的核验；不能因算法新增字段就把正确旧内容说成 hash 损坏，也不能忽略真实旧清单损坏。保持 Phase 1A/1B/1B.1 原样例与 manifest，不覆盖或删掉旧报告来“全绿”；新结果写新阶段证据。

C0R1 修复通过后才允许 C0 后续测量消费这些包。保留事实内部一致性、来源信任和真实模型效度三种不同结论。

## 4. C0.1：最小 EvalSpec 与准入

### 4.1 冻结合同

实现一个有明确 schema/version/content hash 的 EvalSpec，仅含本轮用到的字段：

- 支持的 bundle/scenario/verifier 合同版本与必要完整性条件。
- 指标 ID/version、计算规则或 rubric hash、每个维度的类型/范围/方向与必需上下文。
- evaluator/parser/adapter/source/dependency pins，模式（deterministic 或 controlled_response）。
- 角色 alias 与真实 agent/seat 映射规则，agent 集合从输入推导，不能通用写死 A/B。
- judge 可见数据白名单、截断策略与输入大小上限；不能任意引用宿主文件路径或可执行代码。
- 输出 envelope schema、缺失/无效/内部错误处理策略；每个调用的时间/字节上限与 live budget=0。
- fixture campaign/数据集清单、split/hash、去重与独立单位声明。

更改指标、范围、数据切分或 parser 后生成新 spec，不覆盖既有评估结果。可以只有一个小型确定性 spec 和一个两维 controlled-response spec，避免提前实现任意 evaluator 插件系统。

### 4.2 先准入，再求值

准入使用重新计算的证据结果，不信任存储的 bool、进程退出码或旧 run.state。调用 evaluator 前完成必要验证，拒绝路径用调用计数证明 evaluator 执行 0 次。

结果的至少三轴要正交：evidence admission/原因、task outcome、measurement status/错误。可自行命名稳定枚举，但不能把 infrastructure_failure、insufficient_evidence、invalid_measurement 统一成任务 0 分。

| 条件 | 必须行为 |
|---|---|
| 封装损坏或内部矛盾 | 拒绝准入，保留失败原因；不调用 evaluator |
| partial/active/legacy/缺必要上下文 | 标明具体缺证；无评分，拒绝相应指标 |
| 有明确基础设施失败且轨迹 partial | 保留 infrastructure_failure，评分 null/未执行 |
| complete 的合法任务拒绝 | 保留 task_failure，可计约束失败；不能因任务失败将记录丢弃，也不能伪造未行动 agent 的评分 |
| 完整且符合确定性指标合同 | 从指定事实计算，返回来源引用和 fixture 标记 |
| 完整输入，judge 响应不合 schema | invalid_measurement，任务结果保持原值，不补 0 |
| evaluator 内部异常/超时 | 独立 measurement_error/timeout 或等价诊断；保留失败，不伪装坏输入或正常得分 |

本轮不得把任意 evaluator 抛异常统一吞成“输入无效”。只捕获明确的验证错误；未预期内部错误记录类型和受限诊断，CLI 给出可机器读取的失败。

### 4.3 EvaluationInput 与最小可见视图

从 admitted evidence 构造固定、可重算 hash 的输入包，包含证据 content hash、spec hash、scenario/run/unit 标识、alias→agent/role 映射、保留顺序的动作/结果、该指标必要的前置上下文和源引用。

audit package 中的全量 private observation/GM/memory 不自动成为 judge 输入。按指标白名单选择，记录选取/剔除/截断规则；不能把 expected fixture answer、历史 score、另一个 evaluator 的输出、candidate 标记或测试断言答案夹入 judge view。

判定 action 合法所需 options 可以进入确定性规则；未来 goal 指标所需封存目标可以进入该 judge view。两者不要与运行 fixture provider 所用的强制 `answer` 字段混淆。judge 输入里的内容都是数据，不授予工具执行或规则修改权限。

alias 映射在求值前固定，明确是谁；B→A 行动顺序不等于 agent_1/agent_2 的身份映射，字典插入顺序也不等于身份。反序 JSON keys、不同出现顺序、超出两人或单人助手都需按合同处理，未知 agent 明确拒绝。

现有 social 证据没有充分冻结的社会目标/初始关系量表。禁止给这些历史样例倒填 goals 后宣称 goal/relationship 分数可评估。它们可用于确定性合同指标；社会评分 schema 使用另行封存的、显式标记为 synthetic 的最小输入 fixture，不能冒充真实 runtime 轨迹。

## 5. C0.2：SOTOPIA 最小复用与真实刻画

参考路径：

`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\18_sotopia\repo`

固定 SHA：`a0aaafb440e570e5e61b7c44a44e5e417c545383`；MIT；metadata `0.1.5`。先检查本地状态和 pin，GitHub 用固定 SHA 链接佐证，不默认 pull 浮动 main。

重点源码：

- `sotopia/generation_utils/output_parsers.py` 的 `PydanticOutputParser`。
- `sotopia/database/base_models.py` 的 LLMBaseModel/LLMEvalBaseModel。
- `sotopia/database/evaluation_dimensions.py` 的 reasoning/score models 与范围。
- `sotopia/envs/evaluators.py` 的 EvaluationForAgents/EpisodeLLMEvaluator。
- 对应 tests 与 pyproject/import 闭包。

先做一个窄 reuse decision：优先固定上游模块+adapter；导入闭包若拖入不必要运行栈，可按 MIT 最小源码提取。记录原 SHA/路径/内容 hash、license/notice、原样与修改的边界、依赖锁及差异测试。提取只能是可追踪原代码，不能手写一个相似类后称上游执行通过。

实际执行所选 parser/schema seam，使用隔离环境、无 runtime/无 network/无 Redis 服务。不要为两个字段装整个社会模拟器、API/UI/examples/GPU 栈。必要依赖锁定版本/hash；单独的 eval optional dependency/lock 可以保留 core verifier 的标准库运行能力，不随意重解原 41 wheel 闭包。

审阅的静态风险需以受控输入明确刻画：

1. Parser 的 repair、`value`/`properties` 展开，以及 context 有/无两条路径，不能默默改变严格结果语义。
2. `evaluations.values()` 枚举后重命名 agent_1/agent_2 的行为：倒序键可能错配身份。Actio 读取显式 key/封存映射，不通过排序猜身份。
3. Episode evaluator 以 `[0]/[1]` 访问维度值，而标准 schema 使用 `{reasoning, score}`。用真实上游类的受控 generation seam 验证具体组合；失败保持证据，不用“已返回一个 list”当成功。
4. evaluator 捕异常返回 `[]`、history-only 无 messages 得到零参与人数、过滤 “did nothing” 行的行为。空结果无效；保留不行动事件或显式版本化过滤，不能删失败行为来提高得分。
5. Pydantic 可能将 bool/数字字符串等转换为 int，不能绕过 Actio 的严格类型合同。

若完整 EpisodeLLMEvaluator 有上述缺陷或引入过大的闭包，可以不作为产品路径。产品仍须复用并实际验证合适的 parser/schema，Actio 接管身份/严格 envelope；完整 evaluator 标“兼容性实验失败/未采用”，明确理由。不要求修整个 SOTOPIA 或向外发 issue/PR。

用测试侧注入固定 generation/transport 响应，可以验证上游 prompt/normalization 行为；记录具体替代点。不要将 parser 也 mock 掉后宣称 parser 真执行。若某条路只验证 structured model 返回，另一条独立路必须真实执行原始文本 parser。

依赖/导入不可行时给出最小故障、已试 seam 和成本，不伪造 PASS。parser 复用为本轮目标，优先用有许可的窄提取完成；确无可行范围再标该 Gate BLOCKED，其他离线合同工作仍继续交付。

### 严格 envelope

原 Phase 1A 的 scores=null/list/number/bool 未捕获异常要在新的产品路径中明确回归。旧 probe 与旧 13 项记录保持原样，不回填修好。

严格校验原始响应后再做可追踪的规范化，避免 parser 修复或 coercion 隐藏非法数据。拒绝重复 JSON key、空结果、null/错误容器、错/重复/缺失 agent、错/缺/多余维度、bool/string 伪分数、NaN/Infinity、越界值和超大输入。repaired 结果若保留只能作为诊断，默认不能提升为 valid_measurement。

本轮 controlled-response 优先选两维 `goal` 与 `relationship`，每位 agent 一个 `{reasoning, score}` 对象，明确说明这是选用的最小 schema。沿用上游语义：goal 为整数 0..10，relationship 为整数 -5..5；不能沿用旧 probe 的两个维度都 0..10。若选其他上游维度也逐一冻结原范围/方向，不自动统一归一化。不改变全项目 canonical JSON 只接受 safe integers 的规则来方便评分；其他指标可返回整数计数或显式 numerator/denominator。

保留 raw response hash、选定 parser/source version、验证后的规范结构与 rationale 的有限文本；不是存储无限内部日志。响应顺序变化不改变身份，未知 alias 不通过补位修复。

## 6. C0.3：两条本地可运行路径

### A. 真实 evidence 的确定性指标

最少支持现有助手和社会场景各一个有意义的合同指标：例如工具结果与固定任务合同符合情况、非法 action/GM 裁决规则符合情况。选择源码中已有事实能支持的内容，不单纯把历史 `task=success` 映射成 1。

每个指标给出计算输入、predicate/result、source occurrence/receipt/world refs 和版本。区分“系统正确拦截了非法行动”与“agent 完成任务”：合法拒绝可以说明约束工作正常，同时 agent task_failure。避免把同一成功谓词重新命名为社会能力评测。

### B. Controlled judge response 的结构路径

提供封存的合成输入与预置原始 JSON 响应，经实际 parser、严格 wrapper 和结果写入走完整链路；显式 `CONTROLLED_RESPONSE` / `fixture`，不是 live judge。成功只证明结构与数据流，预置分数没有测量有效性结论。

公共入口应能完成：读取 spec+bundle/明确 synthetic 输入 → 准入 → 构造 EvaluationInput → 执行对应本地 evaluator → 保存 EvaluationRecord → 验证记录。命令名自行确定，最终文档只列实测命令。

EvaluationRecord 至少绑定：源 bundle content/必要清单 hash、当前 verifier 版本与准入结果、EvalSpec/campaign/input view hash、身份映射、evaluator/parser/adapter pins、模式、结果/各轴状态、source refs、raw response hash、错误与实际调用计数。无模型调用不伪造 token usage 或 provider cost，说明 model_requests=0 和本轮无付费调用即可。

保存使用原子发布或等价一致性机制，不覆盖既有结果。相同规范测量请求重复调用返回原记录/明确幂等结果；输入内容或 spec/parser 变化不得复用旧结果。内部 bug 也有失败记录，不能自动反复尝试到某一次得分好看才保留。

## 7. C0.4：小型 fixture campaign 与计数规则

只做一个小型离线 campaign，封存输入清单、EvalSpec、模式、alias mapping、split/provenance 和计数单位。保存所有输入的 admission/测量记录，包括拒绝、partial、invalid 和错误。

去重至少区分：同 content 的重复包；同 run 的不同导出 metadata；同源 scenario 起点 replay 的不同 run。前两者不重复测量/计数，后者保留记录并标关联 cluster/replay group，不能装成独立研究样本。可以做工程性去重/关联，不需要计算置信区间或研究 power。

报告总登记数、唯一证据数、准入数、task_failure 数、infra/missing/invalid/error 数与明确分母。缺证不填 0，无效输出不删除。不同指标的适用集合/分母可不同，必须说明。

五个公开 bundle 是工程 fixture；dev/validation/holdout 字段若做结构验证须标 synthetic fixture split，不能宣称提供了封闭 holdout。真实 pilot 只写下一阶段数据、独立单位、目标/关系基线、人工对照和预算需求，不执行。

## 8. 验收与证据要求

最小行为集合（可合并测试，不追求组数）：

- C0R1 两项重算 hash 反例与输入缺字段/错身份；旧完整/拒绝/partial/unknown 样例兼容且分类正确。
- 不准入输入不调用 evaluator，完整 task_failure 不被丢弃；指标所需 goals/关系基线缺失时相应指标拒绝。
- EvalSpec hash/范围/版本变化生成新测量；输入内容变化不复用旧 key。
- 四种 scores 错误容器、空/缺/多身份、多/缺维度、数字字符串/bool/非有限/越界等均结构化失败，无未捕获输入异常。
- 反序 alias 键与行动顺序变化不串人；单人助手和双人社会输入按各自合同处理。
- 实际上游 parser/schema 被执行；context/repair/coercion/维度形状、空列表和 evaluator 身份行为有明确实际状态。
- 确定性指标来自事实而非旧 outcome；controlled scores 标明预置，不声称真实模型判断。
- judge view 只含必要字段，无 fixture 强制答案/多余 private context/历史 score；实际 evaluator 接收输入的 hash 与记录一致。
- 重复导出/重复请求/同源 replay 去重与关联；各失败记录和分母保留。
- 源 bundle/DB/spec 不因评估被修改；新结果原子写入，离线记录可复核，原目录不可用仍可验证允许的路径。
- 评估运行阶段无网络/DSH/Concordia/模型/Redis 启动；用合适 audit hook、注入计数或隔离进程证据证明，而非只写注释。

更新输入/seal/verify 的部分应跑相关原 evidence/runtime/reliability 回归；新 eval 的纯逻辑不需要无理由重复所有 38 组。若共享核心或打包变更扩大影响则补相应测试。不要为缩短工作省略必要真实边界，也不要为累计数量跑无关上游栈。

在 `docs/validation/phase1c0/` 写独立 evidence manifest，绑定实际命令、退出码、环境/pins、相关 product/test/source hash、模式、原始/脱敏日志、失败和 NOT_RUN。上游原失败与本地补偿后的通过分开，不修改参考仓库或历史样例。

固定依赖与 MIT notice 要能在干净隔离环境重建。verify 的标准库使用路径保持可用；eval optional 依赖缺失时给出明确错误，不能导致所有只读证据命令启动失败。使用新合成身份运行必要集成，既有 spec 不因代码升级被原位改 pins。

## 9. Gate、停止点与发布

最终交付：最小测量模块/CLI、EvalSpec/输入/响应/记录样例、可追踪 SOTOPIA 复用及上游刻画、fixture campaign 与全量报告、关键回归/干净环境 smoke、文档/独立证据，以及已推送 GitHub 的提交。

`CONDITIONAL_GO` 需要：输入绑定漏洞关闭；各维度准入正确；选定 SOTOPIA parser/schema 实际执行；严格 envelope/身份映射正确；真实证据确定性路径与 controlled-response 路径均可复现；零模型费用、原证据只读、原关键回归成立。它仅准入离线测量工程，不宣称测量效度、统计提升或真实社会能力。

关键门槛缺证则 BLOCKED/NO_GO 并说明局部原因；完整上游 evaluator 不采用不等于整个 parser 复用失败。保留已完成工作和真实失败，别为了全绿跳过身份校验、数据前置或把合成分数写成真实结果。

完成后停止。下一轮才规划 Phase 1C1 的真实任务数据/目标、provider 与独立 judge 接入、pilot 及预算；Raven 单 seat 演化、版本激活和完整恢复继续后置。

发布按根 AGENTS.md：检查本轮 diff 与必要测试 → 提交本轮文件（不提交大缓存、秘密、真实个人数据）→ 普通 push 当前实现分支 → 核对远端 ref 与 HEAD → 最终报告 commit/branch/GitHub 链接、实际验收、Gate/限制与复现入口。不要停在“尚未推送”，也不要自动合并 main。
