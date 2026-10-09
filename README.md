# Actio-RSI · Phase 1C2B2

Phase 1C2B2 已完成测量完整性修复与预注册工程 pilot：计划 32 episodes / 64 seats，实际发送 54，admitted 53，not_run 10，unknown 1。raw→adapter→native 文本绑定和 actor own/public 输入边界已验证；独立集合谓词测量与完整分母可离线复核。

入口：[结果](docs/validation/phase1c2b2/RESULTS.md) · [Gate](docs/validation/phase1c2b2/GATES.md) · [合同](docs/validation/phase1c2b2/CONTRACT.md) · [CLI](docs/validation/phase1c2b2/CLI.md) · [预注册](docs/validation/phase1c2b2/preregistration.json) · [manifest](docs/validation/phase1c2b2/evidence_manifest.json)。费用/账单与上游权重身份仍 UNVERIFIED；本轮不构成研究能力排名、judge 校准或演化晋升。

## Phase 1C2B1 历史交付

TokenKey → 官方 DSH `0.1.5rc1` / `llm-pi-ai` → 真实 Concordia 的多模型 solver 闭环已完成，工程 Gate 为 **CONDITIONAL_GO**。`gpt-5.6` 与 `claude-sonnet-4-6` 各完成 compatible、conflict 两个 A→B episode：共 **8 次正式请求、8 份可信 usage，4,100 输入 / 40 输出 token**，无自动重试或新 unknown。compatible 达成调度，conflict 合法拒绝并完整记录 task_failure。

新增 `pilot-config.v5` / `scheduling-tokenkey.v1`，显式采用本轮用户授权的无金额上限策略，继续保留有限批次、请求级长度/期限、原子 Ledger、凭据隔离、幂等和只读导出。当前 **16 suites / 75 组通过**；旧 v2/v3/v4 与历史证据原义保留，C2B0 execute 仍拒绝。

当前入口：[结果与完整计数](docs/validation/phase1c2b1/02_results.md) · [Gate](docs/validation/phase1c2b1/03_gate.md) · [CLI](docs/validation/phase1c2b1/04_usage.md) · [合同](docs/validation/phase1c2b1/01_contract.md) · [账务](docs/validation/phase1c2b1/05_accounting.md) · [官方 adapter 复用](docs/validation/phase1c2b1/06_adapter.md) · [模型选择](docs/validation/phase1c2b1/07_models.md) · [manifest](docs/validation/phase1c2b1/evidence_manifest.json)。`python -m actio.gateway plan/preflight/verify` 不读凭据或联网；真实 execute 仅在精确 TokenKey origin 和显式本轮授权合同下运行。交付推送任务分支及 main。

正式执行仅 2 个响应含 `usage.cost`，币种/单位未核实，**实际费用与供应商接收数仍未知**。前置直接诊断另有 14 次生成尝试和 1 次目录 GET，不混入上述正式分母。上游模型身份及账单仍 UNVERIFIED；binary_source_mapping=unproven、full_controller_recovery=unsupported；judge、真人校准、研究/演化晋升仍 BLOCKED。本轮不是质量排名或生产部署。

## Phase 1C2B0 历史交付

真实 solver 接入的本机准备工程已完成，Gate 为 **CONDITIONAL_GO（仅 local_readiness_engineering）**。新增 `pilot-config.v4` / `scheduling-priced.v1`，沿用固定官方 Chat Completions adapter、DSH `0.1.5rc1`、真实 Concordia 与持久 Ledger，验证 USD 整数报价估算、内存假凭据注入、分层超时、未知占额和只读导出。v2/v3 原语义及历史证据保留。

真实模型请求、外部 provider 请求、真实费用均为 **0**。供应商兼容性和账单对账仍 **UNVERIFIED**；live 授权及执行均 **BLOCKED**。候选为 `deepseek-flash`，精确计费输入上界、1M 单位和额外费用仍未核实，预算建议不是批准。执行入口在读取凭据前拒绝；未进入 C2B1。

