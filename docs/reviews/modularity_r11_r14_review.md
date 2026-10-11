# R11–R14 目录与设计文档审阅

日期：2026-10-11。代码/证据基线：`ccc7399dc3e31367543df7d1c196eefb705c131b`；R7–R10 最终产品提交：`86fcee8daf0cfba3721b40dc8cd19580a1b12a56`。

## 结论

R7–R10 已完成主要职责拆分，下一步应做**有限的目录组织与可读性收尾**。优先改善 evidence、测试导航与边界检查，然后在新的最终 wheel 上做行为保持验收。无需再搭一套架构，也无需继续实验。SQL/事务抽象深化单列为未来工作，不与本轮搬迁捆绑。

本次已更新三份当前设计文档：[系统一页图](../architecture/README.md)、[模块卡片](../architecture/MODULES.md)、[关键流程](../architecture/FLOWS.md)，并修正根 README 的旧路径与过时待办。目录搬迁和新检查器尚未实施；交给[下一 session Prompt](../prompts/refactor_directory_r11_r14.md)。

## 核验了什么

| 项目 | 本次独立核验 |
|---|---|
| 本地及远端 | 本次开始时 main、refactor-modular-architecture 均为基线 SHA，工作树干净 |
| 现有 AST 检查 | 调用 `tools/refactor/architecture.py` 的 inspect：163 modules、594 edges、SCC=0、violations=0、unmigrated_root_modules=0 |
| 历史 manifest | completion manifest 的 49 项逐一与基线 Git blob 做 SHA256 比较，全部相同；采用其声明的 Git blob 字节口径，不混用 CRLF 工作树 |
| 当前目录 | evidence 30 个 Python 文件（29 实现 + init），interfaces 20，application 19；根层 19 shims + init/main |
| 测试与工具 | tests 根层 39 个 Python 文件，其中 34 个 test suite；另有 fixtures/support；tools/refactor 12 个 Python 文件，scripts 根层 88 个 |
| 模块体量 | 最大当前产品文件 349 行，不能据现状声称仍有巨大单文件实现 |
| 建议 evidence 分组 | 将当前 AST 边投影到下面五组，29 实现全部覆盖，组间无环；仅为静态方案核验，尚未执行代码迁移 |

R7–R10 的 34 suites / 164 方法、555 差分向量、最终 C5 12/5/7/6 及清理来自已发布验收，不是本次新执行。原 readiness 启动超时、后续失败与同 wheel 隔离重测均保留；不能概括成单次全绿运行。本次未运行 Worker、未读真实凭据、未进行外部实验请求。

## 按影响排序的发现

| 优先级 | 发现与证据 | 下一步 |
|---|---|---|
| P1 | [test_modularity.py](../../tests/test_modularity.py) 多处用 `glob('*.py')`，只看当前层目录；搬入子包会漏扫。相对导入的边界解析也不完整 | 先升级递归与导入解析，用嵌套违规、相对导入、函数内/字面量动态导入反例证明能拒绝，再搬文件 |
| P1 | [validate.py](../../tools/refactor/validate.py) 依赖平铺 `test_` 模块名；[completion.py](../../tools/refactor/completion.py) 按原路径对照方法；`suite_evidence` 消费同轮 `suite_runtime` | 搬测试前建立稳定 suite ID → 新模块路径及方法映射，防止套件丢失、重复或读旧材料 |
| P2 | evidence 的协议、封包、campaign、谱系与故障诊断共 29 实现在同一级 | 做下列五组划分；其余层暂保持，增加实际入口导航 |
| P2 | 19 个根 shim 与实现混在视觉上；盲目删除会破坏 CLI、IPC 与公开 reader | 逐项记录为何保留、转发到哪里；内部不得反向依赖 shim；不为每个私有旧地址新造 shim |
| P2 | 根 README 仍列 `store.py/database.py/scenarios.py` 等旧根实现，写着“目标设计，尚未实施”“本轮只交付设计” | 本次已修正；下一轮按最终真实目录同步三页简明设计 |
| 后续独立事项 | [StoreOperations](../../src/actio/application/store.py) 仍直接执行 SQL，由 [Store](../../src/actio/interfaces/store.py) 与 Connection 多继承组合 | 如需数据库可替换性，另做单连接 transaction/UoW 设计及行为验证；本轮只诚实记录，不因无 sqlite3 import 宣称已完全解耦 |

现有 AST PASS 有效，但含义有限：它检查模块图、根 shim 和规定的纯层规则，并非全部架构规则的完备证明；shim 判定目前还依赖开头 docstring。SCC=0 不能替代外部 I/O、全局状态、事务语义、包层职责与可安装性的检查。下一版检查规则应标版本，不能倒写旧 G1–G8 的结论。

## 拟议目录：只整理确有收益的位置

下面是目标，不是当前文件系统快照：

