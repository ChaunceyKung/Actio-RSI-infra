# Codex Prompt：R11–R14 目录组织与设计可读性收尾

你接手 Actio-RSI-infra 的下一轮工程重构。请实施并验证本 Prompt，不只给计划；任务完成后普通推送任务分支和 main，并分别核对远端 SHA。用户不希望继续实验迭代，本轮目标是让目录职责更清楚、设计更容易理解，同时保持现有行为。

## 0. 仓库、授权与起点

- 本地：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
- 远端：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
- 已完成的 R7–R10 基线：`ccc7399dc3e31367543df7d1c196eefb705c131b`，产品提交 `86fcee8daf0cfba3721b40dc8cd19580a1b12a56`。后续可能已有本 Prompt 的文档提交，基于实际最新 main 工作，不 reset 回旧 SHA。
- 先读 AGENTS.md，检查 status、分支、worktree、remote 和 fetch 结果。保留用户与并发修改；在当前已授权范围自主推进常规拆分、验证和发布，不为每次移文件另问批准。
- 建议分支 `refactor-directory-clarity`；若已有本任务分支，先查明状态再复用，不覆盖它。
- 本轮外部实验请求=0、真实凭据读取=0，不读取 `.local/credentials`，不发 provider/catalog/MCP 外网请求，不启动 C6、judge、训练、部署、激活。用户此前的无金额上限授权不变，但本轮无需模型调用。Git fetch/push 和必要的锁定依赖获取不属于模型实验。

## 1. 必读资料与真实基线

依次读：

1. `docs/reviews/modularity_r11_r14_review.md`。
2. `docs/architecture/README.md`、`MODULES.md`、`FLOWS.md` 与 `REFACTOR_PLAN.md`。
3. `docs/validation/refactor_modularity/RESULTS.md`、`CLI.md`、`GATES.md`、`compatibility.json`、`migration-map.json`。
4. `docs/validation/refactor_modularity/completion/` 的 manifest、architecture、regression、assertion-preservation、formal-report、cleanup 和历史保全记录。
5. `tools/refactor/architecture.py`、`validate.py`、`completion.py`、`packaging.py`、`freeze.py`、`tests/test_modularity.py` 与 pyproject/package-data。

复核 Git 跟踪文件与当前 import 图，不把 venv、build、缓存和历史受控运行目录当产品布局。原扫描为163模块/594边、SCC=0、根实现=0、违规=0；路径移动后模块和边数可合理变化，不能把固定数量当成优化目标。

旧验收：同一最终 wheel，34 suites、164唯一方法（原163+Clock1）、555差分向量；readiness启动失败与原条件隔离重测都保留。正式C5九场景12 sends、5 settled、7 unknown、6 not_run。这些不是你的新 wheel 的验收，必须另建新证据。

对基线 manifest，按声明的 Git blob 字节口径及固定 SHA 验证，不混用 Windows CRLF 工作树。历史报告不改写。若发现与报告不符，先记录并查明，不能修改旧 hash 让它看似通过。

## 2. 限定结果

本轮交付四件事：

1. 移入子包也有效的递归边界检查，以及明确的公开入口/兼容策略。
2. evidence 目录按能力分组；测试按实际行为分层；现有维护工具和历史脚本有清楚入口。
3. 三页简明设计保持与最终代码一致：整体系统、模块 I/O 与设计、关键流程。
4. 行为保持、最终 wheel、历史保全和清理验收，以及 GitHub main 发布。

保留现有模块化单体。不要新建微服务、插件框架、第二数据库权威、泛化 Repository/UoW，或大规模重新命名全部产品概念。application 内现有 SQL/mixin 是已知现实，本轮保持原连接与事务；不要借目录整理修改事务语义。SDK、Concordia、provider、任务和候选逻辑、评估标准、历史停止点、Clock/live期限不升级。

## 3. R11：先补检查与映射

在移动实现前完成：

- 形成明确的当前路径 → 目标路径 → 职责 → 公开/私有 → 兼容方式 → 测试/资源影响映射；同时保存基线 Git SHA、import 图、公开入口、suite/method 清单。
- 当前 `test_modularity.py` 多处 `glob('*.py')` 漏掉未来子目录。改为递归检查，解析绝对与相对 import（含 `from . import x`、包 init、函数局部导入）、已支持的字面量 `__import__` / `importlib.import_module`，并检测新增子包。
- 不凭一个 `Compatibility` docstring 授予豁免。兼容薄层须在清单中登记、校验转发目标、禁止重新容纳实现；产品内部不能反向导入这些薄层。
- 明确各层允许依赖和窄例外：contracts/domain/tasks/measurement 的纯层；application 不直接导入 runtime/environment/transport/persistence/interfaces；evidence reader 不导入 application 或数据库写入/运行实现；profiles.validation 依赖保持受限。现有 filesystem 辅助和源码身份构造按实际用途记录，不能误称整包纯函数。
- 检查所有当前产品 Python 的模块 SCC，并检查本次新增 evidence 子包的组间 DAG。不要声称所有“父目录折叠图”天然无环；不同粒度需不同规则和明确例外。
- 增加有价值的检查器反例：嵌套文件、相对导入、函数内违规、字面量动态导入、实现反导 shim、跨新子包循环；证明 checker 确实拒绝。未能静态解析的动态导入单列审阅，不隐藏或冒充已解析。
- 允许修正当前维护检查器，但需有独立规则版本/变更说明与反例。保留旧 checker 基线与旧 PASS 事实，不降低原有约束，不用排除目录制造 PASS。

