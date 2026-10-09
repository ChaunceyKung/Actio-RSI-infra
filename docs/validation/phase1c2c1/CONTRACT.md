# C2C1 合同

本轮仅离线与 literal loopback。12 张既有开发卡 × baseline/candidate 两臂 × gpt-5.6 序列化标签 × 1 repeat，24 episodes / 最多 48 次本机 HTTP 发送。标签不代表调用真实 GPT。固定 seed=20261011，卡与 arm 顺序见 preregistration.json；同一个 own_rule fixture，不按 arm 选择更好答案。B 接收自己 arm 的实际 A 行动。fixture 不理解自然语言清单，因此预计 delta=0，不证明清单有效。

运行链复用 Python Control Plane → 官方 DSH SDK/runtime 0.1.5rc1 → 官方 pi-ai translator/TS loop → 真实 Concordia Sequential。每个 episode 独立 Store、Ledger、run、authority 与一次性 claim。第一基础设施失败停止，保留全部未运行位置；不自动 reclaim/retry。60/60/90 秒内层及 115/165 秒外层期限沿用 C2C0，未改 timer 传递或 total deadline；31 秒旧测试不重复执行。

## 版本注册

| 对象 | 新版本 |
|---|---|
| config/profile | pilot-config.v8 / sdk-minimal+actio-tokenkey.v4 |
| task/input | actio-task.v4 / finite-candidate-loopback.v1 |
| channel | single-choice-dual-channel-audit.v2 |
| failure/latency | failure-latency-observation.v2 |
| scaffold/proposal | scaffold-artifact.v1 / candidate-proposal.v1 |
| plan/evidence/measurement | local-execution-plan.v1 / candidate-campaign-evidence.v1 / candidate-measurement.v1 |
| SQLite/lineage | explicit schema 3 / candidate-lineage.v1 |
| binding/decision/policy | candidate-campaign-binding.v1 / candidate-decision.v1 / candidate-admission-policy.v1 |
| portable delivery | candidate-delivery.v1 |

旧 v7/task v3/audit v1 的允许值不变；旧源码固定 reader 重现报告。C2C0 15 sent/usage、14 admitted、33 not_run、0 unknown 不变；累计真实生成尝试 91、目录 GET 1。sidecar 仅重新核验已有结构，不能生成旧 receipt/world 或恢复旧 pilot。

## 通道合同

raw UTF-8 bytes ≤262144，SSE events ≤1024，adapter chunks ≤1024，adapter JSON bytes ≤1048576；reasoning 与 content 共用界限。只接受 single choice index 0，有限标准 SSE、唯一 id/model、重复 key 拒绝；null/空增量不追加字符，非字符串拒绝。最多一个 reasoning block 和一个 text block；各 index 为 0..1023 的不同整数，允许重叠生命周期及分片增量；每块先 start 再 delta/end，全部 end 后一次 usage/finish。不能把 index 0 当作行动。无非空最终 content、length、不完整 stream 均拒绝。

独立核验 raw content → adapter text/end → native action，raw reasoning → adapter reasoning/end → native message reasoning。Ledger 初次审计不声称已检查 native；dispatch 与 portable reader 再查 native。终态可有已观测 pi-ai replayState v2：严格 response identity/API/provider/model/stopReason 与 reasoning/text blocks，reasoning signature 仅 reasoning_content；不支持额外签名、工具、refusal、audio 或未知字段。各层不保存通道时标记 native_reasoning_checked=false，不假称端到端检查。

只把 content 行动送到世界、公开观察、memory 和 oracle。报告只保留 reasoning hash/存在性/块类型与核验结论；历史推理正文不复制到新文件。合成 marker 仅用于本机验收，不是推理质量证据。

失败分类使用结构化 audit category、明确 deadline trigger/native code、accounting 和 oracle 布尔值，不从错误字符串猜原因。类别：unsupported_protocol/channel、content_mismatch、incomplete_stream、timeout、accounting_unknown、syntax_invalid、task_rule_violation、unknown。headers、首个 text delta、total 时钟分别 observed/missing/right-censored；已完整响应的 total 即使行动未准入仍 observed。HTTP200 不证明上游身份或收费。

## 单 seat 与状态所有权

B0 空 scaffold；C1 是唯一人工编写、单父 B0 的通用 checklist。只允许 A 的 /scaffold/checklist，1..6 非空字符串、各 ≤160 字符、合计 ≤1024 UTF-8 bytes。本轮进一步限制为三个已审阅通用词条的有限词汇表，拒绝代码、路径加载器、URL、卡答案/私有值、额外字段或 diff。这是有限数据合同，不是任意自然语言的完整语义安全认证。source、parent、diff、policy 均不可自带执行逻辑。

agent/spec 不更新。task/config 绑定独立 artifact；run manifest 持久记录 base_spec_hash、scaffold_hash、actor_slot、rendered_input_hash。prepared 的独立 UUID4 message IDs 经验证后才可归一化比较；它们由官方序列化器移除，full wire 不含候选/配对/答案 metadata。initial memory 为空，B 无 scaffold。

canonical Store schema 3 仅显式用于候选库；episode Store 仍 schema 2。旧 0/2 只读支持保留，v2→v3 仅复制迁移，backup/hash/失败 stage 保留。candidate、candidate_event、lineage_edge、campaign_binding、decision 都是不可变事实；状态由事件重建。proposed→validated/rejected；validated→evaluating→decided，rejected→decided 仅静态拒绝。evaluating 不自动回收。无效父引用留在原提案，不产生 FK edge；仅 B0→C1 的有效边。JSON 为只读投影，不是第二权威库，不建立 active pointer。

## 决策和分母

静态不合法优先 reject；不完整工程证据为 infrastructure_failure；完整本机 fixture/已用开发卡为 insufficient_evidence。只有标明 policy_fixture 的独立合成函数测试可验收 pass 分支，永不授予 activation。B0、C1 和所有静态负例均 eligible_for_activation=false。

48 个 seat、24 个 A/B episode、12 个 arm pair 分列。每卡保留 baseline/candidate 原值、差值与 missing；不删除缺失或补零。按 scheduling/bargaining 和 arm 分层列格式、A hard、B local、共同结果、toy utility；不作跨 family 排名、显著性、CI、无限 z 或成本归一化结论。independent_research_units=0、human_labels=0。全知上界不成为 actor 隐藏知识惩罚。

实施及计划发布到任务分支和 main 后才运行主矩阵；失败的开发验收原样保留，主矩阵不拼接样本。binary_source_mapping=unproven，full_controller_recovery=unsupported；上游身份、账单、provider 兼容性没有新证据。停止于 C2C1。
