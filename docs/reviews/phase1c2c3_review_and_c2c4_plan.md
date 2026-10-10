# C2C3 审阅与 C2C4 可见规则鲁棒性方案

审阅日期：2026-10-10。产品与审阅基线：`b50b6da28c25ef34da6a620b2b45a576ead5330f`。本轮已通过 `git ls-remote` 核对 origin/main 和 `phase1c2c3-task-diagnostics-and-observability` 均指向该提交；此前两次 TLS 握手失败后正常重试成功，没有关闭证书验证。

**维持 C2C3 的限定工程 PASS；建议 C2C4 实施一次有限的真实 solver 可见规则验证。** C2C3 已证明诊断逻辑能区分合成控制行为，尚未证明原 B0/C1 在新数据上存在差异。本轮只审阅、离线复核和规划，不实施 C2C4，不读取凭据调用模型，不启动 Worker。

[完整 Codex Prompt](../prompts/phase1c2c4_visible_rule_robustness.md) · [本轮审阅证据](phase1c2c3_review_evidence.json) · [原下一阶段草案](../validation/phase1c2c3/NEXT_EXPERIMENT.md)。下一 session 的 Prompt 包含实现、验收、首次发送前冻结发布、一次有限执行及最终推送 main；它不是已经完成的运行记录。

## 1. 实际核对了什么

| 范围 | 本轮结果 | 证据边界 |
|---|---|---|
| 交付绑定 | 28 个 artifacts、14 个产品文件、5 个入口文件、9 个工具文件匹配固定 Git 内容；安装的 14 个纯模块匹配 | AGENTS 的工作副本仅换行差异；实现提交至最终交付产品源码未变 |
| 已发布验收 | 7 项测试、8 条 guard 内 CLI、最小安装与 4 条实际模块命令的 PASS 记录和最终源码绑定一致 | 本轮没有重跑全部发布验收；开发 CLI 失败仍保留 |
| 诊断包实际重算 | 在禁止 key/env/network/process/runtime import/write 的 guard 下，verify、plan、冻结 dataset 一致 | 416 个合法组合、128 个非法/缺失向量、160 个控制输出由核验器重算；不调用 runtime |
| 历史真实来源 | 重验固定 runner 与 67 个归档 source entries，实际执行固定 C2C2 reader，结果与原认证记录精确相等 | 固定 reader 为 `3bef7e15b0eb21beeb10888eb508056592b977b0`，依赖本机受控归档；没有把公开包当原始来源 |
| 历史结果 | C2C2 的 24 episodes / 48 sent / 48 usage / 0 unknown，谱系 2 evaluations / 1 evaluation decision 复核通过 | 未另行重查历史全部数据库、claim 和操作系统清理；这些部分只核对已发布保全记录 |
| 本轮重跑测试 | 可见策略/同分与缺失、纯输入边界、独立路径与分母三项现有纯测试通过 | 是 3 项重跑，不是再次运行原 7 项或全仓测试 |
| 补充结构诊断 | 32 展示只有 16 个不同的精确 A 可见视图，每个出现两次；16 个 normal/reversed 变换 | 隐藏世界的重复不是独立研究单位；实际 DSH prepared/full-wire 尚需 C2C4 验证 |

回顾性结论得到支持：12/12 对两臂行动相同；A 均在合法条件得分 argmax 集合中；11/12 与旧控制策略字符串一致，H5 为同分选择；10 卡联合可行、5 卡实际达成。不相交且非空的隐藏世界可行集见证出现在 S-public、S-hidden、H-hidden，覆盖两个 family。

可移植包的 `raw_authentication_repeated=false` 正确保留。本轮另行在本机重跑了固定历史 reader，这两项验证不能合并成“任意机器仅凭公开包已验证旧 raw”。C2C3 的封存前开发探针、CLI 失败及其时间顺序仍是历史事实，不改称完全盲化预注册。新模型请求、目录 GET、Worker 均为 0；历史生成尝试仍为 139，历史目录 GET 为 1。

## 2. 必须在下一阶段补齐的三个前置条件

### C4R1：诊断数据尚无真实运行合同

[`task_diagnostic_data.task`](../../src/actio/task_diagnostic_data.py) 明确只是供生产纯结果函数使用的最小适配；它不是完整的 live TaskSpec。现有 [`evaluation_campaign`](../../src/actio/evaluation_campaign.py)、[`evaluation_tasks`](../../src/actio/evaluation_tasks.py) 及 transport/terminal/verify 分派绑定原 12 卡、v9、24 episodes 和 12 个配对。

C2C4 需要显式的新 config/task/input/plan/measurement 合同和代码控制的版本分派。继承 C2C3 固定数据、投影和真值，不把 32 展示直接塞进旧 execute，不放宽旧 suite 的卡白名单。建立全量本机真实 DSH/Concordia 接线与独立核验，合成控制答案只用于 rehearsal，不能进入真实 solver 输入。

### C4R2：新评估必须保留 C2C2，而非只保留 C2C1

[`evaluation_store`](../../src/actio/evaluation_store.py) 的 plan/register/verify/decision 仍直接绑定 C2C2 模块，并用当前实现重建计划；[`migrate_evaluation_copy`](../../src/actio/database.py) 只支持 v3→v4。现有 C2C2 原库已经是 v4，再从 C2C1 v3 开始会漏掉 C2C2 真实评估。

