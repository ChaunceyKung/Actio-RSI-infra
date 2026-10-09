# Codex 执行 Prompt：Phase 1C2B2 测量完整性与预注册工程 pilot

请在 Actio-RSI-infra 实施 **Phase 1C2B2**：先修复本次审阅确定的证据语义与 actor 输入边界问题，复用现有 DSH/Concordia/SQLite，完成独立确定性测量、固定任务矩阵与一个预注册的小型 solver pilot。验证后提交、推送任务分支和 main，核对远端 SHA；不要只交付新的准备文档。

当前 Prompt 的上游为 C2B1 `1e00535408e3a3dd12356dbb2cdf934134fb68e4`。先读 `docs/reviews/phase1c2b1_review_and_c2b2_plan.md`、`phase1c2b1_review_evidence.json`、AGENTS.md、C2B1 合同/结果/Gate/CLI/账务/adapter/manifest；从包含本 Prompt 的最新 origin/main 开始，记录真实 HEAD 与祖先关系。

## 0. 当前授权、阶段边界与结果目标

用户已指定 TokenKey `https://api.tokenkey.dev/v1`、本地 key 文件，并要求“不设置预算上限，以推进项目为准”。必要凭据读取、solver 工程验证和有依据的有限诊断沿用此授权；本 Prompt 明确实施的工程 pilot 无需再次请求同一费用批准。保留逐请求输出/期限、Ledger、一次性资格与阶段结束条件。不重新引入 USD1、零预算、两次总调用或精确最大计费输入才能发送的门槛。

这是**预注册工程测量 pilot**：验证测量和实验执行基础设施，观察约束遵守、格式、数据完整性及路由稳定性；不是模型能力排名、正式统计研究或演化晋升。judge/真人标注/训练/自动候选晋升/部署不在本轮。上游权重身份和账单仍可 UNVERIFIED，只有依赖它们的结论受限。

项目：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。建议分支 `phase1c2b2-measurement-integrity-and-pilot`。先 git status/remote，保护已有修改；普通 push、必要时安全整合 main，不 force push。用户明确要求每轮验证后交付 main，阻塞时也提交已验证成果与真实失败。

## 1. 复用基础，不重建已通过部分

