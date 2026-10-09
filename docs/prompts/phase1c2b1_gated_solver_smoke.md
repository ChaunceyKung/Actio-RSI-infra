# Codex 执行 Prompt：Phase 1C2B1 受控 solver 连接 smoke

在 Actio-RSI-infra 执行 **Phase 1C2B1**：先完成真实 solver 的受控执行入口、本机验收与具体批准包；**首次真实调用前向用户确认**。得到明确确认且条件满足后，最多执行一个 baseline episode / 两次 solver 发送，再完成对账与交付。

用户本轮已选择：“先完成执行入口和批准包，下一 session 首次真实调用前再确认”。因此不能一开始只问预算，也不能把本 Prompt 当成付费调用授权。先把可独立完成的准备工作做完、验证并推送；到具体的首次真实调用边界才提确认。用户不回复或拒绝时，保留完整准备成果与 AWAITING_APPROVAL，真实请求仍为 0。

## 0. 基线与发布要求

- 仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
- 已验证产品基线：**`f65045a11d1a4728b98b5564623e4827365f91c8`**，C2B0 已快进推送到 main。
- 最新审阅与本 Prompt 在远端 main；读 AGENTS.md、git status/remote，fetch 并记录实际起始 main HEAD，确认 f65045a 为祖先且已包含本 Prompt。不能从旧 C1 或 C2A.1 开始。已有同任务分支先检查再继续，保护无关修改。
- 推荐工作分支：`phase1c2b1-gated-solver-smoke`。用户最新要求是**验证完成后发布到 origin/main**，覆盖历史 Prompt 的“仅任务分支/不推 main”默认。
- 每次完成一个可交付状态：检查 → commit → 保留/普通 push 任务分支 → 安全合入 main → 普通 push origin/main → 核对远端 main SHA 等于本地 main。主线无分叉时快进；并发更新时先整合并跑相关检查，不强推、不覆盖他人工作。BLOCKED/NO_GO 的诚实交付同样推送。网络/权限阻塞保留本地提交并精确报告。
- main 发布授权不等于真实费用、模型选择、凭据读取、部署或进一步实验授权。不部署。
- 固定 Windows x64 / Python 3.12 / DSH SDK-runtime `0.1.5rc1` / exe hash `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6` / Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。
- 新运行使用隔离短路径、新身份/spec/数据库。复用官方 SDK、TS adapter/loop、Concordia、现有 Ledger/campaign；不升级 DSH，不装新版 Messages 插件，不换 Strands，不自写另一 solver 或通用计费/审批平台。
- 真实调用获准前，仅允许公开官方资料/GitHub/锁定依赖准备、Git push、本机 fake credential 服务与离线工作。不读真实 key，不请求外部鉴权/model-list/余额/模型 API，不自动登录或充值。

## 1. 先承接事实，避免重复建设

必读：

- `docs/reviews/phase1c2b0_review_and_c2b1_plan.md` 和 `phase1c2b0_review_evidence.json`。
- `docs/validation/phase1c2b0/` 的 contract/results/gate/usage/cost_credentials_timeouts、manifest、candidate、approval_package、sources/upstream 和四个公开 sample。
- readiness_contract/readiness/transport/transport_contract/budget/plugins/transport/host/supervisor，以及 task_contract/scenarios/terminal/verify/transport_campaign 的版本分派。
- readiness/readiness_config 测试、rehearsal/CLI/release/legacy 脚本。

当前已完成 68 组本机验收；正式阶段全部尝试为 162 sending / 158 receives，实际模型/外部 provider/费用 0。旧 v3 超时和原参数重跑均保留，根因未证。审阅又完成 11 个配置测试、四个 sample、C0/C1/C2A.1 固定旧版复核和原始材料核对，但没有重跑全部 runtime。

C2B0 execute **无条件拒绝**，TransportPort/host/Ledger 只允许 rehearsal/fake key，因此 live 执行入口仍需实现。v4 的报价算法、authority 独占绑定、未知占额、内存凭据和分层超时可直接复用。

历史 40 个文本路径有 checkout CRLF 差异，Git 内容未变。必要时用明确列出的 LF Git blob 比对解释，不全局忽略 hash，不修改旧 manifest 或重封历史记录。

## 2. 固定本次最小范围

只准备以下具体试运行方案，**仍是提案，未经确认不得执行**：