当前入口：[结果与本轮计数](docs/validation/phase1c2b0/02_results.md) · [Gate](docs/validation/phase1c2b0/03_gate.md) · [CLI](docs/validation/phase1c2b0/04_usage.md) · [合同](docs/validation/phase1c2b0/01_contract.md) · [费用、凭据与超时](docs/validation/phase1c2b0/05_cost_credentials_timeouts.md) · [未批准的具体批准包](docs/validation/phase1c2b0/approval_package.json) · [manifest](docs/validation/phase1c2b0/evidence_manifest.json)。`python -m actio.readiness plan` 零凭据/网络/Worker；本机预演为 `scripts/phase1c2b0_rehearsal.py`；离线核验为 `python -m actio.readiness verify <campaign目录>`。本轮仅推送 `phase1c2b0-solver-live-readiness`。

## Phase 1C2A.1 历史交付

固定 DSH `0.1.5rc1` 的官方 Chat Completions 本机链路已达 **CONDITIONAL_GO（仅 transport_stub 工程）**：无预置答案双 seat、真实 Concordia 两步调度、发送前 SQLite 持久预算、异常保守占额与只读 campaign 对账已验收。配置为 `pilot-config.v3` / `chat-completions.v1`，旧 v2 Messages 语义及历史 NO_GO 证据保留。

真实模型请求、外部 provider 请求和真实费用均为 **0**。本机 HTTP、合成 usage 与历次失败分别统计于结果和 manifest。live、人工校准、judge、研究效度和演化晋升仍 **BLOCKED**。本轮仅发布任务分支 `phase1c2a1-chat-completions-budget`。

当前入口：[结果与实际计数](docs/validation/phase1c2a1/02_results.md) · [Gate](docs/validation/phase1c2a1/03_gate.md) · [CLI](docs/validation/phase1c2a1/04_usage.md) · [合同](docs/validation/phase1c2a1/01_contract.md) · [复用](docs/validation/phase1c2a1/05_reuse.md) · [预算生命周期](docs/validation/phase1c2a1/06_budget.md) · [manifest](docs/validation/phase1c2a1/evidence_manifest.json)。离线复核入口 `python -m actio.transport_campaign <campaign目录>`；本机执行入口 `scripts/phase1c2a1_smoke.py`。preflight 始终 BLOCKED/退出 2，无 live 执行入口。

## Phase 1C2A 历史交付

本轮在官方 Messages adapter 准入处 **NO_GO**：固定 DSH `0.1.5rc1` 实际发送 `/chat/completions`；显式加载参考源码的 `@deepseek-ai/dsh-llm-deepseek-api-key` 报 `ERR_MODULE_NOT_FOUND`。按冻结 Prompt 的停止条件，未继续实现无答案双 seat transport、逐 attempt 预算账本和新模式验收，未升级依赖。

已交付 `pilot-config.v2` 角色配置修正、4 次有界协议定位、47 组通过的配置/旧路径回归及固定旧版 C0/C1 只读复核。真实模型请求和费用均为 **0**，本机 provider HTTP 接收合计 **2**。live、人工校准、研究效度与演化晋升均 **BLOCKED**。发布仅到 `phase1c2a-solver-transport-and-budget`，不合并 main。

当前入口：[结果](docs/validation/phase1c2a/02_results.md) · [Gate 与备选](docs/validation/phase1c2a/03_gate.md) · [CLI](docs/validation/phase1c2a/04_usage.md) · [合同](docs/validation/phase1c2a/01_contract.md) · [复用与协议差异](docs/validation/phase1c2a/05_reuse_and_protocol.md) · [预算状态边界](docs/validation/phase1c2a/06_budget.md) · [证据 manifest](docs/validation/phase1c2a/evidence_manifest.json)。当前 preflight 永远 BLOCKED/退出 2；旧 v1 配置只用固定旧版本核验。新配置完整不代表传输验证或 live 授权。

## Phase 1C1 历史交付

