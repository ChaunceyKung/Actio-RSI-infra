# Starling Memory Adapter 具体开发 Prompt

> 用法：将本文件完整交给另一个 Codex/工程 session 执行。它是基于 [21_starling_memory_adapter_contract.md](21_starling_memory_adapter_contract.md) 的实现任务单，要求先完成可离线验证的 P0/P1 slice，再为 `frozen_context` 留出清晰边界。不要把规划文档当成已完成的产品能力。

## 任务身份与目标

你是 Actio-RSI-infra 的实现工程师。请在当前仓库中实现一个可选、可审计、可回滚的 Starling Memory Adapter，使经过 `Facts.certify()` 的 Actio 来源能够通过 outbox 投影到 Starling，并让 Actio 在明确 profile 下读取带 receipt 的 context。Starling 是派生记忆投影，不得成为 Actio `Store`、`Ledger`、`Facts`、run terminal、evidence 或 replay 的权威来源。

本轮优先交付：

1. 没有 Starling、没有真实 LLM、没有外部网络时，Actio 既有离线测试和最小 CLI 仍能工作。
2. `off`/`shadow` 路径可运行，认证 source 的 source key/hash、payload policy、状态和 receipt 可回链。
3. `frozen_context` 只消费已冻结的 context/receipt；`live_context` 默认拒绝用于 candidate/evaluation/replay。
4. 所有失败保持 `degraded`、`rejected`、`needs_reconcile` 或 `abstained` 等可解释状态，不改变已经认证的 Actio run 结论。

## 开始前必须做的检查

先读取 `AGENTS.md`、`docs/planning/20_starling_memory_integration_plan.md`、`docs/planning/21_starling_memory_adapter_contract.md`、`src/actio/README.md`、`docs/architecture/MODULES.md`、`docs/architecture/FLOWS.md`，再检查 `git status --short --branch`、当前 HEAD、remote、Python 版本和现有测试入口。检查当前源码是否已有同名模块或迁移，避免覆盖用户改动；不要 `reset`、`clean`、force push 或删除未提交文件。

先做 P0 探针并记录结果：能否导入/构建 Starling Python facade、是否需要 sidecar、SQLite writer 约束、`remember → query → tick → working_set → close` 是否能用 stub LLM 离线完成。若 Starling 不可构建，仍交付 Actio 端 contracts、stub adapter、outbox、profile 和测试，并把构建阻断写入诊断；不要伪造真实 Starling 成功。

## 实现范围

按依赖方向新增或调整以下组件（实际路径以仓库结构为准）：

- `src/actio/contracts/memory.py`：定义 `MemoryMode`、`MemoryScope`、`MemorySource`、`MemoryObservation`、`MemoryReceipt`、`MemoryContext`、`MemoryHealth`、错误码和 `StarlingMemoryPort`。只使用 canonical JSON/固定 enum；不得 import Starling。
- `src/actio/application/memory_projection.py`：实现 outbox 入队、有限 claim/lease、投影、receipt 写回、duplicate/reconcile 和有界重试。只依赖 port 与现有 Store/Facts 接口。
- `src/actio/adapters/memory/starling.py`：封装 Starling facade 或 sidecar client；处理 preflight、health、deadline、序列化、stub/offline 模式、单 writer 和 graceful close。Starling/pybind11/IPC/SQLite 依赖只能在 adapter 层出现。
- `src/actio/adapters/memory/README.md`：记录安装 extra、embedded/sidecar 选择、生命周期、配置、协议版本、错误映射和禁用方式。
- `src/actio/profiles/starling_memory.py`：实现 `off|shadow|frozen_context|live_context` capability/profile 校验，默认 `off` 或 `shadow`；旧 manifest 不得被自动解释成 frozen context。
- Store migration/schema：增加独立 `memory_outbox`（`source_key` 唯一、`payload_hash`、状态、attempt、lease、receipt、error、时间列），保持 Actio 事务边界，不声称与 Starling 跨库原子提交。
- CLI/maintenance：按项目现有入口增加 `doctor`、`project`、`reconcile`、`query`、`tick`；命令必须有 deadline/operator scope，`doctor` 只读，禁止 episode finally 无限重试。

## 必须遵守的领域规则