- 官方 DeepSeek Chat Completions，候选 `deepseek-flash`；
- 精确 URL `https://api.deepseek.com/chat/completions`，POST、stream、include_usage、thinking disabled、max_tokens 64；
- **compatible 卡、1 episode、A→B 两 seat、每 seat 最多一次请求**；不同时执行 conflict 卡，不做模型比较；
- GM deterministic，judge/retries/title/compaction/tools/MCP/Files/image/其他模型 producer 关闭；
- 只有合成角色、任务、私有约束与冻结 memory，B 只看到 A 实际发生的公共行动，无预置答案/测试服务响应计划；
- 首 seat 本身就是连接检查，不另开不计账的健康探针。所有实际模型发送尝试包括诊断都计入批准额度；
- 沿用已验证的有限 timeout 作为首选，不在一次付费失败后自动加长并重跑；
- 候选 credential reference 是 `ACTIO_SOLVER_KEY`；只记录引用，不要求用户把 secret 发到聊天或写进批准包；
- 当前约定的保守估算为单次 $0.314649600、两次 $0.629299200。可建议 **1 USD 本地预算**，但 actual_budget 在人类确认前仍为空/0。

用户可以在确认时变更选项；变更后先重新验证/生成合同，不擅自扩成两个 episode 或增加请求。一次连接 smoke 不能证明模型推理、研究效度、校准或演化收益。

## 3. S0：划清发送条件与实验待观察项

复查以下公开页面，记录来源/日期/hash/摘录：

- https://api-docs.deepseek.com/quick_start/pricing/
- https://api-docs.deepseek.com/api/create-chat-completion/
- https://api-docs.deepseek.com/quick_start/token_usage/

固定官方 DSH 源码 tag 为 `dsh-v0.1.5-rc.1` → `183f08e9c6dde7e36cd2318eaee70b0da08fb35e`；只读按需核对 adapter/serializer/translator/SDK 凭据路径，保留 MIT attribution。旧本地较新 checkout 不是固定 binary 的依据。

不要继续把所有未知放进永久固定的 BLOCKERS 列表：

1. **发送前条件**：具体人类授权、合同和实现匹配、未过期的报价/批准、预算可容纳一次保守预留、明确计价依据、指定 credential reference、可信 profile、持久 authority/一次性资格、场景/隐私和清理边界。
2. **本 smoke 要验证的项目**：供应商是否接受固定 adapter 字段、实际 response model/id/usage、正常原生终态、延迟与双 seat 闭环。它们起初 UNVERIFIED，不能同时成为“必须先真实验证才允许首请求”的循环条件。
3. **仍然不解决的项目**：完整 controller 恢复、二进制可复现构建、人工标签/judge、研究/演化晋升。继续明确 unsupported/unproven/BLOCKED，不扩大本轮工程。

对费用上界只能采用有依据的方法：

- 若获得当前模型确切可计费输入上界，引用证据并据此计算；
- 若仍只有“1M”，保留当前覆盖十进制/二进制常见解释的 1,048,576 输入及峰值 cache-miss 包络，标成 **conservative_assumption**，不能改成 verified；
- 精确 tokenizer 与经证明的最大上下文上界是替代方法，不要求两者都必须获得。通用 tokenizer、字符比例或 65,536 bytes 不可冒充证明；
- 如果采用有残余假设的方案，批准包要清楚说明单价时效、单位、额外/错误费用和账单不受本地程序完全控制，**请求用户明确接受这一具体试运行假设**。没有这种接受就不执行；
- 用户若要求绝对供应商账单硬上限，必须有供应商侧可核实的额度保证；本地 1 USD ledger 不能冒充该保证。不自动设置收费账户/充值；
- 不能靠延长 quote 日期、置 input_bound_verified=true 或删除 blocker 来获得批准。新来源、计价策略或实现改变必须改变合同 hash。

保持 USD nano 整数算法、缓存只计一次、峰值 reserve、向上取整和四类量分列：sending、usage、估算/预留、供应商实际账单。尚无账单就 null/UNVERIFIED。

## 4. S1：实现真正可获批的最小入口

为 live 增加明确的新 schema/mode（例如新 config 版本与 `live_solver_smoke`），不静默改 v4 live_candidate 或 priced_rehearsal 的已发布语义。保持无授权默认拒绝与本机测试模式隔离。

### 授权与实际 task 的绑定

- 批准对象绑定源实现/运行 pin、quote、model/origin/path/method、参数、限额、UTC 有时区期限、数据范围、**有序 episode 队列**、具体身份/spec/memory hash 和 credential reference。
- 审阅用占位 PROPOSED_A/B 卡不能直接当成批准后的实际身份。先冻结具体计划；不要把两张候选卡的集合当成任意顺序/次数的运行许可。
- B 的实际输入依赖 A 尚未产生的行动。批准的是冻结的可见性/构造规则、有限 ActionSpec 与单次 B continuation；不要为预演/批准构造答案。实际请求仍在发送前绑定 wire hash。
- 单纯 JSON `approved=true`、正预算、approval_ref、已有 key 或 GitHub/main 授权不能解锁。可信人类回复由执行本任务的 agent 核对范围后记录为操作许可；CLI 同时要求显式执行动作及完全匹配的本地许可记录。不要建设签名服务，也不要声称本机文件抵御恶意管理员。
- 同一许可绑定唯一 authority、ledger 和 episode 队列。复制/换库、重复 invocation、重启或新 Worker 不能重新花一份批准。
- 授权过期、撤回/stop_requested、实现/quote/config 不一致、已有 pending/unknown、预算不足都在启动/发送前拒绝。reserve 和 sending **分别复核**；记录 UTC 决策时间/有效期供离线核验。当前本地时间不是第三方可信时间戳。
- 只有确认已完成且本地发送前条件满足后，才解析指定 credential reference；读不到时零请求退出，不扫描备用变量/配置/账户。

