# Codex 执行 Prompt：Phase 1B.1 可靠性修正与可迁移证据导出

将本文件交给新的 Codex session 执行。本轮允许有限产品实现、测试和文档修订。完成并验证后必须 **提交、推送 GitHub、核对远端 SHA**；不自动合并 main。不要只写计划，不要自动扩展到 live、评估器或演化。

你是 Actio-RSI Infrastructure Engineer。已有 Phase 1B 实现持久身份/spec、单活动 run、受管 DSH、事实/memory、助手与真实 Concordia 两人场景。下一步先修正场景完整性、请求所有权、恢复目标及 replay 输入问题，然后交付能脱离原任务目录离线核对的证据包，为后续评估提供可信输入。

## 0. 基线、授权与持久交付规则

仓库：

`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`

GitHub：`https://github.com/ChaunceyKung/Actio-RSI-infra`

产品基线：`668754fc51915a56818c25d1c0d6b3715f7f5396`，已推送 `phase1b-persistent-vertical-slice`。

本次审阅和交接分支：`docs/phase1b-review-phase1b1-plan`。优先读取这个分支的最新交接提交，创建/续用 `phase1b1-reliability-and-evidence-export` 实现分支，确保包含产品基线和审阅文档。`main` 在审阅时仍为 `fad04fc…`，不要从默认 main 开始而丢失 Phase 1A/1B。

首先检查 AGENTS.md、HEAD/branch/remote/status、未跟踪文件和已有 worktree。参考仓库只读，保留用户未提交内容及已有正确后继工作；需要新 worktree 时显式指定包含上述基线的 ref。不要 reset/clean、force push 或覆盖他人提交。

用户已明确要求每轮完成后推送。执行顺序是：当前任务验证 → 提交本轮文件 → 普通 `git push` 当前任务分支到 origin → 读取远端该 ref 验证与 HEAD 相同。无需重复申请推送许可；没有推送成功就如实报告阻塞，不能宣称完整发布。push 授权不包含 merge/deploy、模型费用或新实验范围。

参考路径：

`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase`

本轮不需要重新排名开源框架，也不需要新建其他 session 或多 agent 团队。

## 1. 首先阅读及不变的边界

依次阅读：

1. `docs/reviews/phase1b_review_and_phase1b1_plan.md` 和 `phase1b_review_evidence.json`。
2. README、`docs/validation/phase1b/01_plan_and_contract.md`、`02_results.md`、`03_gate.md`、`evidence_manifest.json`。
3. `src/actio/store.py`、`schema.sql`、`scenarios.py`、`runtime.py`、`facts.py`、`memory.py`、`cli.py`，以及相关 supervisor/host/plugin。
4. `tests/test_contract.py`、`test_runtime.py`、`test_failures.py`、`test_processes.py` 和证据/安装脚本。
5. 规划 04/05/07/08/10/12 中与 owner、完成性、快照和未来评估相关部分；其他按需查验。

已核对：18 组行为验收为 6+2+6+4；17 个产品文件 hash 与当前基线匹配；4 个当前 suite 及 raw archive hash 匹配；41 个 Job 清理记录为 active=0。这些是原交付证据，不覆盖本次发现的缺失边界。

保持以下限制：Windows x64、Python 3.12、DSH SDK/runtime-bin `0.1.5rc1`、固定 Concordia 源码、隔离短根、合成 fixture、单 store 单活动 run、只读工具、静态最终 guard。具体 wheel/exe/source/schema pins 以已交付锁文件和 artifacts 为准，先验证再继承，不默认升级。

Python 管领域台账和生命周期；DSH 拥有 agent loop/native journal；Concordia Engine/GM 管社会调度和 world；SQLite 是 facts/memory 的唯一领域权威。不得另写一套 agent loop、改造整个 runtime 或为了导出引入新服务。

预算仍为 **0**，不读环境里的凭据来调用 live。模型/GM 继续 fixture。native reopen/resume/fork/catchup、semantic cancel、完整恢复、多活动 run、写效果工具、任意候选代码、Graphiti、远端部署、SOTOPIA live judge、Raven 演化、模型训练均不开放。

