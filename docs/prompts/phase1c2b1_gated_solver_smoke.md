# Codex 执行 Prompt：Phase 1C2B1 TokenKey 多模型真实 solver 闭环

在 Actio-RSI-infra 完成 **Phase 1C2B1**：接入用户指定的 TokenKey OpenAI-compatible 服务，复用官方 DSH 与真实 Concordia，完成真实双 seat 场景、必要诊断和模型适用性记录，然后提交并推送 main。当前 session 的目标是实施，不要只重写一份准备方案。

用户 2026-10-09 最新要求：“check 我们的 api key 是否可用……api key 不设置预算上限，以推进项目为准”，并指定了凭据文件、TokenKey base URL 和 gpt-5.6 示例。**项目必要的凭据读取、模型验证、solver 基线和有依据的诊断已获授权；无需再次等待首次调用或固定费用批准。** 这覆盖旧 Prompt 的零预算、1 USD、严格两次请求和 AWAITING_APPROVAL 门槛。

无金额上限不等于无限循环。按 C2B1 里程碑推进，保留请求级长度/期限、记账、幂等、隐私和进程清理。研究晋升、真人校准、部署及供应商账户修改仍不在本轮范围。

## 0. 已验证连接与起点

- 仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
- 产品基线：`f65045a11d1a4728b98b5564623e4827365f91c8`；前轮审阅：`d98591acbad61fbe67adc596e35b11c2e6c429a7`。从包含本 Prompt 最新修订的 origin/main 开始，记录实际 HEAD 并核对基线祖先关系。
- 用户明确的服务：**`https://api.tokenkey.dev/v1`**；Chat Completions 为 **`https://api.tokenkey.dev/v1/chat/completions`**。不要追加第二个 /v1，不将 key 发到 api.openai.com、api.deepseek.com 或其他猜测域名。
- 用户源凭据文件：`D:\调研\CausalEngine\api_key\token_key.txt`。
- 项目副本：**`.local/credentials/token_key.txt`**，已复制并确认被 Git 忽略。只在内存读取；可注入专用 `ACTIO_SOLVER_KEY`，不要写入系统全局环境、配置或日志。副本不存在时从指定源文件复制，已有不同凭据时先核对，不覆盖不明内容。
- Key 检查与模型探索见 `docs/reviews/phase1c2b1_key_check_and_prompt_update.md` 和 `phase1c2b1_tokenkey_evidence.json`。它是直接 API 诊断，不是 DSH/Concordia 完整运行。
- 最新实测：GET /models 鉴权成功，返回 109 个标识；gpt-5.6 短 completion 与 SSE/usage/DONE 成功。不要因为列表可见就认为每个模型可调用：gemini-3.1-pro 返回 HTTP 400 unsupported_model。
- 当前主选 **gpt-5.6**；跨模型对照候选 **claude-sonnet-4-6**；gpt-5.6-luna、qwen3.8-flash 可作为后续吞吐/多样性候选。deepseek-flash 已见跨请求返回型号变化和一次 SSE ReadTimeout，先调查路由稳定性，不能默认为最稳主选。

先读 AGENTS.md、git status/remote 和适用规则；保护用户无关修改，已有同任务分支先检查再继续。推荐分支 `phase1c2b1-gated-solver-smoke`。每轮验证后 commit → 普通 push 任务分支 → 安全合入 main → 普通 push origin/main → 核对远端 SHA。无分叉时快进，有并发更新先整合和检查。不 force push、不覆盖他人工作；BLOCKED/NO_GO 的已完成材料也交付。不要再次询问是否 push main。

## 1. 保持架构，先查官方可复用适配器

固定 Windows x64、Python 3.12、DSH SDK/runtime `0.1.5rc1`，exe hash `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`，Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。Python Control Plane → 官方 SDK → DSH TS loop → Concordia Engine 保持。

必读 C2B0 合同/结果/用法/manifest/费用说明、readiness_contract/readiness、budget、transport/transport_contract/plugins/transport、host/supervisor、task_contract/scenarios/terminal/verify/transport_campaign 和对应测试。C2B0 execute 仍无条件拒绝，运行链只允许 fake/rehearsal，真实入口尚需实现。

已查到固定源码 tag **dsh-v0.1.5-rc.1 → 183f08e9c6dde7e36cd2318eaee70b0da08fb35e** 中存在官方 **`@deepseek-ai/dsh-llm-pi-ai`**。README 明确支持多 provider 与手工声明的 OpenAI-compatible gateway，配置包含 providers、apiKeyEnv、api=openai-completions、baseURL、models、compat、retryPolicy。源码与 hash 见新审阅证据；本机摘录在 `.local/tokenkey-check-20261009/`。

