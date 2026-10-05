# 08 · 受控演化、评估与准入

一条闭环：Experience→Diagnosis→Proposal→Candidate→Sandbox→Replay/Re-execution→Evaluation→Regression→Statistical Gate→Admission→Version→Production/Experiment→Rollback/Archive。每一阶段输出 immutable evidence ref，不依赖临时目录存活。

MVP 开放 **Prompt/Reasoning Scaffold 的结构化行动前检查清单 seat**，只允许修改有长度上限的提示字段，不允许任意代码、模型、权限、预算或 evaluator 修改。演示可以拒绝所有候选。L2 的 Harness Component/Agent Loop 在 schema 中一等存在，执行能力默认关闭；不把“harness-first”简化为 prompt-only 的长期架构。

## 七个 seat 的四份合同

| Seat | Mutation Contract | Evaluation Contract | Constraint | Rollback Strategy |
|---|---|---|---|---|
| Persona / Social Strategy | 策略参数/交互规则；Persona 修订另需 identity change manifest | 身份连续、行为分布、社会目标与任务质量分报 | 不改数据来源/稳定身份；不以迎合评委替代保真 | 下一 run 旧 spec；真实历史不抹除，必要时独立 memory 修复 |
| Memory / Context Policy | retrieval/ranking/summary/retention policy artifact | 固定初始memory的任务质量、来源保真、泄漏、token成本 | 不写 test split、M5 身份；版本与内容变更分开 | 旧 policy + 兼容旧 snapshot；不回滚已发生世界 |
| Planning / Workflow | 有界节点/edge/timeout与planner配置 | 完成率、延迟、循环检测、失败恢复 | 禁越权工具/隐藏 evaluator；有步骤上限 | pin旧workflow，进行中run排空或终止 |
| Skills / Tool Policy | 已批准 skill版本和选择策略 | task success、参数/schema、权限拒绝、重复副作用 | 新工具能力不可通过候选自行授权 | 新run回旧skill；未确认效果先reconcile |
| Prompt / Reasoning Scaffold | **MVP** allowlist字符串/结构化清单diff | paired任务/场景质量、身份/权限回归、成本 | 提示长度、不可覆盖系统约束/Persona/evaluator；artifact静态校验 | 新run切v1，无memory schema变动 |
| Harness Component | plugin模块/配置diff+ABI声明 | contract suite、隔离、session恢复、双slice回归 | P2；候选进程独立、无生产凭据；禁止直接写control | 新worker旧artifact；必要migration反向方案先批准 |
| Agent Loop | loop策略/组件artifact，不替换domain owner | termination/cancel/budget/tool语义、恢复和收益 | P2+；最强隔离，不能改event/eval/admission协议 | 停候选worker回旧runtime；外部效果不承诺撤销 |

Genome allowlist按 JSON path/seat/类型/长度/兼容版本冻结，denylist至少 evaluator、admission、sealed data、permissions、budget、logging suppression、world rules、identity owner。Mutation validator只接收声明的差异，候选不能携新脚本逃离 seat。

## 实现资产及修改

Raven `paired.py`、TaskEval 和 gate tests 可作为配对诊断基线（C02）；**不能沿用 promoted 来决定准入**：其含义是均值变好，`credited_2sigma` 另报，n=1/零方差可为 inf（E008）。Raven `archive.py` 的 WHERE×WHY 与重组不覆盖冲突过滤可拆为 selector（C03）；banking 对固定 vanilla、champion promotion、生产 admission 是三种不同决策。完整失败谱系、坏JSON/写失败、交易持久化必须改（E009）。拆解闭包见 [17](17_reuse_extraction_plan.md)。

Meta-Harness 提供新domain onboarding、完整执行历史和封存test隔离思路；experimental Harbor controller AST/timeout/reward路径不直接复用，避免为薄wrapper带入大执行闭包。DGM metadata archive/parent selection作为D，Docker/SWE/mutation与指标耦合过深；`best`选择还需复核。ACE仅D，ADD playbook delta不等于完整记忆演化。GSME/HarnessBank论文只作D，Raven实现不得标为作者官方实现。Letta/DSH的plugin/memory lifecycle是候选执行基础，不拥有admission权限。

## 四态结果和数据权限

| Decision | 条件 | 后续 |
|---|---|---|
| pass | 有效实验、最小有意义增益与独立gate满足、所有回归/约束通过 | seal version；可控激活 |
| reject | 确认违反约束、有效数据表明无收益/明显退化 | archive candidate+原因，不改active |
| insufficient_evidence | 样本/配对/方差/指标完整性不足，或CI跨阈值 | 保留不确定性；只在预算内追加预定样本 |
| infrastructure_failure | model outage、judge parsing、环境不一致、缺轨迹等 | 不能奖励也不能混同任务零分；重试单独attempt，报告invalid率 |

开发/search、validation、sealed final test三分。按scenario family、人口生成源、用户/任务族group划分，避免相关样本跨集。proposer只读开发分数/轨迹及预算内诊断；validation反馈有限，sealed test在最终候选选定后一次独立执行，不反哺搜索。失败后如换候选/规则，开新campaign并获取新holdout，否则标exploratory。

评委有可替换确定性指标、SOTOPIA式LLM rubric、人工抽查。SOTOPIA异常返回[]、身份顺序与did-nothing过滤必须wrapper校验（E022）；维度缺失就是invalid。评委能看哪些私有目标明确标注，不能把评委的全知上下文注入solver。Task quality、social fidelity、identity、constraint violation、cost/latency分开报；禁止用一个总分掩盖硬约束失效。

## 统计预注册模板

baseline=v1固定spec/model/环境/初始memory；paired unit为同一独立场景实例/任务族，两个arm共享初始条件，交替/随机运行顺序降低provider漂移。多agent互动以整个episode/社会cluster为单位，不把消息数当样本量。配对失败的单位按预设invalid规则重跑两臂或剔除并报告，禁止只删候选失败。

默认设计先用独立pilot估方差，不用于最终胜负；示例最小有意义任务收益 +3 percentage points、成本增长≤10%、身份/社会指标退化不超过预注册容忍度、硬工具违规0。数值是待领域负责人在B09冻结的假设，不是测得有效阈值。二元结果可用配对exact/McNemar或cluster bootstrap CI；连续结果按distribution预设paired bootstrap/permutation，不机械套z≥2。

计划validation至少30个独立单位作为启动下限，**不保证power**；用pilot估计Δ和方差给出所需N/预算，不足就insufficient。小样本/零方差不给无限可信结论；报原始差异、有效N、CI、最小增益和敏感性。多个候选搜索采用预注册候选上限、alpha分配或最终独立holdout；不对每轮反复peek后宣称固定显著性。sealed final gate的统计方式与回归条件事前冻结。

## 隔离和恢复

MVP structured seat：限制可编辑字段、只读输入、独立namespace、无新代码/工具权限，使用现有worker。L2：先验证Linux隔离、文件/网络/资源限制、artifact可重建与协议观测，再允许代码候选。普通subprocess、AST filter、Cordis effects与Dockerfile都不是自动成立的安全认证（E005/E010/E011）。

每个candidate记录 parent(s)、mutation与seat、source SHA、运行pins、dataset split hash、原始eval refs、四态decision、policy版本、成本、失败与重试。activation CAS失败不能生成第二active版本。Crash后根据已seal artifact/decision恢复，不重评改写旧结果；budget耗尽停止搜索但保留所有候选。回滚只影响未来run，不擦除历史事实或替工具反向操作。
