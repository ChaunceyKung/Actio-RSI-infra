# Codex 执行 Prompt：Phase 1C2B0 真实 solver 接入就绪（零外部调用）

在 Actio-RSI-infra 完成 **Phase 1C2B0：真实 solver 接入就绪**。承接已验证的官方 Chat Completions、无预置答案双 seat、持久预算与离线对账，补齐真实计价合同、凭据注入、分层超时、预演和默认关闭的执行入口，完成本机验收并提交、推送 GitHub。

这是执行任务，不要只交一份计划；本轮真实模型请求、外部 provider 请求和真实费用仍为 **0**。完成可验证的准备工作后停止，不自动执行 C2B1。

## 0. 起点、持续授权与禁止扩大范围

- 仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
- 已验证产品基线：**`b086cbae97fcebd5c818dce611a0c2a331380cb1`**，分支 `phase1c2a1-chat-completions-budget`。
- 交接分支：`docs/phase1c2a1-review-live-readiness`；推荐新执行分支：`phase1c2b0-solver-live-readiness`。
- 先读 AGENTS.md 和适用规则、检查 git status/remote。fetch 后核对远端交接分支包含 b086cba，并记录实际交接 HEAD；从它创建执行分支。已有同任务工作先检查再继续。保护无关修改；不要从仍停在 C1 的 main 直接开工，不 reset 覆盖用户工作。
- **每轮完成并验证后，commit → 普通 push 当前任务分支到 origin → 核对远端 SHA 等于本地 HEAD。** 这是用户持续授权，无需再次问是否 push。NO_GO/BLOCKED 交付也要提交推送真实材料。不 force push，不默认合并/推 main，不部署。
- Windows x64、Python 3.12、DSH SDK/runtime `0.1.5rc1`、exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`、Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db` 保持。使用隔离短路径、新 run/spec/数据库，保留历史 pins。
- 允许读取公开 GitHub/供应商文档、准备锁定依赖、使用本机受控服务与假凭据。**不读取实际 secret、不继承环境 provider/代理回退、不请求模型列表/鉴权/余额等外部 API，不调用 live、不产生费用。**
- 不升级 DSH、不装新版 Messages 插件、不换 Strands、不自写第二 solver loop、不做通用多供应商网关。保持独立 Python Control Plane → 官方 SDK → DSH TS Worker → 真实 Concordia Engine。
- 二进制源码映射和完整控制进程恢复仍未证明；不要把解决这两项变成此次准备 slice 的新增工程目标，也不能宣称已经解决。

## 1. 先读取并核对现有资产

必读：

1. `docs/reviews/phase1c2a1_review_and_live_readiness_plan.md`、`phase1c2a1_review_evidence.json`。
2. `docs/validation/phase1c2a1/` 的 contract/results/gate/usage/reuse/budget、manifest、`c2b_connection_fields.json` 和三个公开 sample。
3. `src/actio/transport_contract.py`、`transport.py`、`plugins/transport.mjs`、`budget.py`、`transport_campaign.py`、preflight/runtime/host/supervisor，以及 task_contract/scenarios/terminal/verify/evaluation 的相关分派。
4. `tests/test_transport.py`、`test_budget.py`、`test_transport_config.py`、`chat_stub.py`，相应 smoke/release/legacy 脚本。
5. 前轮 Prompt 仅用于历史事实；本 Prompt 的阶段、授权和协议要求优先。

准确承接：

- 59 组通过是本机工程；正式批次 49 sending / 48 receives；整阶段 190 本机 receives，真实模型和真实费用 0。
- 同账本只允许一个尚未结清的 reserved/sending/unknown；任何未知占额均阻断后续发送。Worker 中断已经验证，完整 controller 恢复未做。
- 当前 `pilot-config.v3`/`chat-completions.v1` 是 **loopback-only**，MODEL 是合成标识；不得通过替换一个 URL 直接把原模式变成 live。
- 旧 v2 Messages 失败、所有失败/中间记录和原 manifest 保留。不要重封旧样例以适配新源码。
- 本轮审阅额外通过 8 个配置测试、3 个 sample、C0 12 records 和 C1 22 records；不把它们计为新模型实验或研究单位。

## 2. S0：明确一个候选 provider 合同

先复查官方公开文档并记录 URL、访问时间、必要摘录与 hash：

- https://api-docs.deepseek.com/
- https://api-docs.deepseek.com/quick_start/pricing/
- https://api-docs.deepseek.com/api/create-chat-completion/

审阅时的候选是官方 **`deepseek-flash`**，base URL **`https://api.deepseek.com`**，实际 path **`/chat/completions`**，纯文本、`thinking.type=disabled`、无 tools。这只是本轮有依据的设计候选，**不是用户的模型选择或费用授权**。

