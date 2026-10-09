# C2C4 草案：先测试可见规则鲁棒性

本文件是可审阅草案，不是已注册执行资格；本轮不执行live、不新建claim、不自动续跑。既有费用授权继续有效，不重复征求同一许可。下一session先确定合同与新数据的runtime准入，再决定执行。

## 选择理由

C2C3已证明有限度量能检测A公开/自身违规、B错误接受和错误拒绝；对真实solver及B0/C1的区分能力仍NOT_RUN。现有条件得分不含接受概率，隐藏世界又有不相交可行集，直接把联合失败转为“策略差”没有已定义目标。因此先检验同一信息结构下的可见规则鲁棒性；公开沟通、信息获取和期望效用目标留作独立合同，不同时修改信息结构与候选。

## 一个有限问题

在保留两步A→B、私有边界和原规则的情况下，原B0/C1在预先固定的公开限制、自身边界、同分和选项逆序任务上，是否出现可信格式/自身hard/B响应违规或顺序依赖？只作描述性工程观测，不要求出现正差值，不据结果改题、换route或反复补样。

参照仍是B0 `84e9ab99465ada9c47cc17334c305a5f493524f042a218d4be4732c054462fe5`，候选仍是C1 `e381eb3dd58494dde035b7c301331bdc3f5cde8af18c644bf6e7301087a130b2`。不创建C2，唯一直接arm干预仍为A那三个词条。改变的是任务的公开/自身/隐藏数值与options展示；任务信息结构、Persona、模型参数、B规则和候选内容不改。任何效果仅针对这个新开发集，不回写旧C1结论。

## 计划上限与单位

建议固定本次32展示 × B0/C1 × 单route gpt-5.6 × 1repeat =64 episodes、最多128个seat发送。每个seat一次，无隐式重试。8个结构组、16世界、32展示、64episodes、128seats分别记账；隐藏镜像与顺序逆转不是独立研究单位，independent_research_units仍0。若未来要研究有效性，另设计真正独立任务族和预注册分割，不把这个开发集改名held-out。

拟使用seed20261013交错family、world、presentation和arm，组内baseline-first/candidate-first平衡；实际完整有序计划必须首次live前枚举封存。沿用max_tokens=512、未指定temperature/provider sampling seed、原期限和显式阶段uncapped。调度seed不抵消供应商随机性或时间漂移。历史139和目录GET1不入新分母，累计只按实际发送增加。

## 执行前证据与失败条件

1. 新任务/live版本与旧v9解耦，旧12卡和旧claim保持限制；不能直接把诊断卡塞进旧execute。
2. 新版实际DSH/Concordia本机接线，证明A唯一干预、B实际A历史、prepared/full-wire私有反事实和显式options变换；C2C3的纯payload检查不能替代。
3. 每metric适用性/缺失/分母、同分集合、正gap不等于违规、依法拒绝、技术unknown分类及独立oracle再绑定新任务版本。
4. 新evaluation引用原不可变B0/C1，保留所有旧决定；实现、有限计划及政策普通push两个分支/main并核对SHA后才能live。
5. 静态或接线不通过则NO_GO；首个技术unknown/timeout/文本或协议身份冲突停止，后缀not_run，无补样/诊断调用。可信行为错误保留并依合同继续。
6. 零已观察约束gate可判development reject；其余技术完整仍insufficient_evidence。无capability pass/激活路径，不能由合成控制的敏感性代替solver证据。

保留原始通道、账本、一次资格、逐seat逐metric、完整suffix和清理，费用币种与上游身份继续按未核实报告。完成验证后提交并普通推送任务分支和main、核对两端SHA；无分叉快进，有并发先整合验证，不force push，不覆盖无关修改。