保持 Windows x64、Python 3.12、DSH SDK/runtime `0.1.5rc1`、exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`、Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。Python Control Plane → 官方 Python SDK → DSH TS loop → 真实 Concordia Sequential 保持。

官方 `@deepseek-ai/dsh-llm-pi-ai` 已在固定 binary 中真实加载，并完成 TokenKey 双模型闭环。直接复用 `actio-tokenkey` 路由、官方 serializer/translator、无 retry profile 与最终 fetch gate；不再重查插件是否存在、重复 109 模型扫描、建设新网关或用 Python OpenAI SDK 替换 solver。

重点读取：

- `gateway_contract.py`、`gateway.py`、`budget.py`、`transport.py`、`transport_contract.py`、`plugins/transport.mjs`；
- `task_contract.py`、`scenarios.py`、`terminal.py`、`verify.py`、`transport_campaign.py`；
- `eval_contract.py`、`evaluation.py`、`calibration.py` 和 gateway/task/evidence/input_binding 对应测试；
- 现有 bootstrap、validate、historical reader、归档与发布工具。

复用现有领域状态与证据格式，以新版本分派增加能力。历史 C0/C1/C2A.1/C2B0/C2B1 artifact、失败、manifest 和旧合同不能修改或重新封存。C2B1 v5 的固定两场景、实现 hash、观察合同仍有历史意义；新任务、阶段授权与测量计划应显式版本化（如 v6/task v2），不要全局放宽旧校验。新配置明确 C2B2 的执行范围与 uncapped 策略，不能将新运行继续伪标为 C2B1；null 金额仅在明确策略及用户授权依据下有效。

## 2. 先补两个已确认的测量前置缺口

### B2R1：原始模型文本必须绑定到实际行动

审阅发现：现有 `gateway_contract.trusted_usage` 检查 raw SSE 的 usage/finish/id/model，并把 translated block 文本与原生行动比较，但没有校验 **raw SSE delta.content → adapter text → native action** 的完整关系。内存反例仅改变 raw text、同步更新重复事实及结构 hash 后，旧 analyzer 仍接受矛盾。原有 8 条真实记录的三层文本逐条检查一致；不要据此否定原有调用，也不能将 hash 一致冒充语义一致。

新合同增加有界、严格的审计检查，仍由官方 adapter 完成生产翻译：

- 对本轮支持的纯文本、单 choice 流定义明确语义；按 SSE 事件顺序核验 index/role/content/finish/usage/DONE，与 adapter 块和最终原生 answer 对应。
- 对缺失/重复终态、多 choice、未支持 tool/refusal 分支、finish 后内容、非文本 content、坏 JSON、结构重复键及多行 SSE 等给出明确支持或拒绝策略；不要静默过滤后碰巧通过。审计器不是另一个生成/自动修复协议栈。
- 原始字节/文本、响应 ID、HTTP request ID、usage 和世界效果继续保留。仅 usage 可核对不代表文本/行动证据可信；分列 usage accounting 与 measurement admission。
- 正常输出分片、中文/UTF-8 边界、空增量、合理 usage 事件要可解释；不得拼接不同 choice 或 reasoning 为行动文本。
- 新 reader 拒绝内容矛盾，即使结构 hash 一致。新增行为测试应修改真实样例的内存副本，历史文件不动。
- 对 C2B1 8 条记录追加只读复核 sidecar，注明 reader SHA 和新检查结果，保持旧 manifest 原样。

### B2R2：actor 输入对隐藏信息的反事实不变性

`actor_observation` 当前把完整 TaskSpec hash 发给 actor；同一 A 的公开信息、身份和自身约束不变，只将 B 的可用时间切换 compatible/conflict，A 的输入仍因 task_hash 变化。没有发现对手私有明文泄漏，但这不满足严格的“只看 own + public”反事实输入要求，且会混入后续干预比较。

新任务观察版本将完整 task/config/manifest/dataset/split/oracle hash 留在 Control Plane 与 Ledger。模型可见内容只含该 seat 允许看的信息；需要 view hash 时仅由可见内容派生。不要让场景名称 conflict/compatible、正确答案、全知 metric、对方 spec/memory hash、分组标签或隐藏信息派生 ID 进入 solver wire。

具体检查整个 prepared/wire payload，不只检查 observation 子对象：

- 固定 A 的所有允许输入与公共历史，改变 B 私有可用性/偏好/隐藏元数据，A 的模型可见输入逐字节相同。
- 固定 B 自身信息与已公开的 A 行动，改变 A 其他隐藏信息，B 输入逐字节相同。
- 改变该 actor 自己的约束或真实公共行动，输入必须相应改变。
- 随机 op/run/agent 标识如果留在模型可见内容，必须证明不编码隐藏变量，并对反事实测试固定；优先将纯审计标识留在外部绑定层。
- 完整任务仍与授权、实际 wire、世界效果和评估 source 强绑定；不能为输入脱敏删除账本证明。

B2R1/B2R2 的本机行为检查通过后才开启新 pilot。发现其他阻止完整性的真实缺陷时先窄修复并记录，不扩展为任意插件安全平台或完整 controller 恢复。

## 3. 独立确定性测量，不用 task_failure 充当能力分数

旧领域结局不改：compatible 达成可为 success；conflict 中合法 decline 仍可能是 task_failure，因为共同时间未达成。新测量从冻结约束和实际行动**独立重算**，不读取旧结果字段直接转换成正确率，不调用 LLM judge。

至少提供以下维度和明确分母：

| 维度 | 定义 / 边界 |
|---|---|
| 执行与证据完整性 | assigned / sent / response / terminal / admitted / not_run / protocol_error 分开 |
| 格式合法 | 实际 action 是否为 ActionSpec 允许值；非法动作是行为观察，不是重新求解理由 |
| A 自身约束 | 所提 slot 是否在 A 的 own_available；合法选项也可能违反自身约束 |
| B 本地回应 | 按 B 自己可见的 proposal 和 own_available，能够参加才 accept，否则 decline；不要求 B 知道 A 隐藏约束 |
| joint_feasible | 两个冻结可用集合是否相交，仅评估可见，不发给 solver |
| 共同结果 | 实际协议是否达成共同可参加的时间；与 B 的正确拒绝、own violation 分列 |
| 延迟与 usage | headers/首 text/请求/episode 分层；reported token、cache/reasoning 口径及完整率 |
| 路由与成本状态 | requested/response model、adapter、fingerprint、时段；cost/单价/账单证据各自缺失明确为 null |

对预设不可能达成的 conflict，不将“没有共同达成”作为模型能力 0 分。对 A 作出错误但合法 proposal 时，B 是否正确回应按 B 的本地信息评判，不能以全知 evaluator 的答案要求 actor。goal/relationship 继续 NOT_CALIBRATED，不输出假精确社会关系分数。

规则用小有限域真值表/手工列举 oracle 验证，包括正确接受、正确拒绝、接受不可用时间、A 违反 own、可达成却拒绝、非法/缺失/未运行。oracle 实现应从基本集合谓词独立推导，避免直接调用 GM task_result 再声称相互验证。新指标版本、输入白名单、来源 operation/occurrence/receipt 和代码 hash 要可离线核验；复用现有 source_bundle、seal、只读 reader。

## 4. 固定最小任务矩阵与完整计划

先使用成人邻里清洁排期这个既有 family，保持两 seat / 两步与确定性 GM，避免同时引入自由文本协商、多轮记忆、工具或新环境。

默认矩阵在调用前冻结：

1. A/B 的 own_available 各为 morning 或 afternoon 单元素集合，构成 **4 个参数实例**；偏好等于自己的唯一可用时间。
2. 每实例两种 presentation：A 的 proposal 选项与 B 的 accept/decline 选项按规范顺序或同时反序；语义不变。该因素是联合选项呈现变化，不能声称单独识别某一 seat 的位置效应。
3. 两个已接入路由：gpt-5.6、claude-sonnet-4-6；同一 episode 两 seat 使用同一模型。
4. 每个 model × instance × presentation **2 次独立新运行**，初始 memory/spec 重置且固定，episode 间不共享学习结果。

因此计划为 **8 张呈现卡 × 2 模型 × 2 repeats = 32 episodes，最多 64 次 solver 发送**。这是可审计的工程设计规模，不是金额限制，也不授权无限补样。可在首次模型调用前依据实现限制缩减并给出理由；不能看到效果后改任务/重复数、挑成功样本或扩样到“显著”。

4 个参数实例含时间标签互换，只有 1 个任务 family、2 类对称结构（相容/冲突）；16/32 episodes、64 messages 均不代表同样数量的独立研究单位。repeats 反映相同实例重跑，不能通过 UUID、改名或镜像增大独立 N。保留 instance/presentation/symmetry-group/repeat/route/episode 层次，本轮 independent_research_units=0。

运行表提前枚举全部计划，使用固定调度种子交错两模型并平衡模型先后顺序；不先跑完 GPT 再跑全部 Claude。两模型为配对 route cohort，非上游身份已认证的模型品牌对比。provider seed/temperature 继续沿用已支持配置；调度种子不冒充模型采样 seed。

现有 v5 只允许 compatible→conflict，且 Ledger 在开始 episode 时才注册。新版本需单独持有不可变完整计划，覆盖未启动 episode、未注册 seat 和派生 attempt；导出时必须验证计划与实际一一对应，删掉失败/未运行行后重算 hash 不能通过。不能仅从已注册 Ledger 推断全体分母。

现有 Ledger 每份配置固定一个模型。优先在实验计划层映射各执行单元到有明确 authority 的子批次/账本，按冻结顺序调度；保留每份账本内部配置不变及一次性资格。不要为交错两模型临时修改同一账本 model，不要把跨账本汇总误称为已支持全 controller 恢复。

## 5. 计价与路由证据：有限调查，按主张分 Gate

先使用已有 22 次历史生成尝试（14 次直接诊断 + 8 次 C2B1）与 1 次目录 GET；这些仅作历史诊断/smoke，排除于新 pilot 主要分母。不重复 key 验证或全部模型目录探索来“证明更可信”。

查阅 TokenKey 公开说明、页面可见文档和模型/定价信息；如存在已明确的只读账单来源/本地导出，解析所需最小字段。记录 URL、检索时刻、有效期、证据 hash、claim 与覆盖范围。不要猜管理端点、不向其他 origin 发 key、不修改账户或充值；无法取得账单/单位时明确未取得，继续其他工作。

数据至少区分：

- observed_label：实际 requested/response model、HTTP request_id、response_id、fingerprint、服务时间；
- provider_claim：供应商声明的路由/版本/价格，有出处但不等于独立上游权重证明；
- quote：币种、每单位 token 的基准、cache/input/output/reasoning 口径、模型、时段、来源；
- raw_usage_cost：保留实际 Decimal 文本，未知单位不转换成 USD；
- estimated_cost：只有适用单价和口径证据时计算，说明缺项；
- billed_cost：真实交易/请求级账单映射、税费/汇率/账户范围、对账差异；余额差额不直接归因于某个并发请求。

侧挂新 evidence/sidecar，不修改历史 raw、usage、cost=null。部分匹配不得冒称全账单对账。缺可信计价时禁止 cost-normalized ranking，但可以完成约束、格式、usage 和时延的工程测量。缺上游独立证明时结论限定为 TokenKey route 在观测时段的表现；不要求穷尽证明网关内部权重才推进。

## 6. 预注册、发布和执行顺序

先完成新合同、任务/测量、计划/分母、两项修复及本机验收，再输出机器可读预注册文件。至少冻结：

- 研究状态 engineering_pilot、目标与不回答的问题；
- task family/instances/presentations、oracle/metric/source versions、配对与相关性分组；
- 初始身份/spec/memory、精确可见输入构造、模型路由、参数、期限、实现 hash；
- 全部有序 planned episodes/seats、调度 seed、停止/not_run/重试政策；
- 主要指标与分母、缺失/非法/基础设施失败处理、route 变化策略；
- 描述性报告字段，不作显著性检验/推广性 CI/排名或晋升；本轮不预留看似独立但已用于调试的“holdout”；
- 已有诊断/失败的排除与累计计数、用户授权依据与 explicit uncapped 策略。

**在首次新 pilot 调用前，commit 并普通 push 已通过本机验证的实现与预注册到任务分支和 main，核对远端。** 保存 commit/hash 与 first intent 顺序。这是可验证的冻结步骤，无需向用户重复确认费用。若实现变动使预注册失效，先生成明确 superseding 版本；旧运行保留为单独诊断，禁止回填原预注册。

执行第一预定配对 block 后只检查基础设施、语义和清理，不能按模型得分决定是否继续。合同未变时它计入既定 pilot；发现缺陷需修复时保留为旧版本失败/诊断，重新冻结后启动新版本，不拼接不同合同来凑齐 N。

每 seat 单次生成，任何格式/行为错误保留原样，不自动“修答案”。真实 DSH → Concordia，两 seat 中 B 只接收实际 A 公开行动。任务失败和基础设施失败分开；A 无有效行动时 B not_run。未知、身份/协议矛盾或超时停止受影响的有限批次，确认旧 Worker 回收后才能登记有原因的新诊断，不复用原 attempt，不抹去累计 unknown。

所有预定单位都出现在最终表，未执行的给出原因。有限故障调查有具体假设、改变与结束条件；相同错误无新增证据时停止该路径并交付。无需为了凑齐 64 次而调用，亦不把成本未知误作协议故障。

## 7. 验收、历史 reader 与清理

重点验证新增行为，避免为可逆文档另建测试或反复重跑已通过大套件：

- raw/translated/native 内容一致与矛盾拒绝；原 8 条 live 记录新只读附加校验通过；
- 全 wire 的反事实可见性与 external task binding；oracle/答案/hidden hash 不进入 actor；
- 新任务真值表、metric 分母、正确拒绝与协议/task/cost 状态分离；
- 完整计划拒绝漏项/重复/换 model/变参数/混版本，prespecified not_run 不消失；
- 两模型×新呈现矩阵至少一次 loopback 真实 DSH/Concordia 集成，B 使用 A 实际输出；
- 现有零副作用 plan/verify、一次发送、失败/unknown、并发唯一 claim、authority、凭据保护、清理不退化；
- 离线 verifier 在禁止 key/env/网络/subprocess/Worker/evaluator/写入条件下复核新导出；
- 源码与安装一致、pip check、公开 CLI；构建/安装/runtime suite 与 live 顺序执行，避免期限干扰；
- 固定旧 reader：C0/C1 沿用各自受信 SHA；C2A.1=b086cba，C2B0=f65045a，C2B1=1e00535。artifact 不决定执行源码，新 reader 不偷偷替代旧解释。历史原件原 hash，追加检查另存。

密钥仍为 `.local/credentials/token_key.txt`，缺副本才读取用户指定源 `D:\调研\CausalEngine\api_key\token_key.txt`。保持 ignored/untracked，仅内存注入 ACTIO_SOLVER_KEY，目标仅 `https://api.tokenkey.dev`。不打印 key/片段/长度/key hash；不提交真实账户账单敏感信息。