按以下顺序复用：

1. 先核对该固定 tag 的 llm-pi-ai README、配置 catalog/types、入口及 sdk-minimal profile，查清必需服务。先用假 key/loopback 验证当前固定 binary 能否加载并实际选中它。
2. sdk-minimal 默认挂载 llm-deepseek，**源码包存在不等于当前 binary 已包含/可加载**。不要沿用之前 Messages 插件不存在时的错误推断。
3. 若可用，建立显式 TokenKey route，例如 provider=actio-tokenkey、api=openai-completions、baseURL=https://api.tokenkey.dev/v1、apiKeyEnv=ACTIO_SOLVER_KEY、明确少数 model entries。显式关闭所有自动 retry，README 默认可能是五次；关闭旧 llm-deepseek 路由及不适用的 DeepSeek 专有扩展/inventory producer。
4. 若 loader 缺包，记录真实错误，再评估安装/构建**同 tag 同版本官方 package 及必要依赖**。这属于有依据的最小复用，不静默升级 runtime。保留 MIT 归属和依赖闭包。
5. 只有官方固定版本路径经验证确实不可用时，提出最小 adapter 修复：复用官方协议/转换模块并保持 DSH loop。不要偷偷以 Python OpenAI SDK 完成“生产 solver”后声称 DSH 闭环完成，不建设通用多模型网关。
6. current `deepseek-official` 是旧 adapter route 标识，不代表 TokenKey/GPT 的供应商身份。新记录分别保存 gateway、adapter package/route、requested_model、response_model、upstream_identity_verified=false；不可把 TokenKey 调用标为直连官方 DeepSeek/OpenAI。

切换 adapter 后，旧 wire 固定字段、usage/finish 映射、profile/inventory 校验需要新版本分派和真实本机证据。不能只改 URL/模型名并全局放松旧检查。默认 reasoning、max_tokens/max_completion_tokens 和专有 thinking 字段逐模型核对，不从 DeepSeek 原样套给所有模型。

## 2. 新授权与费用策略

新增显式 live config/schema，保留 v2/v3/v4 及历史 limited/SYNTHETIC 语义。建议表达：

- spending_policy=uncapped_for_phase1c2b1；
- cost_limit_minor=null；
- authorization_basis=explicit_user_instruction_2026_10_09；
- credential_ref=file:.local/credentials/token_key.txt（解析到内存中的专用变量）；
- gateway、model、实际任务范围、实现 hash、运行计划和停止策略。

字段名可按仓库惯例选择。`null` 只在明确 uncapped 策略和真实用户授权同时存在时表示无金额限制；未配置、未知 schema、0、负数、NaN、Infinity 或巨大整数不能冒充该策略。不要新建暗中的总金额/总 token/两次调用限制来卡住必要诊断；每个实际批次仍必须是有限且登记清楚的任务计划。

保留 SQLite 原子 intent/reserve/sending、一次性资格、wire hash、并发与归属校验。uncapped 的 reserve 可代表在途请求登记/估算，不必为了发送先证明精确最大可计费输入；这不是删除 Ledger 或把未知费用补零。

计价规则必须改为 **TokenKey 的来源与返回值**。官方 OpenAI/DeepSeek 零售价只能作为另标来源的参考，不能冒充 TokenKey 实际账单。本次部分响应带 usage.cost，其他没有；币种/单位和完整覆盖尚未证明，记录 gateway_reported_cost_raw 与其来源，不把缺失 cost 当 0，不将浮点 cost 直接当整数 USD 入账。单位确认后使用 Decimal/明确整数精度转换。

分别记录发送尝试、可信 usage、估算/未知/网关报值、供应商实际账单。缺最新报价或精确 tokenizer 时保留 usage 并注明待估价；在已授权无金额上限模式下，不能因无法证明有限预算上界再次阻断所有 live。

不设置或修改 TokenKey 账户侧预算、余额/充值、权限或其他供应商账户。API 返回余额/配额限制时如实报告外部阻塞。

## 3. 入口、凭据与模型身份

