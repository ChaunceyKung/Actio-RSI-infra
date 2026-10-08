# Codex 执行 Prompt：Phase 1C2A.1 Chat Completions 适配与预算闭环

在 Actio-RSI-infra 执行 **Phase 1C2A.1**。完成官方固定发行物的 Chat Completions 本机成功链路、无预置答案双 seat、逐请求预算与离线对账，验收、写文档、提交并推送 GitHub。先核实证据再实施；不要只给计划或停在成功探针。

## 0. 本轮决策、授权和版本

本 Prompt **明确选择保持 DSH `0.1.5rc1`，改用其官方 Chat Completions adapter**，取代上一轮 Messages-only 的目标。此前 Messages loader NO_GO 原件保留，不需要重新等待协议选择；这不是升级、外部 provider 或付费调用授权。

- 仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
- 最新产品基线：`7fb2f682b2726ce3bba9b38bc71ebbf893c5de22`，原任务分支 `phase1c2a-solver-transport-and-budget`。main 仍为 C1 `af0a88c…`，不要从 main 开工。
- 交接分支：`docs/phase1c2a-review-chat-completions-plan`；新执行分支：`phase1c2a1-chat-completions-budget`。
- 读 AGENTS.md、适用目录规则、git status/remote。fetch 后核对产品基线是交接分支祖先，从已核对远端交接 HEAD 开始，记录完整 SHA。已存在同任务工作先检查再继续；保护无关修改，不 reset/覆盖。
- 用户持续授权：**每轮验证后 commit → 普通 push 当前任务分支到 origin → 核对远端 SHA 与 HEAD。** 不再次问是否 push；不 force push、不默认推/合并 main、不部署。失败交付也要诚实记录并提交推送已验证的本轮材料。
- Windows x64 / Python 3.12；SDK/runtime `0.1.5rc1`、exe hash `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`、Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db` 保持。新运行用隔离短根、新数据库与新身份/spec。
- 真实模型请求/外部 provider 请求/真实费用均 **0**。仅使用任务创建的假 credential 与 `127.0.0.1` 临时 HTTP 服务；不读取用户真实 secret、登录态或 provider 环境回退。公开 GitHub/源码和锁定依赖准备、Git push 允许。

## 1. 必须承接的事实

读 `docs/reviews/phase1c2a_review_and_chat_completions_plan.md`、`phase1c2a_review_evidence.json`，C2A 的 `01_contract.md`–`06_budget.md`、manifest/probe_findings，以及前轮 C2A Prompt 的尚未实施任务。若旧 Prompt 对协议与本 Prompt 冲突，以本 Prompt 为准。

追读 `src/actio/preflight.py`、runtime/host/scenarios/task_contract/terminal/verify、fact/store/supervisor、campaign/evaluation，以及 `scripts/phase1c2a_probe.py/.mjs`、legacy、相关测试。

当前已完成角色配置修正；47 组是配置和既有 fixture 回归。四个历史探针仅两次 HTTP 接收，均为 `/chat/completions` 错误响应；Messages 插件正确插入时报 ERR_MODULE_NOT_FOUND。没有新传输成功 SSE、无答案双 seat、持久预算或新 transport campaign。

历史诊断 ProbePort 继承的 `pins.provider=actio-fixture` 与实际覆盖后的 HTTP provider 不同，不能拿来作为正式 transport spec。历史 `globalThis.fetch` wrapper 是诊断限制，不是持久预算门控，也不是覆盖所有网络路径的证明。

## 2. S0：按正确标签复用，先实测成功流

已实际查到官方 tag：`dsh-v0.1.5-rc.1` → **`183f08e9c6dde7e36cd2318eaee70b0da08fb35e`**。仓库 https://github.com/deepseek-ai/deepseek-harness 。该 tag 的 llm-deepseek package version=`0.1.5-rc.1`，与当前 wire 都指向 Chat Completions。

本地已下载只读文件在 `.local/phase1c2a-review-upstream/`，hash/URL 见审阅 JSON；若不存在，从该固定 SHA 获取。不要修改原参考目录 `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\01_deepseek-harness\repo`，其 HEAD 是较新的 `5badb150…`，不是本轮协议依据。需要完整 checkout 时使用独立路径或 archive。

窄读取以下旧 tag 文件，不执行上游真实 e2e：

- `packages/llm/llm-deepseek/{README.md,package.json,src/adapter.ts,src/index.ts,src/serialize.ts,src/translate.ts,src/sse.ts}`。
- `packages/llm/llm-deepseek/tests/{mock-server.ts,adapter.spec.ts,sse.spec.ts,translate.spec.ts}`；旧 tag **没有**新版布局的 stream.spec.ts，不把文件缺失视为 adapter 不可用。
- `packages/bundle/sdk-minimal/cordis.patch.yml`、`packages/llm/llm/src/index.ts`、`packages/llm/llm-retry/src/index.ts` 及必要依赖。

保留 MIT attribution；复用官方 serializer/SSE translator，不自写 provider 或第二 solver。源标签/版本/wire 相符不证明二进制可复现构建；记录 `binary_source_mapping=unproven`，不要把完整构建映射变成此次离线 slice 的新增前置条件。

用真实 `0.1.5rc1` SDK/binary/default `@deepseek-ai/dsh-llm-deepseek` 做一次有界 P0：

- route `deepseek-official`，固定假 model 标识/假 key，origin `http://127.0.0.1:<临时端口>`；实际目标为 `/chat/completions`，不要拼成 Messages `/v1/messages` 或盲目追加 `/v1`。
- 纯文本，明确 max_tokens/thinking 等实际支持字段；捕获真实请求的 `stream=true` 和 `stream_options.include_usage`。以发行物观察为准，不能仅照 README 宣称字段生效。
- 本机服务复用旧 tag 的 choices/delta/finish_reason/usage/`[DONE]` 行为。分别验证 finish 附带 usage 与尾部 usage-only 两种完整成功流；输出至少有非空合法行动文本、完整 native/SDK 终态。
- 截断在 finish_reason 之后、DONE 之前不能被当成完整传输；S0 通过后才进入正式任务合同。诊断本身不伪造已 seal 的领域 run/campaign。
- 关闭 retry、title 模型、compaction、工具/MCP、图片/Files 等未授权 producer；读取实际 profile/inventory 并以服务计数验证。只改 entry.name 不足以替换插件，使用已证明的 patch 语义。

