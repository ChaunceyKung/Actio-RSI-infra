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

执行顺序：schema/namespace→permission/budget→domain policy→context augmentation→audit→dispatch。稳定 priority+plugin ID 排序，同字段多 writer 除非声明 composition 否则拒绝；deny 胜过 approve。hook 只能访问能力声明允许的字段。递归 hook 有 depth/trigger allowlist，初值建议 depth≤2；每 hook 有 timeout、取消和错误事件。权限/审计 hook fail-closed，纯 metrics hook 可降级。所有阈值是待 B02 冻结的默认值。

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

原生 journal→mapper→SQLite 事务（event、source cursor、outbox）→ACK；至少一次传输，唯一键 `(source_stream_id, source_event_id或seq, mapping_version)` 去重。相同键不同 hash 隔离，不覆盖。乱序短暂缓冲并补拉；超过 gap timeout 标 incomplete，禁用依赖完整轨迹的 admission。native seq 与 canonical offset 分开，跨流不假设全局序。

先持久化内容文件并校验 hash，再提交引用；崩溃留下 orphan artifact 可后续 GC，不能留下指向未落盘文件的“成功”事实。SQLite commit ACK 是域持久化边界；native flush 的强度必须 B05 查验，通知到达不自动等于断电安全。

默认建议 envelope≤64KiB、payload inline≤16KiB、单 artifact≤16MiB（更大走附件配额）；每 worker 待处理事件/字节有上限，先暂停 dispatch 再 drain/catch-up。DSH Python queue 当前无界（E001），B03 必须量化并限制入口/补足队列边界。不能以丢弃 canonical 事件实现背压；viewer export 可延迟或丢失后重建。

故障例：tool 已写成功但回执丢失→native timeout→canonical tool.unknown→reconciler 查询目标系统 receipt→确认后追加 succeeded；查不到则 needs_reconcile。cancel 与 timeout 不撤销外部效果。原始敏感 payload 只存受限引用；脱敏、访问与删除策略保留审计元信息，不能把秘密复制到 viewer attributes。