Phase 1A/1B 的历史 probes、证据和 manifest 保留原样。新实现和新证据使用 Phase 1B.1 路径；原代码修正与新的 capability 文档正常更新，不能回填旧测试为 PASS。

## 2. 本轮交付目标

先在 `docs/validation/phase1b1/` 写一份小型合同/实施计划，然后按依赖继续编码、验证和交付。无需再次生成一套全量架构规划。

本轮只有四组工作：

- H1：修正 B1R1–B1R4，补有意义的边界回归。
- H2：为本轮 schema 变化建立最小版本/迁移/旧库读取合同，保护既有事实与 pins。
- H3：一致快照导出最小轨迹证据包；独立离线 verifier 给出分层完整性结论。
- H4：相关原回归、新验收、干净安装/使用说明、独立 manifest 与 GitHub 发布。

H1/H2 先解决正确性和数据库兼容，再做 H3。底层 Gate 未成立时不以导出器掩盖错误，提交明确阻塞证据并按用户要求正常推送已完成的安全工作。

## 3. H1：四项修正

### B1R1：场景终态与 operation 完成分开

基线 `Store.finish()` 只检查 `bool(ops) and all(op.state == execution_complete)`。社会场景 B 完成而 A 在创建 operation 前失败时，现有检查可能得到 `execution_complete / infrastructure_failure / complete`。审阅仅以受控 SQLite fixture 验证这一谓词，下一轮要补真实 Engine 失败路径。

实现最小持久场景终态凭据，或等价的不可混淆记录。凭据应有 run、scenario/effective manifest、终止原因、必要 domain/world/operation 引用与版本；只能由已完成该场景规则的 owner 确认。

至少区分：

- operation 的执行及持久事实完成；
- scenario 是否按合同终止；
- task success/task_failure；
- 基础设施故障、unknown/needs_reconcile；
- 已记录前缀完整性与完整 episode，不能共用一个模糊 bool。

社会成功要求两位正确实体、正确顺序的 GM resolved 和 domain receipt；助手要求自己的单步合同。非法 action 在 world 变更前拒绝，可以合法提前结束为 task_failure，但必须有明确终态依据。不要把修正简化为所有 run 必须等于两个 operation，也不要把所有 task_failure 都当 incomplete。

异常收尾不能从“已有 operation 都好了”推断缺失步骤已完成。保留已执行的部分 world、memory 和事实，不回滚已发生的内容；仍须清理 Job，按合同释放或保留 lease。保存主要失败原因，清理失败单独报告，不让后一个异常抹掉第一个原因。

最低新验收：正常助手；正常两人社会场景；原非法 action 拒绝；第一实体完成后第二实体初始化失败；第一步后 Engine/GM 异常；domain receipt 缺失/不一致；所有失败均不误报完整社会 episode。至少一条使用真实 Concordia Engine、真实第一步 DSH fixture 和精确的第二步测试注入，测试注入仅在 tests。

### B1R2：请求幂等与执行资格必须来自同一原子决定

`scenarios.assistant/social` 中的事务外 `existing()` 不是所有权保证，当前 `run,_ = store.begin(...)` 丢弃了 `fresh=False`。

使原子 begin/claim 成为唯一执行资格来源。没有取得新执行资格的调用者只能返回既有 run，不得分配 worker、调用模型/工具、改写执行状态、finish 或释放 lease。单纯持有可读的 run ID/epoch 不等于获得执行权。

明确两层身份：规范化调用方 request/idempotency key 与赢家第一次冻结的 effective input（memory/spec/pins）。相同 request 重试返回第一次冻结输入，不因之后 memory revision 变化而重新执行；不同规范请求同 key 冲突。避免在事务外预查询成功之后仍存在“双方都能执行”的窗口。可以保留方便的预查询，但不能以它替代原子判定。

锁/事务只覆盖小型台账操作，不要把模型执行放进长 SQLite 写事务。保留不同 key 单活动 lease、owner birth、epoch fencing 与 unknown 不自动重发规则。

