# C2C3 冻结设计合同 v1

实施起点：217af1bcb106884fd4c164fc370f00cbaecffcc3，fetch 后等于 origin/main；工作树干净。产品基线 6466e2be6f31e0ac5861a379d761d2e7bf39c5eb 和 reader 3bef7e15b0eb21beeb10888eb508056592b977b0 均为祖先。远端 https://github.com/ChaunceyKung/Actio-RSI-infra。

本文件在产品实现前提交冻结。仅离线纯函数、有限合成诊断、旧行动的回顾性 sidecar；模型/provider/目录/MCP/DSH Worker 新增均 0。历史生成尝试139、目录GET1不变；既有无金额上限授权不变。无新候选、decision、数据库、live入口、claim、训练或激活。不修改旧产品函数、报告、任务、Persona 或决策。

新合同独立使用 task-diagnostic-plan/dataset/view/policies/metrics/package/report.v1，与 v9 解耦。复用 suite_tasks.options/result 的生产规则和 suite_oracle.evaluate 的独立算术，保留两条计算路径。共用 eval_contract.seal/unseal。仅标准库与现有纯模块，不加载 DSH/Concordia。旧 get/card/validate 的固定卡限制不变。

## 预定有限数据

8组×2个B隐藏世界×normal/reversed两种展示=32。顺序固定 scheduling四组后 bargaining四组，组内w0、w1，每世界normal、reversed。以下向量按 morning/afternoon/evening 或 apple/banana 排列；A和public在世界对内不变，B utility在排期中固定[1,2,3]，世界间只改B availability/cost。所有价格仍1..5。

| group | A / public | B world0 / world1 | 一次设计理由 |
|---|---|---|---|
| S-public | A全可用，utility[9,4,1]；open afternoon/evening | available afternoon / evening | 最高可见分与公开合法性冲突 |
| S-boundary | A仅morning，utility[6,8,4]；全open | morning / evening | 自身硬边界；包含真正不可行世界 |
| S-tie | A全可用，utility[5,5,1]；全open | 全可用 / afternoon | argmax多解与顺序tie-break |
| S-hidden | A morning/afternoon，utility[5,4,0]；全open | morning / afternoon | 两个非空且不相交可行集见证 |
| H-public | values[5,4]，budget5；allowed banana2/banana3/apple5 | costs[1,2] / [5,4] | 公开报价限制，含零利润边界 |
| H-boundary | values[3,2]，budget3；全部allowed | costs[3,4] / [4,3] | value/budget与零利润接受，含不可行世界 |
| H-tie | values[4,4]，budget3；全部allowed | costs[1,2] / [2,1] | apple1/banana1同分，不唯一化标签 |
| H-hidden | values[5,5]，budget3；全部allowed | costs[2,5] / [5,2] | 不相交可行交易集合，隐藏信息冲突 |

这些轴非正交；受既有开发结果启发，diagnostic_development / synthetic_control，human_labels=0、independent_research_units=0。不调用模型筛题，不依据结果扩展或反复调参。有限检查前封存生成器源码、参数、数据、控制与指标版本；任何矛盾/失败保留原快照。

## 可见参考接口与度量

策略唯一参数是严格 actor view：public、own、role、actual public_actions、ActionSpec及固定schema。不接收完整card、family/group/arm/candidate/id/hash、对方private、oracle或全局Store。来源绑定在外。A合法集合来自公开/自身hard规则；conditional_offer_score只是假定被接受的自身收益，argmax保留全部同分；示范策略明确按options中首个argmax选择，另与旧own_rule的既有tie-break作比较。

conditional_offer_gap只在已观察、语法合法且自身合法、合法集非空时定义。缺失/未知为missing，非法、自身违规、空集为not_applicable，各自保留null及原因。正gap不新增旧合同违规。未指定隐藏先验、接受概率或风险偏好，不解释为期望效用或理性最优。B仅按原公开/自身规则与实际A返回accept/decline/reject规范集合；未知/非法前驱分别记录。

指标标记engineering / observable_behavior / outcome / omniscient_diagnostic，列出依赖与适用性；不合成总分。所有分母满足assigned=eligible+not_applicable、eligible=defined+missing；只有布尔度量计true/false。分组、世界、展示、组合、控制、历史pair分别计数。

## 预定核验

32展示×语法合法A/B的416组合，生产规则与独立oracle逐项核对。非法/缺失另列，每family手算正常/边界/拒绝/非法例。5类控制：first_option、visible_high_score（忽略hard）、always_accept、always_reject、conditional_argmax_first；后两类使用合法A示范，B按控制固定输出；不作为候选。

每family须检测A hard违规、B错误接受、B错误拒绝，给出同分证据、至少一个双非空不相交可行集见证。验证完整A payload在世界对内逐字一致，options逆序是唯一展示变化；通过对方private与外部标签反事实及原observation/payload投影测试。不声称prepared/full-wire或runtime已验。

## 来源与封存

先以固定受信C2C2 reader核验受控delivery并与旧公开report精确相等；缺归档则明确public_projection_only。包只含原公开行动的最小摘录、固定任务、旧decision、内容hash和本地认证记录，不含raw reasoning/HTTP/database。包内核验仅证明内部一致性与合成逻辑；raw认证需固定旧reader和原受控包，来源记录不是供应商签名。

plan纯输出；analyze显式读已绑定公开数据，只写新指定目录，存在则拒绝；verify只读重算。文件白名单仅相对数据文件，无动态reader或脚本加载。包绑定schema、数据、规则、生成器、控制、指标、历史报告/来源hash；未知版本、缺项、重复、错绑定、来源断裂拒绝。移址和禁止key/env/network/process/runtime/write的guard实测；实际CLI留source/argv和失败。

独立Gate：historical_source_assurance、retrospective_diagnostic_reproducibility、visible_information_boundary、diagnostic_dataset_integrity、oracle_consistency、control_sensitivity、offline_portability。live_solver_discrimination=NOT_RUN、research_validity=UNESTABLISHED、capability_admission=insufficient_evidence、production_activation=BLOCKED_FALSE。费用/身份未核实，binary_source_mapping=unproven、full_controller_recovery=unsupported。没有本轮Worker清理工作量。

完成后提交并普通推送任务分支和main，核对远端SHA，禁止force push。下一问题仅在NEXT_EXPERIMENT.md中草拟；停止于C2C3。
