# Codex 执行 Prompt：Phase 1C2C3 任务判别力与可见信息诊断

请实施 **Phase 1C2C3**，交付可运行的离线任务诊断能力、C2C2 回顾性 sidecar、一个有限合成对照集和独立核验 CLI。目标是解释现有测量能区分什么、哪些结果受信息结构限制，为下一次有限真实试验准备明确问题。完成验证后提交并推送任务分支及 **main**，核对远端 SHA。不要只交付设计文档。

项目：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
仓库：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
建议任务分支：`phase1c2c3-task-diagnostics-and-observability`。
产品基线：`6466e2be6f31e0ac5861a379d761d2e7bf39c5eb`；C2C2 冻结 reader：`3bef7e15b0eb21beeb10888eb508056592b977b0`。当前 README/MILESTONES 升级位于 `f89f39c0b9f001764c3eefad6b993ec46d6eca56` 及其后继。

从包含本 Prompt 的最新 origin/main 开始，记录实际 HEAD、祖先关系、工作树及远端。读取 AGENTS.md、README.md、MILESTONES.md、本次审阅与证据 `docs/reviews/phase1c2c2_review_and_c2c3_plan.md`、`docs/reviews/phase1c2c2_review_evidence.json`，以及 C2C2 CONTRACT / RESULTS / GATES / DEVELOPMENT / CLI / manifest / preregistration / public report / lineage / decision。

## 0. 范围、授权和完成定义

本轮是**离线工程实现**：新增模型请求、provider 请求、目录 GET、MCP 调用和 DSH Worker 均为0；无需凭据，不调用 key smoke、诊断模型或 live judge。这里的零调用是任务范围选择，**不撤销用户既有 TokenKey 无金额上限授权，不新增费用审批，不将政策改回预算0**。

沿用已经通过的运行栈和历史证据；不修改旧候选、Persona、生产任务语义、旧报告或决策，不执行已完成的 C2C2 claim。不开新 live 入口、不删除 claim、不补样，不新增 C2/LLM proposer、训练、部署或自动激活。

完成意味着：

1. 可从已核验 C2C2 行动和固定任务数据重算回顾性诊断；
2. 可见信息参考策略不会接触对方 private 或 oracle；同分集合、未知和不适用有明确语义；
3. 一个确定性、有限、版本化的32展示诊断集具有可核验的隐藏世界与顺序变换关系；
4. 独立 oracle / 生产规则 / 手算样例的交叉检查和控制策略敏感性通过或诚实报告失败；
5. 公共 CLI 和可移植包能离线复核，明确其来源信任范围；
6. 文档、证据、README 当前入口与 MILESTONES 同步，结果发布到 main。

历史真实生成尝试保持139，目录 GET 1另计；C2C2 仍为24 episodes / 48 sends / 12 pairs / 所有 delta=0，C1 insufficient_evidence，activation=false。C2C2 的14项覆盖不是14个独立研究指标。

## 1. 复用与先读代码

优先复用 `suite_tasks.py` 的任务域、options、可见观察与世界规则，`suite_oracle.py` 的独立计算，`suite_measurement.py` / `evaluation_measurement.py` 的适用性与分母思想，`eval_contract.py` 的封存机制和现有只读 guard。检查 `tests/test_suite.py`、`tests/test_evaluation_candidate.py`、C2C2 公开 CLI 与历史 reader 脚本。

已有 suite 测试包含穷举真值、手算边界、first_option / always_accept / always_reject / own_rule。新增的是可复用的可见信息接口与诊断产品，而不是重新包装测试数量。参考策略应从当前机制抽取最小纯函数或作窄适配，不带入网络、Worker、全库状态或持久会话。

Concordia 机制来源保持 `b71d202750e23444ce1bf28d9f114bcd88aa41db`，当前本地参考路径为 `../../codebase/15_concordia/repo`；只在需要核对机制/许可时读固定文件。Raven 配对与档案逻辑继续用现有窄复用，不引入 root fork；SOTOPIA parser/schema 不承担这轮有限算术任务的标签权威。不新增框架、数据库或依赖，除非确有必要且先给出具体理由；目标应可用标准库与现有纯模块完成。