## 4. R12：evidence 按职责分目录

优先采用下列草案。审阅时已经把当前29实现的依赖映射到五组，组间无环；你仍需检查最新实际源码与调用点。

| 子包 | 当前模块名，省略 .py |
|---|---|
| `evidence/audit/` | stream_audit、channel_audit、transport_contract、accounting |
| `evidence/bundles/` | task_evidence、terminal、verify、eval_contract、evaluation |
| `evidence/campaigns/` | transport_campaign、pilot_measurement、suite_measurement、candidate_measurement、evaluation_measurement、robustness_measurement、campaign_registry、campaign、calibration |
| `evidence/lineage/` | candidate_lineage、evaluation_history、evaluation_lineage、candidate、candidate_evaluation、robustness |
| `evidence/diagnostics/` | failure_observation、failure_fixtures、future_schedule、task_diagnostics、transport_diagnostics |

预期组间方向：bundles → audit；campaigns → bundles/audit；lineage → campaigns；diagnostics → campaigns/audit。允许基于真实职责微调并记录理由。每个子包应有简短职责说明和明确入口，不通过大而全的 `__init__` re-export 重建依赖环。

搬迁要同步当前产品、测试、当前维护工具和资源/源码身份定位；检查 `Path(__file__).parents`、硬编码文件表、wheel package-data、动态 import 和子进程模块名。imports 改动不得暗改算法、排序、异常、序列化或指标值。

保留四个 console scripts、所有登记 `python -m` 入口、预算 stdin/stdout/退出码与 child IPC、公开 reader 地址。特别包括 `actio.evidence.failure_observation.from_entry`；不能只保住根 facade 而破坏这个登记公开地址。只为实际公开/必要兼容地址保留薄层，私有 import 迁到 owner；不能给每个旧文件造一个永久平铺副本。兼容入口 smoke 用成功/拒绝等真实语义断言，不能只有 `--help`。

contracts/domain/tasks/measurement/adapters 已有清楚边界，本轮不为整齐而全盘再分包。application/interfaces 可先靠模块卡片与入口清单解释；额外物理移动仅在明确收益、依赖证明与验收成本合理时采用并记入范围。

## 5. R13：测试分层与维护入口

目标目录为 `tests/architecture`、`unit`、`integration`、`runtime`、`support`、`fixtures`。依据测试实际副作用分类，不按名字猜：有的 budget/readiness 测试启动官方 Worker，有的规则测试只做计算。若更少分组已足够，给出完整职责映射即可，不制造大量单文件子目录。

- 保留原34 suites/164方法及断言语义，新增边界检查另计。建立稳定 suite ID → qualified module 与原方法 ID → 新方法 ID 的一一映射；不得重复发现或漏跑。
- 更新当前 runner/packaging 的加载、测试支持路径与输出映射；`suite_evidence` 必须消费同次 `suite_runtime` 的矩阵，不能捡上次留下的产物。
- 显式测试收集清单与实际执行方法一致；不通过更名、skip、xfail 或删除断言变绿。受控收据保留失败及具体重测范围。
- 当前 stub/child helper 归入 support 或相应 fixture，并改正本轮调用者。产品可安装 fixture 继续归 adapters.transport，产品绝不能导入 tests/tools/scripts。
- 区分“开发 runner 可以显式加载测试”与“产品运行依赖仓库 sys.path”。后者禁止；从仓库外 `-I` 使用安装 wheel 仍必须有效。
- `tools/README.md` 列维护命令、用途、运行依赖与输出；`scripts/README.md` 区分当前 bootstrap 和固定历史脚本。不为改名复制整套12个工具，也不批量改写88个历史脚本。
- 旧 completion/history 工具若与旧目录绑定，按固定 Git SHA 重放；新验收可加窄适配或新入口，旧证据不刷新。对真正仍维护的 runner 作必要更新，并记录命令兼容性。

## 6. R14：简明设计与正式验收

维护三页当前设计，避免再写一套阶段百科：

1. `docs/architecture/README.md`：实际目录树、系统关系、输入输出、状态所有权、当前/未来边界。
2. `MODULES.md`：每个核心模块的输入、主要步骤、输出、代码入口、边界、测试入口。对 evidence 五组补足说明。
3. `FLOWS.md`：solver episode、导出/只读核验/decision、C5故障诊断；图中说明调用/数据流与 import 图的区别。