2026-10-08 的官方页面说明旧名 `deepseek-v4-flash` 已转向 DeepSeek-V4.1-Flash；Flash 峰值输入 cache hit $0.006 / 1M、cache miss $0.30 / 1M、输出 $1.20 / 1M，另有谷值价格。下一次不能盲目继承这些价格或把 alias 当不可变模型版本。若页面发生变化，冻结实际查到的合同，记录差异；不探索一批无关 provider。

继续复用固定官方源码 tag：
`deepseek-ai/deepseek-harness` 的 `dsh-v0.1.5-rc.1` → `183f08e9c6dde7e36cd2318eaee70b0da08fb35e`。按需核对 llm-deepseek adapter/serialize/translate/sse、sdk-minimal profile、SDK env 支持。不把较新本地参考 checkout 当作固定 binary 的协议依据。官方 serializer/SSE translator 不重写。

交付一个版本化候选合同，至少绑定：

- provider、请求 model、endpoint 的精确 origin/path/method、protocol、profile/依赖 pin；
- alias/供应商版本限制，响应 model/request ID 的记录与允许差异策略；不能保证固定权重时明确写 unproven；
- 仅两个 authored 排程卡、两 seat、顺序两步、合成角色与私有约束；GM deterministic、judge/retries/other disabled；
- max_tokens（优先沿用 64；必要调整需明示）、thinking、输入大小、响应大小、分层超时；
- calls/input/output/cost 总上限、币种与整数精度、报价来源/有效性、缓存和附加费用口径；
- credential reference，**没有 secret 值**；
- 请求/合同 hash、一次人工批准对象的范围、有效期限、未知冻结和停止条件。

默认批准为空、执行预算为 0。可单独提供非执行的预算测算输入，不能把“建议额度”赋值成“批准额度”。未来 live schema 采用新版本；旧 v2/v3 不重解释。若官方资料缺少必要上界或版本信息，在批准包列明未决项。

## 3. S1：把合成账务扩展为有依据的费用合同

复用现有 Ledger、一次性 attempt、SQLite 原子 reserve/sending、source/wire 绑定与前缀重放。新数据库或明确版本迁移路径，不原位改历史实验库。不得新建第二套世界状态或观测系统。

### 3.1 明确四类量

分别报告：

1. 本系统发送尝试及一次性资格；
2. 可信 provider usage；
3. 依据冻结报价计算的估算费用与保守预留；
4. 实际供应商账单（没有实测证据时为未核对，不能伪造 0）。

原 `cost_minor = prompt + output` 只适用于 SYNTHETIC。新费用使用整数最小单位或整数分子/分母，写清币种、单位、每 1M token 换算和向上取整规则；不使用二进制浮点。

预算检查使用保守 reserve，结算使用验证后的 usage 和冻结报价。prompt 含 cache hit，不重复计数；cache hit/miss 按对应费率计算，reasoning 若已含于 completion 不再加一次。缺失缓存明细不得擅自用优惠价；只允许有合同依据的保守估算，并标明依据。

### 3.2 输入上界不能靠猜

65,536 bytes、字符数或不匹配模型的 tokenizer 不是已证明的真实计费 token 上界。优先查验匹配供应商模型的计数方法；没有时，评估使用官方约束的**最大可计费输入/上下文上界**，加显式最大输出，按缓存未命中/峰值价格预留。

必须说明文档单位及精确数值依据；“1M”的转换不能默默猜测。保守预留可高估并导致小预算不足一次请求，preflight 要显示原因；不能为了执行而缩小未知上界。峰谷切换、报价变化及附加费用若无法覆盖则阻断。基于供应商合同的上界不能被称为供应商账单的绝对硬保证。

### 3.3 保留失败与并发保证

- reserve 在真正发送前持久提交；资格绑定 campaign/run/op/seat/model/endpoint/config/profile/实际 wire hash。任何改动都使旧批准/票据失效。
- 并发争抢调用额度和**金额额度**分别测试；资格一次性消费，重启/重试/新 Worker 不能重复发送。
- reserved/sending/unknown 均占额并阻断后续请求；不得以“进程已退出”“没有拿到 usage”或“查不到服务接收”作为退款证明。
- 缺失/非法/矛盾/超过 reserve 的 usage 保留原始观察、冻结 campaign 并记异常；不截断为上限、不补零、不自动扩额或继续第二 seat。
- length/其他非 stop finish、任务非法输出、网络失败、账务状态独立处理。完整可核验 usage 是否可结算需按明确合同验证；账务结算不意味着任务成功。
- 不实现自动恢复或自动再执行。异常后的只读报告可用；新的预算库不得成为绕过同一未结算授权的路径。

## 4. S2：接入执行路径的最小改造

