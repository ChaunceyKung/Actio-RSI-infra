# Phase 1C2C5 设计合同（实现前提交）

本阶段交付版本化失败观察、固定历史认证、有限本机官方链路故障验收、可移址合成包和未来调度提案。新增真实provider/目录GET/外部MCP请求均0，只用内存假凭据和literal loopback。保留无金额上限授权，但本阶段不执行真实计划。C4原33 sent、unknown1、95 not_run、infrastructure_failure不变，累计真实172、目录GET1。

## 版本与状态所有权

新增 `transport-failure-observation.v1`、`transport-diagnostic-suite.v1`、`transport-diagnostic-package.v1` 和 `future-block-schedule.v1`。纯观察模块只返回结构化事实和矛盾，不提供action、settlement、retry或activation。新本机入口独立命名空间/新目录/只允许rehearsal，窄复用现有run_unit及v10 TaskSpec/官方传输；这些是C5局部fixture，不登记C4 campaign，也不创建candidate Store/evaluation/claim。旧v1/v2成功审计、账务和旧分派不改。运行时领域库仍由现有run_unit管理。

固定官方DSH 0.1.5rc1、Windows x64/Python3.12、官方pi-ai、Concordia b71d202750e23444ce1bf28d9f114bcd88aa41db。源码参考不是二进制构建证明。新增产品模块改变implementation hash；C4使用代码选定3750954固定Git闭包、C2C2/C3各用原固定reader，不刷新历史pins。

## 观察与拒绝合同

分别记录identity/source、transport、protocol、provider-declared error、adapter/native、admission/domain、accounting。实际request/raw/adapter/native摘要及attempt/operation/stream/seat互相绑定，错attempt、字节或身份冲突必须拒绝；历史原attempt精确绑定受认证归档。

结构化error与adapter error相符可标provider_error_observed；优先报告证据损坏/矛盾，其后才是HTTP/deadline/provider声明/不完整。并存signals全部保留。HTTP200和transport error=null不是成功；error.message不参与分类、不公开。type/code只公开有限允许值；未知标签表示unclassified，不原样复制。默认adapter零usage不是可信raw用量。保留原账本状态和已核验usage，诊断不结算；账单始终UNVERIFIED。

原始bytes<=262144，adapter<=1048576；最多1024帧，每帧最多8条data、65536字节；JSON深度<=32，每对象<=128字段，集合<=4096、字符串<=1048576、总节点<=50000；受控单元输入<=16MiB、诊断包<=64MiB。拒绝重复key、非有限值、无效base64/UTF8、未知schema及超限。LF/CRLF等价；bare CR明确不支持。有限multiline data按SSE换行组合后严格JSON；comment和空帧计数，绝不当error。提供合成分段UTF8向量；runtime只宣称实际记录的全bytes一致性，不捏造网络分段观察。

error后成功finish/DONE、重复terminal、末尾追加、raw/adapter/native冲突明确拒绝或contradictory；缺native明确缺口。content前缀错误不成为action。禁止补DONE/usage、删除error帧、提取reasoning或message关键词归因。

## 正式本机矩阵（顺序与上限）

| 顺序 | 场景 | 最大发送 |
|---|---|---:|
| 1 | scheduling正常text A→B | 2 |
| 2 | bargaining正常text+reasoning A→B | 2 |
| 3 | C4结构替身：普通chunk、两个error、无DONE/usage | 1 |
| 4 | 只有data.error、无event字段 | 1 |
| 5 | content前缀后error | 1 |
| 6 | A成功、B结构化error | 2 |
| 7 | HTTP429有限错误body | 1 |
| 8 | HTTP503有限错误body | 1 |
| 9 | 无error对象的中途截断 | 1 |

正式矩阵9场景、最多12次loopback发送，不新增超时长测；总允许上限16，未列明的余量不自动使用。场景错误停止本场景并保留A/B完整slots，套件按预定顺序进入独立下一fixture。真实官方adapter/native实测与人工纯解析向量分列。ready30/RPC5/headers60/idle60/total90/result115/drain5/close5/Worker165及原起算点不变，SDK/fetch无重试。正式矩阵前提交源码/fixture/expected/hash封存；开发与失败运行独立计数、保留。

## 证据与扫描

先落盘原attempt/Ledger/raw/native库存、停止位置和未运行slots，try/finally结束Worker与服务，再观察/导出/扫描。生成日志、DB、native全部扫描；依赖缓存按可信只读内容清单单独核对，不重复扫描相同依赖副本、不将未知新增文件归为缓存。记录进度及实际文件清单，扫描未完成为INCOMPLETE，不重跑模型路径。当前阶段不宣称controller完整恢复；C4缺join收据不改。

控制包可重算实际runtime观察；公开portable仅含合成输入/预期/可重算观察和脱敏历史/runtime摘要。可移址verify验证合成逻辑和内部一致性，不冒充C4原始来源认证。固定历史reader由外层review harness启动，内部guard禁止key/env/network/process/runtime/write。新plan/analyze/verify也实跑此guard；run/export只写指定新目录且拒绝覆盖。

## 只读未来调度

固定seed20261014，各family的4组确定性shuffle，配成4块。每组2world×2presentation×2arm完整8episodes；每块两个family按candidate pair交错，共16episodes/32slots。world依字典序、presentation normal→reversed；组内两臂先后交替，每family共8对baseline-first/8对candidate-first。封存全部64/128及三类各32关系、0..64理想成功前缀曲线。每块完成各新增8对；旧16前缀8/0/0、首次hidden17/presentation21原样保留。不执行、不创建evaluation/claim，不以C4得失筛卡。

## Gate与交付

historical_source_authentication、failure_observation_integrity、success_admission_unchanged、accounting_nonfabrication、runtime_fault_matrix、stop_evidence_and_cleanup、offline_portability、future_schedule_integrity、publication分别报告。若缺受控raw，历史Gate BLOCKED/public_projection_only；不得伪称完整认证。诊断工程PASS不改变provider_availability=NOT_RETESTED、C4 INCOMPLETE、研究UNESTABLISHED、activation=false、费用/上游身份UNVERIFIED、binary_source_mapping=unproven、full_controller_recovery=unsupported。

完成后普通推送任务分支与main并独立核对SHA。失败/修复时序、正式冻结、实际argv和产品/工具来源各自绑定。停止于C2C5，不执行未来live计划。
