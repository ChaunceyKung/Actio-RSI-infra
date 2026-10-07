# 10 · 文档级接口合同 v0.1

本文件不生成SDK/server。合同是Actio语义边界，现有stdio JSON-RPC是DSH transport，不冒充已经实现这些方法。所有请求包含 `contract_version, request_id, idempotency_key, deadline, trace_context, namespace, expected_revision/lease_epoch(适用时)`；响应是 receipt 或 typed result，long operation返回operation_id。未知major/required capability拒绝，不能静默降级。

共同错误：invalid_input、incompatible_version、unsupported_capability、permission_denied、stale_revision、lease_lost、deadline_exceeded、cancelled、dependency_failure、incomplete_evidence、unknown_effect、corrupt_state。错误携retryable与effect_state，retryable不自动授权再次产生效果。相同幂等键+相同hash返回已有receipt，不同hash为conflict。取消必须ack且区分requested/terminal；timeout不证明远端停止。每份合同下方另列特有恢复与成功/失败例。

## RuntimePort

| 项目 | 合同 |
|---|---|
| 输入/输出 | prepare(spec_ref, profile_ref, lease)→RuntimeHandle+capabilities；execute(observation/context refs, budget)→OperationReceipt；events(after_cursor)→NativeEnvelope；cancel/status/close；resume/fork仅capability允许 |
| owner | Python拥有run/spec/lease，worker拥有native session/loop；RuntimeHandle不取得world/memory写权 |
| 版本/能力 | runtime/SDK/native schema/pins；declare cancel、resume、fork_seq、event_catchup、isolated_profile、tool_interceptor；DSH当前public缺口返回unsupported直到C01 |
| 幂等 | prepare按run+profile hash；execute必须durable receipt或拒绝重试，禁止SDK本地timeout后重发prompt |
| 错误/取消/超时 | cancel传worker并等待terminal或unknown；crash=dependency_failure；lease_lost停止新dispatch |
| 事件 | run、model、tool与native status映射；原生seq/hash保留 |
| 恢复 | journal合法前缀+cursor+pending ledger；无法证明完整则needs_reconcile或从episode起点重执行 |
| 成功例 | prepare(v1)→ready→execute(obs17)→accepted(op8)→observed(seq42..48)→独立 native flush barrier→canonical commit→consumer ack；idle 单独记录 |
| 失败例 | prompt已接收后连接断开→op8 unknown→查receipt/catchup；不能另发op9当重试 |

## Worker lifecycle contract

| 项目 | 合同 |
|---|---|
| 输入/输出 | launch(artifact_hash, dsh_home, profile, env allowlist)→worker_id/caps；health→epoch/status；drain→quiescence；terminate→exit_report |
| owner | supervisor拥有process、资源/预算；DSH拥有session锁；每个home独立 |
| 版本/能力 | pin OS/arch/node/wheel/SDK/runtime组合；声明sandbox enforcement与平台缺口 |
| 幂等 | launch reservation以worker_id唯一；重复请求返回同进程记录；不得误认PID复用 |
| 错误/取消/超时 | startup timeout终止并记录；drain超时保留pending；terminate升级到kill须报告未清理效果 |
| 事件 | worker.started/ready/draining/exited/crashed；resource_exceeded；lease变更 |
| 恢复 | 确认旧进程/锁释放后新epoch；活worker不靠TTL抢原生日志锁 |
| 成功例 | reserve w3→launch pinned wheel→SDK initialize→ready→drain→close→exit0 |
| 失败例 | Windows wheel/native dependency启动失败→release reservation并记stderr受限ref→禁止标ready，切备选需ADR |

## EnvironmentPort