最低新验收：用明确同步闸门让两个控制进程竞争同 key 同请求，仅一个执行 owner/一次 runtime 路径/一次工具效果，另一个返回同 run；不同请求同 key 拒绝；完成和 unknown 的重试都不再次派发；重复调用者不能 finish 赢家的 run。覆盖助手和 social 两个入口，纯台账测试不能替代入口级回归。

### B1R3：reconcile/recover 只操作显式目标

当前 CLI 先调用无目标 `store.recover()`，再解析用户指定的 run，可能操作另一条 lease。

先解析目标，再检查 lease 是否属于同一 run/epoch。错误目标、未知目标和历史目标均不得修改另一条活动 run。恢复 owner 死亡的目标前继续核对 process birth 和命名 Job，确认清理；清理后提交台账前再次核对目标与 lease。无法证明目标一致则保守拒绝。

本轮优先实现目标化恢复。若认为需要全局 orphan 命令，单列明确合同，不能隐含在 `reconcile <run>` 中；没有必要就不增加。

最低新验收：未知 run 和历史 run 请求不会调用另一条 Job 的回收逻辑；owner 活着拒绝；目标 owner 已死仅回收该目标；过程中观察到 lease 变化拒绝旧结果；reconcile 只补 facts/核对状态，无新模型/工具派发。

### B1R4：冻结起点 replay 拒绝矛盾 override

当前 replay 复制旧 manifest，却仍接受和记录 `--illegal`、`--memory-revision` 等会改变起点的参数，实际执行忽略它们。

保留严格起点 replay：不允许改变冻结 manifest 的参数，冲突在创建 run/worker 前明确拒绝。可辨别参数“未提供”和“显式提供”；不得只依赖默认 False/None 隐藏用户意图。记录请求与 effective manifest 的一致关系。新实验/干预不是本轮功能。

最低新验收：无 override 重执行，产生新 run/creation/stream，语义 world 一致，原 memory 不变；矛盾 flag/revision 明确失败，未创建 worker；缺失必要 pin/snapshot 不伪造替代输入。

## 4. H2：最小 schema 版本与历史兼容

当前 Store 打开时执行 CREATE IF NOT EXISTS，没有数据库版本判断。新增字段/终态凭据时一起建立最小版本边界，不能让旧库静默被当作新合同。

要求：

1. 明确 schema version，可用 SQLite user_version 或等价单一权威；识别当前已知 Phase 1B schema，拒绝未知未来/不完整结构。
2. 提供显式旧库迁移入口与结果记录；迁移前用一致 SQLite backup 生成可恢复快照/hash，考虑 WAL，不能只复制主 `.sqlite` 文件就称完成备份。
3. 正确处理重复迁移、迁移异常/中断与版本标记更新；失败保留旧事实和可恢复备份，不 reset DB、不清空已有表。只支持必要的已知一步迁移，不造通用迁移框架。
4. 查询/导出支持旧库的清晰策略（显式兼容只读，或提示迁移到副本）；未知 DB 路径的查询不能偷偷新建一个空库并声称查询成功。初始化与读取职责分开。
5. 原 spec、run input、memory source、native creation 与历史 hash 不原位改写；不能为跑新代码自动刷新旧 AgentSpec pins。
6. 历史 complete 是历史声明，不自动补造新场景终态。另给 current verification 状态；推导旧记录时标明版本和来源范围，缺证维持 legacy/unverified/partial。

本轮不建设 AgentVersion 激活、旧 spec 自动升级或完整 memory migration。旧 spec 的整体源码 pin 不兼容新 runtime 时继续明确拒绝执行；确保旧资料仍可查询、迁移到副本并导出。新测试/demo 可以创建明确的新合成 spec/身份，不能假称这已经实现跨版本稳定身份演化。

最小验收：已知旧库保留全部事实和 pins；重复迁移结果稳定；注入失败可恢复；未知未来 schema 拒绝而不写；有 WAL 的一致备份；历史完整声明不被自动签成新合同通过。

## 5. H3：可迁移轨迹证据包

实现一个小型公开 CLI/库入口，从单个 run 导出其最小证据闭包，再提供独立 verifier。命令名称与目录布局自行选择，最终 README 用实际运行过的命令。默认目录+manifest 或简单归档均可，无需 Web、网络服务、云存储或新数据库。

