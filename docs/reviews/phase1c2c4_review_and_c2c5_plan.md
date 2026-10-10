# C2C4 审阅与 C2C5 流错误诊断方案

审阅日期：2026-10-10（Asia/Shanghai）。基线：`70fce468a229d82f7de1f697b2619a95f8503f4b`；冻结 reader：`3750954ea7cc8dff64115039e27bb671fa618d01`。本轮实际 `ls-remote` 核对 main 与 `phase1c2c4-visible-rule-robustness` 均为该最终提交。

**维持 C2C4 的 INCOMPLETE / infrastructure_failure；下一步建议 C2C5：供应商流错误诊断与本机故障验收，新增真实调用为 0。** 停止是正确执行冻结合同的结果。现有证据表明收到明确错误对象，不能通过允许 `event:` 行把它变成成功答案。先把失败分类、来源绑定、停止交付做成可运行能力，再讨论新一轮真实试验。

[完整 Codex Prompt](../prompts/phase1c2c5_stream_failure_diagnostics.md) · [本轮审阅证据](phase1c2c4_review_evidence.json) · [原 RESULTS](../validation/phase1c2c4/RESULTS.md)。本轮只审阅与规划，未实施 C2C5；下一 session 实施本机诊断，不续跑 C2C4。既有无金额上限授权继续有效，零调用是本阶段范围选择。

## 1. 本轮实际复核

| 范围 | 结果 | 限制 |
|---|---|---|
| 发布与版本 | 44 artifacts、77 产品文件、10 工具文件、2 入口文档匹配固定 Git 内容；安装的 77 文件匹配 | 冻结至交付的产品、tests、scripts 未变；本次只读检查 |
| 完整 delivery | 在禁止 key/env/network/process/runtime import/write 的 guard 下实际重算，report 与公开投影精确相等 | 依赖本机受控原始材料；公开 report 本身不是 raw 认证 |
| 权威谱系 | 原 v4 库只读导出等于完整 delivery；3 evaluations / 2 evaluation decisions / 原6 decisions；文件 hash 前后一致 | 未迁移、未写新 decision |
| claim | 19 个已登记文件与发布 hash 相同 | 保留永久资格消耗，不把停止解释为可重领 |
| 已发布验收 | 10 项通过记录均绑定当前产品；完整 rehearsal 与最终10条CLI收据产品绑定一致 | 一些记录的 tests/启动脚本属于早期快照，不称所有测试工具均为最终快照；后续手算/隐藏世界fixture和Git路径修正有独立记录 |
| 本轮重跑 | 4 项现有纯测试通过：调度/任务准入、独立穷举真值、指标缺失分母、双通道 fail-closed | 没有重跑完整64/128 rehearsal，没有启动 Worker |
| 清理 | 核对已发布清理清单与一项缺 join 收据的历史中断记录 | 本轮未重新查询全部306个Job的操作系统状态；不把历史清理计成本轮工作量 |

实际计数获得支持：33 sent/response，32 usage/admitted，unknown=1，not_run=95；16/64 episodes 技术完整，8/32 候选配对完整；隐藏世界、展示对照均0/32完整。失败位于 ep-16 / baseline / S-hidden-w0-reversed / A。累计真实生成尝试仍172，历史目录GET1另计；本轮新增模型、目录请求、Worker均0。

## 2. C5R1：明确的错误流，不是仅有一个未知 SSE 字段

从已核验的原始响应中，只提取结构与允许公开的错误标识，不公开 error.message 或 reasoning 正文：

| 层次 | 实际观察 |
|---|---|
| HTTP / transport | HTTP200；capture 的 response.error 为 null，仅表示该字段没有传输异常 |
| 第一帧 | 普通 chat.completion.chunk，单 choice |
| 第二帧 | data 对象只有 error，type=`api_error` |
| 第三帧 | `event: error`，error.type=`upstream_error`，code=`upstream_stream_truncated` |
| 协议结束 | 无 `[DONE]`，无原始 usage；raw_base64 与文本一致 |
| 官方适配层 | usage 的 input/output/total 全0；finish.kind=`error`，failure.code=`PI_AI_ERROR`；没有可认证行动 |
| 旧审计与账本 | text_integrity=unsupported_protocol/channel；账本原因 gateway missing/extra DONE；usage=null、unknown |

`upstream_stream_truncated` 是中转返回的错误标签，不能独立证明具体上游、供应商责任、是否暂时故障或真实计费。官方适配层输出的零 usage 也不是供应商“零消耗”的证明。识别错误种类与证明实际账单是两件事。

本轮另做了纯内存反事实：只移除 `event:` 行并同步 bytes 投影，旧 reader 仍以 `incomplete_stream / missing/duplicate/nonfinal DONE` 拒绝。未改任何原文件。不能去掉 error、补 `[DONE]`、捏造 usage、取前缀行动或从 reasoning 提取答案来提升准入。

本地 DSH 参考源码 [stream.ts](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/llm/llm-pi-ai/src/stream.ts) 在 checkout `5badb15009ae1756c3afe0ae0cef1faafc290ccc` 中，将 pi-ai error 事件转换成 usage 和 error finish，与观测形态一致。但源码参考和已安装发行物的对应构建未证实，`binary_source_mapping=unproven` 保留；下一阶段应依靠固定实际 runtime 的本机响应注入证明行为。

