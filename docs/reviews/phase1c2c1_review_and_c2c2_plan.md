# C2C1 审阅与 C2C2 有限真实候选配对方案

日期：2026-10-09（Asia/Shanghai）。基线：`6578c742bd5ab3672c97ee002a6559150c70b1fd`。本轮已核对远端 main 与 `phase1c2c1-channel-audit-and-candidate-lineage` 均为该 SHA；此前最终推送阻塞已经解除。

**维持 C2C1 的限定工程 PASS，建议 C2C2：有限真实 B0/C1 配对与跨评估批次谱系。** 保持候选和任务不变，把已经通过的本机链路接回 TokenKey，先处理评估批次复用和行为错误分类。不要再跑一轮相同 fixture 并把零差值当成清单有效，也不要直接实施生产激活。

[完整执行 Prompt](../prompts/phase1c2c2_live_candidate_pairing.md) · [审阅证据](phase1c2c1_review_evidence.json)。本轮仅审阅、离线验证和规划，无产品代码变更，无新真实模型请求。

## 1. 实际核对

| 项目 | 本轮结果 | 证据范围 |
|---|---|---|
| manifest / 版本 | 52 artifacts、60 产品文件、4 入口、95 工具/测试文件匹配 | 工作区与固定 Git blob；AGENTS.md 仅既有换行差异 |
| 原始归档 | 12 ZIP、2,001 成员、143,686,718 未压缩 bytes 匹配 | 归档和成员逐一 hash |
| 安装 / 冻结 | 安装的60文件匹配；冻结至交付产品源码未变 | 冻结 `dc15292bc6827593e8321e31acbcf599dd25d772`；本地发布/intent时间顺序有效 |
| 当前验收 | 8项C2C1成功记录与当前产品来源绑定；2份失败保留 | 未重跑全部runtime；20项旧纯回归属于交付注明的前一源码快照，不冒充当前全量回归 |
| 增量执行 | 2项纯测试通过 | 历史双通道/时延语义、候选policy与完整分母 |
| 完整导出 | 固定reader重新核验delivery；报告与已发表报告完全相同 | 拒绝网络、子进程、runtime import、key/env和文件写入 |
| 账本 | 73数据库文件hash匹配；36份Ledger只读重算、字节未变 | 主矩阵48 sent/48 usage/0 unknown；开发验收20 sent/16 usage/4 unknown，分开保留 |
| 清理 | 68具名Job无活动进程；13登记端口无监听 | 13服务join为历史记录核对 |

主矩阵24 episodes/48 seats，全部结束；12个baseline/candidate arm pairs完整，逐卡format、A hard、B local、joint和双方toy utility差值均为0。实际wire核验支持只有A清单发生直接变化；相同A行动时B输入相同。6份提案和6份决策：4个静态reject、B0/C1两份insufficient_evidence，全部不可激活。

它证明本机干预和证据闭环有效，不能证明自然语言清单改善模型行为。fixture本来为两臂提供相同响应；从零差值无法推断真实模型的有效性或无效性。历史真实生成尝试仍为91，目录GET另计1。

## 2. C2R1：新评估需要独立身份，不能重置旧候选

位置：[candidate_schema.sql](../../src/actio/candidate_schema.sql) 中 `campaign_binding`、`decision` 的 candidate 主键，以及 [candidate_store.py](../../src/actio/candidate_store.py) 的 `bind/state/record_decision`。

C2C1每个候选仅有一份campaign binding/decision，状态为validated→evaluating→decided。这个限制符合单批次演练；对已经decided的B0/C1，不能直接再绑定live campaign。清空旧decision、重置validated或给同一清单换名，都将破坏历史连续性。

下一版本应保留不可变proposal/scaffold身份，引入以 `candidate_id + evaluation_id/campaign_id` 绑定的评估记录、事件和决策。静态proposal校验policy与新campaign评估policy分别引用，不修改原proposal中的policy hash。原C2C1决策保持历史事实，新增live评估从新的evaluation状态机开始；evaluating的旧评估仍不可自动重领。

可采用显式v3→新版本复制迁移：原库及原导出不改，新库保留旧表/旧事实，新增evaluation事实归同一Python Store owner。新reader应能同时列出同一个C1的旧local和新live评估，activation始终false。此扩展不是完整controller恢复。

## 3. C2R2：观察完整与行为成功需要分开

位置：[candidate_measurement.py](../../src/actio/candidate_measurement.py) 的 `comparison/analyze_pilot`，以及 [candidate_contract.py](../../src/actio/candidate_contract.py) 的 `decide`。

