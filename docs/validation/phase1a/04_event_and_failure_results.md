# 事件、receipt 与故障边界

发生身份与派生表示分离。实验的SQLite仅是合同证明，不是产品store/outbox：`occurrence(stream,seq,raw_hash)`；`projection(stream,seq,slot,mapper)`；`pin(consumer,mapper)`；`effect(consumer,stream,seq,slot)`；`cursor(stream,through)`。mapper升级更改projection，不更改occurrence；消费效果键不含mapper。真实来源的raw hash参与冲突检测，projection不同不当源损坏。

逻辑stream需由受管producer/store/session创建台账分配稳定身份，不能只靠进程PID、文件名、时间戳或physical generation。续读同journal保留身份；新home/session创建是新实例；generation变换需显式沿袭映射。此wheel重启已有ID拒绝且文件不变，所以没有假设“进程重启自动resumes”。独立stream序号复用由小实验验证；真实generation迁移未验证。

一对多投影用稳定语义slot（fact/audit）；v1/v2各两slot共四projection，业务effect仍两条。consumer在事务内切换pin，不同时读两版；新增slot不自动授权产生新业务效果，须独立迁移/审阅。

| Boundary | 本轮可观察证据 | 不能据此声称 |
|---|---|---|
| constructed | receipt SQLite先commit操作intent；尚未收accept | 远端已执行 |
| accepted/messageId | 官方SDK session_prompt实际返回ID | 原生journal已flush或完整turn结束 |
| native observed | SDK notification/plugin session event、session+seq | canonical已commit |
| native persistence barrier | plugin调用真实 `sessionPersistence.flush()`，结束后记录session/through；与文件逐seq比对 | SDK已有durable-watermark业务RPC、所有磁盘设备/断电保证 |
| canonical transaction commit | SQLite FULL/WAL transaction写occurrence/projection及连续cursor | 下游外部效果已完成 |
| consumer ack | effect receipt事务完成后可ack；重复delivery查询既有键 | 跨系统远端exactly-once |

`event-integration.json`：真实journal header version3，`session.v3.jsonl`，12条原生事件seq0–11；flush marker through11。SDK观察到的事件逐条等于journal对应记录。倒序ingest仍只在缺口填满后cursor到11；24个稳定slot从v1重投影到v2仍24次本地effect。没有把idle本身当flush。

| 故障窗口 / 触发机制 | 结果 | 状态/限制 |
|---|---|---|
| 已accepted但应用receipt未持久化：SDK返回ID，实际provider-input marker已出现；故意不commit应用receipt，kill worker，重开SQLite | intent仍constructed，转unknown/needs_reconcile；真实inbox事件含ID；自动重发0 | PASS；这是**应用回执持久化丢失**。SDK解码前的wire response字节丢失 NOT_RUN |
| MCP已收到调用但collector尚无结果：watcher读到server fsynced received记录立即kill worker | received1，native tool-result0；unknown，无重试 | PASS；定点依据真实received marker，不是随意sleep猜窗口；只读fixture |
| native event可见但canonical尚未commit：真实seq0送collector，在事务提交前抛出注入异常 | rollback；重开DB occurrence0/cursor-1；再次读native安全提交 | PASS；异常rollback模型，非OS kill SQLite瞬间或断电 |
| canonical/effect已commit但ack丢失：丢弃返回ack，关闭重开collector并重复消费 | effect计数不变，v2切换也不多计 | PASS；本地SQLite，未测远端outbox |
| worker EOF/意外exit/run timeout | 期限内退出；操作unknown，partial不报complete | PASS；termination不是cancel/rollback |
| worker重启旧session | SDK拒绝already exists，hash不变 | PASS行为刻画；不支持任意mid-run恢复 |
| stream seq重用/重复/不同payload/乱序gap | 原流重复去重；同seq改payload冲突；新逻辑流可用seq0；gap cursor -1→0→2 | PASS合同fixture；物理generation转换未测 |

原始事件先保留，缺口/冲突拒绝“完整轨迹”声明；未知效果不自动重试，要求receipt核对或明确从新episode起点重执行。读取同一个journal是重建事实，不是再次调用工具。partial runtime结果和measurement缺证分开：前者可能infrastructure_failure，缺完整测量输入为insufficient_evidence，不能补成成功或任务零分。

本轮未稳定注入并明确NOT_RUN：SDK response解码前wire丢失、精确fsync系统调用中断、disk full、断电/设备缓存、跨主机故障、generation migration。G0所需的有界失败、unknown不重试、稳定去重/冲突/缺口已有证据；这些扩展故障不能由本轮结果外推。产品B05仍需把flush marker和collector cursor做成受信握手及背压，而非依赖probe本地文件。
