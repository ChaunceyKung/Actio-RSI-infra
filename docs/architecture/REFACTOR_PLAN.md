# 模块化迁移状态与验收

本次是行为保持重构，整体 **INCOMPLETE**。已交付部分可安装实现及本机证据，不能称 R0–R6 全部完成。基线 main 为 `6ba6573`，产品基线为 `c5aeec2`；实际冻结产品为 `d64264f`。[RESULTS](../validation/refactor_modularity/RESULTS.md)、[GATES](../validation/refactor_modularity/GATES.md)、[CLI](../validation/refactor_modularity/CLI.md)是本轮验收入口。

## 实际变化

原审阅统计 69 个 Python / 67 个根 Python，407 条依赖、最大 SCC 33；当前全 AST（含函数内 import 和已知动态 literal）为 89 个 Python、403 条依赖，仍有 23/7/3/2/2 节点 SCC。原 inventory 的 84 是产品文件总数，含 69 Python、14 资源及 1 许可，不是 84 Python。根实现及 shim 的当前口径见 architecture.json。

| 阶段 | 已实施 | 尚未满足的退出条件 |
|---|---|---|
| R0 | fetch/main 基线、任务分支、完整文件 hash/历史保全、独立短路径环境 | 无基线材料缺失 |
| R1 | contracts、部分 domain、tasks、独立 measurement；555 完整向量相同 | eval_contract/terminal/verify 及多版本 tasks 循环未消除 |
| R2 | 文件适配器、Ledger 原事务体和 budget IPC 提取；状态回归 | Store 纯规则/用例/SQL、最小 ports、Clock/ProcessIdentity 尚未完整落地 |
| R3 | 产品 loopback fixture、response_policy 显式注入；移除产品→tests/scripts | profiles/application/runtime/environment/transport 仍混合；source identity 未外层注入 |
| R4 | 私有 task/oracle 文件迁移、薄 common 兼容、tests/support、维护中 runner、固定历史 harness | evidence/composition 的完整分层和无环边界未完成 |
| R5 | 标准 wheel 隔离安装、冻结/任务分支推送后新九场景矩阵、最终基础集成/纯/状态/guard | 全量回归仍有 readiness 报价过期失败；不同开发安装证据不能冒充全量最终安装 |
| R6 | 现状文档、迁移/兼容/身份清单、公开摘要、扫描与普通发布 | 全工程成功受 G1/G7 未通过限制；Git 发布不改变结论 |

## G1–G8 证据原则

G1 全量依赖/动态选择/import-time 边界；G2 canonical、任务/可见输入、oracle、候选与拒绝向量；G3 SQLite 原事务及并发/unknown；G4 wheel、资源、四 console、module/child IPC；G5 固定历史认证；G6 最终官方 DSH/Concordia/MCP 和九场景本机运行；G7 全部维护 suite 及失败修复；G8 文档、扫描、清理与两远端核对。当前逐 Gate 结果以 GATES.md 为准，architecture 工具正确退出 1，不用局部纯层测试替代 DAG。

所有 42 个原测试/辅助 Python 与 88 个历史 Python 工具逐项登记。历史工具原文件保留，仅当前辅助逻辑移到 tests/support。每次 runner 使用新目录，先核对安装完整源码与 checkout，不借 editable/source path 证明打包。

## 行为、身份与历史

canonical、数据 schema、任务规则、SQL 及旧注册表/quote/pins 不变。路径/源码实现身份变化明确记入 [identity-and-history](../validation/refactor_modularity/identity-and-history.json)；555 项完整向量对比不删字段。UUID、时间、临时路径和新源码身份的允许差异逐项说明，不忽略原始认证字段。

C2/C3/C4 用代码固定 reader 核验；原 C5 运行认证和最终离线重算单列。本轮新正式矩阵属于新 freeze/new root/新 wheel，绝不把原重算当作本轮实测。原文件/失败/raw/19 claims/六份 candidate decisions/未来计划保留。

两项基线缺陷保留证据：v3 PROFILE 局部遮蔽已修复；原 priced quote 于 2026-10-10T16:00Z 到期，当前 readiness 成功路径仍失败。未刷新旧 quote、改变系统时间、删除断言或改 skip。后续需要跨 child IPC 明确设计测试 Clock，并证明真实路径仍拒绝过期报价，不能只在父进程 monkeypatch 后宣称集成通过。

## 下一步工程缺口

先拆纯版本配置与读包规则，消除 budget→campaign 和任务版本回边；再按原事务边界提取 Store 用例/规则与最小业务端口；将运行接线归 adapters，真实编排归 application，纯读包归 evidence，CLI 做装配。最后在新完整依赖检查通过后重建/freeze 新 wheel，并对受影响范围重验；这不是本轮已完成的能力。

继续暂停 C6 和真实实验。普通分支/main 发布保留 INCOMPLETE 状态，不作为激活或研究有效性声明。
