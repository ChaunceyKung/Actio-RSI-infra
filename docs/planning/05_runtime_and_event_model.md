# 05 · Runtime、Hook 与事实流

DSH 公开 Python API 的同机桥接已实现，内部 session/fork/cancel 更丰富；不能把内部能力直接视为公开 SDK 合同（E001–E003）。选官方 SDK，保持 native journal，并在 C01 中补最窄生命周期接口。正式实现以 [10](10_interface_specification.md) 为合同、B03/B05 为 gate。

## 运行状态与钩子

运行：allocated→initialized→ready→running→draining→terminal。cancel_requested 与 cancelled 分开；deadline_exceeded 是 control 判断，可能仍有未确认工具效果。一个 agent/branch 同时仅一个有效 lease，worker pool 不共享 dsh_home、persona 或 mutable context。

命令是希望发生的事，decision 是待批准/裁决的状态，fact 是已提交结果。`tool.requested` 不等于 `tool.succeeded`，`action.submitted` 不等于 `environment.resolved`，`version.proposed` 不等于 `version.admitted`。

| before hook 能力 | 约束与可见记录 |
|---|---|
| observe / measure | 不改变行为；观测失败记缺口，核心 fact writer 失败必须暂停 |
| block / deny | 权限级最高；明确 denial fact，不伪装普通失败 |
| approve | decision_id、规则版、授权 scope、deadline；审批超时默认不执行 |
| rewrite / augment | 仅未提交请求；保存前/后 hash、规则版本、变换来源；不得改历史 fact |
| retry | 新 attempt；先检查效果类别与剩余预算，不对未知写效果重试 |

执行顺序（2026-10-07 F02 修订）：可选预检→domain policy/context augmentation/rewrite→最终 schema/scope/permission/budget 校验→decision audit→dispatch。最终校验使用 DSH `tools/pre-execute` 之后的单调 `tools.guard`；deny 不能被另一个 allow 覆盖。许可绑定 final request hash、tool artifact/version、policy hash/version、run/scope、lease 与 expiry；后续改工具或参数使旧许可失效。hook 只能访问声明字段，同字段多 writer 必须声明 composition。递归 depth/timeout 等仍待产品合同冻结；权限/审计失败必须阻止 dispatch。Phase 1A 静态 policy artifact 在启动时冻结，Python 不参与逐次审批 RPC，只有 Worker 执行工具。证据与未覆盖范围见 [Phase 1A](../validation/phase1a/03_runtime_and_tool_results.md)。

Cordis disposer 逆序释放可复用（E004），它不是外部事务；只在 run boundary 换 plugin/profile，L2 新 worker 启动候选，不承诺任意热改。

## Canonical Event envelope

| 字段 | 含义/校验 |
|---|---|
| event_id、schema_version、type | 唯一 ID、合同版本、语义事件名 |
| parent_event_ids、edge_types | 多来源父事件；consumed/derived/triggered/observed，不默认 causal |
| run_id、episode_id、agent_id、agent_version | 必要关联；无 agent 的环境事件允许 null agent，不能伪造 |
| component_version、pins_ref | producer 与 runtime/plugin/model/evaluator 版本 |
| source_stream_id、source_event_id、stream_seq | 原生去重/顺序；映射版本另存，不用 timestamp 排序 |
| experiment_id、branch_id、population_id | 实验与分支隔离；基线也显式 branch |
| command_id、operation_id、attempt、idempotency_key | 请求和多次执行关联；重试 attempt+1 |
| input_ref、output_ref、state_ref、environment_ref | 不可变 artifact ref，内含 hash/size/type |
| wall_timestamp、simulation_clock | UTC wall time+environment logical time；逻辑顺序优先 |
| visibility、observer_ids、sensitivity | 控制 payload 读取，viewer 脱敏不改变 canonical hash |
| payload_hash、payload_ref、status、error | 可验证内容；大内容外置；unknown/denied/cancelled 明确 |