默认关闭 live。本轮只以本机服务和假凭据验证未来执行所需的共同路径，不连接真实 endpoint。

### 4.1 凭据注入与本机文件

当前假 key 写在 `host-config.json` 的方案不能照搬真实 key。设计并实现可复用的显式引用/内存注入：

- preflight/plan/verify 不解析 secret 引用，不扫用户环境，不创建 SDK client/Worker。
- 只有未来已明确批准、合同 hash/额度/期限有效、其他 preflight 通过后，执行入口才可解析**指定** credential reference。当前本轮禁止实际解析。
- 凭据不得进入命令行、磁盘配置、manifest、日志、SQLite、原始归档、导出包或 Git；通过受控进程环境/IPC 注入内存即可，不引入凭据平台。
- clean_env 仍按最小集合构造；SDK/TS 所需的明确 key 不传播给不需要 key 的预算 IPC 子进程。禁止 ambient provider、代理、模型或 endpoint 回退。
- 用明显的假 secret sentinel，验证正常、400/401、异常退出、stderr 和归档等路径均无 sentinel 落盘。若上游不可避免泄露，先定位修复；不能用事后删除日志充当合格。

### 4.2 endpoint、官方 adapter 与 profile

- 复用 DSH 官方 adapter/loop、真实 Concordia 和现有发送 gate；不以自建 HTTP solver 替换它。
- live 合同只接受明确 HTTPS origin/path，禁止 redirect；使用正常 TLS 验证，不设置全局关闭证书校验。
- 本机测试 URL/假 key 与未来 live 有明确不同模式和 pin；测试例外不能被 live config 激活。若需本机 TLS，只使用局部测试信任链。
- 冻结 trusted profile/inventory，关闭 retry/title/compaction/tools/MCP/Files/image 等额外 producer。global fetch gate 的范围仍是固定可信 profile，不能声称隔离任意恶意插件。
- 配置/参数/实际 wire 必须一致；校验失败在发送前拒绝。HTTP 层实际计数验证每 seat 最多一次，不能拿 hook 次数当发送数。

### 4.3 分层超时

当前 idle 1.5 秒、fetch 3 秒、SDK request 5 秒、controller result 15 秒仅用于 stub。为候选 live 增加有限且相容的 deadline 合同，逐项查清 SDK request timeout 约束的是 RPC 收据还是整次生成。

至少覆盖启动、RPC/首响应、流 idle、整请求、controller 等待及 drain/close；controller 的期限要容纳内层期限和清理余量，外层总期限仍有界。不要只增大一个 timer，也不要取消超时。

用本机服务验证超过旧 3 秒但低于新期限的成功响应、无首字节/流中断/不终止响应的超时，检查每次实际发送数、账务冻结和进程清理。沿用 bounded audit capture，避免 consumer finish 与 capture 竞态；不因读取审计副本改变已观察事实。

## 5. S3：预演、批准包与只读 campaign

提供可复制、公开 CLI；名称可按仓库惯例决定，不必建立新的框架：

- **plan/preflight**：零凭据读取、零网络、零 Worker。校验候选合同、冻结输入/报价/limits，输出拟发 wire 的语义绑定、所需 reserve、授权缺失项、合同 hash。没有实际 op/发送时标明 proposal，不能伪造执行记录。
- **本机 rehearsal**：走与未来执行相同的核心合同/计价/gate 逻辑，仅受控 loopback + 假 key；记录模拟 usage/估算金额，真实费用始终 0。不能用原 SYNTHETIC 公式假装验证真实币种逻辑。
- **未来 execute**：默认拒绝。必须要求独立、显式的操作批准与完全匹配合同，批准引用只是审计信息，单靠 JSON 的 `approved=true`、非零金额、现成 credential 或“用户要求 push”都不能解锁。本轮不执行该入口的 live 分支；不开发签名/审批服务。
- **verify/export**：只读，不读取 secret、不创建 Worker/evaluator、不发网络请求，复用不可变 artifact/campaign 机制。

live 报告不能硬编码 real_cost=0 或 real_model_requests=0；根据模式和证据生成。客户端 sending 不等于服务端 received；无独立供应商接收凭据时保留 unknown/null。响应 request ID 可用于未来对账，但不冒充服务端完整访问日志。估算费用已结算与实际账单已验证分开。

历史 schema 不混淆：C2A.1 用 b086cba 的固定受信 reader 验证三个公开 sample，C0/C1 继续固定原 SHA。artifact 不能指定要运行的代码版本；新模式 reader 遇到未知协议拒绝。保留所有失败、not_run、unknown 的登记与分母。

