# C2C2 冻结合同

本轮仅 B0/C1 的有限开发集探索性工程试验。保留原 12 卡、生产 world/oracle、persona、空 memory 和两个 actor 的规则。唯一直接干预为 A 的已有三个 checklist 词条；没有新候选、proposer、搜索、训练、judge、真人标签、生产激活或能力 pass 路径。既有 C2C1 proposal/scaffold hash 从已发表对象重算，旧静态 policy 不改。

## 版本与所有权

| 对象 | C2C2 版本 |
|---|---|
| config / profile | pilot-config.v9 / sdk-minimal+actio-tokenkey.v5 |
| task / input | actio-task.v5 / finite-candidate-tokenkey.v1 |
| mode | candidate_live / candidate_rehearsal |
| plan / campaign / measurement | candidate-execution-plan.v2 / candidate-campaign-evidence.v2 / candidate-measurement.v2 |
| evaluation / binding / policy / decision | candidate-evaluation.v1 / evaluation-binding.v1 / candidate-evaluation-policy.v1 / evaluation-decision.v1 |
| Store / lineage / delivery | schema 4 / evaluation-lineage.v1 / candidate-delivery.v2 |
| 通道、任务 oracle | 沿用 single-choice-dual-channel-audit.v2 / finite-independent-measurement.v1 |

v8/candidate_loopback 继续拒绝 provider origin；旧 task/profile 允许值不扩大。新分派覆盖 cfg、task、host、transport、fetch gate、Ledger、raw/native audit、measurement、delivery。官方 DSH SDK/runtime 0.1.5rc1、Windows x64/Python 3.12、Concordia b71d202750e23444ce1bf28d9f114bcd88aa41db 不变。没有替换官方 pi-ai、Python OpenAI SDK、新 gateway 或升级 runtime。

candidate、parent edge、旧 campaign_binding/decision 和旧 decided 状态解释不变。v3→v4 只读复制迁移，保留原库、backup/hash、原 Store identity、所有旧事件与六份 decision；新增 evaluation、evaluation_binding、evaluation_event、evaluation_decision、evaluation_migration 均为 Store 所有的不可变事实。两臂每个 evaluation 各一 binding；仅 C1 获得相对 B0 的新 decision，B0 为参照诊断。新注册幂等，claimed 不重领、不恢复旧 evaluating。无 active pointer，不调用 Store.agent 更新或 CAS 激活。

历史关联固定为 C2C1 reader 6578c742bd5ab3672c97ee002a6559150c70b1fd 和已发表 lineage SHA256 46ff0b339969c6889119a2a04378389bbe65065e748a3c0e73a84b40d8cedabe。迁移后旧投影必须精确相等；完整 delivery 绑定新 plan、每 arm 原始/native/领域/账本、测量和新 decision。JSON 是只读导出，不能成为第二权威库。仅证明登记/复制迁移持久性；full_controller_recovery=unsupported。

## 执行、观测与指标

| 情况 | 技术证据 / 执行结束 | 格式 / hard | joint / utility |
|---|---|---|---|
| 两个可信合法行动 | 原始/native/账务/receipt 可核验则完整 | 分别计算 | defined；合法拒绝可为 false / 0 |
| 可信非空非法 A | 合法拒绝 receipt；B 按规则跳过；可完整结束 | A format=false；B task_predecessor_invalid，不适用 | null / not_applicable |
| 可信非空非法 B | B 拒绝 receipt；可完整结束 | B format=false；相应 hard 不适用 | null / not_applicable |
| 合法但违反自身/公开 hard rule | 完整观测到行为错误，不停止 campaign | 对应 hard=false | 原 oracle 保留；阻止违规交易后合法完整 pair 的效用为 0 |
| 依法拒绝 / 联合不可行 / 非全知最优 | 不作为技术错误 | 按实际自身规则核验，不把 joint/regret 当 hard | 独立诊断，不据此判格式违规 |
| unknown、timeout、通道/文本/身份矛盾 | 技术不完整，停止；保留 suffix | 未核验的文本不计行为正确/错误 | missing/null |