- plan/preflight/verify 默认无网络、无 key 读取；明确 live execute 才解析指定文件并发送。
- 用户最新指令是授权依据；生成绑定当前实现/任务的执行说明，替代旧未批准的批准包。不因合同 hash 或有依据的配置修复改变而重复请求同一费用授权。
- 仅读取给定凭据，不打印值/前后缀/长度/key hash；复制前后可以在内存比较，不公开摘要。文件保持 Git ignored，公开样例不包含实际 key。
- 保留受管 stdin → SDK 显式 env 内存注入，clean_env 不继承无关 provider/proxy，helper 不带 key。明确 TokenKey route 的 apiKeyEnv，禁止 ambient OAuth/provider fallback。
- 对新 adapter/resolver 先用 fake sentinel 检查配置、native/cache、诊断/stderr、数据库、导出包及分段输出。检测泄漏先修复，保留安全失败证据，不事后删日志冒充无泄漏。
- TLS 正常验证、禁止 redirect；key 只去用户指定 origin。第三方网关的 model ID/response model 是路由标签，不能独立证明上游权重版本。
- 每个请求记录 requested_model/response_model、响应正文 response_id，以及可取得的 HTTP request_id/fingerprint；未返回的字段为 null，不编造，不将正文 id 冒充供应商请求头。本次直接诊断旧字段 request_id 实际存放正文 id，reader 必须遵循新证据里的字段说明。深度比较需要稳定 route/cohort；型号变化不能静默合并到同一独立实验单位。
- 不需要一次接入全部 109 模型。先实现 gpt-5.6，再对一个已通过直接调用的跨模型候选验证相同合同；为下一阶段保留可解释选择依据。

## 4. 真实任务计划与工程边界

先完成一个 compatible 的 A→B episode，正常后再做一个 conflict episode。GM deterministic、judge 禁用；不运行训练/演化或正式模型评审研究。准备多模型角色时只记录未来 judge 候选，不在本轮开放 judge Gate。

冻结具体 task/agent/spec/memory 与有序 episode/seat 计划。B 实际输入依赖 A 真正输出，批准的是可见性/构造规则，不是预置答案。actor payload 仅含自身合成信息、公共场景/行动历史、冻结 memory、ActionSpec；不含对手私有数据、judge 内容或测试响应计划。

单个正式 seat 只发一次模型请求，原始输出不通过“重试到合法”挑选。行动非法是观察结果；区分任务失败与基础设施失败。A 失败/不完整时 B not_run，保留已发生事实。

每请求 max output/bytes/chunks/time 保持有界。先依据模型 profile 选择足够的输出额度，记下是否包含 reasoning；本次 qwen/DeepSeek/luna 的部分 usage 含 reasoning，不能将思考 token 当额外重复费用，也不能用过小上限错误判断模型不可用。

沿用 C2B0 分层 timeout 思路，但要适配网关实测，不能机械继承官方 DeepSeek 的 6 秒首响应。记录首 headers、首 token、流 idle、总时长；本次非流式总耗时不能冒充首响应耗时。根据证据做有限调整并验收，不取消总期限。

默认关闭 SDK/provider 自动重试、title/compaction/tools/MCP/Files/image 等额外 producer。网络发送资格在 actual fetch 前核对；adapter 改变后重新证明门控仍覆盖实际请求，hook 次数不是发送数。

## 5. 未知账务与推进原则

首个 unknown、协议/身份异常或超时先停止受影响 episode，保留响应、native/usage 和已发生世界效果；不退款、不补 0、不重用原 attempt。

在用户已选择 uncapped 的条件下，历史 unknown 不应成为永久全项目死锁。确认旧 Worker 回收、定位原因后，可登记新的诊断批次继续；每次写明假设、输入变化、结束条件和与旧失败的关系。不得通过另建库抹掉累计发送/未知费用，不能重放可能有不确定外部效果的原操作。

有界处理故障：

- 401/403/402：按实际鉴权/权限/余额类型停止该路径，不能自动换账户或充值；
- 400 unsupported_model：模型列表不代表该协议可用；查服务说明/必要时选择已证可用模型，保留原失败；
- 429：遵守 Retry-After，有限等待，所有尝试记账；
- timeout/length/usage 映射：定位具体层，必要本机测试后以新 run 验证；
- 同一故障无新增证据时停止无目的请求，交付精确阻塞。无预算上限不是无限重试。

## 6. 本机验收、证据与历史兼容

重点验收真实改变：

