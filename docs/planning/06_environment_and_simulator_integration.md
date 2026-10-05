# 06 · 环境接入与两条切片

环境唯一拥有 world、规则、可见性、时钟、scheduler 与 action resolution。Actio Agent 只提出 intent；RuntimePort 不能向 simulator 私有状态任意写入。契约详情见 [10](10_interface_specification.md)，源码 E017–E020。

## 最小 contract 与可选能力

必需：open_episode(config/pins)→handle/capabilities；next_observations(scope/cursor)→visible observation/action space/clock；submit_intents(expected_revision,op_id)→accepted/rejected/pending；poll_outcomes(cursor)→resolved facts；termination_status；close_episode。同步环境也可立即给 outcome，不能强迫平台 step 返回不存在的数据。

能力声明：snapshot、restore、branch、batch_step、async_pending、deterministic_io、external_effects、clock_kind、visibility_enforcement、quiescence。snapshot/branch 是 optional，附 coverage/excluded_state；缺失返回 unsupported，不空快照假成功。能力变化必须新 env_version。

## 方法级映射：Concordia 主选

| Actio 语义 | 当前上游入口 | owner/实际行为 | wrapper 与缺口 |
|---|---|---|---|
| open/close episode | generic simulation 构造/run；Engine.run_loop | simulator 管实体/GM；没有完全对称通用 close API | scope/取消/清理适配，不能臆造上游 reset/close |
| 观察与可见范围 | Engine.make_observation；Entity.observe | GM 定制逐 entity 观察 | bridge 记录 observer_id/hash，禁止把 GM private log 全量给 agent |
| 下一行动者/space | Engine.next_acting，ActionSpec FREE/CHOICE/FLOAT | GM 选择 entity 与有效行动形式 | 校验输出 schema/合法 choices，再交给 resolve |
| agent 决策 | Entity.act(action_spec) | 作为外部 Entity seam | 同步 act 调用预配置 RuntimePort；避免在既有 asyncio loop 嵌套 run_until_complete，采用专用线程/明确同步门面探针 |
| 提交与裁决 | sequential.resolve；GM.observe + GM.act(RESOLVE) | 返回 None；GM 接收 putative event 再产生 EVENT | 采集 resolved event/log，不能把 None 当成功 outcome；裁决失败显式标记 |
| clock/scheduler | sequential.run_loop、step_controller、GM | 环境负责推进，不属于 DSH session | Actio 记录 step/cursor；不能双重推进 |
| checkpoint/restore | generic.make_checkpoint_data/load_from_checkpoint | 只部分 component states；不恢复 engine cursors | external Entity 会被跳过；完整 manifest额外组合 control/DSH/memory，默认不宣称 mid-run branch |

预计第一 adapter 1–2 人周，另加 checkpoint 探针 0.5–1 人周；先支持从 episode 初始条件重执行、固定 ActionSpec 的小场景。工程量区间来自同步/异步桥接、观察权限和裁决返回差异，不是实测工时。

## 方法级映射：AgentSociety v2 第二结构

| Actio 语义 | 当前入口 | owner/实际行为 | 新要求与成本 |
|---|---|---|---|
| 创建/恢复 | Society workspace 初始化/恢复路径 | v2.9.3 metadata、agent/env 文件 | 配置重建与 Ray actor/proxy 重连；不套 v1 MQTT/Postgres 描述 |
| agent 环境调用 | ServiceProxy + EnvRouter base/actor | agent 通过代理访问环境服务 | adapter 必须显式序列化 refs，不能把 Python runtime 对象直接跨 Ray |
| batch | Society.step → step_agent_batch.remote → gather | 所有批次 barrier，再 EnvRouter.step | async pending、batch_id、deadline、部分失败列表 |
| resolution/clock | EnvRouter.step 后 advance t | 环境更新世界与逻辑时间 | 只有完成 barrier 才宣布 tick committed |
| failure | gather failures→raise | agent workspace 可能已部分写入 | failed tick 不当全局原子回滚；需 per-agent revision/reconcile |
| checkpoint | to_workspace/from_workspace、EnvRouter 恢复 | 文件状态真实存在，in-flight Ray queue 未证实捕获 | 重建式 resume；quiescent barrier manifest |
| trace/replay | sharded trace + timeline | 支持观察/可视 replay，不证明确定重执行 | Replay capability 单独描述，不从页面名字推断 |

预计 P2 2–4 人周加部署/故障注入；MVP 只用此映射验证契约支持结构差异，不实现第二 adapter。

## OASIS 兼容检查

`OasisEnv.reset` 启动 platform task/signup；`step` 先更新推荐，再 gather ManualAction/LLMAction；step 无 Outcome 返回（E020）。Actio 首选 ManualAction，从 platform DB/channel 捕获结果。禁用 LLMAction 避免第二 solver loop；manual interview 也可能调用 LLM，需禁用或预算单列。Platform 管 recommendation、agent graph、数据库与时钟，close 发送 EXIT 并等待 task。DB dump 不是所有 in-flight channel/RNG 的完整 snapshot。

## Mock 设计与双 slice 验收（本轮不实现）

未来 contract fake 仅做三种可控情形：两人资源协商、stale revision 拒绝、pending resolution 后取消；world 是小状态机，只为 contract test，不成长为新 simulator。输入/输出固定，支持 snapshot=false 与 true 两档，防止测试假装所有环境可逆。

Social：synthetic Persona→visible Observation→Mind context→DSH intent→Concordia GM裁决→Outcome→Memory→Event。验收两 agent 不能看到彼此私有 belief；非法行动不改世界；一次裁决有完整 source chain；重新绑定同 AgentSpec/Version 不创建另一身份。

Assistant：Persistent Agent→planning→同一 DSH MCP loop→结果→Memory→Event。首期只读本地检索工具，后续 idempotent-write fixture；权限拒绝/timeout/回执丢失分别留档。两条链共享相同 RuntimePort/Event/Memory/Evaluator/Version/Evolution，没有 simulator 自带 LLM agent 再参与决策。共享性用合同 fixture 与相同失败场景验收，不报代码复用百分比。
