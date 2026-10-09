# C2C3 结果

已交付纯离线 `actio.task_diagnostics plan/analyze/verify`、C2C2 回顾性 sidecar 和可移植诊断包。七项范围内的工程 Gate 通过；真实模型判别力尚未运行，研究有效性未建立，C1 原决策仍为 `insufficient_evidence`，activation=false。本轮不写候选准入决定。

## 回顾性重算

先用受信 reader `3bef7e15b0eb21beeb10888eb508056592b977b0` 在拒绝 key/env/network/process/runtime import/write 的 guard 下核验原受控 delivery，结果与原公开 report 精确相等。[认证记录](historical-source.json) 只记录本机核验，不是供应商签名。随后从固定 hash 的公开报告提取行动，不读取 reasoning 来解释行为。

| 观察 | 重算结果 |
|---|---|
| 两臂 A/B 行动逐字相同 | 12/12 pairs |
| A 在自身合法条件得分 argmax 集合 | 12/12 cards |
| 与旧 own_rule 具体行动字符串相同 | 11/12；H5 的 apple1/banana1 同分 |
| 联合可行／实际达成 | 10/12／5/12 |
| 可行未达成 | S1、S3、H1、H3、H4 |
| 全知 regret 为正 | S1、S3、S6、H1、H3 |

[逐卡两臂诊断](package/retrospective.json) 保留任务、报告、reader/source hash，format、自身约束、B规则、joint、效用、全知上界/regret和原decision。[公开行动摘录](package/historical-actions.json) 不含 raw reasoning、HTTP或数据库。原 report、manifest、lineage、decision、claim 均未修改。

C1三个词条分别与基础 Persona 中“公开/自身硬约束”“自身上下文和实际公开行动”“精确返回选项”重合；ActionSpec也要求精确选项与hard rules。[逐项对照](package/overlap.json) 是文本内容对照。两臂本轮零违规只说明这些约束指标的观测上限，不证明重复提示必然无效、模型等效或假响应。

## 有限合成诊断

| 层次 | 数量／范围 |
|---|---|
| family / structure group | 2 / 8 |
| hidden world | 16；每组2个仅B私有条件不同的世界 |
| presentation | 32；每世界normal/reversed，仅options顺序改变 |
| 合法A/B组合 | 416 = 16×3×2 + 16×10×2 |
| 非法／缺失向量 | 128，单列 |
| synthetic policy controls | 160 = 32×5；不是候选、真实episode或独立研究N |
| 手算样例 | 10；两family正常、边界、拒绝、非法 |
| 对方private／外部标签反事实 | 64个actor视图与生产payload对照 |
| 顺序变换 | 16个world，显式选项索引映射，完整语义真值不变 |

数据 hash：`3e37ca1cb71a90f3bef100a1ec4bff4721d584c19c3442ae04de42207630a02a`。规则、有限参数和排序见[设计合同](CONTRACT.md)与[数据](package/dataset.json)。全部416合法组合及128额外向量的生产规则/独立oracle一致，可见策略的自身规则判断也逐项一致。完整真值、控制、分母、分组和变换在[合成报告](package/synthetic-report.json)。

| family | A hard违规控制输出 | B错误接受 | B错误拒绝 |
|---|---:|---:|---:|
| scheduling | 14 | 12 | 12 |
| bargaining | 14 | 19 | 10 |

每family的分母为80个控制输出。控制在某卡正确时同样保留；这些计数仅说明诊断能区分预设行为。没有模型筛题、模型请求、live judge或C2候选。集合正确性与确定性示范的选项顺序tie-break分开。

## 可见信息见证与指标限制

S-hidden两世界A视图与生产payload逐字相同，可行集分别只有morning、afternoon。H-hidden对应可行集分别为apple报价2/3、banana报价2/3。两family均有两个非空且不相交的可行集；S-public另有afternoon/evening见证。它们证明不存在同一行动保证这些世界都达成，不提供自然成功率、先验或期望效用结论。

真正无可行交易世界和zero-profit接受边界已覆盖。conditional_offer_score仅指假设被接受的自身收益，gap>0不升级为旧合同违规；非法、unknown、空集合和不适用分别保留null/原因。合法拒绝与任意拒绝按原公开规则区分。所有度量分母保留assigned=eligible+not_applicable、eligible=defined+missing；仅布尔项出现true/false。

[指标依赖](package/metrics.json)区分engineering、observable_behavior、outcome、omniscient_diagnostic。原14项覆盖包括同源字段，不作为14种独立能力，不合成score。32展示是开发启发的synthetic_control，human_labels=0、independent_research_units=0。仅验证纯payload；prepared/full-wire/runtime须在后续接线时另验。

## 验收、来源与执行边界

7项纯测试通过，含原12卡合同回归、两条独立计算路径、可见策略禁用oracle、正gap/同分/空集合、移址、覆盖拒绝及10种坏包/文件拒绝。8条guard内CLI流程通过；另实跑最小安装及4条literal `-m`命令。最小环境仅标准库和14个固定文件，无pip/第三方包，无DSH/Concordia导入。源码与安装一致。

可移植包独立重算封装、受信公开摘录、合成逻辑和分母；包不依赖原实验盘符、现场DB或凭据。包中的固定reader认证是既往本机事实记录，verify返回`raw_authentication_repeated=false`，不能替代原受控材料的raw核验。无认证记录时analyze明确降级`public_projection_only`；不能将自封hash当供应商签名。

设计合同先提交于`bc645c1`，产品实现及正式验收前快照为`0a66334`。机器可读冻结前曾运行一次开发探针，数据和控制没有按其结果修改；因此不声称严格做到“首次有限计算前全部机器可读封存”。该顺序偏差、隔离导入失败、guard误拦公开引用失败及来源快照均在[开发记录](DEVELOPMENT.md)保留。正式验收使用封存数据和同一产品源码。这是过程限制，不改变真值检查结果。

本轮真实模型/provider/目录/MCP/DSH Worker均0；历史真实生成尝试保持139，目录GET1另计。既有TokenKey无金额上限授权未改变。本轮未创建受管Worker/Job、HTTP服务或监听端口；不把历史197个Job当成本轮工作量。原账本、unknown和once-only claim不动。

费用币种/单位/账单及上游权重身份未核实；binary_source_mapping=unproven、full_controller_recovery=unsupported。下一问题建议先验证可见规则在真实solver下的鲁棒性，具体有限草案见[NEXT_EXPERIMENT](NEXT_EXPERIMENT.md)，本轮不执行。

[Gate](GATES.md) · [CLI](CLI.md) · [交付manifest](evidence_manifest.json) · [可移植包manifest](package/manifest.json)。停止于C2C3。
