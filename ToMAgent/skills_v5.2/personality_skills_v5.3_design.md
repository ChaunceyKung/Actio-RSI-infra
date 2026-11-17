# skills_v5.2 人格 Skills 设计文档

## 1. 设计目标

在 `skills_v5.1` 的社会心智框架上，新增一个“人格与个体差异层”，用于建模稳定的行为倾向、表达风格和互动偏好。该层的目标不是替代既有的 `belief / desire / emotion / pragmatics / norm / relationship` skills，而是在这些变量仍然不足以唯一决定答案时，提供一个可解释、可控、可评测的先验调制项。

换句话说，`人格 skills` 解决的不是“他知道什么”，而是“在相同心理状态和情境约束下，这种人更可能怎么想、怎么说、怎么做”。

## 2. 为什么需要人格层

`skills_v5.1` 已经覆盖了社会心智的主干链条，但实际题目中仍存在一类问题：

1. 显式线索不足，多个答案都“说得通”。
2. 角色行为受稳定风格影响，而不仅是当前信念或目标。
3. 同样的礼貌、拒绝、协商、情绪表达，会因人格差异而不同。
4. 真实 benchmark 中，许多题的关键不是纯粹 ToM，而是“人格化的社会推断”。

前期验证也说明，人格 skills 对 ToMBench 一类任务有小幅增益。这意味着人格层更适合作为 **tie-break prior**，而不是主推理层。

## 3. 设计原则

### 3.1 人格是先验，不是主因

人格层只在以下情况介入：

- 现有 v5.1 skills 已经得到多个候选解释；
- 题目明确要求“通常”“更像”“一贯”“风格上”这类稳定倾向；
- 角色历史行为能支持某种稳定特质；
- 需要预测表达方式、互动策略或情绪阈值。

如果文本中已经有明确 belief、goal、emotion 或 norm 证据，则优先使用既有 skill；人格不能推翻显式证据。

### 3.2 人格必须与状态分离

人格只表示稳定倾向，不表示临时状态。必须严格区分：

- trait vs state
- persona vs disposition
- role requirement vs private tendency
- social mask vs internal style

### 3.3 人格只做任务相关建模

不建议直接把人格设计成完整心理测量学标签库。对 skills 来说，更有用的是任务相关人格维度，例如：

- 冲突回避 / 直接表达
- 谨慎 / 冒险
- 合作 / 自利
- 情绪反应强 / 弱
- 主导 / 退让
- 印象管理强 / 弱

### 3.4 人格不应过拟合单句线索

人格判断需要累积证据。单句礼貌、一次沉默、一个玩笑，都不足以推出稳定人格。优先使用：

- 多次行为重复
- 长期关系历史
- 叙事中的一致风格
- 明确的角色描述

## 4. 层级定位

建议在 `skills_v5.2` 中新增一个独立的 `P-layer` 或 `L8 人格与个体差异层`，位置高于当前 `L0-L7` 的具体推理层，作用方式是横向调制：

`文本证据 -> 当前心理状态 -> 人格先验 -> 行为/语言/情绪/关系预测`

它不是和 `L3 / L4 / L5 / L6` 并列的替代层，而是可调用的补充层。

## 5. 人格层的技能划分

### 5.1 Micro Skills（建议 8-10 个）

| ID | 名称 | 核心变量 | 何时使用 | 不要使用的情况 |
| --- | --- | --- | --- | --- |
| personality-01 | Trait Cue Aggregation | 从重复行为中提取稳定倾向 | 需要从多次行为归纳人格线索时 | 只有一次短暂行为时 |
| personality-02 | Trait-State Separation | 区分稳定特质与临时状态 | 情绪、压力、角色要求可能混淆时 | 题目只问当前状态时 |
| personality-03 | Trait Confidence Estimation | 该人格判断有多稳 | 线索稀少、需要控制过推断时 | 证据已经充分时 |
| personality-04 | Persona vs Disposition | 公共人设与真实倾向的差异 | 角色有社交包装或表演性表达时 | 没有人设/伪装线索时 |
| personality-05 | Conflict Style | 冲突回避、直接、折中、压制 | 协商、拒绝、反馈、冒犯场景 | 题目不涉及互动风格时 |
| personality-06 | Risk Preference | 谨慎、保守、冒险倾向 | 行动预测、选择偏好、试探场景 | 题目只需要事实判断时 |
| personality-07 | Cooperation Orientation | 合作 vs 自利倾向 | 资源分配、互惠、共同方案时 | 只有单方行动时 |
| personality-08 | Emotional Reactivity | 情绪阈值与反应强度 | hidden emotion、emotion regulation、冲突场景 | 不涉及情绪反应时 |
| personality-09 | Assertiveness / Dominance | 主导、退让、控制互动的倾向 | 上下级、协商、群体互动时 | 题目只问角色身份时 |
| personality-10 | Impression Management | 是否重视形象与社会评价 | 自我呈现、礼貌表达、白色谎言时 | 没有公开场合/评价压力时 |