定义明确的新 `task-diagnostic-*` 数据版本（具体名称可按代码风格调整），与 v9/candidate campaign 解耦。旧 `suite_tasks.get/card/validate` 继续只接受原卡；不得为诊断数据解除旧 live 合同的硬编码限制。若需要共用算法，保留旧输出逐字回归，新增入口使用自己的严格数据合同。

## 2. C2C2 回顾性诊断 sidecar

先用受信的固定 reader 检查原完整 delivery。若受控归档缺失，仍可从已发表 report 做描述性分析，但必须标记 `source_assurance=public_projection_only`，不能声称完成 raw 协议复核；不得让 artifact 提供任意源码或动态插件来选择 reader。读取原库时仅只读，不迁移、不写新 evaluation decision。

旧12卡每卡保留两臂行动、任务/报告/reader/source hash、format、自身约束、B规则、joint、实际效用、全知上界/regret和原 decision。只新增解释字段，不回写 C2C2 的 report / manifest / lineage。

本次审阅得到的结果需独立重算：12/12 对两 actor 行动完全相同；A 都在自身合法选项的条件得分 argmax 集合中；11/12卡与现有 own_rule 的具体字符串一致，H5 的 apple/banana 同分，不能把控制策略的字符串 tie-break当唯一正确答案。10卡联合可行、5卡达成；S1/S3/H1/H3/H4可行未达成；S1/S3/S6/H1/H3全知regret为正。若重算不一致，保留差异并定位，不能为了匹配这份 Prompt 改数据。

将 C1 的三个通用词条与基础 Persona、ActionSpec call-to-action 逐项对照。只说明内容重合和本次约束指标观测上限，不宣称自然语言重复必然无效、模型等效或虚假响应。

## 3. 可见信息与条件得分合同

参考策略以 **actor-visible view** 为唯一参数：public、own、role、当前允许的实际 public actions、ActionSpec。不传整个 card/task/全局 Store，不接受 opponent private、oracle、joint feasibility、card/group/arm/candidate标签或其派生hash。来源/分组信息置于外部绑定。

对A定义：

- `own_legal_set`：由公开规则和自身硬约束判断；原ActionSpec语法合法不等于自身规则合法。
- `conditional_offer_score`：仅表示被接受时的自身收益；排期为 own utility，议价为 own value−price。
- `conditional_argmax_set`：所有最高分合法行动，保留同分；不把字符串顺序硬编码成正确性。
- `conditional_offer_gap`：有合法行动且可信行动满足自身约束时，最大条件得分减行动条件得分；不适用/未观察/格式错误分别用null及原因，不补0。

这些字段是诊断，不是期望实际效用，也不是“理性最优”标签。未指定隐藏状态先验、接受概率或风险偏好时，禁止推出期望收益最优或将正gap升级为旧合同违规。不要加入推测概率或LLM判断来补足信息。

B参考策略只看其own、公规则和实际A提案，输出原规则的accept/decline/reject集合。在有唯一规范时可以是单元素集合；依法拒绝和任意拒绝必须按原任务区分。空行动集、未知/缺失、语法非法、已观察约束违反和未达成单列。

保留两类 oracle：仅有可见输入的策略控制，和使用完整世界的独立离线评价器。全知上界、regret、联合可行性只属于后者，不回灌策略。为每项指标标注 `engineering / observable_behavior / outcome / omniscient_diagnostic`、所需信息、适用条件和与其他指标的依赖；不组合成总score或把同源字段当独立证据。

## 4. 固定有限诊断集：8组、16世界、32展示

新集标为 `diagnostic_development`、`synthetic_control`，明确受现有开发结果启发；independent_research_units=0、human_labels=0。它不是封闭holdout，也不是32个独立实验或新的真实episode。

两个family各4个结构组。每组固定A自身信息和公开语义，构造2个仅B私有条件不同的世界；每个世界分别使用normal/reversed两种**仅ActionSpec options顺序变化**的展示。总计8 groups × 2 worlds × 2 presentations=32 cards。保留现有排期3 slots、议价2 items / prices1..5和原规则域，不扩展为自由文本任务。

结构轴预先固定为：

1. 公开合法性与高条件得分选项冲突（例如closed slot或非允许报价）；
2. 自身边界（availability、budget/value、zero-profit接受等可手算边界）；
3. 多个条件最优选项同分，区分集合正确性与顺序tie-break；
4. 隐藏条件改变联合可行性或可达结果，用于信息冲突见证。