## 3. C5R2：需要独立的失败观察，不应放宽成功准入

[`channel_audit.py`](../../src/actio/channel_audit.py) 是成功文本的一致性审计，遇到未知 SSE 字段即拒绝；[`candidate_measurement.classify`](../../src/actio/candidate_measurement.py) 目前主要继承该分类，不能充分展示“中转明确报错、适配层 error、缺 usage、缺 DONE”同时存在的事实。`response.error is None`、HTTP200、出现 usage chunk 均不足以证明成功。

新增只读、版本化失败观察层，绑定 config/attempt/实际发送/response/raw/adapter/native/旧verdict；同时保留传输、协议、供应商声明、原生终态、行动准入和账务状态。不只取单一优先级覆盖其他信号，不依据英文 message 中的 timeout/rate 等关键词断言原因或解锁重试。

它应明确区分：错误结构可以完整验证，成功行动仍不可准入；错误类型可观测，账务仍unknown；usage可观测与供应商账单核对不同。旧C2C4报告、unknown、claims、decision和来源hash不变，只生成新的回顾性sidecar。不新增candidate evaluation，不迁移旧库，不宣布provider故障已修复。

## 4. C5R3：原顺序推迟了另两类对照的完成

本轮仅从冻结 units 重算理想成功前缀，不依赖模型输出或删选卡片：

| 顺序前缀 | 候选配对 | 隐藏世界对照 | 展示对照 |
|---|---:|---:|---:|
| 前16个episode全部完成 | 8 | 0 | 0 |
| 首次出现一个完整对照所需episode数 | 2 | 17 | 21 |
| 全64个episode全部完成 | 32 | 32 | 32 |

这不是C2C4违反合同：原计划只保证同展示的两臂相邻和family交错，没有保证另外两类对照较早完成。技术停止使这个取舍变得明显。已有失败和完整分母不能回写成更有利的顺序。

建议 C2C5 同时生成一个**仅规划、不执行**的分块顺序：每个结构组完整包含2世界×2展示×2臂=8 episodes；两个family各选一组构成16-episode块，块内按同展示两臂配对交错family。每完整块可完成三类对照各8个，全计划仍64/128、各32对。固定新调度seed、完整顺序和0..64前缀覆盖曲线，与旧计划并列。分组顺序不依据C4的胜负、实际行动或错误卡筛选，也不承诺对任意短前缀都占优。

该顺序可能减少停止时对照孤立的情况，不修复provider、不保证独立样本，也不识别稳定顺序效应。未来若进行新live，需要新版本、完整预注册、新evaluation/claim并保留C4历史；不是继续旧95个not_run或给旧数据补样。

## 5. 两个非零差值的边界

H-tie-w1-reversed：B0选apple1被拒，C1选banana1获接受，joint delta=+1。S-tie-w1-normal：B0选afternoon获接受，C1选morning被拒，joint delta=−1。两者都是A合法条件argmax集合内的同分选择，已认证的原format/hard/B响应规则均满足。

这些说明目前能观察到行动与结果差异；一正一负不能作为C1获益或损害的稳定结论，条件得分gap=0也不是期望效用最优证明。没有隐藏先验、接受概率和独立样本，不作排名、总分、显著性或晋升；24个未完成候选对保持missing。

## 6. 推荐的下一阶段及完成定义

C2C5交付可运行的失败诊断CLI、保留多层信号的严格合同、经过固定官方DSH链路的有限loopback故障矩阵、可移植合成证据包及独立核验器。重放C4错误只用受控归档或经结构保持的合成替身，不能把原错误报文直接公开。覆盖A报错不启动B、B报错不产生最终世界结果、有效前缀后报错不准入、错误时adapter零usage不当可信消耗、停止后无重试及完整后缀。

正常成功流的旧准入不放宽；未知/损坏/矛盾结构仍拒绝或明确未分类。新观察层可识别 `event: error` 和 data.error，但不成为新的成功解析器。离线plan/analyze/verify拒绝key/env/network/runtime/write；本机run只允许literal loopback和假凭据。无需重新运行64/128正常主矩阵，采用明确的有限故障场景和成功对照。

补齐失败后的最小证据保存与清理收据顺序：先保存attempt/账本/停止库存，再扫描导出；扫描失败不能销毁已保存证据，也不能记整包PASS。不以删除期限或跳过敏感材料扫描作为完成方式。既有一次缺join记录保留，本阶段只验证新本机运行的清理，不宣称完整controller恢复。

C5本机工程PASS只证明失败诊断与停止交付可以复核；provider可用性仍NOT_RETESTED，账务与上游身份未核实，研究UNESTABLISHED、activation=false。未来live仅在独立合同中讨论，不因本机识别了错误自动重启128次campaign。原无金额上限授权保留，无需为同一费用许可重复询问。

本轮更新README下一步入口，保留整体介绍和里程碑历史；不把规划记为完成里程碑。文档验证后普通提交并推送main，核对远端SHA。下一session的Prompt也明确要求完成验证后推送任务分支及main。