根 README 链接三页并更新实际路径；历史 `REFACTOR_PLAN`、阶段验证与 MILESTONES 旧条目保持，必要时追加新里程碑。每张图和每个示例要能对应真实代码；尚未实施的 UoW、恢复、训练或激活不得画成可用功能。Mermaid 若只做静态校验，应明确未做渲染验证。

### 验收顺序

开发期定向验证，最终代码稳定后构建一个新的最终 wheel，记录代码/构建/安装身份。可运行目录使用新的短 ASCII 路径；不覆盖 `D:/ar-complete-20261011` 等历史受控目录。

| Gate | 必须验证 |
|---|---|
| D1 目录与依赖 | 最新递归边界反例、模块 SCC=0、规定子包 DAG、无未登记根实现、无产品→测试依赖、公开兼容清单正确 |
| D2 测试保持 | 34原suite、164原方法一一映射及执行，加新检查器测试；无丢失/重复/掩盖；同一最终 wheel |
| D3 行为保持 | 原555向量完整JSON差分，事务/幂等/可见性/unknown/Clock/离线reader语义保持 |
| D4 可安装性 | 干净安装、pip check、最小依赖环境、仓库外隔离模式、资源/许可/SQL/TS bytes、四console scripts/登记module/预算IPC成功与拒绝路径 |
| D5 历史 | 原1048文件保全集合及固定reader、报价/pins、19 claims与旧evaluation/decisions、C4缺失后缀按原合同核验；新身份不伪装旧身份 |
| D6 本机正式 | 新最终wheel正式C5九场景，预期12 sends/5 settled/7 unknown/6 not_run；端口/Job/服务/发送状态清理，有独立复算 |
| D7 文档 | 三页与实际目录相符、相对链接有效、无把历史结果说成本轮实测、没有泄露受控raw/密钥 |
| D8 发布 | 提交并普通推送任务分支和main，分别ls-remote核对；工作树与并发处理状态明确 |

原34 suites在同一最终wheel全跑；readiness保留显式Clock合同，不能改报价日期、降低断言、放宽超时或全局mock时间。不同测试使用隔离运行目录，避免 lease/进程污染。若失败，保留首次证据、定位并修复；产品变更后重新建立最终wheel证据，不拼接旧wheel成绩。仅测试harness修正且wheel未变时，可明确保留失败并按原参数隔离复核。

正式C5只需在最终代码稳定后执行一次；若失败需清楚记录与修复原因再验证。所有开发、失败、重测、正式loopback发送分别记账、再汇总；模型外部请求始终0，历史172生成尝试与1目录GET不变。状态为unknown的场景是预期诊断事实，不等同测试失败，也不能被“修复”为settled。

新包身份必须绑定新完整源码清单；因目录层级变化而修正身份枚举属于当前工程工作，不能删除校验字段或放松大小/深度/节点限制。旧reader、schema及信任表保持历史语义；确有格式变化则显式新版本，不使用旧名称暗改合同。

本轮证据放 `docs/validation/refactor_directory/`，至少 RESULTS.md、CLI.md、evidence_manifest.json，以及机器可复算的目录/方法映射、架构、差分、wheel/安装、运行/清理、历史保全和发布引用。只提交可发布摘要与必要合成证据，受控raw和大型运行数据仍留忽略/短目录。无需为每个步骤增写独立长文。

## 7. Git 交付与停止

- 检查差异、凭据模式和受控raw发布边界，不读取真实凭据来完成本轮扫描；不提交venv、cache、DB、密钥、wheel或无关改动。
- 完成本轮必要检查后提交任务分支；fetch并检查main。无并发分叉则安全快进；有分叉先读变化、整合与针对性复验，不强推，不reset覆盖他人工作。
- 普通推送任务分支及origin/main，分别用 `git ls-remote --heads origin <branch>` 与 main 查询远端SHA，记录本地/远端一致证据。遇网络失败，做有限诊断重试，保留本地提交并精确报告发布阻塞；不能写“已发布”。
- 发布回执可在后续仅文档提交中补充，但区分实际验收的产品commit/wheel与最终交付commit。不要制造无限“为回执再提交回执”的循环，旧manifest不刷新。
- 最终中文回复：目录变动、三页设计入口、公开兼容性、原/新增测试数及失败重测、差分/正式C5/清理、历史保全、外部调用0、Gate、提交与两个远端SHA、剩余限制。

完成D1–D8后结束本轮目录重构。保留 C4=INCOMPLETE、C1=infrastructure_failure、research=UNESTABLISHED、activation=false、binary_source_mapping=unproven、full_controller_recovery=unsupported；不进入C6。不因目录审美继续开启无止境的分包，也不把本轮工程通过说成研究能力晋升。