| 面向 | 要求 |
|---|---|
| adapter | 固定官方包能加载，route/model/参数实际生效；无隐式 retry/fallback |
| uncapped | 显式策略不触发金额耗尽；未配置/伪造策略拒绝；旧有限额行为不退化 |
| 记账/幂等 | 一次性发送、并发一致、累计完整、unknown 保留，新诊断不重播 |
| 凭据 | 只去指定 origin，helper/日志/磁盘不泄漏 |
| 双 seat | 输入隔离、A→B 实际行动传递、失败/not_run/世界效果正确 |
| 协议 | raw/SSE/usage/stop/DONE 与官方 adapter/native 一致，缺失和差异显式处理 |
| 生命周期 | 分层 timeout 有界，异常后 Job/服务/端口可清理 |
| 离线 reader | 不读 key、不发网络、不启 Worker/evaluator，按新版本核对 source/wire/usage/计划 |

live 记录 sending、observed_responses、usage-bearing responses；无独立服务端日志时 supplier_received=null，不伪造本机 receives。estimated/unknown/gateway-reported/supplier-billed cost 分开。HTTP200 不直接等于任务成功或账单核对。

本机 simulation 与真实 API 诊断/正式 DSH episode 分组计数；新模型探索不是独立研究单位，不当作正式质量排名。所有失败和 not_run 保留。

C0/C1 reader 固定原 SHA，C2A.1 固定 b086cba，C2B0 固定 f65045a。artifact 不指定执行源码；旧 manifest/spec/失败保持不变。顺序构建、安装和紧 deadline 的 runtime suite，保存真实 argv。必要回归、干净安装、源码/安装一致、pip check、CLI 与清理通过后停止扩大测试。

## 7. 模型探索与选择

以本轮证据为起点，不重复全部可用性探针：

- **gpt-5.6**：用户示例模型；直接普通/流式调用与两步结构化任务均通过，优先做正式 solver 基线。
- **claude-sonnet-4-6**：两步约束任务通过，可作为跨供应商标签的对照；不能仅凭一次较低延迟宣称整体最快或更优。
- **gpt-5.6-luna**：两步通过；候选轻量/吞吐组，但需在 TokenKey 上独立量测吞吐、质量和计价，本轮曾有较长单次耗时。
- **qwen3.8-flash**：两步通过，候选另一模型族；注意 reasoning usage 与终态合同。
- **deepseek-flash**：普通调用通过但实际响应型号不同，流式诊断一次 ReadTimeout；先稳定 route/参数/期限后再纳入严格对照。
- **gemini-3.1-pro**：列表可见却在 Chat Completions 返回 unsupported_model；此路径暂不选，不能说整个 Gemini 家族或 key 无效。

上述每模型只有两个小任务或更少，不能证明广泛推理/社交能力。后续正式选型应预注册固定任务、重复次数、seed/参数、模型/路由身份、延迟/格式/约束/成本/不确定性指标，并把模型族与 gateway 路由混杂单列。本轮只完成必要接入与有限候选验证，不做大规模 benchmark 或未经校准的 live judge。

## 8. 交付与停止点

交付 `docs/validation/phase1c2b1/`：合同/用户授权依据、adapter 复用与真实加载证据、uncapped 记账语义、结果/Gate、manifest、CLI、模型选择说明、失败及清理、归档 hash。README 更新当前入口。

最终目标是 TokenKey → 官方 DSH → Concordia 的真实单/双场景闭环。直接 OpenAI SDK 成功只能作为 key/协议诊断，不满足此目标。固定 adapter 若真实受阻，先窄修复；无法解决时准确交付 NO_GO 和可复用进展，不能假冒完整集成。

真实模型请求已有发生，不能再写“所有真实请求与费用均为 0”；实际费用未知时明确未知。分别报告诊断/本机/正式运行计数、usage 完整性、gateway cost 是否有单位证据、账单未核对状态、每个 gate。继续保留 binary_source_mapping=unproven、full_controller_recovery=unsupported，judge/人工校准/研究晋升不自动开放。

只 stage 本轮安全文件，commit、普通 push 任务分支、安全合入并 push main，核对 `git rev-parse main` 与 `git ls-remote origin refs/heads/main`。密钥副本必须仍被忽略且未被跟踪；公开材料做 secret 扫描但不打印匹配内容。推送失败保留本地提交和精确原因，不强推。

最终中文报告给出 Gate、真实闭环/模型探索及其限制、请求/usage/费用账务、失败/清理、main 提交与结果/manifest/CLI 链接。停止于 C2B1，按新发现提出下一步，不无限续跑。