新增离线两人共同排程 TaskSpec、真实 DSH + Concordia 两步闭环、独立只读 campaign 核验、盲化标注交接与始终 BLOCKED 的 provider preflight。42 组相关行为验收通过；模型请求、真实人工标签、独立研究单位均为 0。工程 Gate 为 **CONDITIONAL_GO**，人工校准 / live / 研究效度与演化晋升仍为 **BLOCKED**。

当前入口：[结果](docs/validation/phase1c1/02_results.md) · [CLI 复现](docs/validation/phase1c1/04_usage.md) · [冻结合同](docs/validation/phase1c1/01_contract.md) · [Gate](docs/validation/phase1c1/03_gate.md) · [证据 manifest](docs/validation/phase1c1/evidence_manifest.json) · [标注指南](docs/validation/phase1c1/05_annotation.md) · [pilot 草案](docs/validation/phase1c1/06_pilot.md)。`python -m actio.campaign verify-campaign <目录>` 完全只读；`python -m actio.preflight <配置>` 当前始终退出 2。代码 pins 改变后须新身份/新卡，不刷新旧身份；C0 原记录由固定 C0 提交复核。

## Phase 1C0 历史交付

新增离线测量准入、确定性合同指标、严格 controlled-response envelope 与 SOTOPIA 最小 parser/schema 复用。输入绑定修正由在线 seal 和离线 verifier 共用；原证据不改写。35 组相关行为验收、零模型请求，Gate 为 **CONDITIONAL_GO（仅离线工程）**。

本阶段入口：[结果与计数](docs/validation/phase1c0/02_results.md) · [实测复现](docs/validation/phase1c0/04_usage.md) · [SOTOPIA 复用](docs/validation/phase1c0/05_sotopia_reuse.md) · [Gate](docs/validation/phase1c0/03_gate.md) · [独立证据](docs/validation/phase1c0/evidence_manifest.json)。离线入口是 `python -m actio.evaluation` / `actio-eval`，只读源包，结果另存不可变文件。RuntimePort 的 evaluator capability 仍为 false，运行中的 agent 不获得评估或 judge 上下文。

下文保留 Phase 1B.1 runtime 准备与运行说明；其中 evaluator 未开放的描述指 runtime/live 路径。当前 stored verification.json 的历史处理以 Phase 1C0 合同为准。

单机、持久化、合成 fixture 双场景基础设施。Python 管身份/spec、run/lease/receipt、SQLite facts/memory；官方 DSH SDK + TS executable 管 agent loop、MCP 和原生 journal；真实 Concordia Sequential 管社会场景调度及 GM 裁决。预算 **0**，模型和 GM 输出为固定 fixture，未开放 live provider。

入口：[本轮合同](docs/validation/phase1b1/01_contract.md) · [实现与验收](docs/validation/phase1b1/02_results.md) · [Gate](docs/validation/phase1b1/03_gate.md) · [独立证据](docs/validation/phase1b1/evidence_manifest.json) · [包格式与离线核验](docs/validation/phase1b1/04_bundle_format.md)。[Phase 1B 历史证据](docs/validation/phase1b/evidence_manifest.json) 与 Phase 1A probes 保留原样。

本轮修正：场景终态独立于 operation 完成；原子 request claim 的赢家才可执行；recover 只操作指定 run；冻结起点 replay 拒绝显式 override。SQLite schema 版本为 2，旧库只读或显式迁移到新副本。新增单 run 审计包导出与标准库离线 verifier。

## 准备

要求 Windows x64、Python **3.12**（实测 3.12.10），仓库外可写短目录，例如 `D:\actio-p1b`。不改系统长路径设置，不安装全局依赖。发行物及闭包使用 [requirements.lock](requirements.lock)，Concordia 使用固定源码及逐文件 [hash](src/actio/pins/concordia.json)，只安装必要导入闭包。

从仓库根执行。联网准备入口如下；无缓存全量网络下载在本机曾超时，最终验收使用相同 hash 的缓存 wheel，不把网络超时计作产品通过。

```powershell
python -X utf8 scripts/bootstrap.py
```

