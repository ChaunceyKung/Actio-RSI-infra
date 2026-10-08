# Codex 执行 Prompt：Phase 1C2A solver 传输与调用预算离线准入

请在 Actio-RSI-infra 完成 **Phase 1C2A** 的有界实现、验收、文档、提交和 GitHub 推送。先核实来源和合同，再实施。目标是让现有排程任务经过官方 DSH provider 的真实协议路径访问**本机测试服务**，移除模型可见的预置答案，并建立可复核的请求预算。此轮不执行真实模型或外部 provider 调用。

## 0. 起点、授权与发布

仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。

- 产品基线 `af0a88cfff23c22c396fd7c9ef9916f0df8cd21f`，此前 main 与 `phase1c1-task-contract-and-calibration` 都已推送至此。
- 交接分支 `docs/phase1c1-review-phase1c2a-plan`；执行分支 `phase1c2a-solver-transport-and-budget`。
- 读取 AGENTS.md 和适用目录规则，检查 git status/remote，保护无关修改。fetch origin，核对产品基线是交接分支祖先，从已核对的交接远端 HEAD 开始，并记录完整 SHA；目标分支已有工作则先核实再继续，不 reset 或覆盖。不能默默从其他起点开工。
- **用户持续授权每轮完成验证后 commit、普通 push 当前任务分支到 origin、核对远端 SHA。** 无需再次问是否推送。本轮不默认合并或推 main，不 force push，不部署。若网络/鉴权/并发更新阻塞，保留本地提交并报告精确原因，不宣称已推送。
- 真实模型费用、真实模型请求均为 **0**；不得访问外部模型端点，包括免费端点，不读取已有 provider secret/账号登录态。允许公开源码/文档查验、锁定依赖准备、GitHub 发布和本机临时 HTTP 服务测试。
- 实测平台继续 Windows x64 / Python 3.12、DSH SDK/runtime `0.1.5rc1`、Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`、隔离短路径。源码与二进制构建映射仍未证；不要静默升级版本来获得新功能。

本轮普通实现和可逆检查自行推进；不要因为缺 live 授权或人工标签而停掉已经授权的离线任务。所有 live 入口保持 BLOCKED。停止于本阶段，不接 Raven、训练、候选晋升、第二状态权威、完整恢复、原生 fork/resume 或 semantic cancel。

## 1. 必读和验收基线

阅读：

1. `docs/reviews/phase1c1_review_and_phase1c2a_plan.md`、`phase1c1_review_evidence.json`。
2. `docs/validation/phase1c1/01_contract.md` 至 `07_reuse.md` 的相关内容及 `evidence_manifest.json`、`pilot-config.json`。
3. `src/actio/runtime.py`、`host.py`、`scenarios.py`、`task_contract.py`、`preflight.py`、`fixtures/provider.mjs`，再追读 supervisor、store、事实/终态/导出/评估/标注路径与相关测试。

C1 为 42 组历史验收 PASS；本次审阅额外重跑 14 组通过，当前 campaign 25 登记/22 请求只读核验通过，原 C0 12 记录由固定旧版再次复核。真实模型、人工标签和独立研究单位都为 0。历史 59 Jobs 已记录退出，不把历史清理说成本轮实测。

当前 `run_engine` 把 scripted `answer` 传给 DSH，fixture provider 从请求读取后返回它。新路径必须独立定义合同，不能在原 fixture 上换一个 provider/key 就宣称真实推理。

## 2. P0：修正配置并查验可复用协议路径

先修 C2R1：`preflight.py` 当前要求每个角色有正预算，导致确定性 GM、关闭重试和 other 也得填写假额度/报价。

设计明确角色模式，例如 disabled、deterministic_local、transport_stub、future_live：

- GM 固定 deterministic_local；judge、retries、other 默认 disabled，远端费用/调用上限为 0，不要求真实模型名或报价，不可携带无意义的凭据。
- 本机 stub 使用独立合成预算和测试标记；它的配置完整不等于获得 live 授权。
- 未来远端 solver 配置必须显式 provider/精确 model/protocol/data scope、授权引用、calls/input/output tokens/总费用/币种/报价版本。金额使用整数最小单位或明确精度的十进制定点表示；不把二进制 float 当费用权威。
- `configuration_valid`、`transport_validated`、`live_authorized`、`live_ready` 独立。零预算、伪造批准字符串、未授权 endpoint 或只有正数预算均不能开启 live；此轮 live 无执行路径。
- 严格检查类型、重复 JSON key、未知字段、有限数值和角色之间约束；返回可解释错误，不补默认付费配置。

窄查验本地与 GitHub 固定 DSH 源码：

`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\01_deepseek-harness\repo`

SHA `5badb15009ae1756c3afe0ae0cef1faafc290ccc`；GitHub `deepseek-ai/deepseek-harness`。重点：`packages/llm/llm-deepseek`、`llm-deepseek-api-key`、`llm`、`llm-retry`、`packages/bundle/sdk-minimal`，及 `llm-deepseek/tests/mock-server.ts`、stream/transport 测试。

优先复用官方 Messages-compatible adapter、请求序列化/SSE/usage 处理和已有 mock 行为。该源码的 `baseURL` 不是任意 Chat Completions 接口；默认 retryPolicy 也不能当作禁止重试。记录 URL、SHA、许可、抽取/适配范围与实际安装包可用性。参考 checkout 只读，不 pull 改写；不执行上游 e2e 中的真实网络调用。

用发行物 `0.1.5rc1` 做最小真实 adapter→loopback 探针，确认 config、路由名、协议、关闭 retry/title/compaction 等能力。若发行物不支持，应在必要定位后给出 NO_GO/精确差异及最小备选，不无限试错或静默升级。通过后继续完整实现；不重写 DSH loop/协议栈或另起 Python solver。

## 3. P1：没有预置答案的 actor payload 与本机传输

只使用现有两个任务卡、两 seat、固定两步。不要扩大任务族/自由多轮/模型平台。

新增版本化的 transport_stub 执行合同，保留旧 fixture 合同和运行入口：

- actor 输入包含正确角色、公共场景、自己的目标/私有约束/初始关系、实际公共行动历史、冻结 memory 和完整 ActionSpec，以及必要的非评分关联标识。
- 实际模型可见请求不得包含 `answer`、scripted_actions、测试响应计划、期望任务结果、对手私有信息、GM 私有内容或 judge rubric/历史评分。不能只删字段名而把答案放到另一段文本。
- 请求内容与 manifest→dispatch→native→实际 wire 请求可对应；SSE 返回的行动进入原事实与领域链。成功/合法未达成/非法/partial 仍有原语义。
- 测试返回计划只留在本机服务的测试控制侧。服务不能从 actor 请求读取一个预置答案再原样回显；服务端固定响应仍明确是 stub，不是模型推理。
- 使用官方 Python SDK → 官方 DSH TS Worker → 官方 provider adapter → loopback HTTP/SSE。不得 patch 掉 SDK/adapter 核心序列化后宣称该协议已实测。
- 服务仅绑定本机地址和临时端口，只使用任务创建的假 credential。禁用环境 endpoint/代理/真实 credential 回退和远端重定向；不枚举用户 secret。限制路径为实际协议所需，拒绝 Files、工具、上传和其他未启用调用。
- 新 profile 不加载不需要的 MCP/工具/后台任务；不改变旧只读助手 fixture 的合同。题名生成、压缩、retry、恢复等任何额外调用要被禁用并由实际请求计数确认。

新的输入与 mode 需要在线终态、离线 verifier 和 evaluator admission 都认识。不要让旧 verifier 的 fixture-only 判断被普遍放宽；无法识别的模式必须明确拒绝。代码 pins 变化使用新身份/spec 和新实验库，不刷新旧身份。

## 4. P2：每次实际请求的有界预算和证据

先选并记录最终调用检查位于哪个已验证 DSH seam：Python 持有实验授权/冻结额度，TS 在每次真实 provider attempt 前执行检查。只在任务开始处检查 budget 不够；DSH 可能产生多个 provider attempt。

采用最小本地单机账本，与 campaign/run/operation/attempt/配置 hash 明确关联。优先新实验库/独立预算表，旧产品 DB 不原位迁移；若需新增 schema，先写新库创建与版本说明，不建设通用计费平台。

必须实现和验证：

1. **发送前持久 reserve**：冻结的请求 hash、可用 calls、输入估算上界/输出硬上限、合成价格版本、总费用额度一起核对；并发竞争最后额度只有一个请求获得资格。重用 attempt ID 不再次发送。
2. **attempt 与完成证据**：允许、开始发送、本机服务实际接收、响应终态、usage/缺失、领域结果分开记录，使用可关联 ID；关联元数据不得污染模型上下文。服务计数不能独自替代控制面事实，控制面也不能只靠自报“0 请求”。
3. **settle/unknown**：仅对可信且完整的终态结算；断流/发送后失联/usage 缺失/进程崩溃保留 unknown 或保守预留，不把未知当零费用，不自动释放后重试。能证明未发送的 reserve 可按明确规则释放，保留原因。
4. **无隐式重试**：HTTP 429/500、空响应、超时等没有第二次服务接收；所有额外 provider 尝试仍受最终门控，不仅依赖 SDK timeout。超时停止进程不等于远端取消；本轮只对本机服务证明清理。
5. **上限与误差**：请求数硬上限必须真实成立。token/费用必须区分 provider usage、合成 usage、保守估算与未知。没有能证明的 tokenizer/收费上界时，不声称真实费用硬封顶；保留未来 live BLOCKED。

合成费用、合成 token 只用来验证算账和状态流；真实费用=0。本地 HTTP 请求数按实际值报告。单个/总 deadline、响应字节数、SSE event 数量、stdout/journal 大小和受管 Job 清理沿用现有有界机制。

## 5. P3：验收、复核与版本路径

本轮不接 live judge。新路径做确定性任务结果和预算/协议验收即可；现有 controlled score 仅保留回归。人工 relationship 可不可判断不是本轮需要用模型强行补齐的问题。conflict 卡按设计不可达成，不能降低准入来保证任务全成功。

至少完成这些行为检查：

| 类别 | 实际证据 |
|---|---|
| 官方 adapter | 实际发行物连到 loopback，捕获正确协议请求及 SSE/usage，回答经真实 DSH 进入事实链；列出真实插件与版本 |
| 上下文 | 双 seat wire 输入逐项证明可见性；第二 actor 得到真实第一行动；没有预置答案/对手私有信息/评分提示 |
| 任务 | 达成、合法未达成、非法 action、缺第二步/故障维持各自语义；第二步失败不抹掉第一步世界效果 |
| 传输负例 | 至少 HTTP 429、500、提前断流、deadline、空或畸形响应；不自动重试，不伪造完整结果；有界进程退出 |
| 预算 | 零/耗尽额度发送前拒绝；末额度并发竞争；重复 attempt 不再发送；发送前/发送后/结算前中断按定义保留 reserve/unknown；usage 缺失不计零 |
| 模式阻断 | 非 loopback、环境回退、远端重定向、正预算但缺真实授权仍不产生外部请求；禁用角色保持零预算；preflight 不读取真实 secret |
| 只读核验 | campaign/register/source/spec/view/attempt/reservation/服务捕获相互对应；改总额/漏失败/重复结算/错请求归属被拒绝；核验不启动 Worker、evaluator 或 HTTP |
| 旧版与回归 | 原 C0 12 记录、C1 campaign 22 请求分别由明确固定源码版本复核；新证据绑定最终新版本；相关 runtime/任务/输入/证据/评估/标注回归不退化 |

不同 transport error 是否在实际 SDK 映射为同一错误应记录真实观察，不根据 README编造细粒度可用能力。将局部 stub 单元测试、真实 SDK/runtime 回归和未验证的远端行为分开。

可沿用 `phase1c1_legacy.py` 的固定 commit 归档思路增加 C1 复核路径；禁止根据 artifact 内路径动态导入代码。保留历史原件、旧 pins 和失败；新 evidence 使用新目录/ID，不重封历史 campaign。

## 6. 交付与下一步边界

交付 `docs/validation/phase1c2a/`：合同/复用说明、结果、Gate、可复制 CLI、证据 manifest、provider 协议探针、预算状态说明、将来 live smoke 配置模板。更新 README 当前入口。每次失败与修复均保留，最终 source/installed package/test/raw capture/manifest 相互绑定。

执行适当的相关回归、干净安装与公开 CLI smoke、core+eval pip check，核对所有本轮 DSH/测试服务/子进程已退出。不为文档变更重复整套 runtime；产品边界变更的相关真实行为必须验收。

分列 Gate：

- transport_stub 工程：通过官方 adapter、无答案输入、预算和证据验收后才 CONDITIONAL_GO。
- live provider：BLOCKED；没有用户选定 provider/model、明确总费用/调用/token 上限和必要真实验证。
- 人工校准、研究效度、演化晋升：BLOCKED；本轮无真实模型、真实标签或独立研究单位。

下一阶段建议 C2B 为另行授权后的 1–2 个 baseline episode 真实 solver 连接 smoke，确定性 GM、无 judge/工具/重试。准备好具体待确认字段和复现命令草案即可，本轮不执行。连接 smoke 不需等待社会评分人工校准，但不能支持能力结论；judge/人工标签与有效任务数据之后单独安排。

最后检查 diff，只 stage 本轮文件；commit 后普通推送 `phase1c2a-solver-transport-and-budget`（若继续同任务已有分支则推实际分支），核对 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/<branch>` 相同，报告工作树状态。不要自动合并 main。最终中文报告提供分支/提交链接、结果/manifest/复现入口、真实模型请求和本地测试请求分别计数、受管进程清理、阻塞项及已验证范围。停止于 C2A。