成功后**直接继续 S1–S3**。局部配置/fixture/测试错误先修并保留失败，不因第一次失败自动停止。只有完成最小定位、证据证明固定发行物确实无法提供必要成功流或可靠预算边界时才 NO_GO；说明具体能力、已尝试窄修复和最小备选，不静默升级/装新版 Messages 插件/换 Strands/写新 loop。

## 3. S1：正式无答案双 seat 合同

仍是原两个 authored 排程卡、两 seat、固定两步，不新增任务 DSL/多模型平台。

1. 新 config/运行协议采用明确版本，固定 Chat Completions、真实 provider/model/profile/plugin 和 schema pins。历史 `pilot-config.v2` 的 Messages 示例只能按旧语义读取或明确 unsupported，不能静默改解释/重封旧记录。保留已修好的 deterministic/disabled 角色零预算规则。
2. 新 actor payload 仅含自身角色/目标/私有约束/关系、公共场景、实际公共行动历史、冻结 memory、完整 ActionSpec 及必要关联 ID；**无 answer、scripted_actions、服务响应计划、期望任务结果、对手私有信息或 judge 内容**。在实际 wire 上验证，不只查 Python 对象字段名。
3. 固定响应计划只在本机测试服务控制侧，不能从请求取 answer 回显，也不能把预期答案伪装成另一段提示。stub 输出仍不代表模型推理。
4. 新 run 使用现有 RuntimePort/官方 SDK/TS loop、真实 Concordia Entity/Engine、事实和世界效果链。A 的实际行动到达 B 的观察；达成、合法未达成、非法拒绝和 partial 分开。第二步失败保留第一步已经发生的效果。
5. `execution_mode=transport_stub` 与 protocol/input version 明确分派；在线 seal 与离线 verifier 共用必要语义。不全局放宽旧 fixture 校验，新 mode 未识别则拒绝。
6. HTTP 服务只绑定 literal loopback 临时端口、限制确切 path/method/大小/deadline，禁止 redirect/外部 endpoint/环境代理和凭据回退。假 key 通过独立引用注入，报告其是假值；不要读取或发布真实 credential。