### 5.2 Macro Skills（建议 4-5 个）

| ID | 名称 | 场景决策变量 | 对应微观展开 |
| --- | --- | --- | --- |
| personality-macro-01 | 人格驱动的歧义行动预测 | 当 belief / goal 相同但行动不唯一时，谁更可能这样做 | personality-02/05/06/07/09 |
| personality-macro-02 | 人格驱动的表达与语气选择 | 同样的信息，在不同人格下如何说出来 | personality-05/08/10 |
| personality-macro-03 | 人格驱动的情绪反应 | 同样事件下情绪更强还是更弱、内收还是外放 | personality-02/08 |
| personality-macro-04 | 人格驱动的协商与修复 | 冲突后更倾向回避、道歉、反击还是补救 | personality-05/07/09/10 |
| personality-macro-05 | 人格与人设不一致识别 | 公开表现和稳定倾向是否冲突 | personality-01/02/04/10 |

## 6. 与现有 v5.1 的接口关系

人格层不单独替代任何现有 skill，而是主要接到以下节点：

- `micro-23` 行动预测
- `micro-26` 基本情绪评价
- `micro-27` 非典型情绪
- `micro-28` 隐藏情绪
- `micro-29` 情绪伪装与展示规则
- `micro-33` 情绪调节
- `micro-39` 说话动机
- `micro-40` 受众校准
- `micro-45` 信任与声誉
- `micro-50` 自我呈现
- `micro-51` 协商让步
- `micro-52` 权力应对

推荐调用顺序如下：

1. 先用 `v5.1` 的既有 skill 做主判断。
2. 如果多个候选答案都成立，再调用人格层做偏好排序。
3. 如果题目明确在问“这种人通常怎样”，则直接路由到人格 macro。
4. 如果文本证据不足以支持人格判断，则回退到既有 skill，不强行人格化。

## 7. 与 benchmark 的关系

人格层最可能带来提升的场景主要是：

- `Strange Story`
- `Persuasion Story`
- `Hidden Emotions`
- `Emotion Regulation`
- `Faux Pas`
- `White lies / Misleading expression`
- `Trust / relationship / self-presentation`
- `Negotiation / repair / hierarchical communication`

它对 ToMBench 的作用更像是“在多个可接受解释之间提供更稳的排序”，而不是替代 false belief、语用或情绪技能。

## 8. 验证策略

### 8.1 数据层

建议构造三类验证集：

- 明确人格线索题
- 人格与状态冲突题
- 人格对答案只产生 tie-break 的歧义题

### 8.2 消融层

至少做四组对比：

- `v5.1 baseline`
- `v5.1 + personality priors`
- `v5.1 + personality + review`
- `v5.1 + personality only`

重点看：

- overall accuracy
- ambiguous-item accuracy
- calibration
- over-personalization rate

### 8.3 风险检查

要重点防止三类错误：

- 单句过拟合成人格
- 用人格覆盖显式文本证据
- 把角色要求误判为稳定特质

## 9. 结论

人格 skills 最适合以“横切先验层”的方式加入 `skills_v5.2`。它不应被做成一个独立的社会心智大模块，而应作为现有技能库的稳定偏好调制器，用来处理歧义、排序和风格预测。这样既能保持 `v5.1` 的结构清晰，也能把你已经观察到的增益转化成可扩展、可评测、可解释的系统设计。

