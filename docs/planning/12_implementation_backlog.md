# 12 · 后续实施 Backlog（本轮不执行）

Priority：P0阻断主链，P1主MVP可延后外观，P2扩展。Source E-ID指向[15](15_evidence_registry.md)的完整SHA/文件；任务开工必须锁该版本或重新审差异，不用浮动main。角色：I=infra工程师，E=环境/实验工程师，R=研究负责人。每个task输出可审查证据，不只写“能跑”。

| Task | Epic / Feature / 要做什么 | Dependency / Priority / owner | Reuse Source / Risk | Acceptance Criteria |
|---|---|---|---|---|
| B01 | Asset admission：SDK/runtime配对、许可证/NOTICE/SBOM、artifact hash、平台最小启动清单 | 无/P0/I | R01–R15；E001/E005/E024–E029/E042；EE/依赖再分发风险 | 每A/B/C有pin+许可范围+notices；不兼容项blocked；Windows/Linux artifact组合清晰；无模型/数据默认授权 |
| B02 | Contract freeze：对象schema、owner、caps、error、mutation allowlist、协议版本 | B01/P0/I+R | E001/E017–E020/E036；接口过度抽象 | [10](10_interface_specification.md)十合同有fixtures及兼容决策；同一状态只有一个writer；Genome禁改规则/权限 |
| B03 | DSH public lifecycle探针：官方wheel+SDK、双profile、cancel/resume/fork/catchup seam、queue上限 | B01/B02/P0/I | E001–E006；C01，alpha API/平台 | 5日出go/no-go；真实worker启停/model/tool无mock成功证明；receipt/seq可关联；未达则Strands探针，不新RPC |
| B04 | Canonical store：SQLite事务、artifacts、cursor去重、namespace、outbox、lease | B02/P0/I | E003/E029/E042；双写/缺seq | 相同event重复仅一条，不同hash冲突；kill在artifact/commit间不悬挂引用；viewer断开事实继续；旧epoch禁写 |
| B05 | Worker恢复与C01窄补丁：稳定receipt/status/catchup、quiescence、kill清理 | B03/B04/P0/I | E001–E005；SDK无界queue/原生锁 | 中途crash恢复或明确needs_reconcile；活旧worker不被TTL抢锁；重复prompt不重复工具；native/canonical gap可检测 |
| B06 | Mind/Memory：Persona来源、M0–M6、关系双时间、visibility、CAS/consolidation | B02/B04/P0/E | E012–E014/E021/E023；branch/test泄漏 | 主观belief不覆盖world；两个branch交叉读写拒绝；source chain完整；migration前后hash/rollback有证据 |
| B07 | Social slice：Concordia external Entity、ActionSpec、GM outcome/clock、起点manifest | B05/B06/P0/E | E017/E018；sync/async bridge、checkpoint skip | 至少2 agent真实GM裁决；非法action不改world；观察私有数据不泄漏；不自称mid-run完整checkpoint；同RuntimePort |
| B08 | Assistant slice：DSH MCP只读tool、效果账本、permission/deadline与协议兼容 | B05/B06/P0/I | E006/E026；旧/新MCP协商、unknown效果 | stdio discovery/legacy测试记录；tools schema/isError/取消分开；deny不调用；回执丢失不盲重试写；与B07共享contracts |
| B09 | Eval基础设施：冻结split/rubric、SOTOPIA wrapper、确定性约束、paired unit/power pilot | B02，集成需B07/B08/P0/R+E | E008/E010/E022；judge偏差/样本不足 | []/错identity/缺维度变invalid；pilot估N、Δ/CI/成本阈值事先seal；proposer不可访问holdout；报告invalid率 |
| B10 | 单seat Candidate/Admission + C02：四态、回归、统计计划、预算、权限隔离 | B09/P0/E+R | E008/E036；promoted误用/多重比较 | 违规mutation拒绝；n=1/零方差非自动pass；infra不混task0；search/test分离；无提升也完成演示 |
| B11 | Version/Lineage + C03 selector：多父、全部失败记录、activation CAS、rollback | B04/B10/P0/I | E009/E011/E037；best-effort archive丢记录 | candidate无论结果均可追溯；archive损坏不空表成功；晋升和banking分离；旧run保留pin，新run切版本 |
| B12 | Replay/branch/intervention：manifest、I/O匹配、起点分支、配对干预报告 | B07/B08/B11/P1/E+R | E002/E018–E020/E029/E033；不完整快照 | partial manifest拒绝resume/branch声明；改变输入不复用旧响应；cluster CI与confounds明确，输出受控差异而非泛化因果 |
| B13 | Viewer：Langfuse社区部署探针、OTLP exporter pin、dataset/score投影、脱敏 | B01/B04/P1/I | E024/E025/E029/E042；EE/资源/queue丢失 | 列服务RSS/磁盘与LICENSE例外；OTLP畸形批次/重试/背压实测；viewer重建不改canonical；内部Phoenix备选合法 |
| B14 | Reliability/capacity：100人口、4–8活跃受限池、预算与故障矩阵 | B05/B07/B08/B11；B12/P1/I+E | E003/E005/E019；子进程泄漏/磁盘耗尽 | 记录吞吐/P95/RSS/latency/cost而非承诺值；loss/duplicate/gap测试；工具unknown、满磁盘、取消、旧lease、Unicode路径均有结果 |
| B15 | 第二环境：AgentSociety batch/Ray proxy与OASIS ManualAction兼容 | B12/B14/P2/E | E019/E020；failed tick非原子 | partial batch失败不提前推进clock；恢复pending映射；Manual interview模型成本显式；同EnvironmentPort无新增world owner |
| B16 | Graphiti可选投影：group/UUID scope、防泄漏、删除传播、ROI | B06/B14/P2/E | E021；抽取成本/branch串读 | 预注册检索集对比SQL质量/latency/cost；namespace强制且UUID查owner；无收益不启用 |
| B17 | L2/L3及远端接口：隔离准入、external training contract、A2A/ACP重评 | B10/B14/P2/I+R | E010/E011/E027/E028/E030–E041 | L2隔离未证实则blocked；训练只接dataset/evidence/job/artifact+独立eval，不引GPU栈到control |

任务分解建议：每个B先产contract fixture/失败用例设计，再最小实现，再验证报告。已有上游测试按C拆解包保留；不写只镜像实现而无行为价值的测试。B03/B09是最高不确定性，不能后移到全部功能完成后。artifact admission若失败不再扩大同类调研，按R矩阵退出。
