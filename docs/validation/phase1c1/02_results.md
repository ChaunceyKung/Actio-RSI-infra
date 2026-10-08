# Phase 1C1 实现与验收

工程 Gate **CONDITIONAL_GO**。新增 7 组任务合同验收及 35 组相关回归全部通过，共 42 组；这些是聚合行为测试，不是研究样本。[最终 manifest](evidence_manifest.json) 绑定实际命令、最终源码/安装包、每次尝试、原始日志归档与 Job 清理；[合同](01_contract.md)、[复现入口](04_usage.md) 与 [Gate/限制](03_gate.md) 分开记录。

真实执行继续使用官方 DSH 0.1.5rc1、既有 RuntimePort 和固定 Concordia Sequential/Entity/ActionSpec。新任务完整路径包括 compatible 达成、conflict 合法 accept 但未达成、decline 未达成、第一/第二步非法行动、replay、角色交换；受控第二 actor 初始化故障保留真实第一步与 partial。公开 CLI 另跑两个卡、重复 key 与两次导出。没有纯 Python 模拟替代真实运行。

冻结的 authored TaskSpec 含 seat→真实 agent/spec、目标/私有约束/初始关系、完整 ActionSpec 与结果规则。A 一次观察、B 两次观察，由实际 Engine 行为和 dispatch/native 输入核对。B 的最终 view 包含 A 的实际公开提议；own private 与 GM audit 上下文不跨 seat。合法行为的 world/domain 结果按冻结共同约束重算；运行退出不等于达成。非法行动在该行动的世界效果前拒绝，第二步非法时第一步效果仍保留。

在线 seal 与离线 verifier 共用版本化检查。临时重算包装 hash 后的目标、关系、约束、seat、公开历史、ActionSpec 与 world 结果矛盾均拒绝，原生 raw 未修改。缺字段在 run/Worker 创建前拒绝；重复 key 不启动第二执行；replay 显式覆盖拒绝。旧 v1/v2 合同规则不放宽。

最终 [campaign index](campaign/campaign.json) 相对于冻结 dataset 与 inventory 的只读独立复核通过：

| 项目 | 数量 |
|---|---:|
| 登记（保留重复） | 25 |
| 唯一 evidence identity（含拒绝源） | 10 |
| 唯一 evaluation request | 22 |
| admitted / rejected / insufficient | 15 / 2 / 5 |
| valid / invalid measurement | 14 / 1 |
| measurement_error / timeout / not_run | 0 / 0 / 7 |
| task_failure / infrastructure_failure | 8 / 2 |
| 独立研究单位 / 模型请求 | 0 / 0 |

以上状态轴相互重叠，计数基于唯一请求而非登记数；每模式分母在 report 内独立存储。22 个请求来自不同 source/spec/response。重复导出与重复请求保留登记、不重测；不同 preset 响应新增测量请求、不新增研究单位。两个卡、角色交换、replay 同属 development family；没有 candidate 或 holdout。

只读核验重新计算 source/spec/record/alias/view、登记完整性、请求指针/claim、group、hash inventory 和所有分母。删登记、错计数、错 source/spec、缺/多 current 文件、把当前记录误标 historical、跨分组登记均失败；显式 historical 额外文件允许保留但不进入当前计数。独立标准库迁移验收禁止原目录读取、写入、网络、进程、runtime 导入及 evaluator 调用。

Controlled response 的 goal/relationship 来自冻结 task view 和新 rubric，反序 alias 保持身份；无完整合法双方动作则不生成分数。旧 social 包仍因无运行前目标/关系而 insufficient，零 evaluator 调用。非法 envelope、依赖缺失、内部错误、超时、claim 中断及不自动重试继续通过 C0 evaluation 回归；最终 campaign 不伪造内部错误/超时数量，这两类故障注入在测试证据中单列。

原 C0 12 份记录用固定 `1e85d8c2fb4a756de81acb333905190df9e97592` 的受控源码在 `-I -S` 标准库子进程逐一通过；新 EvalSpec 为 actio-eval.v2，新 verifier 为 actio-verifier.3，新实现明确拒绝旧 pins。旧记录、旧 spec/hash、旧阶段证据、Concordia/SOTOPIA 源码及所有依赖锁保持不变。

[3 份盲化标注 case](annotations/annotation.md) 与 [空白模板](annotations/blank-labels.jsonl) 已导出，真实标签 0。synthetic_label_fixture 验收覆盖正向绑定、task/episode/trace/rubric/view/alias/group 错绑定、缺标、重复冲突及维度分歧；不产生人工 gold 或专家共识。preflight 的零预算及完整正预算均在环境读取、文件写入、网络、客户端或 Worker 动作前阻断。

本轮失败均保留：

- 首轮 task suite 1 处测试断言错误：partial 包应为 facts_consistency=partial、recorded_prefix=consistent，修复测试后 7 组全过。中间源码归档保留。
- 首轮 public CLI 与固定旧版本脚本遇到中文路径 pipe 编码不一致；增加子进程 `-X utf8`，重跑通过，失败日志与脚本版本归档保留。
- 第二次 campaign 发布在深层文档路径遇到 Windows 长路径限制；改在新的受管短根创建，再复制至较短文档目录并重新只读核验，失败 staging 和原因保留。未修改系统设置，也未重写失败文件。
- 首轮最终交付审计的 SOTOPIA extraction 子进程在最小环境中找不到 Git；只向准备工具的 PATH 添加已定位的 Git 目录后重跑，产品与运行时环境未改动。失败交付记录和脚本归档保留。
- 最终清单审阅排除了仍在写入的 release stdout 日志 hash，改由已封存的 delivery JSON 保存该次命令记录；中间清单移入 historical-manifest-attempt2.json 保留，不作为当前证据入口。

全部准备使用新 venv、hash 锁定 wheel 和固定本地源码 archive。最终 release 环境做 core+eval pip check、产品源文件集合和逐字节 hash 核对、公开 CLI 与迁移核验。模型/judge/embedding/训练请求均 0；本轮受管 Jobs 最终 active=0，精确数量见 manifest。人工校准、live、研究效度与演化晋升均 BLOCKED，停止在 1C1。