```text
src/actio/
├── contracts/ domain/ tasks/ measurement/ profiles/  保留现有职责层
├── application/ interfaces/ adapters/               保留现有边界
├── evidence/
│   ├── audit/        协议、通道、传输合同、账务认证
│   ├── bundles/      单包、输入、terminal 与评估 envelope 核验
│   ├── campaigns/    campaign 测量、registry、校准
│   ├── lineage/      候选与 evaluation 历史、报告入口
│   └── diagnostics/  失败观察、合成夹具、任务诊断、未来计划
└── 登记根 shims 与资源                             保持外部兼容

tests/
├── architecture/    递归边界、兼容入口、依赖规则
├── unit/            按实际依赖核实的规则与计算测试
├── integration/     SQLite、快照、文件与组件集成
├── runtime/         官方 Worker / Concordia / loopback 验收
├── support/         当前共享 helper、子进程入口与测试 stub
└── fixtures/        数据和测试资源

tools/README.md      标明现有 tools/refactor 的维护命令与历史专用命令
scripts/README.md    分辨仍维护的 bootstrap 与固定历史阶段脚本
```

不为 contracts/domain 等小包强行再加一层，也不要求把每层都拆成相同子目录。interfaces 的 CLI、装配、IPC 可先在模块卡片中分清；只有实际导航收益与依赖证据支持时才追加物理移动，不能作为无限扩展范围的理由。

### evidence 文件映射草案

表内名称省略 `.py`，共 29 个。迁移前应逐项检查外部公开性、调用点、源码身份清单、测试和资源路径；方案允许据证据微调并记录原因。

| 子包 | 当前文件 |
|---|---|
| audit | stream_audit、channel_audit、transport_contract、accounting |
| bundles | task_evidence、terminal、verify、eval_contract、evaluation |
| campaigns | transport_campaign、pilot_measurement、suite_measurement、candidate_measurement、evaluation_measurement、robustness_measurement、campaign_registry、campaign、calibration |
| lineage | candidate_lineage、evaluation_history、evaluation_lineage、candidate、candidate_evaluation、robustness |
| diagnostics | failure_observation、failure_fixtures、future_schedule、task_diagnostics、transport_diagnostics |

现有边的组间关系为：bundles → audit；campaigns → bundles/audit；lineage → campaigns；diagnostics → campaigns/audit。该图无环。不要在 `__init__.py` 中批量重新导出全部实现，从而重新制造隐藏循环。已登记的 `actio.evidence.failure_observation.from_entry` 等公开地址须保持；它与私有 import 的迁移策略不同。

## 执行顺序与完成条件

| 步骤 | 交付 | 完成条件 |
|---|---|---|
| R11 先补检查 | 有版本的递归检查、包分组规则、兼容清单、迁移映射 | 当前代码通过；嵌套/相对/局部/动态违规反例被拒绝；未解析导入明确列出，不记作已验证 |
| R12 evidence 分组 | 五组职责目录、最少必要兼容 facade、所有当前调用点同步 | 模块及规定子包依赖无环、内部不依赖 facade、业务逻辑保持；旧公开地址可用 |
| R13 测试与工具导航 | 按行为分层测试、support、稳定 suite/method 映射、两份命令导航 | 原 34 suites / 164 方法一一对应，无遗失/重复；runner、wheel、资源、子进程路径和顺序正常 |
| R14 文档与最终安装验收 | 三页更新、独立新 wheel、差分与历史保全、当前 C5、清理、结果与发布 | 新最终 wheel 上全部必要检查通过，明确失败与重测；普通推送任务分支及 main，独立核对 SHA |

这是一轮有终点的可读性收尾。验收通过即可关闭本轮重构，不因“目录还可以更漂亮”自动开启另一轮分包。

## 测试与历史策略

- 开发期按受影响能力做定向检查；最终源文件移动后，以同一最终 wheel 跑完整 34 suites、原 164 方法加新边界测试、555 向量差分、安装/CLI/预算 IPC 和一次正式 C5 九场景。全部通过且源码不再改变时不重复昂贵检查。
- 受控 runtime 使用已验证的短 ASCII 路径与锁定依赖。只允许 loopback 实验发送，真实凭据读取/外部实验请求为 0；Git 发布网络是另一个用途。
- 旧 1,048 文件保全集合、固定脚本、报价、pins、SQL/TS/许可资源、失败和旧 claims/decisions 按原身份验证。当前源码移动允许产生新身份，但旧证据始终按旧 Git reader 验证。不能修改旧 manifest 以适配新路径。
- 新测试路径需要升级当前维护 runner 的映射；历史专用 completion/readers 保持可按固定 SHA 重放。不要把所有旧脚本批量替换成当前私有 import。
- 新结果落入独立 `docs/validation/refactor_directory/`；最少保留 RESULTS、CLI、manifest 与必要机器证据，不新增一套冗长设计体系。
- 文档审阅只做链接、源目录、静态图、manifest 和 Git 范围核验，不重跑上述完整运行验收。本轮记录不改变 C4=INCOMPLETE、C1=infrastructure_failure、activation=false、累计真实生成 172 / 目录 GET 1。

本次交付检查：六份变更文档的157个本地链接均存在，Markdown代码围栏闭合，Git diff空白检查通过；既有publication_scan以verify-only模式检查336个文件，凭据模式与受控raw拷贝排除通过，真实凭据读取0。产品、测试、工具及历史validation文件无改动。Mermaid仅核对语法结构与代码关系，未做渲染验证。完整运行测试留给实际实施目录迁移的session。