应先用固定 C2C2 reader 认证旧交付，再从其 v4 数据库建立一致快照副本，在副本追加 C2C4 evaluation。保留六份原候选/决策、C2C1 reference、C2C2 live evaluation/decision、所有旧绑定和事件。补齐受信版本分派与历史 source 绑定，禁止 artifact 指定任意可执行 reader，也不通过刷新历史 plan/hash 让旧证据迁就新源码。

schema 4 足够则保留；必要迁移只能在新副本上显式完成，记录 backup/hash/失败。C2C4 主交付应至少包含三个 evaluations（C1 reference、C2 live、C4 live）和两个 evaluation decisions（C2、C4 的 C1），六份原 decision 另外保留；rehearsal 另用隔离副本。仍无 active pointer 和恢复承诺。

### C4R3：输入不变性、候选差异、展示差异是不同检查

| 比较 | 冻结的分组与分母 | 正确解释 |
|---|---|---|
| B0/C1 | 同一 presentation 的 32 对 | A 只有 scaffold 直接改变；B 使用本臂实际 A 历史。只有某指标两臂均 defined 才给 delta |
| normal/reversed | 16 worlds × 2 arms = 32 个展示对照 | 两个 actor 的 options 都逆序；若 A 行动改变，B 还收到不同公开历史，不能将 B 差异都归因于其 options 顺序 |
| 隐藏世界 w0/w1 | 8 groups × 2 presentations × 2 arms = 32 个描述性对照 | 同组/展示/臂的 A prepared/full-wire 应相同；同输入的随机输出不同不是信息泄漏，也不是独立任务证据 |

本轮已重算 A 只有 16 个不同可见视图；两臂形成 32 种输入条件，每种因两个隐藏世界出现两次，共 64 次计划 A 调用。这些是相关的工程观测。调度随机化和每条件一次抽样不能识别稳定的选项位置效应；只报告本轮观察到的行动一致性、集合成员和顺序差异。

若额外报告 B 的“实际 A 相同”子集，应明确它是运行后条件化子集，给出 assigned/eligible/defined/missing/not_applicable，不代替全部展示对照，更不能据此作无条件因果结论。hidden/private 不泄漏要由请求输入证据证明，不能由输出相等证明。

## 3. 推荐的 C2C4 范围

继承原 B0/C1、两步 A→B 信息结构、Persona、空初始 memory、B 规则与模型参数。使用 C2C3 现成的 8 groups / 16 worlds / 32 presentations，单 TokenKey `gpt-5.6` route、单 repeat：**64 episodes、最多 128 seat sends、32 baseline/candidate pairs**。这不是重新取样的新数据集，`independent_research_units=0`、`human_labels=0`。

先解决上述接线和谱系问题，完成本机全 64 episodes 的 rehearsal 与必要错误分支，冻结完整有序计划、分析规则和实现，再普通推送任务分支及 main 并核对远端 SHA。只有这一步通过，下一 session 才执行一次真实 campaign。阶段使用显式 uncapped，沿用既有费用授权，不重新请求同一许可；有限调用数、长度、期限、账务和清理仍有效。

首个技术 unknown/timeout/协议、文本、身份或输入绑定不一致即停止整个 campaign，保留完整后缀、不重试、不补样、不换 route、不追加直接诊断。可信行为错误按照冻结合同继续，非法 A 导致 B 不适用并跳过。不要为了凑足 128 次而发送本应跳过的 B。

首要观测是格式、公开/自身 hard、B 原响应规则是否满足；条件得分 gap、联合结果、效用和全知诊断分别报告，不拼成总分。条件得分只是假定接受时的自身收益，没有隐藏状态先验与接受概率，不是期望收益目标。B local_hard 与 response_rule 的共同来源、format/domain 等依赖必须显示。

静态不合法不发送；技术不完整为 infrastructure_failure；技术完整但 C1 出现已观察合同违规，为本开发集 reject；其他情况一律 insufficient_evidence，即使正 delta 或全零。全部 `eligible_for_activation=false`。不新增候选、训练、LLM proposer、judge、真人校准、沟通轮次、排名或能力晋升。

## 4. 完成定义与后续分流

下一 session 的交付应让另一位审阅者从固定合同、逐 seat 协议与账本、领域事实、完整计划及谱系导出重算结果。至少包含新任务版本、v4 副本追加历史的证据、三类输入/比较合同、独立只读 verifier、实际公开 CLI、冻结发布记录、本机/真实分列统计及全部失败。

若执行前发现新任务或历史绑定无法成立，交付 NO_GO 和已验证准备成果，真实调用保持 0。若真实执行提前技术停止，交付完整分母和 infrastructure_failure，不自动恢复。若完整结束，无论违规和差值如何，完成该阶段并停止；有可信可见规则错误再定位具体失效条件，若继续零违规/零差异，则保留无改善空间的开发观测，另起研究合同讨论信息获取或期望效用，不重复本批寻找效果。

费用币种/单位、实际账单及上游权重身份仍未核实；`binary_source_mapping=unproven`、`full_controller_recovery=unsupported`。这些限制不被本轮工程 PASS 消除。真实累计只增加实际 sent；全部 128 次都发送时才可能为 267，不提前填写该数字。

本轮只在 README 增加当前审阅/Prompt 链接，不新增“C2C4 已完成”里程碑，不修改 C2C3 的封存文件。文档验证后提交并普通推送 main，最终消息给出独立远端核对结果；推送失败不能称为已发布。