这些轴是诊断分类，允许组内共同出现多个性质，不声称严格正交。具体数值由上述结构要求一次设计并列明理由，不能按真实模型成功/失败率选题，不调用模型筛题，不悄悄扩成自动搜索器。冻结生成器、参数、输出顺序、规则与数据hash；不按诊断报告结果无限调参。发现合同自身矛盾可修订并记录版本/失败原因，不隐藏旧生成结果。

每个family至少有1组满足：两个隐藏世界的A可见输入相同，双方各自的联合可行行动集合非空，但两个集合不相交。该见证证明没有同一行动能保证这两个世界都达成；不引入未声明分布，不把它转换为自然成功率或研究结论。也覆盖至少一处真正无可行交易与一处zero-profit接受边界。

世界对内必须验证A的完整可见payload逐字一致；B视图随自身信息变化是预期。正常/逆序展示的payload允许options顺序不同，做明确且唯一的语义映射，不把变化藏进通用归一化。若将来接DSH，prepared/full-wire仍需另验；本轮只验证纯payload，不能标为实际wire/runtime验证。

所有group/world/presentation/源卡关联和oracle参数只能出现在诊断封装，不能进入准备给actor的payload。当前 `observation/payload` 投影需要通过对方private反事实与标签变化测试；不能仅依靠代码审查声称隔离。

## 5. 诊断控制与真值检查

复用既有控制思想，但通过新的可见输入接口实现并记录独立类别：

- 格式合法的first-option控制；
- 不遵守自身/公开hard rule的可见高分控制；
- B always-accept / always-reject控制；
- 合法条件argmax的参考集合，以及单独注明tie-break的确定性示范策略。

这些都是合成测试控制，不登记为待晋升候选，不与C1组成新的真实arm。控制输出仅用于诊断，不能作为solver预置答案或训练标签。使用完整世界来判断控制是否违规时，不让完整世界进入生成控制行动的函数。

对有限域执行穷举：32展示的语法合法A/B组合共416种（16排期×3×2 + 16议价×10×2）。逐项核对生产世界规则适配与独立oracle，额外的非法/缺失向量单列。继承代码路径独立性，不用同一个函数生成和验证自身正确答案；至少提供每个family可手算的正常、边界、拒绝、非法示例。

判别力 Gate 要求：两个family均存在可检测的A hard违规、B错误接受和B错误拒绝；有同分集合证据、隐藏世界不相容见证、顺序变换不改变语义真值。某控制恰好在某卡正确时如实记录，不要求所有弱控制处处失败。控制之间的区分能力不等于可区分真实模型或候选效果。

每个观测层次分开计数：group、world、presentation、action combination、policy control、历史live pair。所有指标保留assigned/eligible/defined/missing/not_applicable恒等式；对布尔项才使用true/false。格式错误、未知和语义不适用不删除、不补零；不要把镜像世界与选项逆序当独立研究N。

## 6. 可用CLI、封存与独立核验

设计最小公开入口，例如 `python -m actio.task_diagnostics plan/analyze/verify`；具体名称可以调整，但文档命令必须实际执行。建议职责：

- `plan`：纯输出合同、数据设计、版本和范围，零key/env/network/process/runtime/write；
- `analyze`：显式读入受信报告/诊断数据，在新输出目录中生成sidecar、有限真值表、指标依赖表、分组证据及manifest；只写指定新目录，不覆盖原数据；
- `verify`：仅对诊断包重算封装、引用、来源范围、投影不变性、真值、指标和分母，零key/env/network/process/runtime/write。

新包应可复制到其他目录复核，不依赖原实验盘符、现场数据库、凭据或绝对路径。包含重算所需的最小合成输入和**公开行动摘录**，不复制历史 raw reasoning、HTTP秘密或整个受控delivery。明确两层验证：诊断包内部一致性/合成逻辑可移植复核；旧真实行动的完整raw来源认证需固定旧reader和受控原包。不能把自行重封的公开行动当供应商签名，诊断核验成功不冒充旧live协议完整核验。