不要同时本地构建多个环境而争用 `build/lib`；准备和安装顺序执行。保持锁定核心依赖，只有确有必要且说明闭包时才增加最小测试依赖。

## 4. S2：实际 provider attempt 前的预算闭环

Python 冻结实验合同并持有权威预算台账；TS 在实际发送前核对资格。建议复用旧 tag 的 `llm/stream` 等窄 seam，但必须用实际 binary 验证 hook 次数与 HTTP 次数及额外请求行为；`一个 turn/一次 prepareCall/一次 hook` 都不能直接当成一次发送。

采用新的本地实验 SQLite 账本，绑定 campaign/run/op/attempt/config/profile。现有任务库与历史证据不原位迁移。不做通用网关/计费平台。

必须保证：

- 原子、持久 reserve 在发送前完成；输入/输出上限、calls、合成单价/总费用一起核对。同预算的两个独立控制进程竞争最后额度时，仅一方有发送资格。重复 attempt ID 不发第二次。
- 预序列化请求 hash 与实际 wire-body hash分别保存；如两者不同，通过明确转换/关联证据绑定，不能伪称相同。一次性资格绑定方法、endpoint、实际请求/配置和运行归属，不能授权另一 body 或后台调用。
- 若采用全局 fetch wrapper，仅可作为经过实测、严格作用域、可清理的窄门控；不得替换官方序列化/SSE/error 处理。需证明固定纯文本 profile 的每次模型发送经过它，且超时/异常/多 Worker 不绕过；日志计数器不是执行权威。
- 记录 reserved、sending、settled、unknown，以及仅在确证未发送时允许的 released。发送后失败/断流/丢 usage/崩溃不结为零费用、不自动退款或重试；未知预留阻断后续尝试。
- 官方 stream 终态、任务结果和账务结果独立。保留已经观察到的文本/事实/世界效果；不能因账务 unknown 删除它们或伪造未发生。
- 关闭和验证所有自动重试；HTTP 429/500、空流/超时均不产生意外第二次接收。额外工具、title/compaction、Files/image 请求全部不在合同内。
- 附带/尾部 usage、缓存字段和 inputTokens 的映射按官方 raw/native 证据核对；不把 raw prompt_tokens 与 cacheRead 再相加导致重复，也不能漏掉 cache 部分。缺失、负数、非整数、矛盾 total 或异常超限按无可信 usage/诊断保留，不能靠转换成 0 成功结算。
- token 和 cost 用整数/明确精度。此轮只是合成价格与配额验收；真实收费上界、供应商 tokenization 和账单尚未证实，live 继续 BLOCKED。请求数硬上限必须真实成立。

未实现预算前的 S0 探针必须有独立固定接收上限和明确 diagnostic 标记，不宣称已由新台账管控；预算落地后的所有正式任务验收用新路径。

## 5. S3：行为验收、只读复核和交付

最低验收矩阵如下，按实际行为而非测试数量交付：

