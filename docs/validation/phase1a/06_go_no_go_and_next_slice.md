# Gate 与下一最小 slice

**CONDITIONAL_GO：继续使用 DSH，限定Windows x64官方0.1.5rc1、隔离短路径、固定profile/plugin、静态只读授权和确定性fixture。** 这不是production ready，也不是live已接通。没有触发Strands探针：G0没有被证明必须重写DSH loop/storage，当前配置与窄plugin可满足范围。不能因完整fork/cancel缺失或曾经下载超时就推翻主选。

| Gate | 结论 | 证据/限制 |
|---|---|---|
| G0 artifact+真实loop启停 | PASS | 官方wheel/hash/exe已明确；真实SDK/TS/loop/journal启动和停止；中文空格路径通过，短根配置必需 |
| G0 home/session/context/tool/policy隔离 | PASS | 双home并发、session上下文、同op两策略1/0调用；最终tool inventory受控；rewrite后hash/schema/scope/权限/预算deny0 |
| G0 shared Runtime | PASS | assistant与真实Concordia external Entity共用同一个adapter，无第二solver loop |
| G0 occurrence/projection | PASS | 真实journal比对+SQLite重复/冲突/gap/remap；mapper升级不增业务effect |
| G0 bounded failure/unknown | PASS | deadline/EOF/exit/MCP收到后kill、receipt未持久化、commit/ack丢失；有界关闭，unknown不自动重试，partial不伪装成功 |
| G0 single owners | PASS | DSH唯一native session/loop；GM唯一world/调度；SQLite唯一probe occurrence/effect writer；未实现第二memory权威 |
| G1完整生命周期/扩展 | unsupported/NOT_RUN，原生cancel兼容性单列FAIL | 精细cancel/status/catchup/resume/fork、remote worker、viewer/graph、第二simulator、100Agent压力后置；不能把安全有界停止后置 |
| G2 live/研究效果 | BLOCKED | budget0，无明确provider/model/正预算；不调用、不报费用/模型成功 |

最重要的未决问题：binary→source build映射未证；该artifact的较新cancel决策不可靠，最终profile只发allow/deny；SDK本身的通知队列/whole-run等待仍需产品supervisor与背压；原生flush需要受信交接给canonical collector；旧session重启拒绝，完整恢复不能默认；精确wire/fsync故障与power loss未测。当前只读范围不依赖这些G1能力，未知状态仍必须人工/明确receipt reconcile。

下一slice只规划：**单机、单活动run、持久身份、只读MCP助手和两人Concordia共享Runtime；canonical facts、最小memory revision与诚实失败状态。** 以下是可审阅任务，不在本轮实现。

| Task / B映射 | 具体交付与验收 | 依赖 / 可继承 / 要丢弃 |
|---|---|---|
| S1 pin/身份/运行台账；B04+必要B06 | 持久agent ID、run ID、native store/session creation identity；单活动lease；相同identity重启可查但不隐式resume | B02b；继承source身份规则与artifact锁；probe硬编码stream/临时UUID不直接当产品API |
| S2 supervisor/readonly policy；B05+B08 | 从零allowlist env、短根、最终registry核验、冻结policy与schema/tool hash；deny0；初始化/运行/close总期限；无遗留子进程；unknown禁止重发 | S1；继承guard/Job行为测试；替换 `_proc`探针监测、测试fault flags、fixture provider、一次性trace文件 |
| S3 canonical facts/receipt；B04+B05 | 原生raw不可变，occurrence/slot/projection、consumer pin、连续cursor、flush marker交接；真实journal重读不双计；gap/conflict暂停完整性声明；本地事务/恢复验收 | S1/S2；继承SQL合同向量与真实seq样例；丢弃简易Collector，产品化最小事务/幂等/背压，不扩大成全事件平台 |
| S4 最小memory revision；必要B06 | agent/branch namespace、来源fact、CAS revision、一次受控retrieve/write；同事实重投影不增一次memory发生；不做M0–M6全集或图数据库 | S3；继承consumer/occurrence去重规则；没有现成memory实现可继承 |
| S5 assistant与两人social；B07+B08 | 同RuntimePort；ActionSpec→intent→GM resolved串联；实际provider输入隔离；只读工具许可；起点manifest可重执行，mid-run明确unsupported | S2/S3/S4；继承external Entity薄桥、GM resolution/输入隔离测试；fixture场景保留作测试，不包装成通用simulator |
| S6 run/失败恢复验收；B05+B07+B08 | 正常run完成；收到工具后崩溃/receipt丢失/commit后ack丢失均可识别；canonical只消费一次；partial/unknown UI或API状态诚实；进程和端口清理 | S1–S5；保留定点故障证据模型，新增产品级集成测试；真实provider另受预算gate |

B09–B11在S6运行/恢复验收之后，先pilot/效度与测量合同，再演化准入/lineage；C03 selector可后置，不能为了“复用完整”提前搬入Raven。暂不允许写效果工具、任意候选代码执行、自动中途resume、多活动run并发、全profile热更新或动态Python审批。

本轮到此停止。交付本地验证分支与提交，未授权自动开始以上slice；未自动push/merge main。复测采用 [probes README](../../../probes/phase1a/README.md) 的固定命令，证据manifest列出每项真实状态，历史失败保留独立文件。