绑定输入内容hash、reader/source版本、数据schema、规则、生成器、策略控制、逐指标定义与报告。包内路径仅允许列明的相对数据文件，hash登记不授予执行任意脚本的权力。未知schema、缺世界/展示、重复identity、错误绑定、来源断裂应明确失败。保持导出只读事实与权威Store的区别，本阶段无需创建第二套谱系数据库。

## 7. 验收与证据范围

只做与本轮相关的必要验证：

1. C2C2固定reader精确复核或明确归档缺失降级；旧decision/hash不变；
2. 仅可见输入参考策略、argmax多解、正gap与违规区分、非法/缺失/空集合；
3. 8/16/32分层与416合法组合、独立oracle/生产规则/手算边界一致；
4. hidden world / options order 的明确变换关系，分组标签和私有字段不泄漏；
5. 控制策略敏感性、指标依赖、完整分母；
6. 新输出不可覆盖、移址复核、必要坏包拒绝、read-only guard、干净安装或最小读取环境和实际CLI。

若沿用原产品安装环境，应核对当前源码与installed package一致；纯诊断入口运行时仍不import/启动DSH或Concordia。无需重跑与本轮无关的长超时/真实runtime矩阵或所有历史suite，也不为文档改动调用provider。旧完整suite真值已验证的部分复用来源，新数据和新抽象必须有实际测试。

任何失败记录保留真实source/argv/版本，不把前一源码测试改标为最终通过。C2C2 `local-acceptance.failed_attempts_retained=[]`不代表从未失败；已有CLI开发失败及早期快照要继续保持可见。

本轮没有受管Worker/模型请求，清理报告应如实写“本轮未创建”，不复用历史197个Job当成本轮清理工作量。现有账本不改，unknown仍按原历史保留。

## 8. Gate、后续问题与发布

独立报告：`historical_source_assurance`、`retrospective_diagnostic_reproducibility`、`visible_information_boundary`、`diagnostic_dataset_integrity`、`oracle_consistency`、`control_sensitivity`、`offline_portability`。`live_solver_discrimination=NOT_RUN`、`research_validity=UNESTABLISHED`、`capability_admission=insufficient_evidence`、`production_activation=BLOCKED_FALSE`。不要为已有候选新增或覆盖准入decision来表示诊断完成。

若找出规则/oracle实质矛盾或预定诊断集无法满足见证条件，相关Gate标NO_GO/PARTIAL，交付已完成代码、有限失败、精确原因及建议；不静默改旧结果或扩大范围。全知上界与可见策略差异本身不是oracle错误。工程PASS不说明C1具备收益，也不能宣称已解决计价、上游身份、binary_source_mapping或full_controller_recovery。

在 `NEXT_EXPERIMENT.md` 中写一个有选择理由的C2C4草案：根据诊断决定先测试可见规则鲁棒性，还是先设计公开沟通/信息获取与新的效用目标。明确哪些变量会改变、研究问题、候选/参照、独立单位、有限调用计划、失败条件与证据需求；不要同时改变任务信息结构和候选后仍把结果归因给旧C1。暂不执行新live、不征求重复费用批准、不增加自动续跑。

交付 `docs/validation/phase1c2c3/` 的 CONTRACT / RESULTS / GATES / CLI / NEXT_EXPERIMENT、diagnostic dataset、回顾性sidecar、各项诊断报告、必要测试证据和manifest。更新根README的当前入口与范围，保留整体项目介绍；在MILESTONES顶部追加阶段摘要，不把根README恢复成阶段日志。

实施前冻结设计合同；有限数据检查前封存数据、策略和评价版本。由于本阶段没有live，发布前置与模型授权无关；验证完成后普通commit并push任务分支，安全合入main并普通push，独立核对远端两个SHA和工作树。无分叉快进，有并发先整合验证，不force push、不覆盖无关修改。完成精确凭据及敏感材料扫描，不上传受控原始reasoning、数据库或缓存。网络阻塞时保留本地提交并说明未发布，有限正常重试，不能声称远端已完成。

最终中文报告给出：回顾性关键发现、8/16/32数据与真值覆盖、信息边界见证、各Gate与限制、真实调用0/历史139、测试范围、下一问题建议、main提交及RESULTS/manifest/CLI链接。**停止于C2C3**，下一session再决定执行C2C4。