| 项目 | 合同 |
|---|---|
| 输入/输出 | open_episode(config/pins)→handle/caps；next_observations(scope,cursor)→obs/action_space/clock；submit_intents(op_id,expected_world_revision)→accepted/rejected/pending；poll_outcomes→resolved event refs；termination/close |
| owner | environment独占world/clock/scheduling，Actio控制调用预算与关联记录 |
| 版本/能力 | env/scenario版本；batch_step、async_pending、snapshot/restore/branch、quiescence、visibility、clock_kind显式声明 |
| 幂等 | op_id+world revision+intent hash；无法持久幂等的上游必须拒绝自动重试 |
| 错误/取消/超时 | illegal_action、stale_world、partial_tick；已裁决行动不能cancel成未发生；pending timeout不推进时钟 |
| 事件 | observation、action.submitted/rejected、environment.resolved、tick.failed/committed、episode.ended |
| 恢复 | env独立manifest；Concordia partial checkpoint不默认restore完整，Ray failed batch逐项reconcile |
| 成功例 | obs at t5/rev9→intent op4→GM resolve→outcome rev10→记录t6 |
| 失败例 | op4基于rev9、world已rev10→stale_world拒绝→重新观察；绝不直接覆盖world |

## EventPort

| 项目 | 合同 |
|---|---|
| 输入/输出 | append(envelopes,source_cursor)→committed_offset/ack；read(scope,offset)→ordered facts；export projection→outbox cursor |
| owner | canonical writer；producer只提交事实声明，scope由可信映射校验 |
| 版本/能力 | envelope major/minor、mapping_version、source schema；声明max bytes/batch与catchup |
| 幂等 | occurrence=producer+logical stream instance+native id/seq；稳定语义 slot；mapper version 只属于 projection revision。consumer+occurrence+slot 去重效果，切换版本不双写 memory/score/outbox；同 occurrence 不同 raw hash 才是源冲突 |
| 错误/取消/超时 | missing_parent/seq、oversized、corrupt_payload；超时查commit receipt；已commit不取消，追加修正 |
| 事件 | append failure为独立受限操作日志；恢复后补记录gap/correction，不递归无限产event |
| 恢复 | 一事务 occurrence/projection+连续前缀 cursor+本地效果 receipt；consumer pin 投影版本。进程重启保留原逻辑 stream；新创建 session/home 分配新实例；physical generation 需 lineage 映射，不自动生新事实。缺失 seq 阻断完整轨迹声明；详情见 05 与 Phase 1A P3 |
| 成功例 | source seq7重发两次→仅一条fact→两次均ack相同offset |
| 失败例 | 同seq7不同hash→conflict/quarantine→原事实保留，不后写覆盖 |

## MemoryPort

| 项目 | 合同 |
|---|---|
| 输入/输出 | retrieve(query,scope,as_of,budget,policy)→refs/scores/context_hash；write(delta,source_events,expected_revision)→new_revision；consolidate(snapshot,policy)→proposal/new snapshot；forget→tombstone receipt |
| owner | Python memory唯一写者；worker只提案/读context；graph/vector是投影 |
| 版本/能力 | memory schema、M层、policy/model/extractor；declare temporal_query、namespace、tombstone、migration |
| 幂等 | write key+source set+delta hash；consolidation按input snapshot+policy确定job identity，输出不假定LLM确定 |
| 错误/取消/超时 | visibility_denied、stale_revision、missing_sources；cancel未commit提案，已commit新revision保留 |
| 事件 | memory.retrieved/written/consolidated/forgotten；保存实际上下文顺序和截断 |
| 恢复 | snapshot+event projection cursor；分支overlay隔离，迁移前后hash与版本留存 |
| 成功例 | branchB读取baseline r12→write(delta,r12)→B:r13，baseline仍r12 |
| 失败例 | consolidation基于r12但已有r13→stale_revision→重算/人工合并；不能覆盖r13 |

## EvaluatorPort

