# 当前模块、所有权与流程

本页以冻结产品 `d64264f` 为准，完整模块化状态 **INCOMPLETE**；依赖图见 [README](README.md)，全部文件和资源去向见 [migration-map](../validation/refactor_modularity/migration-map.json)。

## 已有职责与 I/O

| 实际模块 | 输入 → 输出 | I/O / 状态 owner / 当前边界 |
|---|---|---|
| `contracts` | JSON 值/文本 → 受限解析、canonical、digest、seal/unseal、ContractError | 纯函数，无状态；编码与错误拒绝保持 |
| `domain` | 候选 artifact、namespace、attempt 值 → 校验和聚合 | 纯规则，无 SQLite；不是全部 Store 规则的提取 |
| `tasks` | 固定卡、seat、自身上下文、公开历史、行动 → TaskSpec、可见输入、世界结果 | 纯逻辑；多版本分派仍构成 7 节点循环 |
| `measurement` | 卡/观察/行动 → 独立 oracle、诊断统计 | 不执行生产裁决；原独立算法保留；其他 measurement 仍在根模块 |
| `adapters.filesystem` | 路径/值/环境配置 → 文件 hash、JSON/行读写、受限子进程环境 | 文件/环境 I/O；原 common 的纯部分已分离 |
| `adapters.persistence.ledger` | 原配置、资格、请求、响应 → 单一账务连接及快照 | 原 SQLite 事务体，WAL/readonly；仍依赖根 budget/readiness/channel 规则 |
| `adapters.transport` | 有限 fixture plans、内存假凭据、显式 response_policy → loopback 服务/接收记录 | 只做本机服务 I/O；服务生命周期和扫描保留，不导入测试，不 monkeypatch |
| `interfaces.budget` | TS 插件 stdin JSON → 账务操作/JSON stdout | 保留 `python -m actio.budget`；其他 CLI 仍在根 |
| 根 `store/database/memory/facts/*_store` | 来源事件/命令 → 事务化事实、revision、谱系 | 领域 SQLite owner；进程身份、纯规则、用例、SQL 尚未完整解耦 |
| 根 `runtime/supervisor/host/mcp_server/scenarios` | 冻结 run 与输入 → 官方回执、世界裁决、清理 | DSH/Windows/Concordia/MCP I/O；未迁入目标 runtime/environment adapters |
| 根 `transport/pilot/gateway/*_campaign/*_contract` | 显式版本配置/任务 → 顺序执行、资格、计划/报告 | 编排、profile 构造、源文件 hash 和部分证据校验仍混合 |
| 根 `verify/evidence/*_measurement/diagnostics/evaluation` | 受控来源或导出包 → 核验/评估/诊断 | 部分纯函数与外层文件 I/O 未拆；纯 reader guard 有明确受测入口 |
| 根 `common` / `budget` | 旧调用 → 新 owner | common 是薄兼容导出；budget 的 Ledger/main 是延迟导出，但文件仍保留预算实现 |

包初始化没有用批量 re-export 隐藏装配。新实现直接调用新 owner，不反向依赖 common shim。旧私有 task/oracle 文件移除；公共 CLI/reader/child IPC 兼容范围单列，未承诺所有旧私有 import 永久存在。

## 流程一：执行一个双 seat episode

根 CLI/pilot/gateway → Store 冻结输入和取得执行资格 → TransportPort/Supervisor 启动官方 Worker → TS 发送 gate 经 budget IPC 原子 reserve/sending → 本机 fixture 返回 → 来源/输入/通道核验 → 原规则决定 settled 或 unknown → Concordia/任务裁决 → Store 保存 world receipt 和允许的 memory effect → 导出 → finally 清理 Job 与服务。

A 先执行，B 仅获得同一臂实际 A 的公开行动；A 技术失败则 B 留 not_run。请求失败不能通过诊断恢复资格，unknown 不按零费用结算。Store 与 Ledger 仍是各自状态权威，跨库流程不宣称分布式原子提交。该流程尚未集中到 application 用例。

## 流程二：离线核验与决策

外层读取 evidence → 根 verifier 检查封包、来源、行间事实和 native/adapter/raw → 独立 measurement 计算指标/完整分母 → 根 evaluation/candidate 用例检查计划和 claim → 同一 Store 连接追加 decision/lineage。纯 verify 到结果即停止，不启动 runtime、不写 decision。

需要历史源码时，`tools/refactor/history*.py` 从代码内固定 commit 取得 reader，内层使用原 guard 只读核验。artifact 不提供可执行命令。C2/C4 原始 delivery/DB 认证与 C3 公开 package 分别报告；受控材料缺失必须 BLOCKED。旧摘要不用于重建 raw。

## 流程三：C5 本机失败诊断

`python -m actio.transport_diagnostics run-local` → 根 diagnostic_runtime 核对已安装 freeze → 产品 GatewayStub 使用显式 response_policy → 官方 Worker 执行有限九场景 → 保存原 attempt/usage/unknown → Job、服务和端口清理 → 纯 failure observation/核验 → 新报告。

该入口不再注入 tests 路径、不导入测试、不修改测试服务器类。repo 外独立 wheel 不传 `--project` 可运行；显式传入时仍核对源码镜像。结构化 provider 错误只是观察，不推断上游责任、重试许可或实际收费。

## 扩展边界与尚未实现的端口

目标 `DomainUnitOfWork/AttemptLedger/AgentRuntime/Environment/EvidenceSource/ArtifactSink` 尚未形成实际统一端口。后续应从现有事务粒度和调用推导，不能新增万能 SQL 接口或任意 artifact 执行引擎；Clock/ProcessIdentity 仅在真实替换点引入。显式版本 profiles 应接收经过外层核对的完整源码身份，不能自行降低历史认证强度。

不支持完整 controller 恢复、原生 resume/fork、训练/部署、自动激活或未授权外部调用；本轮未升级 SDK。