最低事件词表：run/episode.started/ended；observation.received；persona.bound；mental_state.updated；belief/goal.changed；memory.retrieved/written/consolidated；plan.created/revised；model.requested/completed/failed；tool.requested/approved/started/succeeded/failed/unknown；action.submitted/rejected；environment.resolved；reflection.created；evaluation.completed/invalid；intervention.applied；candidate.created；admission.decided；version.activated/reverted。只记录实际产生的规划/解释产物，不承诺获取模型隐藏思维链。

## 原生映射与可靠性

| 来源 | canonical | 缺口处理 |
|---|---|---|
| DSH session/inbox 与 turn 状态 | command accepted、run lifecycle | accepted/idle 不等于 world 已提交；需 env event |
| native model/tool events | model/tool fact，保留原 event ref | 原生缺字段由域 plugin补，不从文本猜效果成功 |
| environment GM/DB/log | observation、resolved fact | resolve 返回 None 时从裁决边界采集，不伪造函数返回 |
| memory/evaluator/version transaction | 对应域 fact | 同事务写 state revision 与 outbox |

原生 journal→occurrence→mapper projection→SQLite transaction→consumer ack（2026-10-07 F01 修订）。发生唯一键为 `(producer_id, logical_stream_instance, native_event_id或seq)`，**不含 mapping_version**。同一原始键不同 raw hash 为 conflict，保留原文并隔离；合法 v1→v2 重投影不比较派生 hash 判断源损坏。

logical stream 包含受管 store identity、native session identity 和原生创建 identity。进程重启不自动创建新发生；继续同一 journal 前缀使用原 stream，新建 session/独立 home 的创建实例才分配新 stream。physical journal generation 是存储/格式版本，不直接作为发生身份：能证明沿袭同一 occurrence 时保存 lineage/seq 对应，不能证明则标 unresolved，禁止将两代都作为新事实消费。

一对多映射使用稳定的语义 `slot_id`，如同一工具结果的 fact/audit，不按数组位置或 mapper 版本编号。projection 主键含 occurrence+slot+mapper revision；消费效果键只含 consumer+occurrence+slot。consumer 原子 pin 或切换投影版本，禁止两版同时进入 memory/score/outbox。新增或拆分 slot 要单独迁移与语义审阅，不能借 mapper 升级创造业务发生。

cursor 仅推进至已连续提交前缀。乱序事件可落库但不越过 gap 对外确认；重复投递不推进效果计数，冲突不覆盖。gap timeout 标 incomplete；native seq、canonical offset 与跨流顺序分开。最小实验见 [P3](../validation/phase1a/04_event_and_failure_results.md)，不是完整产品 store/outbox。

明确分开 constructed、accepted/messageId、native observed、native persistence barrier、canonical transaction commit、consumer ack。先持久化内容文件再提交引用，orphan 可后续 GC；SDK idle 不充当屏障。DSH `sessionPersistence.flush()` 是可调用的本地原生屏障 seam，需独立记录 watermark 并比对 journal；SDK 没有对应业务 RPC。进程 kill 实验不代表断电或设备缓存保证。SQLite effect+receipt 同事务仅证明本地去重，不能推导远端 exactly-once。

默认建议 envelope≤64KiB、payload inline≤16KiB、单 artifact≤16MiB（更大走附件配额）；每 worker 待处理事件/字节有上限，先暂停 dispatch 再 drain/catch-up。DSH Python queue 当前无界（E001），B03 必须量化并限制入口/补足队列边界。不能以丢弃 canonical 事件实现背压；viewer export 可延迟或丢失后重建。

故障例：tool 已写成功但回执丢失→native timeout→canonical tool.unknown→reconciler 查询目标系统 receipt→确认后追加 succeeded；查不到则 needs_reconcile。cancel 与 timeout 不撤销外部效果。原始敏感 payload 只存受限引用；脱敏、访问与删除策略保留审计元信息，不能把秘密复制到 viewer attributes。