| 项目 | 合同 |
|---|---|
| 输入/输出 | evaluate(candidate/baseline artifacts, frozen_eval, dataset_split, trajectories)→EvalReport{metrics,unit_results,validity,cost,raw_refs} |
| owner | independent evaluator executor；proposer无write权限、无sealed输入访问 |
| 版本/能力 | evaluator/rubric/judge/data/split hash；metrics schemas、paired unit、visibility、deterministic/LLM标识 |
| 幂等 | evaluation_id封存输入；重新执行有新attempt，不覆盖旧report |
| 错误/取消/超时 | judge空/错identity/缺维度/非数值/受控judge异常=invalid_measurement；worker/transport故障=infrastructure_failure；缺完整轨迹/屏障=insufficient_evidence；合法运行但约束失败=task_failure。不得都折成task0分 |
| 事件 | evaluation.started/unit_completed/invalid/completed；raw response受限存储 |
| 恢复 | 按unit receipt续跑，冻结条件不一致开新evaluation_id；不混不同judge版本 |
| 成功例 | 30 paired clusters完整→report含N/CI/constraints与unit refs→交Admission |
| 失败例 | SOTOPIA返回[]→invalid unit→按冻结规则双臂重跑或insufficient，不能算满分/零分 |

## Evolution / AdmissionPort

| 项目 | 合同 |
|---|---|
| 输入/输出 | propose(base,seat,allowed_evidence)→CandidateDraft；validate/seal→Candidate；admit(candidate,reports,frozen_policy)→pass/reject/insufficient_evidence/infrastructure_failure+decision_ref |
| owner | proposer只写draft；validator/sealer、evaluator、admission主体分离；active pointer归version registry |
| 版本/能力 | genome seat allowlist、campaign/mutation/admission policy hashes；L0/L1/L2 support；L3仅external |
| 幂等 | candidate按artifact hash+parents；decision按campaign+candidate+evidence set；新evidence产生superseding decision而非覆盖 |
| 错误/取消/超时 | forbidden_mutation直接invalid/reject；budget_exhausted停搜索；timeout不得降阈值；cancel不撤销旧admission |
| 事件 | candidate.created/invalid；evaluation refs；admission.decided；version.activated/revoked |
| 恢复 | sealed candidate与决策日志恢复stage；只有有效pass且CAS成功激活，failed candidate也留archive |
| 成功例 | allowlisted清单diff→seal c2→独立eval→pass d2→CAS v1→v2（新run） |
| 失败例 | candidate试改evaluator hash→validator拒绝→保存c3及原因→v1仍active |

## LineagePort

| 项目 | 合同 |
|---|---|
| 输入/输出 | record(candidate,parents,mutation,evidence,decision)→lineage receipt；query(version/ancestor/scope)→DAG refs；archive_select(descriptor,budget)→candidate parent suggestions |
| owner | canonical lineage writer；Raven selector只是纯读取建议，不能自行admit |
| 版本/能力 | lineage schema、descriptor taxonomy、selector版本；支持multi-parent与failed nodes |
| 幂等 | edge key+content hash；检测cycle及跨scope parent |
| 错误/取消/超时 | missing_parent、cycle、store_failure；写失败向上失败，不吞错；已commit只追加revocation |
| 事件 | lineage.recorded、archive.selection_proposed；候选未晋升也记录 |
| 恢复 | DB事务+artifact refs；selector可重算；损坏拒绝服务并修复，不空表成功 |
| 成功例 | c7 parents[v1,c4]→记录两条来源及失败/成功decision→可审计重组 |
| 失败例 | c7把自身写为ancestor→cycle拒绝→保留原DAG，报告candidate invalid |

## ReplayPort

