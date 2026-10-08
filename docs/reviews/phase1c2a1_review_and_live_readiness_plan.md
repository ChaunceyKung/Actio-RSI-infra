# Phase 1C2A.1 审阅与下一步行动方案

审阅基线：`b086cbae97fcebd5c818dce611a0c2a331380cb1`。本轮仅审阅、离线复核及编写交接文档；没有实现下一阶段。审阅证据见 [JSON](phase1c2a1_review_evidence.json)，下一 session 使用 [完整执行 Prompt](../prompts/phase1c2b0_solver_live_readiness.md)。

## 结论

**维持 CONDITIONAL_GO，仅限既定 transport_stub 工程。建议进入 Phase 1C2B0：真实 solver 接入就绪，默认零外部 provider 调用。** 不建议重建 runtime、再扩一轮同类 fixture，或立即进入 judge、人工校准与演化实验。

当前闭环已有可复用的主体：官方 DSH adapter/loop、真实 Concordia Engine、双 seat 输入隔离、发送前持久预留、未知账务冻结、不可变 campaign 与离线对账。下一轮应解决真实接入特有的缺口。完成 C2B0 后，另行取得明确参数和费用授权，才进入 **C2B1 的 1–2 个 baseline episode 连接 smoke**。

未发现足以推翻本轮已声明窄 Gate 的问题；这不等于全量安全审计、真实 provider 兼容性或真实计费保证。

## 已独立核对的证据

| 核对项 | 本次结果 | 证据含义 |
|---|---|---|
| Git 基线 | 本地与远端任务分支均为 b086cba；远端 main 仍为 af0a88c | 下一阶段须从包含 C2A.1 的交接分支开工 |
| 交付哈希 | 71 个阶段 artifact、38 个产品文件、20 个测试文件、28 个工具文件、4 个锁/包配置、2 个入口、3 个中间源码归档、19 个准备日志全部匹配 | 已发表材料与本机文件一致 |
| 旧材料 | 537 个历史文件保持匹配 | 不重封或覆盖旧失败记录 |
| 安装内容 | runtime/eval/release2 三环境，各 38 文件与产品源码一致 | 减少“测试的是旧安装”歧义 |
| 已发表 59 组 | 12 个最终 suite 的成功结果、源码与测试绑定匹配 | 本次没有重跑 59 组 runtime 测试 |
| 原始归档 | 73 ZIP、6,891 成员、15,524,688 bytes；归档及成员哈希匹配 | 哈希不是签名或第三方证明 |
| 接收与发送 | 直接复核 service 捕获与只读 SQLite：正式 49 sending / 48 receives；全部阶段 190 receives，其中 3 diagnostic | 不能把两种计数混用 |
| 当前公开样例 | success、missing-done、last-call 均通过当前源码只读 verifier | 读取时禁止网络、进程和写入；未启动新实验 |
| 固定旧版复核 | C0 12 records、C1 22 records 及 campaign 通过 | 源码逐文件比对受信 Git SHA 后读取；不使用 artifact 自选代码 |
| 本次配置回归 | 8 项通过 | preflight 5 + transport_config 3；非新增模型样本 |
| 清理 | 查询 298 个历史具名 Job 均无活动进程；115 个历史服务端口当前未见监听 | 原有 117 线程 joined 属于已核对的历史交付记录 |

本次新增模型请求、外部 provider 请求、本机 HTTP 接收、DSH Worker、evaluator 调用及费用均为 **0**。读取公开官方文档和 GitHub 不属于模型 API 调用。

## 需要在真实接入前处理的差异

这些是从当前实现外推到 live 时的必改项，不是把原本明确限于 stub 的实现判成失败。

| 项目 | 已查实现/来源 | 下一轮动作 |
|---|---|---|
| 模型与供应商合同会变化 | 官方当前推荐 `deepseek-flash`；旧 `deepseek-v4-flash` 已映射到 DeepSeek-V4.1-Flash | 冻结请求模型名、文档快照、访问日期、允许的响应标识；明确 alias 不等于不可变权重版本 |
| 真实计价未实现 | `budget.py:trusted_usage` 直接使用 prompt + output；MAX_INPUT 是 65,536 bytes 配额 | 新版本加入真实币种、整数金额精度、带来源的单价与保守 reserve；保留原 SYNTHETIC 语义 |
| 凭据目前是可持久化假值 | `transport.py:prepare` 把固定假 key 写进 host-config；预算 IPC 默认继承 TS 环境 | live 改成明确引用、仅内存/受控进程注入；不把真实 key 写配置/台账/归档，也不传给无需 key 的预算 helper |
| 超时仍针对本机服务 | adapter idle 1.5 秒、fetch 总时限 3 秒、SDK request 5 秒、controller result 15 秒 | 冻结分层 timeout 合同，查清 SDK 各计时器实际语义；补延迟成功和超时结算测试 |
| 服务端接收证据不可照搬 | 当前 campaign 可拿到本机 service 的完整 receives | live 只能记录客户端发送尝试、响应、provider request ID/usage 等；无独立服务端记录时接收数必须未知 |
| 实际账单未知 | 当前 settled 只证明 synthetic usage 一致 | live usage 与估算费用、预留上界、供应商账单分列；不凭一条 usage 声称账单已对齐 |
| 完整控制进程恢复未实现 | pending/unknown 占额并阻断，Worker 中断已有证据 | 保留 fail closed；不因进程退出自动释放或另建新账本绕过同一预算 |
| 公开 API 的终态和错误细节 | 当前官方说明 usage 随最后 content chunk，随后 DONE；无单独 usage-only chunk | 已有 attached 测试可复用；保留 trailing 兼容测试但不称其为当前供应商实测；补 400/401 与 length 的独立语义 |