### 5.1 一致输入与最小闭包

导出基于一致 SQLite 读取快照，明确来源 store/run/schema 与导出时状态，不混用不同时间的查询结果。允许导出 partial/unknown，但不能将活动 run 的瞬间前缀宣称完整。需要读取原生文件时只读、核对已登记的 stream 和 hash；不能借导出重新执行场景。

包中应有足够的、相互可校验的内容：

- 包格式、schema/mapper 版本和内容清单；每个文件/对象 hash、大小、必要 ID。
- frozen effective manifest、AgentSpec/Persona 来源、场景/fixture/provider/工具/runtime/plugin pins、预算和能力限制。
- operation intent/accepted receipt/终态/flush barrier；native source stream/session creation/seq 原始内容或其不可缺少的可核验副本。
- canonical occurrence/projection、连续 cursor、完整性冲突/缺口记录；引用必须可解析且 scope 正确。
- domain receipt、GM intent/resolved/world 与场景终态凭据；不能只有汇总 `trajectory=complete`。
- 实际使用的 memory snapshot/条目/revision/选择顺序/截断/policy，以及验证来源所需的最小前序事实闭包。
- 原执行状态、当前证据核验状态、fixture 标记、未测限制和必要清理摘要。

不要默认复制整份数据库或整个 DSH home。只导出该 run 及其引用闭包；闭包缺失时明确列缺失项，不能以原机器的绝对路径充当内容。引用到前序 memory 事实时，导出最小证明或报告缺证；不要退化成无限历史全库复制。设置合理条数/大小上限，超限明确失败/不完整。

审计包不是 agent 上下文包。说明审计读取者的可见范围；私有 observation/GM/memory 只按本次明确的合成审计范围入包，不改变 agent 原有 ACL，也不自动回灌 solver。默认公开交付只使用合成数据，原始大包留 ignored，本轮小型脱敏样例可入 Git。

包在写完且核验后原子发布，保留失败原因；不得出现目录已命名为成功但内容只写一半。固定证据重复导出时内容 hash 应稳定；导出时间/存储位置等易变 metadata 可以单列，不要求它们逐字节相同。

### 5.2 独立离线 verifier

Verifier 只读取证据与公开格式，不启动 DSH/Concordia，不调用模型/工具，不联网、不执行包中代码。可复用 SQLite/JSON/hash/已有验证库的成熟能力；优先最小依赖。归档输入若实现，限制路径和读取量，使用普通安全解析方式。

至少分别返回：

1. `bundle_integrity`：内容是否存在、hash/格式/版本是否一致。
2. `facts_consistency`：stream/seq/receipt/terminal/barrier/cursor/source refs 内部是否一致；gap、conflict、不对应的 operation 不能通过。
3. `scenario_completeness`：场景终态与世界/领域回执是否满足该冻结合同。
4. `task_outcome` 与 `execution_mode`：成功/明确拒绝/未知等，以及固定 fixture 属性。
5. 来源信任限制：hash 证明包内一致性，不能凭自述 manifest 证明上游二进制来源、签名真实性或真实模型执行。

合法 partial 包可以通过封装完整性，但其场景完成性仍为 partial/unknown，不能简化为单一 PASS；内部 task_failure 也不能被换成“缺证”掩盖。不要生成综合能力分数。

无需原任务根、原 DB 或作者缓存，verifier 仍应给出同样结论。对源 run 后续发现的完整性问题保留独立核验记录，不抹掉过去的历史声明，也不继续把过去 complete 当作当前可评估的充分条件。

### 5.3 最小导出验收

- 当前正确助手、两人社会场景、合法拒绝各有包并正确分类。
- 第二实体失败/unknown/缺 receipt 的包诚实 partial。
- 完整目录复制到新位置，原任务根不可访问的条件下仍可核验；不破坏用户原目录，可用独立测试进程/受控测试副本验证。
- 缺文件/hash 变化/重复或冲突 seq/不匹配 barrier/缺 memory source/未知格式版本不能被判完整。
- 用 hash 重新计算后的内部矛盾包也被语义 verifier 拒绝，不能只检查表面 hash。
- 相同 frozen 内容重复导出稳定；导出不产生新 run/worker/模型/工具/effect、不改旧 spec。
- 单 run 的包不夹带其他未引用身份或轨迹的数据；读写量与失败状态有上限。