新归档用明确运行目录和文件清单，复用 manifest；优先 hash/diff 定位需要复核的增量，不无目的反复扫描整个 node_modules/venv。保留失败、诊断、源码版本与真实 argv。清理以具名 Job/受管服务为准，不按复用 PID 终止其他进程。记录全部模型发送、响应/usage、未知/费用、Worker、服务及端口。

## 8. 交付与停止点

交付 `docs/validation/phase1c2b2/`：修复合同与差异、结果/Gate、manifest、CLI、不可变 preregistration/plan、任务卡与独立 metric、route/cost evidence registry、逐单位结果及失败/未运行、历史追加复核、清理与下一阶段建议。更新 README 的当前入口。

最终 Gate 分开报告：measurement_integrity、engineering_pilot_execution、billing_reconciliation、route_observation、upstream_identity、human_calibration/judge、research_validity/evolution_promotion。只对满足证据的项放行；binary_source_mapping=unproven、full_controller_recovery=unsupported 不顺带宣称解决。

完成后再次 commit → 普通 push 任务分支 → 安全合入 main → 普通 push origin/main → 核对远端 SHA/工作树。推送失败说明真实原因并保留本地提交，不强推。发布范围只含本轮安全文件。

最终中文报告说明两项修复、预注册冻结提交、planned/attempted/not_run/usage/unknown/费用、实际 pilot 覆盖与相关性限制、失败/清理、main SHA 和结果/manifest/CLI 链接。停止于 C2B2。后续 C2C 应增加有区分度且有来源的任务、独立校准与评估准入，再做单 seat 候选及谱系；不要因 pilot 满分直接晋升，也不要把下一阶段自动执行。
