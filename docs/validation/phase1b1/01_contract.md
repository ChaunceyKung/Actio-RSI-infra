# Phase 1B.1 实施合同

基线：产品 `668754fc`、交接 `4e0a473`；分支 `phase1b1-reliability-and-evidence-export`。预算 0，Windows x64 / Python 3.12 / DSH 0.1.5rc1 / 固定 Concordia；所有运行和公开样例均为合成 fixture。

先完成 H1/H2 并通过小型合同和真实边界测试，再完成 H3/H4。SQLite 管领域事实；DSH 管 loop/journal；真实 Concordia Sequential/GM 管社会调度。历史 Phase 1A/1B 证据不修改。

| 需求 | 实现合同 | 验证边界 |
|---|---|---|
| B1R1 | operation 完成与 scenario terminal 独立。版本化终态绑定冻结 manifest、owner、operation/domain/world 引用；finish 重新检查，异常不签完整 episode | 助手、两人成功、合法拒绝；真实第一步后第二实体初始化/Engine 异常；receipt 缺失及不一致；主要异常与清理错误分记 |
| B1R2 | BEGIN IMMEDIATE 内检查规范 request，赢家才冻结 effective input；进程内执行资格不从 run ID/epoch 派生；输家只返回原 run | 两控制进程在两个入口同步竞争、一次运行/工具/effect；重试和冲突；旁观者不能 finish |
| B1R3 | recover 必须显式目标；前后检查同一 lease/epoch、owner birth、worker 清单；活 owner 拒绝 | 未知/历史目标不回收别的 Job；死 owner 精确回收；并发变化拒绝；reconcile 不派发 |
| B1R4 | replay 不接收显式起点 override；验证所有必要冻结字段、pins、memory hash，创建 run 前失败 | 原样重执行、新 creation、同 world、原 memory 不变；显式 flag/revision 与缺 pin/snapshot 拒绝 |
| H2 | user_version=2；仅识别已知 legacy=0。新建显式、查询只读；迁移仅到新副本，SQLite backup 含 WAL，保留 backup/hash 和原始 pins；DDL/版本事务提交 | 保留全部旧表内容，重复稳定，故障 rollback/可恢复备份，未来/残缺库拒绝且不写；历史 complete=legacy_unverified |
| H3 | 一个 run 的一致 SQLite 读快照，有限前序 memory source 证明；目录 manifest+JSON 内容，大小/条数上限，核验后原子发布 | 可迁移完整/拒绝/partial 分类；离线受控进程；重算 hash 后矛盾仍失败；scope 和稳定导出 |
| H4 | 每次测试独立记录，绑定源码/测试 hash，干净安装/公开 CLI，manifest 和 Job 清理 | 受影响原 6+2+6+4 回归及新需求测试；commit→普通 push→远端 SHA |

包格式设计：`manifest.json`（format/version/source/content inventory）+ `evidence.json`（冻结输入、spec、操作、原生行、投影、领域/终态、memory source 闭包、清理记录）+ `verification.json`（可重建分层核验）+ `export.json`（时间等非内容 metadata）。发布前在同父目录 staging 写完并核验；失败保留 staging 和失败报告，不出现成功目标半包。目录输入，不实现归档解包。

核验分别报告 bundle_integrity、facts_consistency、scenario_completeness、task_outcome、execution_mode。完整前缀不是完整 episode；合法 task_failure 可以 complete；活动/unknown 缺证必须 partial。hash 只证明内部一致性，不证明发行物来源或真实模型执行。审计包包含该合成 run 必要的 private memory/GM 信息，不改变 agent ACL、不用于 solver 上下文。

不开放 live、evaluator、candidate、resume/fork/catchup、semantic cancel、多活动 run、写工具、完整世界恢复或身份版本激活。全部关键 Gate 成立才 CONDITIONAL_GO，否则保留明确 BLOCKED/NO_GO 及安全成果并推送。