可先按锁文件准备 ` .local/wheels ` 缓存（所有 wheel 仍由 pip 校验 hash）：

```powershell
python -m pip download --require-hashes --only-binary=:all: -r requirements.lock -d .local/wheels
```

本机已验证的完全离线方式（参考源码仓库只读；相对路径对应本工作区布局）：

```powershell
python -X utf8 scripts/bootstrap.py --offline-wheels --concordia-source ../../codebase/15_concordia/repo
```

`--venv <新目录>` 可建立另一干净环境；`--wheel-cache <目录>` 只用于安装加速。省略 `--concordia-source` 会获取固定 commit 的 GitHub 归档并检查每个 Python 文件及 LICENSE。`--offline-wheels` 仅关闭 pip index，不关闭这一步源码下载。安装后的产品从自己的环境导入包，不引用参考仓库或 Phase 1A `.local`。

## 运行与查询

以下均为公开 CLI；每条命令都是新的控制进程。所有身份/内容均为合成数据。

```powershell
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite init
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite agent A --create
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite agent B --create
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite assistant --agent A --key assistant-one
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite memory --agent A --environment assistant --target social --revision 1
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite social --a A --b B --key social-one --memory-revision 1
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite query social-one
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite reconcile assistant-one
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite social --a A --b B --key replay-one --replay social-one
.local/venv/Scripts/python.exe -m actio capabilities
```

可以把全局 `--short-root D:\actio-p1b` 放在子命令之前。相同 request key/请求返回原记录，包括 unknown；不同请求复用 key 被拒绝。新代码/pins 不会改写已有 AgentSpec，需创建明确的新身份/spec；本 slice 不提供 spec 自动迁移。`social --illegal` 是固定非法行动演示，真实 ActionSpec 验证会在 world 更新前拒绝，记录 task_failure。

重启后遗留的活动 owner 必须先被证明已死亡，才可回收 lease：

```powershell
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite reconcile assistant-one --recover-owner
```

命令只核对受管 journal 和本地事实，**不会再次调用模型或工具**。owner 活着时拒绝接管，TTL 不授权接管。缺 receipt、flush 或领域效果时维持 incomplete/needs_reconcile。status 是本地台账状态。

未知 run、历史 run 的恢复请求不会回收另一条 lease 的 Job。相同 key 的并发调用以 SQLite 原子决定为准；未取得执行资格的调用者只返回赢家的首次冻结输入。`social --replay ...` 不允许同时提供 `--illegal` 或 `--memory-revision`，即使 revision 恰巧相同也拒绝。

## 旧库与证据包

只有 `init` 可以创建数据库。`query`、`agent <id>` 和 `export` 可以只读打开已知 Phase 1B schema=0；不存在路径、未知版本和残缺结构明确失败。旧 spec 的源码 pins 不会自动刷新；不兼容的旧身份仍可查询、迁移和导出，但不能用新 runtime 执行。

迁移仅支持 0→2 到**新的副本**。先用 SQLite backup 读取含 WAL 的一致快照，再在副本事务中增加表和版本。保留 `.backup.sqlite`、hash 和 `.migration.json`；失败保留备份/staging，重新尝试用新输出名。重复迁移到同一已成功副本只核对来源，不覆盖。不要将旧 `trajectory=complete` 视作新合同通过；无新终态凭据的历史记录核验为 `legacy_unverified`。

以下命令已在新隔离环境按同样 CLI 调用运行；数据库和输出位置可替换为自己的合成任务路径。导出父目录须存在、目标目录须不存在。

```powershell
.local/phase1b1-delivery-venv/Scripts/python.exe -m actio --db .local/legacy.sqlite query social-one
.local/phase1b1-delivery-venv/Scripts/python.exe -m actio --db .local/legacy.sqlite migrate --output .local/migrated.sqlite
.local/phase1b1-delivery-venv/Scripts/python.exe -m actio --db .local/demo.sqlite export social-one --output .local/social-bundle
.local/phase1b1-delivery-venv/Scripts/python.exe -m actio verify .local/social-bundle
.local/phase1b1-delivery-venv/Scripts/python.exe -m actio.verify docs/validation/phase1b1/samples/social
```

