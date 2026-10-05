# 07 · Persona、社会心智与记忆

采用自有 Memory contract + SQLite/immutable artifacts；不是自研数据库。Letta 当前本地/云后端与 git MemFS 有真实价值，但 LocalStore、agent/conversation、system prompt compilation 深度耦合；整体接入会增加第二权威 owner（E012–E014）。Graphiti 时序边适合作可重建关系投影，暂不增加 graph/vector 服务（E021）。

## 四种不同变化

PersonaSpec 是相对稳定的身份基线；MentalState 是观察后形成的 belief/goal/intention；Social Strategy 是可学习的行动策略；prompt 是上述内容的执行表达。改变 prompt renderer 不等于改变人格，改变策略也不能静默重写出生/背景等身份事实。persona 修订必须记录 diff、原因、来源与新版本，评估身份连续性。

最小 PersonaInput：source_kind、source_ref/hash、population_id、attributes+uncertainty、sampling_method/version/seed、calibration_version、generator_model/prompt_version、license_ref、consent_scope（适用时）。无法授权的数据不入 candidate training/evaluation；MVP synthetic。

## M0–M6 是语义层，不是七个数据库

| 层 | 内容与写入来源 | 检索/保留/版本 |
|---|---|---|
| M0 working | 当前 observation、context、计划引用 | run/session 窗口，budget 截断必须记策略 |
| M1 episodic | 看到/做过的事件、Outcome、主观体验 | source_event_ids，不可变事实引用；privacy 到期可删 payload留必要 tombstone |
| M2 semantic | 从多事件抽取的概念/规则 | derived_from、多版本置信度；错误可被后续 revision否定 |
| M3 social/relationship | observer→subject 关系、信任、承诺/角色 | valid_time + learned_time + evidence/confidence；非全知世界图 |
| M4 procedural | skill/playbook、工具使用经验 | skill/policy artifact版本；更新走 seat/eval |
| M5 identity | Persona基线、长期目标、身份承诺 | 单独授权修订，不能被常规 consolidation覆盖 |
| M6 evolution archive | candidate/decision/evidence/lineage refs | canonical archive不可变；memory只引用，不复制另一套版本档案 |

关系记录最小为 `(namespace, observer_agent_id, subject_id, predicate, value, confidence, valid_from/to, learned_at, source_event_ids, extraction_policy/model/version)`。世界真相来自 env event；agent 对真相的信念可能错误或互相矛盾。不能用 Graphiti 一个 fact 字符串替代 observer/visibility。

## Namespace 与写入流水线

Namespace = project/population/environment/experiment/branch/agent；共享群体知识另设有 ACL 的 scope，不能通过省略 agent 自动读全库。检索同时带 observer/time/visibility。counterfactual branch 读冻结 baseline snapshot，写自身 overlay；不得将候选评测 memory 合回 production。

`write` 输入 source facts+expected_revision+policy_ref→检查可见性/来源→保存新 memory revision+event（同事务）→可选投影 outbox。`retrieve` 输入 query/scope/as_of/token budget→结果 refs、scores、policy/model版本和未命中原因→memory.retrieved，保存实际给模型的顺序与截断边界。`consolidate` 输入有界 source set+冻结 policy/model→提案 delta→校验/冲突检测→新 revision，原记录保留 derived/tombstone linkage；失败不能返回原文并当成功。

ACE 可参考 propose_operations，但本次 `apply_curator_operations` 主要实现 ADD，UPDATE/MERGE/DELETE 等仍 TODO（E023）；不把它当完整 memory CRUD。Letta file lease/git merge 参考序列化与可见变更机制，不复制整个 backend。

## Graphiti 的采用门槛

graphiti-core 当前边有 episodes、valid_at、invalid_at、expired_at、reference_time，可注入 driver/LLM/embedder。每次抽取/embedding 都计成本；统一 writer将 canonical memory投影到 graph。wrapper 强制 group_ids，UUID lookup也核 owner；上游 namespace模块不是 branch隔离证明。删除/遗忘须 canonical tombstone→projector删除→核查cache/vector残留，不能只删一个 graph节点。

B16 只有当 M3 query 的准确率/时延在预注册样本上优于 SQLite 简单检索且成本可接受才启用。未通过时保留 SQL+人工标注关系；不为“社会”标签堆三种 DB。

## 迁移、回滚与归因

memory policy变化与memory内容变化分开记录。评估新 policy 时冻结初始memory snapshot，baseline/candidate分别运行；否则无法辨别策略收益还是额外经验收益。schema migration生成新snapshot/hash，兼容验证后CAS active pointer；失败保留旧版本。

agent version rollback不擦除生产期间真实发生的事件。memory rollback须明确丢弃/保留哪些派生知识，世界不能因此回到过去；在隔离 experiment中才可同时恢复允许的 world snapshot。persona修订、关系遗忘和训练导出各自保留访问/授权记录。跨branch、跨persona、跨test split泄漏是 P0 failure。