现版本用joint指标defined判断pair完整，要求24个可评估完整episode才能得到engineering PASS；否则给decision `complete=false` 并进入infrastructure_failure。可信且格式错误的输出会使joint不可评估，A无效还会按合同跳过B。**这可能是完整观察到的模型行为失败，不是基础设施故障。** C2C1主矩阵没有这种输出，因此本轮发表结果不受影响。

新版本应分别报告：技术证据是否完整、每个planned episode是否依合同结束、每项指标是否defined、每个arm pair是否有足够的相应指标可比较。一个格式失败可以有完整证据，format=false，joint/utility=null，B为明确的task_predecessor_invalid；不应自动变成provider unknown或基础设施失败。具体delta仍按指标适用条件计算，不补零、不删除错误。

new policy在技术不完整时阻断，完整且已确认违反预先冻结的候选格式/自身硬约束时可以拒绝该候选的本轮开发准入；其余完整小样本仍为insufficient_evidence。正差值不升级成能力PASS。任务可行性、全知regret和合法拒绝不构成actor违规。

## 4. C2R3：真实模式需单独接线，不能全局解除本机限制

C2C1是明确的v8/local-only设计：config、task、controller、channel dispatch和账务/reader分派都绑定该模式，报告还固定external_provider_requests=0和历史91。下一阶段不是将endpoint替换成HTTPS这么简单。

新增版本化live/rehearsal合同及public execute入口，连接已有TokenKey resolver、官方pi-ai与最终fetch gate；更新原始请求→任务/scaffold→native→评估→谱系的全部绑定及计数。旧v8继续只允许literal loopback，旧reader保持解释不变。新报告依据实际attempt/response/usage计算，不能沿用fixture零请求常量。

真实A可能在两臂给出不同输出。现有comparison只在A相同时检查B wire相等；新版本还应正向验证A不同时，B差异准确来自各自真实公开历史，B的自身条件、模型、指令和权限不变。用本地两种合法A输出覆盖这条路径，不能只测试相同行动。

## 5. 有限实验设计与复用

保持原B0/C1的proposal与scaffold hash，原12张开发卡/两个family、Persona、memory、世界和oracle不变。选择已使用的 `gpt-5.6` TokenKey路由，两个actor同一路由；只测试候选干预，不同时开展跨模型排名。GPT先前的reasoning_content已由C2C1在本地和历史sidecar覆盖，新live仍只报告实际观察的协议兼容性。

计划 **12 cards × baseline/candidate × 1 route × 1 repeat =24 episodes，最多48次真实seat发送**。固定seed、交错arm顺序，平衡两个family；固定模型参数、输出长度、所有期限和停止规则。前一个完整pair计入正式计划，只按证据/清理决定继续，不根据得分停或扩样。

已有12张卡继续明确为开发/探索材料，不能因为换UUID、参数或重跑称为独立holdout；independent_research_units=0。本轮不添加“更多独立任务”来制造表面N，真正外部效度数据另阶段设计。候选保持原三个通用词条，即使与原Persona部分重复也不临时优化；可能没有增益，照实报告。

复用C2C1的candidate/scaffold/绑定/双通道和Raven窄诊断，C2B1–C2C0的真实TokenKey凭据/账本/停止链、C2C0的oracle与任务。DSH/Raven固定源3处本轮重新核对本地与Git blob，未新增依赖或重复完整上游审计；GitHub来源见审阅JSON。已有许可证保留，不重建网关、运行器、评估器或搜索树。

## 6. 下一阶段完成条件

先完成上述三项版本边界及必要本机验收，再冻结并发布实现和计划到任务分支/main；随后执行一次有限live campaign。用户无金额上限授权继续有效，不重复询问同一费用批准，不用成本币种未核实阻断所有工程进度。

每seat一次发送，可信格式/行为失误按任务规则记录并继续；首个基础设施/完整性/路由身份异常按合同停止，保留未运行后缀，不重试、补样、换模型或另起第二live批次。账务unknown与文本准入独立，未知费用不填0，reasoning仅作协议证据，不公开正文或作为下游输入。

成功或停止都要交付完整分母、输入绑定、逐指标delta、缺失原因、旧/新评估关联、四态decision和清理。即使48次都通过，仍为开发集单次探索，不作模型/候选排名、显著性、推广CI或自动晋升。所有版本保持inactive；人工校准、live judge、正式研究、生产激活、自动候选生成均不在本轮。

后续C2C3才根据真实结果决定是否需要新的泛化任务、候选修改或实验设计；没有证据时不扩展为自主演化循环。binary_source_mapping=unproven、full_controller_recovery=unsupported、费用/账单/upstream identity未核实继续列出。

## 7. 本次交付

只增加本报告、审阅证据和下一session Prompt。文档/JSON/引用/计数/精确凭据检查后提交并普通推送main，核对远端SHA。产品修正、迁移和真实配对属于下一session，本次不提前执行。