### 官方文档核验

于 **2026-10-08 15:46 UTC** 读取以下公开页面，HTTP 200，URL/字节数/SHA256 见审阅 JSON；本机快照在 `.local/phase1c2a1-review/`，未提交整页 HTML：

- [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/)：推荐模型 `deepseek-flash`；当前页面的 Flash 峰值报价为输入缓存命中 **$0.006 / 1M tokens**、缓存未命中 **$0.30 / 1M**、输出 **$1.20 / 1M**，谷值为一半。供应商保留调价权。
- [Chat Completion API](https://api-docs.deepseek.com/api/create-chat-completion/)：显式 `thinking.type=disabled`；`max_tokens` 限制生成量；usage、finish_reason 与 DONE 的语义需按合同处理。
- [API 入口](https://api-docs.deepseek.com/)：OpenAI 格式 base URL 为 `https://api.deepseek.com`；Anthropic URL 是另一个入口，不能混用。

以上用于提出 **官方 DeepSeek Chat Completions 单供应商方案**，不表示用户已选择模型或批准费用，也不是下一轮可永远复用的有效报价。下一 session 应复查官方资料并冻结新快照；禁止把旧 alias 默认当旧模型。

## 建议的下一 slice

1. **C2B0-A：冻结候选连接合同与费用计算。** 候选为官方 `https://api.deepseek.com/chat/completions`、`deepseek-flash`、非 thinking、无工具、顺序两 seat。只列候选，不补造用户授权。预演输出缺失项、完整 actor/wire 绑定、保守单次/全程占额以及批准对象 hash。
2. **C2B0-B：复用现有链路，完成禁用默认的接入路径。** 改动集中在合同、预算、凭据与超时边界；维持官方 adapter、SQLite 权威和 campaign 机制。以本机响应与假 key 验收价格计算、错误、秘密不落盘、未知阻断和停机。
3. **C2B0-C：交付可检查的批准包。** 新 CLI 的 preflight/plan 不读 secret、不启动 Worker、不发网络请求。新模式有版本分派，旧 v2/v3 与 C2A.1 样例按原语义/固定源码复核。缺少实际授权时，交付工程结果与精确 blockers 后提交推送即可，不必等待用户才能完成这一轮。
4. **C2B1：另行明确授权后的连接 smoke。** 最多 1–2 episode / 2–4 solver 请求，所有诊断也计入同一授权上限；无单独不计费探针，无补跑凑成功。GM 仍确定性、judge 禁用。它只证明连接和记账能力，不证明研究效度。
5. 只有连接与成本行为得到实测，再讨论人工校准及后续 pilot。RSI/演化晋升仍未获准。

### 如何避免“精确 tokenizer 未知”导致无限准备

先查能否获得与所选供应商模型匹配的可信计数上界。若不能，不把通用 tokenizer 或字符串 byte 数伪装成证明；可评估按该模型**被文档明确约束的最大可计费输入**及显式最大输出，采用缓存未命中/峰值价格预留。这个方法可以高估且可能让很小的预算无法容纳一次请求，必须显示给用户。

单价、缓存、取整、币种、可能的附加费用与错误收费口径未能界定时，继续阻断 live。基于公开合同的费用上界是有前提的估计；本地 SQLite 能控制本系统的发送资格，不能控制供应商任意计费。不要把建立完整 tokenizer、复现 DSH 二进制、自动恢复全系统或通用计费平台设为本轮新目标。

## 本轮交付边界

产品源码、测试、依赖锁与历史 validation 材料不改。新文档位于 `docs/reviews/` 与 `docs/prompts/`，基于 b086cba 的独立分支 `docs/phase1c2a1-review-live-readiness` 提交并普通推送，核对远端 SHA。未推 main、未合并、未部署。

下轮推荐执行分支：`phase1c2b0-solver-live-readiness`。读 [执行 Prompt](../prompts/phase1c2b0_solver_live_readiness.md) 后开始；其中持续包含用户要求的 **验证 → commit → push → 远端 SHA 核对**。
