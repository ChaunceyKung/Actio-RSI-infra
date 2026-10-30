# Actio-RSI

**面向持久身份、社会交互与受控演化 Agent 的实验基础设施。**

Actio-RSI 将 Agent 的身份与记忆、模型运行、环境裁决、事实记录、独立评估和候选谱系连接起来。系统采用 **九个核心模块组成的模块化单体**：Python 控制面调用受管 DSH Worker 与 Concordia，SQLite 和文件证据保存可核验的执行过程。

## 模块化设计：九个核心模块

模块按职责分目录；表中的输入输出说明合作关系，不表示九个独立服务。

| 模块／源码目录 | 负责什么 | 主要输入 → 输出 |
|---|---|---|
| [contracts](src/actio/contracts/) · 合同 | 数据格式、受限编码、wire、最小运行端口 | 原始数据 → 规范化数据、seal 或合同错误 |
| [domain](src/actio/domain/) · 领域规则 | 身份边界、状态规则、namespace、账务与 Clock | 状态与约束 → 合法状态、聚合与决策值 |
| [tasks](src/actio/tasks/) · 任务定义 | 任务 family、actor 可见性、行动空间与版本选择 | 任务卡与 actor → 可见观察、合法行动与任务结果 |
| [profiles](src/actio/profiles/) · 运行配置 | 模式、期限、准入、用量及版本规则 | 配置与模式 → 经校验的运行合同 |
| [application](src/actio/application/) · 用例编排 | run/lease、memory、episode、campaign、导出与决策写入 | 命令与冻结输入 → 持久状态、执行结果与证据包 |
| [adapters](src/actio/adapters/) · 外部能力 | 数据库、DSH/Worker、Concordia、传输与文件接入 | 受控操作 → 外部效果、原生回执及资源 |
| [evidence](src/actio/evidence/) · 证据核验 | 认证输入/协议/账务，核验封包、谱系和失败 | 封存材料 → 可信度、完整分母、缺失与诊断报告 |
| [measurement](src/actio/measurement/) · 独立测量 | 独立 oracle、指标与诊断计算 | 卡片和行动 → 指标值、适用性及原因 |
| [interfaces](src/actio/interfaces/) · 入口装配 | 参数解析、可信选择、CLI/IPC 与 ports 装配 | 外部命令／协议 → 用例调用、stdout 与退出码 |

`adapters` 分为 **persistence / runtime / environment / transport / filesystem** 五组；`evidence` 分为 **audit / bundles / campaigns / lineage / diagnostics** 五组。固定 JSON、pins 和 `_vendor` 是支持资源，不是额外业务模块。

主要数据流：**身份／任务／配置冻结 → 执行资格与受管运行 → 行动认证和环境效果 → 状态与事实持久化 → 只读核验和独立测量 → 追加评估决策**。Store、Ledger、DSH 原生 session 各有权威边界；文件报告是投影，不是第二数据库。

[源码目录导航](src/actio/README.md) · [系统一页图](docs/architecture/README.md) · [模块输入输出与入口](docs/architecture/MODULES.md) · [关键流程](docs/architecture/FLOWS.md)

**当前工程状态：0.2.0 入口迁移已实现，R15–R18 验收进行中（INCOMPLETE）。** 根层只有 `__init__.py`、`__main__.py`、`README.md`；19 个旧根模块和旧 reader facade 已移除。所有本轮 Gate 以[新验收记录](docs/validation/refactor_entrypoints/RESULTS.md)为准。R7–R10 的 PASS 与 R11–R14 的 INCOMPLETE 保留为历史事实，不能替代当前 wheel 验证。

**实验停在 C5，未进入 C6。** 累计真实生成172、历史目录GET1；C4=INCOMPLETE、C1=infrastructure_failure、research=UNESTABLISHED、activation=false、binary_source_mapping=unproven、full_controller_recovery=unsupported。本轮只进行本机工程验证，不读取真实凭据，不发外部实验请求。

## 当前入口

运行路径和 LLM 选项现在由根目录 [actio.toml](actio.toml) 配置；使用 `actio config show --settings actio.toml` 查看解析结果，`actio gateway run --settings actio.toml --rehearsal` 验证真实本机 DSH/Concordia 链路。配置、uv 安装及真实 LLM 命令见 [配置指南](docs/architecture/CONFIGURATION.md)。

2026-10-30：新增可运行的 [Environment Session 与 TicTacToe 实验](docs/architecture/ENVIRONMENTS.md)。使用 `pwsh -File scripts/environment_setup.ps1` 通过 uv 在项目 `.local` 内安装 Python、依赖及固定 Concordia 源码；`actio run experiment` 复用 Store 的 Run/lease、审计、导出和离线核验。完整命令、能力边界及 OpenRA 下一阶段工作见链接文档。

安装 Python 3.12 对应的 0.2.0 wheel（完整运行环境另需固定 DSH/Concordia 依赖）。唯一用户命令是 `actio`，等价于 `python -m actio`：

```powershell
python -m pip install ./actio_rsi-0.2.0-py3-none-any.whl
actio --help
python -m actio --version
actio diagnostics transport plan
actio diagnostics transport export ./diagnostic-package
actio diagnostics transport verify ./diagnostic-package/package.json
actio run --help
```

命令族：`run`、`verify`、`evaluate`、`candidate`、`candidate-evaluation`、`preflight`、`readiness`、`gateway`、`pilot`、`suite`、`robustness`、`diagnostics task|transport`、`campaign verify`。内部 budget IPC 与 Worker 单独位于 `interfaces/ipc`、`interfaces/workers`，不经用户 dispatcher。

旧 CLI/API 不再可用；逐项替代与固定历史版本复现见[0.2 迁移指南](docs/architecture/MIGRATION_0_2.md)。`--no-deps` minimal 环境仅用于离线 reader，不是完整运行环境。

## 子组与边界

| 模块 | 五组职责 |
|---|---|
| adapters | persistence：SQLite/事务/Ledger；runtime：DSH/Job/MCP/清理；environment：Concordia / PettingZoo Session；transport：协议/TS/fixture；filesystem：身份与受控文件 |
| evidence | audit：协议/账务认证；bundles：封包核验；campaigns：完整分母报告；lineage：候选/评估历史；diagnostics：失败分类与诊断 |

`resources/{pricing,trust,pins}` 保存五份固定 JSON，内容保持原字节；SQL、MJS 和许可证仍归实际 owner。`_vendor` 保存窄复用代码和来源。应用层仍含 SQL/mixin，保持同连接多表事务；Store 与 Ledger 各有权威，不宣称跨库原子提交。

## 设计与历史

- [系统](docs/architecture/README.md)、[模块卡片](docs/architecture/MODULES.md)、[关键流程](docs/architecture/FLOWS.md)。
- [项目定位](docs/planning/00_project_positioning.md)、[复用决策](docs/planning/02_reuse_decision_matrix.md)、[架构取舍](docs/planning/13_architecture_decisions.md)。
- [里程碑](MILESTONES.md)、[固定 C5](docs/validation/phase1c2c5/RESULTS.md)、[R7–R10](docs/validation/refactor_modularity/RESULTS.md)、[R11–R14](docs/validation/refactor_directory/RESULTS.md)。
- [维护工具](tools/README.md)、[本轮验收命令](docs/validation/refactor_entrypoints/CLI.md)。

历史材料按对应 commit 的 reader 重放，不能用新版路径重写旧 manifest 或补齐 C4 缺失后缀。工程验收不建立研究有效性、训练成果或激活资格。
