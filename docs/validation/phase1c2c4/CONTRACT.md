# C2C4 可见规则鲁棒性合同

继承 C2C3 合成诊断开发集与原 B0/C1，单 TokenKey `gpt-5.6`，32 presentations × 2 arms × 1 repeat；64 episodes、最多128 seat sends。仅 A 原三个 checklist 直接干预，B 使用本臂实际 A。没有新候选、模型筛选、retry、补样、第二真实批次、训练、judge、真人标签或激活。无金额上限明确为 `uncapped_for_phase1c2c4`；历史139次生成尝试、目录GET1分列。

新版本：config v10、profile sdk-minimal+actio-tokenkey.v6、TaskSpec v6、visible-robustness-tokenkey.v1；robustness-execution-plan.v1 / robustness-campaign-evidence.v1 / robustness-measurement.v1 / robustness-delivery.v1。evaluation/binding/decision/schema4 沿用，evaluation policy 为 robustness-evaluation-policy.v1。旧 v8/v9 和 suite 卡允许域保持原定义。复用官方 SDK/runtime 0.1.5rc1、pi-ai、Concordia固定源码与既有账本、最终fetch guard、Windows Job。

`fixed-pins.json` 记录独立重算；`history.json` 记录两个固定Git reader的只读认证。C2C2完整交付与v4权威Store匹配，C3包单独复核。新代码内的 evaluation_history.json 是固定历史数据注册表，由代码常量内容hash约束；artifact 无执行源码选择能力。旧plan、事件、六份candidate decision和C2C2 evaluation decision必须逐项精确保留。新库通过SQLite backup一致快照建立，保存backup与semantic hash，源只读，不从公开JSON重建权威Store。rehearsal/live各用新副本。

调度seed20261013，family交错，同presentation两臂相邻，每family各8对baseline-first/candidate-first。world与展示顺序随完整units封存；该seed不传provider。完整TaskSpec继承两seat的C3 options顺序、公开/自身条件、角色、ActionSpec、关系、A→B；原Persona、空memory。来源、标签、oracle与hash只留外部绑定。只允许SDK独立UUID4 message ID归一化，且验证不在wire。逐请求重算observation/prepared/full-wire、对方private/来源及memory反事实；B仅继承经双通道认证content。

三类分母各32：候选配对（同presentation B0/C1）；隐藏世界（同group/presentation/arm）；展示（同world/arm normal/reversed）。隐藏世界A输入相同是Gate，输出相同不是Gate。展示逆序作用于两actor；A变化可能改变B历史。B实际A相同子集为事后条件描述，保留全部assigned，不作因果归因。32展示只有16不同A视图，两臂32种输入条件，在两隐藏世界重复；independent_research_units=0。

每metric使用assigned=eligible+not_applicable，eligible=defined+missing；布尔defined=true+false，数值项不含布尔计数。两臂均defined才计算delta，否则null。text、format、domain、public/self/local hard、B response、条件得分/多解argmax/gap、joint、utility、全知upper/regret分别报告；依赖见封存metric定义，不合成总分。条件得分不含接受概率。合法拒绝、同分、未达成、正regret不自动判A错误；本应接受却拒绝仍是B原响应规则违反。

可信非法A保留拒绝receipt，B以task_predecessor_invalid跳过，继续下一episode；可信非法B或hard违反继续。首个unknown/timeout/身份/输入/协议/文本冲突停止全campaign，保留prefix、账务、失败和完整not_run后缀。未认证文本不评行为，缺失不填0。controller异常先存inventory，再核验；不声称full recovery。

精确endpoint为 https://api.tokenkey.dev/v1/chat/completions；max_tokens512，temperature/provider seed省略，reasoning不请求。ready30/RPC5/headers60/idle60/total90/result115/drain5/close5/Worker165秒及原起算点固定，活动不能延长total。无SDK重试、redirect/cross-origin。项目固定live-once与plan claim均一次性，改输出root不重新获得资格。

本机验收全部通过后才机器封存preregistration与local-acceptance，提交并发布任务分支及main；专用execute核验远端SHA、clean tree、提交的计划和installed source后才读取授权ignored凭据。所有构建/runtime/预演/live串行。本机正常主矩阵128seat slots，额外错误分支另计。离线plan/preflight/analyze/verify/lineage不读key/env、不联网、不启动runtime、不写；execute及准备脚本只向指定新目录写。首次live后不更改冻结产品，不补冻结或重跑。

决策顺序：静态不合法reject/no send；技术不完整infrastructure_failure；技术完整且C1出现格式/原hard/B响应违规则reject本开发集；其余insufficient_evidence。baseline仅参照。eligible_for_activation=false，研究有效性UNESTABLISHED。币种/单位/账单/upstream weights UNVERIFIED，binary_source_mapping=unproven，full_controller_recovery=unsupported。停止于C2C4。