| 范围 | 验证内容 |
|---|---|
| 完整协议 | 官方 binary/adapter 的非空文本成功流、attached/trailing usage、DONE；真实 SDK/native 与 HTTP 捕获一致 |
| 双 seat | 成功、合法未达成、非法、第二步失败；公开行动交付，私有隔离，wire 无预置答案 |
| 传输失败 | 必测 429、500、缺 DONE、缺 usage、空/畸形响应、deadline；按需要补 400/401。每个记录实际错误、发送数、接收数、终态与账务，不 mock 成一条理想错误 |
| 额度与幂等 | 零/耗尽额度在发送前拒绝、并发最后额度、重复 attempt、发送前后/结算前中断、未知预留保持和无隐式重试 |
| 使用量 | 最终 usage 与尾部覆盖规则、缓存字段、缺失/矛盾/非法数值、额度越界，不漏计、不重复、不补零 |
| 配置与身份 | 协议版本不混用，profile/pins 与真实 provider 一致；disabled/local 零预算；正预算/批准字符串不解锁 live |
| 只读对账 | dataset/register/source/spec/actor view/wire/attempt/reservation/接收/终态/世界效果绑定；遗漏失败、改归属/计数/金额/重复结算不能通过。复核不建 Worker/evaluator/HTTP |
| 回归 | 对修改范围跑真实 runtime/task/可靠性/证据回归及 preflight/input/evaluation/SOTOPIA 等相关检查；最终安装包和源码一致 |

服务接收数不等于全部发送尝试：连接前失败可发送尝试存在而接收为 0，账本必须诚实表达差异。成功、失败、not_run、unknown 都保留注册和正确分母。表中的负例可使用临时合成数据；历史原件不可改写。

采用现有 immutable artifact/campaign 机制，新增预算和 wire 索引的只读校验，不建设第二套观测系统。公开材料只含合成样例和必要 hash/摘要，原生大日志/数据库保留有 hash 的本地归档。

固定旧版复核继续覆盖 C0 12 记录和 C1 22 请求/25 登记，使用代码中固定受信 Git commit，不能让 artifact 指定执行源码。C2A 旧协议/失败/配置材料保留并核对 hash，新目录独立。新源码 pins 变化后，不为了通过旧记录而删除验证或刷新旧 spec。

交付 `docs/validation/phase1c2a1/` 的合同/复用来源、结果、Gate、manifest、可复制 CLI 和预算生命周期说明；更新 README 当前入口。新 manifest 绑定最终源码、安装包、实际命令、失败记录、raw archive，区分本轮与历史数字。

干净安装、公开 CLI smoke、core+eval pip check、所有本轮受管 Job/测试服务/端口清理需验收。不要重跑历史失败探针以“刷新”旧统计，也不要用测试 PASS 掩盖 transport NO_GO。

## 6. Gate、推送及停止点

- 新 transport_stub 工程只有在成功协议、无答案运行、持久预算、错误/并发/对账都通过后才 CONDITIONAL_GO；部分通过列明边界，剩余关键缺口为 NO_GO。
- live provider、人工校准、研究效度、judge 与演化晋升继续 BLOCKED。真实模型/外部 provider 请求和真实费用=0，本机 HTTP/合成 usage 按实际非零值单列。
- 不自动执行 C2B。只列出未来 1–2 个 baseline episode solver 连接 smoke 所需 provider/model/endpoint/数据范围/预算/报价/credential reference；不要求用户把 secret 写进 Prompt，不把当前字段齐全当费用授权。

完成并验证后仅 stage 本轮文件，commit 并普通 `git push -u origin phase1c2a1-chat-completions-budget`（如继续同任务已有分支则使用实际分支），核对 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/<branch>` 相同；报告工作树状态。push 阻塞保留提交和精确失败，不强推，不宣称已交付远端。

最终中文报告必须包含 Gate、真实验收/未验收边界、配置与协议版本、真实模型与本地 HTTP 分开计数、进程清理、GitHub 分支/提交链接、结果/manifest/复现入口。停止于 Phase 1C2A.1，不推 main、不部署、不开放真实模型。