包只含该 run、登记的 native 原始行和所引用 memory 的最小来源证明，不复制整库或 DSH home；单包 32 MiB、20,000 行预算。基于同一个 SQLite 读事务，在 staging 写完并核验后原子 rename。失败保留原因；重复导出的内容 hash 稳定，时间 metadata 单列。包内绝对路径若存在只是原始审计文本，verifier 不跟随读取。

核验分别输出 `bundle_integrity`、`facts_consistency`、`scenario_completeness`、`task_outcome` 和 `execution_mode`。合法拒绝可为 `complete/task_failure`；合法 partial 包可通过封装完整性，不能当完整 episode。退出码 0 也可能是诚实 partial，消费方必须读取各维度；格式损坏/内部矛盾退出 2。历史状态与当前核验单独显示。保留新导出包即可保存之后发现的缺口，既有包和历史 run 声明不改写。

`python -m actio.verify` 只依赖标准库与产品的 common/terminal/verify 模块，不导入或启动 DSH/Concordia、不联网、不执行包中代码。hash 不证明作者签名、二进制来源或真实模型能力。公开样例仅合成数据；审计读者能看见必要 private observation/GM/memory，这不改变 agent ACL，也不自动回灌 solver。

干净环境准备和完整公开 CLI smoke（每次创建新的受管短根）：

```powershell
.local/venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --venv .local/phase1b1-delivery-venv --offline-wheels --concordia-source ../../codebase/15_concordia/repo *> .local/phase1b1-delivery-bootstrap.log
.local/phase1b1-delivery-venv/Scripts/python.exe -X utf8 scripts/phase1b1_smoke.py --bootstrap-log .local/phase1b1-delivery-bootstrap.log
```

首次没有既有 venv 时以 Windows Python 3.12 执行 `scripts/bootstrap.py` 即可。本轮准备使用 41 个已校验的缓存 wheel 和固定本地 Git archive；未重新做全量网络下载。

## 验证

```powershell
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py contract
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py runtime
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py failures
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py processes
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py reliability
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py entry_concurrency
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py schema
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py evidence
.local/venv/Scripts/python.exe -m pip check
```

必须先安装当前源码；runner 会逐文件拒绝源码与 installed package 不一致的测试。每次运行创建新的 evidence JSON，失败也保留。测试创建的 `D:\actio-p1b-tests\<唯一目录>` 保存合成 raw journal/SQLite/日志，不自动删除；venv、wheel、binary 不入 Git。故障注入只在 `tests/`，不进入产品包。每组 suite 为聚合行为验收，不能把聚合数量当作研究样本量。

新测试使用 `D:\actio-p1b1-tests\<唯一目录>`；本轮所有验收记录写入 `docs/validation/phase1b1/evidence/`。原 RuntimePort 同 host 两 turn 测试继续核对两次原生 receipt 和 memory effect；其结果现在明确为 operation complete、scenario incomplete，因为它没有完成助手的一步场景合同。

## 范围

支持持久身份/spec/query、新 native session、当前 host 内串行 turn、只读 MCP、显式停止、只读 reconcile 和冻结起点重执行。RuntimePort 位于 [runtime.py](src/actio/runtime.py)，Memory 控制入口位于 [memory.py](src/actio/memory.py)。运行 freeze memory 内容、实际选中 ID/revision、顺序、截断和 namespace；A→social 的共享在 spec 中显式授权，B 无权检索 A 的 private namespace。

强制结束 Job 不是 semantic cancel 或效果回滚。native reopen/resume/fork、在线 catchup、完整 world restore、动态逐调用审批、任意写工具、evaluator/live provider 明确 unsupported。没有 Web/UI/HTTP 服务，没有完整心智/演化/训练栈。外部 `.mjs` 是受信固定闭包，不承诺恶意插件沙箱安全。二进制到源码构建映射仍未证明。
