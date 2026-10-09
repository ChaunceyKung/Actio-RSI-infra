# Phase 1C2B2 测量合同

上游 main 为 `6436fc7bc4d25570ee93fb44ab2428635bf6b218`，包含 C2B1 `1e00535408e3a3dd12356dbb2cdf934134fb68e4`。本轮增加 `pilot-config.v6` / `actio-task.v2` / `scheduling-observation.v3` / `attempt-ledger.v4`。旧合同仍按原版本分派，历史产物由固定旧 reader 解释，追加的 raw 文本复核存于独立 sidecar。

## 文本与输入边界

`single-choice-text-audit.v1` 仅审计官方 pi-ai adapter 的事实，不替代生产翻译。上限为 262144 raw bytes、1024 events/chunks；严格 UTF-8、唯一 JSON 键、有限数值、单 choice index=0、assistant role、文本 content、唯一 finish、唯一 usage、唯一最终 DONE。支持普通分片、空增量、CRLF、SSE 注释心跳、附在终态或 trailing choices=[] 的 usage。拒绝多行 data、非文本、工具/refusal/reasoning 分支、额外 SSE 字段、终态后内容及多终态。raw bytes→raw delta.content→adapter deltas/block→native answer 必须一致；length 可记 usage，未完成的原生行动不可进入测量或世界。

账务 settlement 与 measurement admission 分开。可核对 usage 不能消除文本矛盾；被拒绝文本不能产生 domain receipt。未知调用占据原一次性资格，不自动重试。

actor payload 白名单只有 observations、空 memory、ActionSpec。观察只含 seat/role、公共任务、自己的 available/preferred/goal、自己的初始 relationship、实际公开历史。完整 task、config、spec、memory、分组 hash 与 op/run/worker ID 在 Control Plane、manifest、Ledger、native marker 外部层绑定，不进入模型消息。prepared 与 wire 全文的反事实比较覆盖 A 不变/B 私有改变；B 的隐藏反事实固定自身信息和真实 A 行动。

## 测量与分母

`scheduling-measurement.v1` 从两个冻结集合和实际 admitted action 独立计算，不调用 GM task_result，不读取旧 outcome 来换算正确率。

|指标|分母/缺失|
|---|---|
|assigned/sent/response/terminal/admitted/not_run/protocol_error|完整计划 64 seats；attempted 是已分配 operation 的数量|
|格式合法|admitted native answers；未运行/未准入为 null|
|A own|admitted 且合法的 proposal；判断 slot∈A.available|
|B local|A 合法公开 proposal 与 B admitted 合法回应；accept iff slot∈B.available|
|joint_feasible|冻结 A.available∩B.available 是否非空；仅 evaluator 可见|
|joint_achieved|完整 admitted 合法 pair，accept 且 slot 同属 A/B；按 feasibility 分层，不给不可能任务填能力 0 分|
|usage/timing|reported tokens 原口径，cache 为 input 子集、reasoning 为 output 子集；headers/首 text/请求/episode 分列|

非法 action 是行为记录，A 非法时 B not_run。infrastructure error/unknown/text/identity 错误停止整个有限 pilot，剩余行保留 reason。合法 decline 可以对应旧领域 task_failure，但 B local 正确。goal/relationship 保持 NOT_CALIBRATED。

## 冻结与执行

固定 4 singleton availability instances × 2 joint presentations × 2 routes × 2 repeats =32 episodes/max64 sends。调度 seed=20261009，只控制顺序，不冒充 provider seed。每个相同 card/repeat 的两模型 block 交错，block 之间交替先后顺序。每 episode 新 Store/固定 persona/空 memory/独立子 Ledger；同一 Ledger model 不变。

首次 live 前实现与机器可读 preregistration 必须普通推送任务分支及 main。执行器从 Git 核验 clean checkout、远端 SHA、已提交的 preregistration；随后解析凭据。实验 claim 位于项目固定 `.local/phase1c2b2-claims/<prehash>.json`，跨输出目录独占。每个 child 还有一次性 authority。计划及 intent 先持久化，模型发送带 UTC，支持离线核对 freeze→intent→send 顺序。首配对 block 只依据完整性与清理继续，不看分数。无完整 controller 恢复、无自动补样。

`independent_research_units=0`。只有一个 family、两个对称结构；重复、镜像和 UUID 不增加研究独立 N。presentation 同时反转两 seat 选项，不能识别单 seat 位置效应。禁止排名、显著性检验、推广 CI、cost-normalized ranking、judge、训练和晋升。

## 路由/费用 Gate

observed label、provider claim、公开 quote、raw usage.cost、估算和 billed cost 分列。未知 Decimal 单位不可转换为 USD。账单/权重身份缺失仅限制相关结论，不阻止有限工程 pilot。保留 binary_source_mapping=unproven、full_controller_recovery=unsupported。