### 凭据、传输和停止规则

- 延用受控 stdin → SDK 显式 env 注入内存，真实 key 不进入 CLI 参数、host-config、profile、SQLite、native/诊断日志或归档；预算 helper 不带 key。
- 本机假 key 测试与 live key 解析要有明确模式区分，不能只去掉 ACTIO_FAKE_ 前缀检查就开放 live。
- 新解析入口和日志路径补 fake sentinel 验收，覆盖异常与分段诊断输出；只能假凭据测试。检测到落盘先修并保留失败证据，不事后删日志冒充无泄漏。
- 精确 HTTPS URL、正常 TLS、禁 redirect、禁环境 proxy/provider fallback。官方 serializer/SSE translator 保持；不新写 provider HTTP solver。
- trusted profile 所有实际发送均经过现有持久 gate。global fetch wrapper 不被描述成恶意插件沙箱。
- 查验响应 id/model 的有限允许值及官方 raw/native 映射；只在批准前有依据地设置 allowlist。第一请求返回未知型号/缺 identity 就记录并冻结，不能自动学习 allowlist 后补跑。
- 检查 64 输出 token 与 adapter event/chunk 上限是否相容；若需修改，批准前以本机可解释边界验收，保留 byte/count/time 限制。
- 预算 settled、场景成功、campaign 可继续是三种不同判断。length、unknown、协议/身份错误或停止请求都应阻止后续模型发送；可信 usage 即使能结算也不能把 run 自动解冻。
- A 原生执行完整、ActionSpec 合法、账务可信且无停止条件后才能发 B；否则 B 为 not_run。已发生世界效果保留。任务合法失败可以作为完整失败样本，不补答案/反复尝试。

## 5. S2：补 live 证据合同与本机验收

现有 campaign 的 receives 是本机服务日志。为 live 使用新证据版本/明确分派：

- 记录批准摘要/hash、预算事件、发送尝试、官方 SDK/native 观察、HTTP 状态/安全 response 元数据、provider request id/model/usage、估算费用、原生终态和领域效果；
- **不能生成假服务端接收日志**。无独立供应商接收证据时 supplier_received=null；本地 send_attempts、observed_responses、带 usage 请求数分开；
- 客户端发送可能没有到达供应商，发送失败仍不退款。真实供应商实际计费没有证据时保留未知，不把估算当账单、不硬编码 real_cost=0；
- 显式本机 rehearsal 的 actual/model cost 仍为 0。不同模式金额/计数不可相加；
- 注册所有计划 seat、失败、not_run、unknown，不只导出成功条目；
- 离线 verify 不读 key、不发网络、不启动 Worker/evaluator，核对批准/quote/time/config/authority/episode 与账务的绑定；
- 保存原始事实语义，不能为脱敏重写已封存事实。预先不采集 Authorization；若发现敏感输出，阻断公开发布该材料，仅提交安全摘要并说明限制。

新增本机验收只覆盖这些变化，不再重新铺一套通用 fixture：

| 项目 | 核心行为 |
|---|---|
| 人类许可 | 未批/过期/不匹配/仅字符串或 flag/仅 Git 授权均零发送、零真实 key 读取 |
| 执行计划 | 一份许可只允许具体 episode 的 A→B；多余 episode/seat/换身份/换 memory 拒绝 |
| 最终发送检查 | reserve 后批准过期/stop 或合同改变时发送拒绝，资格不能重用；时间事件可离线核验 |
| 成本与未知 | 最后一次/最后金额争抢受控；unknown 阻断；超限 usage 保留异常、不补零、不退款 |
| 生命周期 | 入口到实际 SDK/TS/Concordia 能跑完假服务成功；异常仍清理 Job/服务；不实现自动恢复 |
| 停止 | A 协议异常/length/未知时 B not_run；任务结果与费用结果独立 |
| 凭据 | 新 resolver 仅指定引用、无回退、无磁盘/日志泄漏、helper 不继承 |
| 证据 | live 形状的本机测试证据标注 simulation；无假 supplier receives；估算/实际账单区分 |
| 回归 | 修改范围相关的 task/runtime/budget/transport/验证和凭据测试；固定 C0/C1/C2A.1/C2B0 reader 验证历史 |