1. 只有 `Facts.certify()` 后的允许来源可入队；默认只接收 `assistant.final`，tool/world observation 必须显式 profile 开启。
2. `source_key` 至少由 `stream/seq/slot/mapper` 组成；`source_hash` 与脱敏 `payload_hash` 必须绑定。相同 key+hash 返回 duplicate/原 receipt，不能生成第二个 Engram/Statement；同 key 不同 hash 必须拒绝。
3. namespace 必须 canonicalize 后生成稳定 tenant digest；agent 映射为 self/holder，跨 agent、environment、tenant 和 social sharing 必须按 policy 检查。
4. 凭据、`GM_PRIVATE_FULL_LOG`、stderr、transport 私密原文、未批准 prompt 不得进入 payload。执行 secret scan 和 UTF-8 16 KiB/byte budget。
5. Actio run 成功与否由现有 run/Ledger/Facts 决定。Starling failure 不回滚 run、不制造 task success；`task_failure` 默认不写成社会事实。
6. replay 默认禁止写入 Starling；允许时必须携带 `replay_of` 和实验 profile。replay 只读取 manifest 中冻结的 context，不重新 query 当前 Starling。
7. `MemoryContext` 必须保留 `context_hash`、`abstained`、`abstention_reason`、sections 和完整 retrieval receipt；不能把 abstention 伪装成空成功。
8. `tick(now)` 使用 Actio Clock 的 UTC 时间和 bounded deadline；记录 TickStats/stage timings/health，不能使用演示默认时间。
9. embedded 模式只能有一个受控 writer；Windows 若无法稳定构建则实现 sidecar contract/诊断，不偷偷使用多个 SQLite writer。

## 建议实施顺序

### Slice A：contracts、profile、stub

先实现纯类型、wire round-trip、enum/capability 校验、错误映射和 deterministic stub port。让 `mode=off` 完全短路，不导入 Starling；让 `shadow` 能返回 receipt/health 而不改变 solver 输入。

### Slice B：outbox/saga

在现有 Store migration 机制中加入 `memory_outbox`。在 Facts certification 成功的同一 Actio 事务内入队；事务提交后才调用 adapter。实现 `queued → in_flight → committed|duplicate|degraded|rejected|needs_reconcile`，lease 超时只用相同 source key 重试。模拟“Starling 已提交但 Actio receipt 写失败”时必须进入 reconcile，禁止盲写第二次。

### Slice C：Starling facade/sidecar

用公开 facade 或独立 RPC contract 调用 `remember/query/render_working_set/tick/forget/close`；不要依赖 dashboard 内部 FastAPI route 或私有 `_core`。把 `RememberResult`、`QueryResult`、UNREADY、LLMNotConfigured、extraction_failed、DB locked、timeout、crash 映射到稳定错误码。没有真实模型配置时使用 stub 或明确 `degraded`，不能声称完成语义抽取。

### Slice D：冻结上下文

在 run freeze 阶段只对 `frozen_context` 调用 query/working_set；将 provider、mode、context pack、hash、as_of、receipt、source hashes、adapter/version/capabilities、policy/model pins 纳入 manifest input hash。`live_context` 只能用于交互式/实验 profile，并在每次 recall 封存完整结果；candidate/evaluation/replay 默认拒绝。

### Slice E：CLI、diagnostics、文档

完成 `doctor/project/reconcile/query/tick` 的最小离线路径，输出未结 outbox、writer ownership、schema/model/embedding pin、projection lag、abstention 和错误原因。补充 adapter README、配置示例、回滚到 `off` 的步骤和 Starling 构建阻断。

## 测试与验收

新增有意义的测试，至少覆盖：

- namespace/tenant/holder 映射、跨环境和跨 tenant 正反例；
- source key/hash 幂等、同 key 冲突、payload secret scan、16 KiB 限制；
- `off/shadow/frozen_context/live_context` 的准入、manifest hash 和 replay 行为；
- stub `remember/query/tick/working_set/close` 的 receipt、abstention、固定时间和 wire round-trip；
- Starling disabled、UNREADY、缺 LLM、抽取失败、DB locked、timeout、sidecar crash、graceful drain；
- Actio run 成功但 Starling 失败、run 失败但 outbox 已排队、双写后进程崩溃、reconcile 和 duplicate；
- correction 使用新 source/version/supersedes；replay 不读取 live Starling；
- 无 Starling optional extra 时既有测试、minimal reader、`actio --help` 仍通过。

先运行受影响的小测试，再运行现有 memory/runtime/facts/evidence/replay 回归和项目规定的静态检查。不要因本任务新增真实模型调用、在线实验或大规模 corpus；离线 stub 通过才可作为本轮完成依据。

## 交付物与停止条件

最终必须交付实现、migration、测试、adapter README、诊断输出和必要 ADR/contract 修订，并在最终报告中列出：实际测试命令及结果、Starling 构建/ABI 结论、运行模式、未解决风险、修改文件、commit SHA、branch 和远端 SHA。若发现 contract 与现有源码冲突，先用最小兼容实现或新增 ADR 记录，不悄悄改变 Actio 权威边界。

本轮禁止：真实付费 LLM 调用、改变生产 solver 默认输入、把 Starling statement 当 Actio effect/evidence 成功、共享跨库事务、无限重试、依赖 dashboard 私有 API、force push、覆盖他人提交。

## Git 交付要求

完成实现和验证后，必须提交本轮文件并普通推送 GitHub `origin/main`。推送前检查工作区和待提交 diff；远端有新提交时先 fetch、审阅并安全整合，绝不 force push。推送后执行并记录：

```powershell
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

只有两者完全一致才可报告“已同步到 main”。网络、鉴权或远端并发更新导致失败时，保留本地提交并明确报告“本地已提交但 push 受阻”、失败命令和待推送 SHA，不能把本地提交说成已发布。