批准包应是可审阅的具体结果，至少包括候选连接字段、合成数据范围、拟运行 1 或 2 个 episode、最多 2 或 4 次请求、单次与全程保守费用测算、timeout、未知冻结策略、credential reference、有效期、合同 hash，以及未解决项。无新增人类授权时保持未批准，不需要等待用户才能交付 C2B0。

## 6. 验收要求

按行为交付，测试数量不是目标；避免无限扩展 fixture 矩阵。

| 验收面 | 必需行为 |
|---|---|
| 默认关闭 | 0 预算、缺批准、过期/不匹配合同、只填批准字符串或现成 key 均无外部请求；preflight 不读 secret |
| 版本与模型 | v2/v3 原语义保留；新 schema 不把合成模型当 live；alias/quote 变化会使旧批准失效 |
| 计价 | cache hit/miss、单位换算、向上取整、峰值 reserve、过期报价、额度不足；实算与预留可独立复核 |
| 输入上界 | 有来源的界限或明确 BLOCKED；无效 tokenizer/bytes 假设不能通过 |
| 并发/幂等 | 两独立控制进程争抢最后调用和最后金额，只有允许的真实本机请求发生；重复资格不发送 |
| 未知账务 | 缺/坏/超限 usage、发送前后中断、pending 重开仍占额并阻断；不得换库绕过 |
| 原生协议 | 固定 SDK/TS adapter 的 attached usage + DONE 成功；400/401、429/500、延迟/断流/length 按实际语义记录，无隐式 retry |
| 双 seat | actor wire 无预置答案、对手私有数据或 judge 内容；A 实际行动到 B；partial 保留已发生世界效果 |
| 凭据 | 假 secret 只存在必要内存/进程；配置、helper 环境、输出/归档均不含 sentinel；清理可证 |
| 对账 | 新币种/quote/attempt/归属/分母/估算和未知语义绑定；不依赖伪造的供应商 received |
| 交付 | 干净安装、CLI plan/preflight/本机 rehearsal/verify、相关 runtime 与历史回归、pip check；全部本轮 Job/服务/端口清理 |

先做有必要的局部测试，再跑修改范围内回归；不要为了漂亮数字重复运行整套实验。源码与实际安装包一致性要核对，构建安装顺序执行，避免多个环境争用 build/lib。每次本机实验新增计数和失败记录，不混入 C2A.1 历史 190 接收。

若固定官方 adapter 或安全的凭据路径出现真实阻塞，先完成最小定位和窄修复；只有证明无法满足必要条件才 NO_GO，并给最小备选建议。不静默升级或转到第二套 runtime。

## 7. 交付、Gate、推送与停止点

交付 `docs/validation/phase1c2b0/`，包含合同与上游来源、结果、Gate、复现命令、预算/凭据/超时说明、批准包、evidence_manifest；更新 README 当前入口。新 manifest 绑定最终源码/安装内容、实际命令、所有失败与本机请求计数、清理记录和必要归档 hash。只公开合成样例、必要来源摘录与脱敏摘要，不发布真实数据或 key。

Gate 至少分列：

- `local_readiness_engineering`：必要本机验收通过才 CONDITIONAL_GO；
- `provider_compatibility`：UNVERIFIED，未调用供应商；
- `live_authorization`、`live_execution`：BLOCKED，本 Prompt 不提供费用授权；
- `billing_reconciliation`：UNVERIFIED；
- `human_calibration`、`judge`、`research_validity`、`evolution_promotion`：BLOCKED；
- `binary_source_mapping`、`full_controller_recovery`：沿用 unproven/unsupported。

缺少用户 provider/model/实际预算授权不妨碍完成可复核的 C2B0；只在相应执行边界停下，不把整轮只写成“等待用户”。也不把本机准备完成叫作 live 已就绪/已验证。

后续 C2B1 的建议范围仅写进批准包，不执行：1–2 个 baseline episode、最多 2–4 次 solver 请求、全部 diagnostic 也计入总额度，首个 seat 可同时充当连接检查，不另开免记账探针。未知费用/首个协议错误/任何上限到达即停止，无自动重试和补跑。任务未达成可成为合法失败样本，不能为了成功绕过 ActionSpec 或补预置答案。一次连接 smoke 不产生研究晋升依据。

完成检查后，只 stage 本轮文件，commit 并执行普通：
`git push -u origin phase1c2b0-solver-live-readiness`
（继续已有同任务分支时用实际名称）。核对 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/<branch>` 完全一致，并报告工作树状态。推送失败保留本地提交与具体原因，不 force push、不声称已到远端。

最终中文报告：各 Gate、实现与未验证边界、配置/协议/报价版本、本轮本机发送/接收与真实请求/费用分别计数、失败保留与清理状态、GitHub 分支/提交链接、结果/manifest/CLI/批准包入口。**停止于 C2B0，未推 main、未部署、未进入 C2B1。**
