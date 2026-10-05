# 14 · 未决问题与风险门槛

高风险不等于必须停止本次规划；以下都绑定最小验证与降级。阻塞指后续功能admission，非阻塞文档交付。

| ID / Question | Why | 当前假设 | 所需证据 / 最小实验 | 级别 / owner / 出口 |
|---|---|---|---|---|
| Q01 SDK可否小补丁完整暴露生命周期？ | 单runtime恢复关键路径 | 内部seam可在原transport暴露 | 真实wheel运行cancel/resume/fork/catchup，记录native seq/receipt，5日探针 | P0/I/B03；超界换Strands |
| Q02 事件通知与native durable flush何时一致？ | crash可能ACK后事实丢失 | 需要显式flush/cursor确认 | 在接受prompt、tool完成、journal flush、canonical commit各点终止，比较合法前缀 | P0/I/B05；不完整时禁止resume |
| Q03 worker配置隔离与背压实际成本？ | 10–100人口不宜默认一进程一人 | 同配置顺序复用可行但未证 | 双人格并发/顺序污染探针，queue压力/RSS/latency测量 | P0/I/B03/B14；限制活跃池 |
| Q04 Concordia external Entity与checkpoint缺口能否补齐？ | prefab跳过外部实体且无engine cursor | 起点重执行足够MVP | 小场景observe/act/GM日志映射；capture比对engine/GM/agent清单 | P0 social，P1 branch/E/B07/B12；mid-run false |
| Q05 社会评分是否有效且可配对？ | judge顺序/偏差、agent干扰 | 约束指标+LLM rubric+人工校准 | 盲审样本、身份映射错误/[]探针，cluster pilot方差与power | P0/R/B09；不稳定则只报exploratory |
| Q06 Raven退役后谁维护拆取模块？ | 原tree planned retirement | 小闭包可独立维护 | C02/C03真实LOC/import闭包、测试移植、patch责任人 | P0/E/B10/B11；移除selector或标准统计诊断 |
| Q07 Windows sandbox够不够L2？ | partial enforcement不能保护宿主 | 不够默认要求；首期不运行候选代码 | Linux隔离能力/资源/文件/网络验证，scope含依赖与工具 | P2 blocker/I/B17；保持L1 |
| Q08 Viewer社区部署/商业边界？ | ELv2、EE、ClickHouse等运维 | Langfuse社区可用但要闭包审 | exact deployment依赖/目录license审阅，最小OTLP+score压测 | P1/I/B13；延迟viewer/内部Phoenix |
| Q09 Graphiti有净收益吗？ | 抽取/embedding成本、scope可省 | 关系复杂后有收益 | 同样M3数据对SQL/graph检索准确率时延成本，跨branch UUID隔离 | P2/E/B16；不启用graph |
| Q10 MCP modern/legacy/auth/resources兼容？ | spec与SDK/wrapper覆盖不同 | stdio只读最可控 | modern与legacy server工具fixture，schema/isError/取消；HTTP OAuth另探针 | P0 tool/I/B08；不支持能力显式拒绝 |
| Q11 unknown外部写效果怎么确认？ | timeout≠失败，exactly-once不可保证 | 首期只读，写必须receipt/reconcile | 幂等写回执丢失，目标查询确认，拒绝盲重试 | P0扩展写工具/I/B08；无查询seam标needs_reconcile |
| Q12 1K人口的活跃池/存储性能？ | 人口/并发混淆会夸大容量 | 批调度可扩，未测 | B14实测100人口后估1K，指标含数据库写延迟/队列/RSS | P2/I；不宣传已支持1K |
| Q13 论文/博客是否有新官方代码？ | 访问失败/abs未链接不是不存在 | 当前仅D | 后续采用前从作者官方索引重新核验repo/license/artifact | 可延后/R；不作为MVP依赖 |
| Q14 训练数据/Persona/模型artifact的再使用权？ | 根代码许可不覆盖数据/模型 | synthetic+授权API满足首期 | asset admission登记来源/条款/用途；导出dataset再审 | P0涉及该数据/R/B01；无授权不纳入 |

三项最大交付风险：DSH生命周期与平台闭包（Q01–03）；跨runtime/world/tool一致性（Q02/Q04/Q11）；评价有效性与选择偏差（Q05）。许可/维护/资源风险已分配gate；本轮没有付费调用、GPU训练或真实服务部署以“验证”未知项。