C2B0 四个 sample 用固定受信 **f65045a** reader；C2A.1 固定 b086cba，C0/C1 原 SHA。artifact 不可选择代码版本。固定旧文件/失败/manifest 不改。新阶段 source pin 改变后，不能为旧记录通过而删除校验。

构建、依赖准备和带紧 deadline 的真实 runtime suites 顺序执行，避免争用；这只是减少干扰，不能声称已证明旧失败根因。保存全部失败与命令实际 argv。最终干净安装、源码/安装一致、pip check、公开 CLI 验收及本轮全部 Job/端口清理通过后，停止扩大测试。

## 6. S3：先交付具体批准包并发布 main

交付 `docs/validation/phase1c2b1/`：

- 合同/复用来源、实现说明、结果、Gate、evidence_manifest、CLI；
- 单 episode 的 **未批准** operation proposal，含具体任务/spec/memory/quote/code hash、预计发送上限、每次 reserve 与全程预算、计价假设与停止规则；
- plan/preflight、默认拒绝、本机 rehearsal、只读 verify 的可复制命令；尚未获准的真实 execute 命令必须明确标注为“仅批准后执行”；
- 逐次本机与外部计数、失败、清理和归档 hash，README 当前入口。

准备完成后的状态可以是 `local_execution_engineering=CONDITIONAL_GO`、`live=AWAITING_APPROVAL`；provider_compatibility/billing_reconciliation 仍 UNVERIFIED，真实请求/费用 0。把已验证准备成果提交、推送任务分支与 main，确认远端一致。

**随后才向用户展示一份具体的首次调用确认**，包括：

- 运行目标、候选模型和精确 URL；
- compatible 1 episode / 最多 2 次发送，包含所有诊断，无 retry；
- 最终批准对象 hash、报价窗口及批准期限；
- 单次与总保守费用测算，建议实际本地预算 1 USD（或最终有依据的其他提案），并明确这不是供应商绝对计费保证；
- 未核实的上界/价格/额外费用假设，请求明确接受或选择继续零调用；
- credential reference 与不提供 secret 到聊天的说明；
- 首个 unknown/协议错误/停止/上限触发即停，账单仍需单独核对。

说明需要确认的来源是**用户 2026-10-09 在审阅会话明确要求首次真实调用前再确认**，以及尚未授权本次具体费用；不是 Git push 需要重新批准。若有异步提问工具可使用。没有回复就结束在准备完成/待批准，不持续空等，不把时间经过当成批准。

## 7. S4：仅在获得上述确认后执行

核对回复确实批准具体 model/数据/请求数/预算/残余假设。如果回复修改参数，重新冻结并核对范围；实质扩大范围再次确认。最终合同/报价在等待期间过期则先复查，不能沿用旧批准。

只在批准后读取指定凭据并运行同一冻结版本。首 seat A 即唯一连接检查；若 A 的传输、身份、终态、账务任一异常立即停止，不额外 ping provider，不 retry。满足 continuation 条件才发 B。所有尝试共享一个已批准 authority/账本，完整记录 sending 与可观察响应的区别。

如果用户选择继续零调用、凭据缺失、上界假设不被接受或技术条件不满足，保留已交付工程与具体 BLOCKED 原因；不换 provider、不静默降低安全边界、不扩大模型调用数。

执行后记录实际观察：provider 请求/响应、raw/native usage、估算、供应商实际账单是否可核对、任务结果与未运行 seat、清理。不要登录用户账单后台或读取其他无关数据；无账单证据继续 UNVERIFIED。失败也是应交付结果。

只公开合成输入及经过检查的必要输出/安全元数据；密钥、Authorization、账户信息不进 Git。完成增量检查，再 commit、普通 push 任务分支，安全合入并 push main，核对远端 SHA。停止于这一 episode，不自动冲突卡、第二 episode、judge、人工校准或演化阶段。

## 8. 最终报告

中文简明报告必须分开“入口工程完成”“是否有人类批准”“是否真正执行”“实测兼容范围”“实际账单是否核对”。

包含：各 Gate、版本/quote/授权对象 hash、测试及未验证范围、本机/真实 send_attempts 与 observed_responses 分开计数、provider received 未知情况、估算/预留/实际账单区分、失败与 not_run、Job/服务/端口清理、GitHub main 和任务提交链接、结果/manifest/CLI/批准包入口。

没有首次真实调用确认时，明确 **准备已完成并推送 main，等待用户批准；真实调用 0**。收到确认并做完允许的运行后，报告实际结果及停止点，不能把一次 smoke 升格为研究效度。