## 6. 测试、证据与实现取舍

针对上述合同写有行为价值的测试，避免为了数量镜像实现。主路径复用 Phase 1B 的 fixture、公共 SDK 和真实 Engine，不用伪进程证明真实集成。

新证据放 `docs/validation/phase1b1/`，按测试实际语义标注：纯 SQLite 合同、受控并发/故障注入、真实 DSH fixture 集成、真实 Engine 边界、离线包验证等。状态保留 PASS/FAIL/BLOCKED/NOT_RUN，失败重跑创建新记录。

先跑相关小测试，再跑受影响的原 contract/runtime/failures/processes 回归；store/场景完成规则修改影响面大，应覆盖原成功、非法 action、四个关键故障窗口、去重/CAS、Job 清理。仅当新变更或失败需要时重复整套验证。无需为本轮重跑 Raven、安装 Harbor 或改变 DSH 依赖。

证据登记至少包括实际命令、退出码、平台、pins、测试/需求 ID、相关源码与测试文件 hash、清理结果、脱敏日志/原包 hash，以及未证明事项。只核对 product hash 不足以证明所有测试适用于当前变更；按影响范围保留运行后的绑定，文档变化可只做文档检查。

新增字段/CLI/包格式先设计小型可审阅样例；然后实现、测试。实现时持续检查源代码与安装包一致，避免测试用了旧 wheel。最后按锁文件完成干净环境的准备/安装与公开 CLI smoke；缓存 wheel 可复用，但要校验 hash 并如实标注网络获取范围。

测试和临时数据均用本任务受管目录。保持既有短路径、环境 allowlist、资源上限、owner 标记和 Job 清理。不为本轮改变系统设置或全局依赖。

## 7. 交付清单与结束 Gate

交付：

- H1–H3 所需最小产品改动及相应测试，没有空壳服务或未使用抽象。
- README 的新行为、已验证命令、旧库兼容、导出/验证与限制。
- Phase 1B.1 合同/结果/Gate、B1R1–B1R4 逐项结论、独立 evidence manifest；必要 ADR/backlog 更新。
- 一组小型合成完整/partial 包或可确定重建的 fixture，离线 verifier 文档。
- 用户要求的本地提交与 GitHub 推送，远端 SHA 校验结果。

`CONDITIONAL_GO` 需要：四项边界修正通过；旧库不被破坏；新完整性结论能从必要事实和场景终态核验；证据包脱离作者目录仍可验证；相关原回归与清理成立。通过仍仅是受限 fixture 基础设施，不是生产就绪、社会评估有效或模型能力提升。

关键 Gate 不成立时标 BLOCKED/NO_GO，说明缺口、已经完成的工作和最小后续修复。不要为显示进度放宽完成谓词，也不要把 budget=0 当成本轮本地工作阻塞。修正涉及旧声明时保留历史证据，通过新核验结论说明差异。

完成后停止。下一轮才规划 Phase 1C0 的离线 envelope/SOTOPIA parser 复用及测量合同；原 scores 对 null/list/number/bool 的缺陷仍是该阶段前置。本轮不实现 evaluator，不以 evidence verifier 冒充 evaluator，不开始 live 或 candidate 搜索。

最终发布步骤不可省略：

1. 检查本轮 diff、文档链接、schema/包格式样例及必要测试；确认没有无关修改/秘密/大缓存入提交。
2. 提交本轮源码、测试、文档和小型证据；保留失败记录与历史 manifest。
3. 普通 push 当前任务分支到 origin，并核对远端 ref SHA 与本地 HEAD 一致；远端有新提交先审阅整合，不 force push。
4. 最终中文报告：完成内容、实际测试、Gate/限制、commit/branch、GitHub 入口和复现入口。网络或鉴权失败时明确“本地已提交但 push 受阻”及原因，不能仅结束在“尚未推送”。不自动合并 main。
