# 模块化重构续作计划

本计划针对已发布的 `91895097fe2661709cc465bdb393d784523fdbdb`。远端 `main` 和 `refactor-modular-architecture` 已核对到该 SHA，网络发布阻塞已经解除；当前阻塞是工程验收未完成。

## 当前判断

| 项目 | 结论 |
|---|---|
| 产品可安装性和本机闭环 | 已通过范围内验收；最终 wheel 完成 9 场景、12 次 loopback，5 settled/usage/admitted、7 unknown、6 not_run |
| 行为差分 | 555 项完整 JSON 差分一致 |
| 历史保全 | 1,048 个历史文件和工具字节未变，固定 reader 通过 |
| 架构 Gate | **INCOMPLETE**；89 个 Python 模块、403 条内部依赖，SCC 为 23/7/3/2/2，仍有 54 个根实现模块 |
| 回归 Gate | **INCOMPLETE**；34 个 suite、163 个测试方法中 157 个通过；readiness 6 个方法包含 15 个失败和 1 个错误 |
| 发布 | PASS；但发布成功不改变上述两个 Gate |
| 实验边界 | 继续暂停 C6、真实 provider、目录 GET、judge、人工校准和候选晋升 |

readiness 的失败首先发生在报价检查：当前系统日期已经晚于 `readiness_quote.json` 的 `valid_until=2026-10-10T16:00:00Z`。之后的 `receipt/terminal evidence missing`、`denied` 和 `usage=None` 是同一前置拒绝造成的级联，不应逐条放宽断言。报价文件不能刷新成“永久有效”，也不能改系统时钟或 skip 测试来获得 PASS。

## 推荐顺序

### R7：先修复可重复的 rehearsal 时间

目标是让本机 rehearsal 的成功路径有一个显式、可审计、跨进程一致的时钟，同时保留真实系统时钟下的过期拒绝。

1. 在 `contracts`/`profiles` 中定义小型 `ClockSpec`：生产/live 默认为 `system`；仅本机 `priced_rehearsal` 允许 `fixed`，时间戳必须是显式 UTC 字符串，并由合同绑定。
2. `readiness_contract.rehearsal()` 为当前测试返回冻结在旧报价有效窗口内的 fixed time；不要修改旧报价、报价来源、金额、币种或 valid_until。
3. 将 Clock 传入 Ledger 的报价检查，并保存在 Ledger config 中；TS budget IPC 从已持久化 config 取得同一 Clock。禁止用环境变量、全局 monkeypatch 或子进程本地当前时间绕过合同。
4. `quote_current(c, now=...)` 的默认路径仍使用系统时钟。新增边界向量：valid_from 前拒绝、起点接受、窗口内接受、valid_until 正好拒绝、之后拒绝；live/system 过期拒绝必须保留。
5. 先只运行 readiness suite，逐一确认所有 6 个方法通过，再确认预算、receipt、unknown、跨 IPC 和篡改测试仍成立。任何剩余失败按首个异常修复，不把后续级联错误单独打补丁。

### R8：消除任务层的 7 节点循环

当前 `tasks.candidate/evaluation/finite/robustness/scheduling/scheduling_v2/diagnostic` 互相导入，根因是 `scheduling.py` 既是公共原语又是版本 dispatcher。

- 新建无业务依赖的 `tasks.core`，放 `require`、sealed TaskSpec、行动/观察的共享结构和纯通用检查。
- 各 family/version 模块只依赖 `contracts`、`domain`、`tasks.core` 或更低层数据；不得导入 dispatcher。
- 新建 `tasks.registry` 作为唯一版本选择点，由 application/interfaces 调用；dispatcher 可导入叶模块，叶模块不能反向导入 registry。
- `task_evidence`、terminal、transport contract 只依赖 registry 的稳定协议，不再自行导入所有阶段任务。
- 原根 `task_*` 路径只保留薄兼容 shim；shim 不被新实现导入，架构检查器必须把它识别为兼容入口而非实现。

退出条件：任务 SCC=0；555 差分、输入可见性、B 使用实际 A 历史、独立 oracle 与非法输入拒绝保持一致。

### R9：把 profile/账务选择从 Ledger 中抽离

