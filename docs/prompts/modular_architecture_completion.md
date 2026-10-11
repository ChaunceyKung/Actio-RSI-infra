# Codex Prompt：完成 Actio-RSI 模块化重构

请在本仓库继续完成模块化重构，并在最终验证后提交、推送任务分支和 `main`。这是工程重构任务，不是 C6 实验任务。

仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`

当前已发布 SHA：`91895097fe2661709cc465bdb393d784523fdbdb`。先 `fetch`，确认本地和远端；不要 reset、force push 或覆盖并发提交。

## 先读并保留的事实

读取 `AGENTS.md`、`docs/architecture/CONTINUATION_PLAN.md`、`README.md`、`MODULES.md`、`REFACTOR_PLAN.md`，以及 `docs/validation/refactor_modularity/{RESULTS,GATES,CLI,architecture.json,regression-summary.json,identity-and-history.json,compatibility.json}`。

局部成果包括 contracts、tasks 的部分提取、domain accounting/candidate、独立 oracle、Ledger/fixture adapter、wheel、四 console scripts、module/IPC 入口、产品→tests/scripts 清除、555 项差分和最终 C5 fixture 矩阵。不要回退这些工作。

尚未完成：全局依赖 SCC 为 23/7/3/2/2，89 个 Python 中仍有 54 个根实现模块；Store、profiles、application、evidence、runtime/environment 没有完成分层；readiness 34-suite 中 6 个方法产生 15 failures + 1 error。整体必须继续标为 INCOMPLETE，直到本 Prompt 的退出条件全部满足。

## 范围边界

- 暂停 C6、真实 provider、目录 GET、外部 MCP、judge、人工校准、训练、部署、候选激活和完整 controller 恢复。
- 新的外部请求和真实 provider 请求必须为 0。使用 loopback fixture、固定向量和本机官方 DSH/Concordia；不读取或发送真实 API key。
- 不升级 DSH/Concordia/依赖，不修改历史阶段合同、旧 quote、pins、manifest、raw/DB、失败记录、19 claims、evaluation/candidate decisions 或未来计划。
- 不改写 C4 缺失后缀，不补样，不把新的本机运行合并到旧实验分母。
- 用户已授权正常提交和推送 GitHub；每轮完成适用验证后都提交，并普通推送任务分支及 `main`，分别用 `git ls-remote` 核对 SHA。网络失败时保留提交并准确报告，绝不声称已发布。

## R7：修复 readiness 的可重复 rehearsal 时间

当前 `src/actio/readiness_quote.json` 的窗口为 `2026-10-08T16:00:00Z` 至 `2026-10-10T16:00:00Z`，在当前日期已经过期。系统时钟下拒绝是正确行为；现有成功路径的后续 receipt/usage 错误是级联。

实现小型 `ClockSpec`/Clock port：

1. live/system 模式使用真实 UTC 当前时间；过期报价必须拒绝。
2. 仅 `priced_rehearsal` 允许合同内的 fixed UTC instant。`rehearsal()` 默认使用原报价窗口内的固定 instant，并将其写入 config/ledger meta，使父进程、TS worker 和 `python -m actio.budget` IPC 使用同一值。
3. 禁止环境变量时间、全局 datetime monkeypatch、测试进程本地时间和忽略 `quote_current` 的开关。Clock 必须进入 hash、账务快照和证据。
4. 增加边界测试：valid_from 前拒绝、valid_from 接受、窗口内接受、valid_until 正好拒绝、valid_until 后拒绝；另测 system-clock expired rejection 和 fixed-clock child IPC success。
5. 先执行 readiness suite；保留 unknown、reservation、receipt/terminal、usage、跨进程竞争和篡改断言。按首个异常修复，不删除断言或 skip。

如果需要新字段，创建当前 profile 的明确 revision 和新的 refactor evidence；不要修改历史 quote 或历史 manifest。新配置必须能与旧固定 reader 区分。

## R8：消除任务 SCC

当前 `tasks.candidate/evaluation/finite/robustness/scheduling/scheduling_v2/diagnostic` 构成 7 节点 SCC。将公共 sealed/require/基础 TaskSpec/visibility 放入 `actio.tasks.core`；family/version 模块变成叶模块；建立唯一 `actio.tasks.registry` dispatcher。

叶模块不得导入 registry、其它阶段 dispatcher 或 application；registry 可以导入叶模块。`task_evidence`、terminal、transport contract 通过 registry 的稳定协议使用任务版本。保留 schema、行动、可见性、B 使用实际 A 历史和独立 oracle。根旧路径只能是薄 shim，新实现不得依赖 shim。

## R9：拆 profile、Ledger 和 preflight

当前最大 SCC 主干是 `ledger → budget → 各阶段 contracts/campaigns → preflight → 各阶段 contract`。建立 `actio.profiles.registry`：

- 集中 schema/profile 分类、endpoint、reservation/caps、wire binding、trusted usage、terminal keys、mode 选择。
- profile validators 只依赖 contracts/domain/tasks，不导入 Ledger、application、preflight 或其它 profile validator。
- `adapters.persistence.ledger` 只依赖 contracts、domain accounting、filesystem identity 和 profile policy，不导入根 `budget.py`。
- `interfaces.budget` 装配 Ledger 和 policy；根 `budget.py` 仅为兼容 shim。
- preflight 是 application/interfaces use case；profile 不导入它。

保持 SQLite schema、WAL/readonly、事务边界、authority anchor、一次资格、unknown/usage 语义和 TS IPC stdout/exit code。不能用多个 repository 或第二 Ledger 替代原子事务。

## R10：完成 Store、runtime、evidence、application

1. Store/database/schema/migration 分为 persistence 资源、连接/事务和 domain 状态规则；candidate/evaluation/episode/memory 用例进入 application；保持同一连接多表事务。
2. runtime/host/supervisor/MCP/native journal 进入 `adapters.runtime`；Concordia 进入 `adapters.environment`；transport/fixture/TS plugin 进入 `adapters.transport`；application 只依赖最小 ports。
3. verify、stream/channel audit、history trust、diagnostic package 进入 `evidence`；纯 reader 不导入 runtime、SDK、DB 写入或执行 artifact；diagnostic runtime 与 transport diagnostics 不互相导入。
4. application 统一 episode/campaign/evaluation/diagnostic 编排；interfaces 只负责解析、受信 profile 选择、装配和退出码。
5. 所有根实现模块必须迁移或拆分；根目录只可保留 `__init__`、`__main__` 和登记的 console/module/IPC shim。不要修改架构工具去忽略根实现或循环。

## 终验

1. 架构工具真实返回 `PASS`：SCC=0、unmigrated root=0、violations=0；继续扫描函数内和 literal dynamic import。
2. readiness 6/6 通过，附 boundary 和跨 IPC Clock 收据。
3. 同一个最终 wheel 执行全部 34 suite、163 个测试方法，163/163 通过；旧安装收据不能拼接成最终结果。
4. 最终 wheel repo 外安装、`pip check`、四 console/module/child IPC、SQL/JSON/MJS/license resources 通过；minimal `--no-deps` 纯 reader 单独通过。
5. 最终新源码只做一次必要的本机 DSH/Concordia/MCP 和 C5 fixture 验收；外部请求 0，正式计数为 12 sends、5 settled、7 unknown、6 not_run，所有 Worker/服务/端口清理。
6. 固定历史 reader 和旧材料保持不变；新实现使用新的 refactor identity。

更新架构、验证、迁移、兼容、identity、regression、freeze、publication 文档。只有 G1/G7 和受影响 G2–G6 全部重验通过，整体才可改为 PASS；否则准确保留 INCOMPLETE/BLOCKED。完成后安全快进更新任务分支和 `main`，分别 `git ls-remote` 核对远端 SHA，工作树干净。停在重构，不进入 C6。