| 项目 | 合同 |
|---|---|
| 输入/输出 | capture(run,boundary)→manifest complete/partial；replay(mode,manifest,scope)→ReplayReport；branch(manifest,branch_id)→isolated refs |
| owner | coordinator组合各owner快照，不能代替env/tool承诺；source artifacts不可变 |
| 版本/能力 | modes=log/io/resume/reexecution/branch；每owner coverage/exclusions、request_normalizer版本 |
| 幂等 | replay_job_id；branch namespace唯一且copy-on-write；capture epoch+offset固定 |
| 错误/取消/超时 | unsupported_snapshot、hash_mismatch、unresolved_effect；deadline保留partial，cancel不清理原artifact |
| 事件 | checkpoint.sealed、replay.started/mismatch/completed、branch.created |
| 恢复 | hash验证→owner capabilities→pending reconcile→执行；输入改变后拒绝旧I/O匹配 |
| 成功例 | 完整起点manifest→branchB→相同请求hash读录制response→输出匹配报告 |
| 失败例 | 干预改变tool参数→录制hash不匹配→按policy重执行或unsupported，绝不套旧结果 |

## AttributionPort

| 项目 | 合同 |
|---|---|
| 输入/输出 | register_experiment(unit,intervention,control,freezes,metrics,N/budget,analysis)→sealed design；run/analyze→difference report{estimates,CI,confounds,identifiability,evidence} |
| owner | independent experiment/evaluator steward；proposer不改已封analysis plan |
| 版本/能力 | experiment/analysis versions；cluster/paired design、branch支持、claim_level=descriptive/controlled/causal_under_assumptions |
| 幂等 | design hash固定；重复分析有analysis_id并引用同证据，不挑最优结果覆盖 |
| 错误/取消/超时 | interference_unmodeled、insufficient_N、branch_leak、missing_freeze；终止报告partial/insufficient |
| 事件 | experiment.registered、intervention.assigned/applied、analysis.completed/invalid |
| 恢复 | 按episode receipt恢复；freeze漂移停止，不把新旧运行混为同experiment |
| 成功例 | 随机arm顺序的paired episodes→cluster CI→受控差异报告，声明外推限制 |
| 失败例 | 候选memory泄漏到baseline→invalidate experiment→新namespace重建，禁输出因果结论 |

## 协议逐项映射

| 协议/版本 | transport/协商 | auth/能力与错误 | Actio边界 |
|---|---|---|---|
| MCP spec2026-07-28 + client2.0.0 | stdio newline JSON-RPC；HTTP POST/SSE；modern server/discover/per-request meta，SDK兼容legacy initialize | DSH stdio scrub env、HTTP headers；SDK有authProvider但DSH此工厂未接互动OAuth；tool schema/result/isError分开；resources单独plugin；取消best effort/HTTP关流非回滚 | MVP stdio只读tools；兼容矩阵/timeout/contents实测，重连不重做有副作用call |
| A2A fixed proto SHA | AgentCard/Task，多transport | 任务取消/订阅不是world事务；未选SDK | P2对外任务协作，不取代内域合同 |
| Agent Client Protocol | 当前稳定wire v1 schema；package版本另记 | client-agent/editor权限与消息；canonical org迁移 | P2客户端门面；不是AGNTCY ACP |
| OTel spec/proto + SDK1.45.0候选 | OTLP exporter组合待pin；span parent+links | exporter失败/drop可发生，SDK flush不作canonical ACK | 只投影；不导出秘密，不当多父DAG或归因引擎 |

源版本/许可见 E006/E026–E029/E042；以上是 2026-10-05 的规划候选。2026-10-07 实际 artifact/协议组合以 [Phase 1A](../validation/phase1a/README.md) 为准，不用源码 spec 版本代替发行包协议证据。只冻结 B02b 本次验证的最小子集，十个完整 API 仍是草案。

只读工具首期采用 Python 冻结 policy artifact、TS 本地 guard 校验并记录决定。授权绑定 final hash/tool version/policy/run/scope/lease/expiry；rewrite 后再检查 schema 与预算。逐调用动态 Python 审批为 unsupported；没有许可、过期或版本不匹配直接拒绝。新增动态审批需单独定义 op correlation、超时/断线/取消协议并验证，不由通用 incoming-request API 推定支持。