B 原公共规则要求“恰在公开允许且自身条件满足时接受”。依法拒绝不违规；语法合法但任意拒绝本应接受的提案，仍是原 B response-rule 违反。新 policy 不改变任务规则，也不使用对方隐藏状态惩罚 A。

text_verified、format、domain_executable、local_hard、B response rule、joint、双方 utility、Pareto/regret 分列。每 metric 均 assigned=eligible+not_applicable、eligible=defined+missing；布尔 defined=true+false。按 family/arm/feasibility 分层；每个 arm pair 的执行完成与各 metric 的配对 defined/missing/not_applicable 分开。只有两臂该指标均 defined 才给 delta，否则 null 并带原因，不补零、不删除错误 pair。指标相减不是整体 score，也不做排名、显著性、推广 CI 或成本归一化获益。

## 输入边界

所有请求均正向重算 observation、prepared 和 full wire。B 只看本臂实际 A 行动；A 相同则 B 输入相同，A 不同时去掉已核验的公开历史后，B 的自身信息、指令、options、参数、权限及 scaffold 必须相同。hidden 反事实改变对方 private，不改变自己的允许输入。candidate/card/arm/pair/oracle/hash 标签不进提示。

只归一化独立 SDK UUID4 message IDs，并验证它们不在 full wire。只有 content 进入公开行动、世界、B 和 memory；reasoning 仅核验结构/一致性，公开报告只保留 hash/类型/核验结果。空 content、length 和现有不支持通道仍拒绝，不在 live 后放宽。

## 唯一有限 live

原 12 cards × 2 arms × gpt-5.6 × 1 repeat =24 episodes / 最多 48 seat sends。seed=20261012 仅调度；family 交替，卡内两臂相邻，每 family 各 3 baseline-first 和 3 candidate-first。max_tokens=512，temperature/供应商 sampling seed 不设置，reasoning 不主动请求。重复使用开发卡：split=development_exploratory、independent_research_units=0、human_labels=0，不是 holdout。

精确 TokenKey https://api.tokenkey.dev/v1/chat/completions；原 redirect/cross-origin/一次 fetch 限制保留。明确 uncapped_for_phase1c2c2，仅解除金额限制，不解除有限计划、输出长度、期限与账务。ready30、RPC5、headers60、idle60、total90、result115、drain5、close5、Worker165 秒及原起点不变；活动不能延长 total。无 SDK/transport 自动重试。

完整本机新模式验收、干净安装、固定 reader 和 CLI 通过后，将实现与 preregistration 普通推送任务分支及 main，核对远端 SHA、clean checkout 和已提交计划。只有专用 execute 在核验发布与 source-bound local admission 后解析凭据。凭据来自 ignored/untracked .local/credentials/token_key.txt，缺副本才使用已授权源；不打印、记录或传给其他 origin。计划/preflight/verify 不读 key/env、不联网、不启动 Worker、不写文件。

项目固定 live-once claim 与 plan claim 均不可重领，输出目录变更不授予第二批。每 episode 独立 Ledger/Store/authority，串行 A→B、每 seat 一次。首个完整 arm block 只检查完整性/清理。行为错误继续；首个技术错误停止整个 campaign，不补样、不换 route、不再诊断调用。controller 异常先保存 entries、pilot、原账本 inventory 和完整未运行后缀，再尝试 verifier；verifier 失败单独存缺口文件，保留 claimed 状态，不声称恢复成功。

## 决策与历史

优先级：静态不合法 reject/不发送；技术不完整 infrastructure_failure（保留行为事实）；技术完整且 C1 存在已观察格式/自身 hard 违反，reject 本轮开发约束；其余 insufficient_evidence，无论 delta 正负或 0。不存在 C2C2 capability pass；所有 eligible_for_activation=false。baseline 不写晋升决定。

历史 91 次生成尝试、目录 GET 1 排除于本轮主分母；本机尝试另计。累计仅加实际 live sent，不能预填 139。raw Decimal cost 原文保留；币种/单位、报价、账单/upstream weights 身份未核实，不估 USD、不填未知为 0。binary_source_mapping=unproven。旧 C2C1 的 24/48/12 与零差值、C2C0/C2B2 停止/unknown/not_run、claim 和原始产物均保留，固定 reader 独立重现。停止于 C2C2。