当前最大 SCC 的主干是 `adapters.persistence.ledger → budget → 各阶段 campaign/contract → preflight → 各阶段 contract`。应建立单向的 profile registry：

```text
contracts → domain → profiles/registry → adapters.persistence.ledger
                                  ↘ application
```

- 从根 `budget.py` 抽出纯的 schema/profile 分类、endpoint、reservation、wire binding、usage、terminal key 和 cap policy。
- `profiles.registry` 是唯一阶段选择点；每个 profile validator 只能依赖 contracts/domain/tasks，不得导入 Ledger、application 或其它 profile 的 validator。
- Ledger 只依赖 contracts、domain accounting、filesystem identity 和 profile registry；不再导入 `budget.py`，也不反向导入 readiness/gateway/pilot/suite/candidate campaign。
- `interfaces.budget` 只组装 Ledger 和 registry；`actio.budget` 根文件变成兼容 shim。
- `preflight` 变成 application/interfaces 的显式 use case；profile 模块不能导入它。

退出条件：最大 profile/ledger SCC=0；Ledger 的 SQLite 事务、一次资格、unknown 保留和 budget IPC 输出逐字段不变。

### R10：完成 Store、runtime、evidence 和 application 分层

按依赖顺序处理，避免一次性搬运：

1. `persistence.schema/migrations` 只负责资源和复制迁移；`persistence.store` 只持有连接/事务；`domain` 持有状态转移规则；`application` 持有 candidate/evaluation/episode/memory 用例。保留同一连接内的多表事务，不引入第二 Store。
2. `adapters.runtime` 接 DSH、Windows Job、MCP、native journal；`adapters.environment` 接 Concordia；`adapters.transport` 接发送和 loopback fixture；`application` 只调用小型 ports。
3. `evidence` 拆为纯 bytes/对象核验、history trust registry 和外层受限 I/O；`diagnostic_runtime` 与 `transport_diagnostics` 不再相互导入。
4. `application` 统一 episode/campaign/evaluation/diagnostic 编排；`interfaces` 只负责参数、选择受信 profile、装配 adapters。
5. 所有根目录实现模块都必须迁移或拆分；只保留登记的 `__init__`、`__main__`、console/module/IPC 兼容 shim。不能把大实现改名成 shim，也不能修改架构工具让根实现被忽略。

## 必须达到的最终 Gate

1. 架构检查器真实返回 `PASS`：SCC=0、无未迁移根实现、无 product→tests/scripts、无纯层副作用或反向 shim 依赖。检查器继续扫描函数内 import 和 literal dynamic import，不加“历史模块白名单”隐藏循环。
2. readiness 6/6 方法通过；另有明确的 system-clock expired rejection 和 fixed-clock cross-IPC rehearsal 收据。
3. 全部 34 suite 在同一个最终 wheel 上执行，163/163 通过；旧安装上的 PASS 不能合并成最终 wheel 的 PASS。
4. 最终 wheel repo 外安装、`pip check`、四 console scripts、module/child IPC、SQL/JSON/MJS/license resources 全部通过；纯 reader 使用无 DSH/Concordia 的 `--no-deps` 环境独立通过。
5. 最终新源码只做一次必要的本机 DSH/Concordia/MCP 和 C5 fixture 验收；仍保持外部请求 0，并记录正式 12 sends、5 settled、7 unknown、6 not_run 及清理。开发接收数与正式矩阵分开。
6. 固定历史 reader、旧 quote/pins/manifest、1,048 个历史文件、失败记录、19 claims、evaluation/candidate decisions 保持不变。

## 不建议的做法

- 不刷新 `readiness_quote.json`，不把过期报价改为当前价，不为通过测试改变系统时间。
- 不把 23 节点循环拆成通用 service/repository 或微服务；目标是可读的模块化单体。
- 不把全部旧根文件保留为“兼容层”；兼容层只能转发，且新实现不能依赖它。
- 不用旧 wheel、旧 runtime04 或混合安装的回归结果宣称最终全量通过。
- 不因架构重构启动真实 provider、补 C4、做 judge 或进入 C6。

只有在 G1/G7 和受影响 G2–G6 重新验证后，才能把整体状态从 INCOMPLETE 改为 PASS；否则保留精确的 BLOCKED/INCOMPLETE 结论并正常发布。
