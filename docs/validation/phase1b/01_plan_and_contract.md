# Phase 1B 实施合同

基线 `56865ac`；Windows x64 / Python 3.12 / DSH 0.1.5rc1。预算 0，仅合成数据。先实现台账、静态许可和受管 RuntimePort，验收后接入 journal、memory 和 Concordia。最终以实际证据决定 Gate，不以实现文件数量决定。

## 所有权与顺序

SQLite 唯一拥有 Agent/spec、run/request、operation、lease/epoch、native creation、canonical occurrence/projection、memory/effect。DSH 独占原生 loop/journal/工具派发。Concordia Sequential 独占调度及 GM world 更新。Python 不实现模型循环。

1. B1.1：持久输入和不可变 pins；单活动 run；派发前 intent；Popen SDK host 在 stdin 闸门前进入 Windows Job。公开 SDK 生命周期，无 `_proc`。冻结完整工具 schema/实现 hash 和允许参数；最终 guard 不预知 callId。
2. B1.2：自有 SDK host 与 plugin append-only spool 绑定 run/creation/epoch/operation；真实 flush 之后 marker。增量 journal 到 SQLite；连续前缀、receipt、终态和 effect 一起决定完整性。只读 reconcile 永不派发。
3. B1.3：一个 episodic memory 类型；来源 slot、namespace、CAS revision 和 effect 同事务。consumer pin 仅显式迁移。run 冻结检索结果。
4. B1.4：助手只读 MCP；两实体真实 Concordia；同 RuntimePort；跨控制进程保持领域身份和授权 memory；冻结起点重执行分配新 run/stream。

## 窄能力

支持目标：持久身份/spec/query、新 native session、当前 host 内串行 turn、单活动 run、只读 MCP、本地状态、有界强停、只读 reconcile、冻结起点重执行。unsupported：native reopen/resume/fork、在线 catchup、semantic cancel、完整 world restore、动态审批、写工具、live provider、研究 evaluator。R5 原 envelope 的 scores 错误类型问题保留为 B09 前置；产品不导入它。

R1 使用受限 canonical JSON（null/bool、安全整数、Unicode 标量字符串、列表、字符串键对象；无浮点和孤立 surrogate）。策略只包含冻结规则，provider 与测试注入分别独立。按 native creation + callId 去重，参数冲突拒绝；唯一 dispatch 前扣预算，不退款。

R2 单活动 turn 相关性由 dispatch intent、受控 active-turn 文件和消息 receipt 共同核对。marker 必须匹配 run/creation/epoch/op/session，target seq 必须覆盖对应 receipt 与发行物实际的 completed 终态（provider stop 独立）；不接受任意旧 trace。spool 只由受管可信代码写；不是恶意插件隔离沙箱。

R3 每阶段外层 deadline；Job kill-on-close + 内存限制；数据按行和总量限额处理，超限保留前缀并失败。SDK 内部队列未修复，受进程内存与时间约束。任务根带 owner 标记，不自动删除 evidence，不跟随 reparse point。租约 TTL 不授权接管；旧 owner/命名 Job 的死亡与清理经检查后才释放旧 lease。

R4 namespace 固定 project/agent/environment/branch/visibility；跨环境仅 spec 明示授权。source、revision、effect 原子提交；重复 effect 返回原 revision，纠正必须显式 correction。检索保存实际 ID/revision/顺序/截断，运行冻结结果。

## 验收

先 SQLite/合同，再真实发行物。策略、lease 竞争、stale epoch、阶段期限、进程死亡/Job 失败、数据上限、四个崩溃窗口、真实 journal 链、memory 隔离/CAS、实际 provider 输入隐私与非法 action。注入依据明确事件/事务边界。异常 rollback、进程 kill、断电分别标记。wire 字节丢失、断电、disk-full、跨 generation、Linux/WSL 和规模测试 NOT_RUN。Phase 1A 文件与失败证据不修改。本轮本地 commit，不 push/merge。
