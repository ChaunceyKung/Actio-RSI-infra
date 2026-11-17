# skills_v5.1 设计原因与完备性论证

## 1. 结论摘要

`skills_v5.1` 的 76 个 skill（56 个 micro + 20 个 macro）不是任意堆叠出来的 prompt 集，而是一个面向“社会心智”问题的分层能力库。它的设计合理性主要体现在四点：

1. 它把社会心智拆成了“可判定的原子变量”与“可直接路由的场景原型”两层，这和心理学中将 Theory of Mind 视为多子能力空间、而非单一“会/不会 false belief”的观点一致。[P1][P2][P3][C1]
2. 它把 `感知/注意 -> 记忆/知识 -> 信念 -> 欲望/目标 -> 行动 -> 情绪 -> 语用 -> 规范/关系` 串成了一条完整推理链，这与经典 ToM、语用学、情绪评价、社会互动和关系修复文献是同构的。[P1][P4][P5][P6][P7][S1][S2][S3]
3. 它单独保留了 L0 元控制层（任务路由、证据链、解释竞争、反偏误检查），这和近两年 ToM/社会推理 benchmark 对“是否先正确识别需要哪种 mentalizing depth、是否把证据与猜测分开”的强调高度一致。[C6][C7][C8][C9]
4. 它的 macro 层并不是随意聚类，而是直接对齐当前主流文本型社会心智 benchmark 的高频题型：false belief、higher-order belief、情绪偏差、非字面语言、faux pas、说服、信任/关系、协商/层级沟通等。因此，如果目标是覆盖主流 LLM 社会心智评测场景，`skills_v5.1` 已经覆盖了绝大多数核心文本场景；不足主要在于多模态感知和长期交互记忆两个方向。[C1][C2][C3][C4][C5][C10][C11][C12]

## 2. 为什么要做成 “56 micro + 20 macro” 的两层结构

### 2.1 micro 层的必要性：社会心智不是单一能力

Theory of Mind 的经典定义是：主体需要把信念、意图、愿望、知识、情绪等不可直接观察的心理状态归因给自己和他人，并据此预测行为。[P1] 后续发展心理学工作进一步说明，false belief 只是 ToM 的一个入口，而不是全部；研究对象、任务类型和所测子能力都应被区分开来。[P2][P3]  

ATOMS（Abilities in Theory of Mind Space）系统综述与后续机器 ToM 版图工作都指出，ToM 测量本身就是多维度的能力空间，而不是一个单分数指标。[P3][C17] ToMBench 正是沿着这条路线，将 benchmark 明确拆成 `8 tasks + 31 abilities`。[C1] 这直接支持了 `skills_v5.1` 的 micro 设计原则：每个 micro skill 只负责一个“decision variable”，并给出边界，避免把“看到”和“注意到”、“知道”和“记得”、“隐含意义”和“间接言语行为”、“责任”和“因果”混在一起。

### 2.2 macro 层的必要性：benchmark 问题首先是“场景原型”，不是“原子标签”

虽然底层能力是原子的，但 benchmark 和真实使用中的问题通常不是以“请判断该角色的二阶信念”这种方式出现，而是以“这个人为什么这样说”“他会去哪里找”“这是不是冒犯”“应不应该道歉”“如何在上下级关系里沟通”这类场景原型出现。  

近年的 benchmark 设计也都在朝“scene prototype”靠近，而不是只考 isolated labels：

- ToMBench 以 8 类任务组织能力。[C1]
- FANToM 强调信息不对称对话中的 ToM 压力测试。[C2]
- OpenToM 强调自然叙事、人格特征、心理世界与物理世界并存。[C3]
- SOTOPIA 进一步把社会智能放到开放式多轮互动、协调、竞争和协商里评估。[C10]

因此，`skills_v5.1` 采用 “micro 保证能力完备，macro 保证高频场景完备” 的结构是合理的：  

- micro 解决“能力边界不清”的问题；
- macro 解决“实际路由入口不自然”的问题；
- hierarchical routing 则让场景原型在需要时展开到原子能力，这与本地 `eval/README.md` 中的 `hierarchical` 路由设计完全一致。

## 3. 分层设计的学理依据

下面按 `skills_v5.1` 的分层来论证其设计原因。

### 3.1 L0 元控制层：为什么需要单独的 routing / evidence / explanation / anti-bias

`micro-01` 到 `micro-04` 并不直接回答社会心智问题，而是在控制“解题过程本身”：

- `micro-01 Task Routing`：先识别题目真正要求的 mental variable。
- `micro-02 Evidence-Chain Construction`：区分文本证据、推断和常识补全。
- `micro-03 Multiple-Explanation Competition`：保留多个可行解释。
- `micro-04 Anti-Bias Check`：防止 solver 站在全知视角或道德直觉上抢答。

这一层不是“额外装饰”，而是近年 ToM benchmark 反思中最需要补的一层：

- Mind Your Theory 指出 ToM 任务至少有两个阶段：先决定是否需要调用 ToM、以及需要多深的 mentalizing depth；然后才是具体推理。[C7]
- FANToM 通过“同一底层 reasoning、多个表面问法”的设计，专门检查模型是不是只是做了表面模式匹配。[C2]
- Rethinking ToM Benchmarks for LLMs 指出把人类 ToM 任务直接照搬给 LLM，会继承并放大原任务的理论与方法学局限。[C8]
- EPITOME 也发现模型在 belief attribution、emotion inference、pragmatic reasoning 上表现不均衡，说明“先判定任务类型与证据来源”本身就是难点。[C9]
- 社会认知偏差研究长期表明，人类在社会推断中会系统性低估情境因素、过度依赖直觉性归因，这为 `anti-bias` 的必要性提供了经典心理学支持。[S8]

因此，L0 的存在使这套 skills 不只是“知识条目库”，而是“可审计的解题程序”。

### 3.2 L1-L3：从感知到信念、再到目标与行动，是 ToM 的主干链条

经典 ToM 文献的中心链条是：他人通过何种渠道接触到信息，是否注意到、是否记住、是否拥有背景知识，进而形成何种信念，再据此采取何种行动。[P1][P4][P5]

这正对应了 v5.1 的三层：

- L1：`sensory access / spatial perspective / attention / temporal update / memory / knowledge boundary`
- L2：`first-order belief / false belief / second-order belief / appearance-reality / evidence update / common knowledge / uncertainty / source credibility`
- L3：`self preference / other preference / goal hierarchy / intention recognition / action prediction / commitment priority / goal conflict`

这条链条有明确的跨学科依据：

- Premack & Woodruff 将 belief、doubt、guessing、pretending、liking 等都视为 ToM 的核心对象。[P1]
- Wimmer & Perner、Baron-Cohen et al. 证明错误信念与二阶表征是理解他人行为预测的关键里程碑。[P4][P5]
- BigToM 直接用 `percepts, beliefs, desires, actions` 的因果模板来构造评测，这与 v5.1 把这些变量拆成独立 micro 完全同构。[C5]
- Perceptions to Beliefs 进一步说明，LLM 在 belief 之前的 precursor inference（尤其是 perception inference 和 perception-to-belief inference）本身就是短板，因此 L1 不是冗余层，而是 belief 层的必要前置层。[C6]
- SymbolicToM 则从算法角度说明，显式 belief tracking 会显著帮助 ToM 推理，这从反面证明“把 belief state 独立出来建模”是必要的。[C18]

因此，L1-L3 的设计不是“把心理学概念列个表”，而是明确按照社会推理中的因果依赖关系做了能力分解。

### 3.3 L4 情绪层：情绪不是附属项，而是社会心智判断的核心输出

很多 LLM ToM 讨论过度集中在 false belief，但 EPITOME 明确把 emotional inference 和 pragmatic reasoning 与 belief attribution 并列为 ToM 的关键实验维度。[C9] OpenToM 也指出，模型对“物理世界中的 mental states”往往比对“心理世界中的 mental states”更强。[C3]

`skills_v5.1` 的 L4 单列了 8 个情绪相关 micro：

- 基本情绪评价
- 非典型情绪
- 隐藏情绪
- 展示规则与伪装
- 道德情绪
- 反事实情绪
- 共情与情绪感染
- 情绪调节

它们分别对应了情绪研究中的几个经典脉络：

- Ekman 的 basic emotions 说明情绪与适应性任务、典型诱发条件和外显线索之间存在稳定关联，对 `micro-26` 有直接支持。[P6]
- Scherer 与 Lazarus 的 appraisal tradition 说明情绪来自对事件与目标、资源、责任、替代结果等变量的评估，这支持 `moral emotion`、`counterfactual emotion`、`atypical emotion` 等进一步细分。[P7][P8]
- Gross 的 emotion regulation process model 直接支持将“情绪调节”单列，而不是把它混入一般情绪识别。[P9]
- Decety & Jackson、Singer & Lamm、Hatfield et al. 分别从 empathy、affective sharing 和 emotional contagion 角度支持 `micro-32` 的独立性。[P10][P11][P12]

所以，L4 的存在使这套 skill 库不再局限于“belief-only ToM”，而扩展到了更接近真实社会互动的 affective social cognition。

### 3.4 L5 语言与语用层：真正的社会心智问题往往出现在“说了什么”和“真正想表达什么”之间

如果技能库只覆盖 belief/desire/emotion，而不覆盖语用，它将无法解释主流 benchmark 中大量的 hinting、irony、white lies、scalar implicature、faux pas、persuasion 场景。ToMBench、SocKET、EPITOME 都证明了这一点。[C1][C9][C12]

L5 的 8 个 micro 之所以必要，主要有以下依据：

- Grice 的 conversational implicature 理论为 `literal meaning` 与 `implicature` 的分离提供了经典基础。[S1]
- Searle 的 indirect speech acts 理论说明“这句话在做什么”与“这句话显式说了什么”是两个不同变量，这正对应 `micro-35` 与 `micro-36` 的边界设计。[S2]
- Brown & Levinson 的礼貌理论说明 power、distance、face threat 会系统性影响说话方式，这支持 `speaker motivation`、`audience calibration`、`power navigation` 等技能。[S3]
- Clark & Brennan 的 grounding 理论说明对话理解依赖共同基础和实时协调，这为 `macro-16 对话误解修复与澄清` 提供了理论支撑。[S4]
- SocKET 明确把 humor/sarcasm、offensiveness、sentiment/emotion、trustworthiness 等都纳入 social knowledge benchmark。[C12]

因此，L5 不是语言附属模块，而是把 ToM 从“读故事猜信念”扩展到“真实交流中的社会理解”所必需的一层。

### 3.5 L6 社会规范、关系与修复层：从“能读心”到“会互动”

真实社会心智不止是判断别人想什么，还包括判断：

- 有没有失礼/冒犯
- 谁应承担责任
- 资源是否公平
- 这个人值不值得信任
- 这里有没有权力差
- 哪些信息有隐私边界
- 关系受损后要怎么修复
- 如何做自我呈现
- 如何在分歧中协商与让步

这一层的设计与社会学、社会心理学和交互 benchmark 是一致的：

- Goffman 的 face-work 为 `faux pas / offense / embarrassment / apology / repair` 提供了直接理论背景。[S5]
- Goffman 的 self-presentation 为 `micro-50` 和 `macro-19` 提供了社会学基础。[S6]
- French & Raven 的权力基础理论支持 `power, status, role` 与 `hierarchical communication` 的拆分。[S7]
- Tajfel & Turner 的 social identity theory 支持将 `group identity` 单列，而不是混入一般角色关系。[S9]
- Fehr & Schmidt、Berg et al. 分别从公平/互惠与信任/回报角度支持 `fairness & reciprocity`、`trust & reputation` 的独立性。[S10][S11]
- SOTOPIA 证明真正的社会智能评估已经扩展到协调、合作、竞争、协商、关系管理和策略沟通，而不再只是单轮 MCQ。[C10]

所以，L6 是把 skills_v5.1 从“社会认知能力库”推进到“社会互动能力库”的关键层。

### 3.6 L7 数量、概率与因果归因层：社会心智推理的支持性底座

L7 看起来不像传统 ToM，但它解决的是社会推理里常见的支撑性问题：

- 听到“有些/多数/几乎没有”时如何做模糊数量估计；
- 看到部分样本后如何更新；
- 已知基率时如何做典型性判断；
- 一个后果应该归因于谁或什么条件。

这一层的合理性主要来自两点：

1. BigToM 本身就是围绕 causal template 构造出来的，说明社会心智 benchmark 并不只考心理词汇，还考因果链上各变量的依赖关系。[C5]
2. 社会归因理论长期表明，人会不断对行为和结果做因果解释，而这种解释会进一步影响责任、情绪和关系判断。[S8][S12]

因此，L7 可以理解为“社会心智的数理与归因支撑层”，它不抢占 ToM 的中心地位，但能防止上层情绪、责任、公平、信任判断失去推理底盘。

## 4. 完备性论证：为什么说它已经覆盖了主流文本型社会心智能力空间

### 4.1 对本地 ToMBench 任务空间的覆盖

本地 `skills_v5.1/data/ToMBench_en.jsonl` 共有 2860 条英文样本。按任务统计，主要任务包括：

| ToMBench 任务 | 数量 | 对应 skill 覆盖 |
| --- | ---: | --- |
| False Belief Task | 600 | `macro-01`, `macro-02`, `macro-03`, `macro-13` |
| Faux-pas Recognition Test | 560 | `macro-12`, `macro-17` |
| Strange Story Task | 407 | `macro-07`, `macro-08`, `macro-09`, `macro-16` |
| Unexpected Outcome Test | 300 | `macro-05`, `macro-06` |
| Ambiguous Story Task | 200 | `micro-02`, `micro-03`, `macro-03`, `macro-16` |
| Scalar Implicature Test | 200 | `micro-36`, `micro-53`, `macro-07`, `macro-14` |
| Hinting Task Test | 103 | `macro-07` |
| Persuasion Story Task | 100 | `macro-09` |
| Hidden Emotions | 80 | `macro-05` |
| Discrepant Emotions | 40 | `macro-05` |
| Discrepant Intentions | 40 | `macro-04` |
| Moral Emotions | 40 | `macro-06` |
| Percepts-Knowledge Links | 40 | `micro-05`, `micro-10`, `macro-03`, `macro-13` |
| Knowledge-Pretend Play Links | 30 | `micro-10`, `micro-14`, `macro-03` |
| Completion of Failed Actions | 20 | `micro-22`, `micro-23`, `macro-04`, `macro-11` |
| Discrepant Desires | 20 | `micro-19`, `micro-20`, `macro-10` |
| Emotion Regulation | 20 | `micro-33`, `macro-05`, `macro-06` |
| Knowledge-Attention Links | 20 | `micro-07`, `micro-10`, `macro-13` |
| Multiple Desires | 20 | `micro-21`, `micro-25`, `macro-10` |
| Prediction of Actions | 20 | `micro-23`, `macro-11` |

从这个对表可以看到：本地 ToMBench 的 20 类任务都能在现有 skill 库中找到直接入口，没有出现“大类任务完全无对应 skill”的缺口。换句话说，若以 ToMBench 作为当前文本型 ToM benchmark 的代表，`skills_v5.1` 在任务场景层面已经是高覆盖的。

### 4.2 对主流 LLM 社会心智 benchmark 的覆盖

下面把更广义的主流 benchmark 放到同一张图里看。这里的“主流”是本文基于近年综述与 benchmark 原论文做的归纳，重点覆盖 2023-2025 年在 LLM ToM / social reasoning 讨论中最常出现的文本型基准。[C4][C8]

| Benchmark | 原论文强调的能力 | `skills_v5.1` 对应层/skill | 覆盖判断 |
| --- | --- | --- | --- |
| ToMBench | 8 tasks, 31 abilities 的系统 ToM 测试。[C1] | `macro-01` 到 `macro-14` 为主，辅以 L0-L7 多数 micro | 高覆盖 |
| FANToM | 信息不对称对话、同一 reasoning 多种问法、交互式 ToM 压测。[C2] | `macro-02`, `macro-07`, `macro-08`, `macro-16`; `micro-13`, `micro-16`, `micro-34`-`39`, `micro-48` | 高覆盖 |
| OpenToM | 更自然叙事、人格与偏好、物理世界与心理世界并存。[C3] | `macro-03`, `macro-05`, `macro-10`, `macro-11`, `macro-15`, `macro-19`; `micro-10`, `micro-19`-`33`, `micro-50` | 高覆盖 |
| HI-TOM | 高阶/递归信念推理。[C4] | `macro-02`; `micro-13`, `micro-16`, `micro-17`, `micro-18` | 高覆盖 |
| BigToM | percepts-beliefs-desires-actions 因果模板，前向/后向社会推理。[C5] | L1-L3 几乎全覆盖；尤其是 `micro-05`, `micro-08`, `micro-11`, `micro-12`, `micro-19`-`25`; `macro-01`, `macro-10`, `macro-11` | 高覆盖 |
| EPITOME | belief attribution、emotional inference、pragmatic reasoning 的实验协议包。[C9] | `macro-01`, `macro-02`, `macro-05`, `macro-07`; L2/L4/L5 多数 micro | 高覆盖 |
| Social IQa | 日常社会情境中的意图、反应、情绪和社会常识。[C11] | `macro-04`, `macro-05`, `macro-09`, `macro-10`, `macro-11`, `macro-15`, `macro-18` | 高覆盖 |
| SocKET | humor/sarcasm、offensiveness、sentiment/emotion、trustworthiness 等 social language。[C12] | `macro-05`, `macro-07`, `macro-08`, `macro-12`, `macro-15`, `macro-19`, `macro-20`; L4-L6 多数 micro | 高覆盖 |
| SOTOPIA | 开放式互动中的协调、合作、竞争、社会目标、策略沟通。[C10] | `macro-09`, `macro-15`, `macro-16`, `macro-17`, `macro-18`, `macro-19`, `macro-20`; `micro-39`-`52` | 中高覆盖 |

结论是：

- 对 **文本型、单轮或短叙事型** benchmark，`skills_v5.1` 基本已经覆盖主流问题场景。
- 对 **交互型 benchmark**，skill 本体层面覆盖较强，但如果要完全发挥，还需要 agent memory、turn-level state tracking、长期历史管理等执行框架配合。

## 5. 为什么说它“覆盖大部分主流 benchmark”，而不是只覆盖 false-belief

如果只覆盖 false belief，skill 库只需要 `sensory access + temporal update + first-order belief + false belief + action prediction` 这一小段链条即可。但 `skills_v5.1` 明显远超这一范围：

1. 它覆盖了 belief 系之外的 `emotion / pragmatics / norm / trust / hierarchy / negotiation / repair`。
2. 它覆盖了 benchmark 常见的“同一句话要同时判断 truth value、speaker motive、misleading effect”这类复合任务。
3. 它覆盖了“人际关系历史”“群体身份”“隐私边界”“权力差”这些在开放式 agent 评测中越来越重要的变量。

这与近年的 benchmark 发展方向是一致的：

- ToMBench 从单一任务扩展到 8 任务、31 能力。[C1]
- OpenToM 把 personality 和 psychological world 拉进来。[C3]
- EPITOME 把情绪与语用并列成 ToM 维度。[C9]
- SocKET 和 SOTOPIA 把社会语言、信任、策略沟通、协商与长期互动拉进来。[C10][C12]

所以，从 benchmark evolution 的角度看，v5.1 不是“题型拼接”，而是在向更广义的社会智能能力空间靠拢。

## 6. 仍然存在的边界与不足

这套 skills 很强，但如果论文写作需要更严谨，建议明确它的边界，而不是宣称“完全覆盖所有社会心智 benchmark”。

### 6.1 多模态 ToM 仍是部分覆盖

MMToM-QA 明确把视频与文本联合输入作为 machine ToM 的评测对象。[C13] 这类 benchmark 需要的不只是“概念上的 sensory access”，还包括：

- 视觉线索抽取；
- 面部/姿态/场景状态跟踪；
- 多模态证据对齐。

因此，`micro-05` 和 `micro-06` 在概念上能对齐，但 `skills_v5.1` 仍主要是文本型 skill 库，对多模态 benchmark 应定义为“部分覆盖、可扩展”而非“完全覆盖”。

### 6.2 长期交互记忆与显式 belief state 仍可增强

SOTOPIA 一类 benchmark 已经进入多轮交互、角色持续博弈与长期关系管理阶段。[C10] 2026 年的新 benchmark 也在往“更细粒度能力图谱”和“显式 belief modeling”方向走，例如 CogToM 与 OmniToM。[C14][C15]  

这说明 v5.1 的下一步增强方向更可能是：

- 在执行层加入长期记忆与 turn-level belief store；
- 为多角色递归信念建立结构化 state；
- 为多模态场景加上 cue grounding 层。

这不否定 v5.1 的完备性，而是说明它已经完成了“文本社会心智能力库”的主体框架，接下来要补的是“执行器”和“感知器”。

## 7. 论文写作时可直接采用的核心论点

如果你要把这部分写进论文或报告，可以直接使用下面这段论证框架：

> `skills_v5.1` 的设计遵循“微观能力完备、宏观场景完备”的双层原则。微观层将社会心智分解为 56 个具有独立 decision variable 的原子能力，覆盖感知、注意、记忆、知识、信念、欲望、目标、行动、情绪、语用、社会规范、关系修复以及数量/因果支撑推理；宏观层则将这些能力重新组织为 20 个可直接路由的高频社会场景原型。这样的设计与心理学对 ToM 多维结构的理解、语用学与社会学对真实互动的分析、以及当前主流 LLM 社会心智 benchmark 从 false-belief 向情绪、语用、关系与交互扩展的趋势保持一致。[P1][P2][P3][C1][C2][C3][C9][C10]  
>  
> 进一步地，对本地 ToMBench 数据的逐任务对表表明，现有 20 类任务均可在 `skills_v5.1` 中找到直接入口；对 ToMBench、FANToM、OpenToM、HI-TOM、BigToM、EPITOME、Social IQa、SocKET、SOTOPIA 的 benchmark 级映射则表明，该 skill 库已经覆盖了大部分主流文本型社会心智问题场景和能力需求。其主要边界不在文本社会推理本身，而在多模态感知与长期交互状态管理两个方向。[C1][C2][C3][C4][C5][C9][C10][C11][C12][C13]

## 8. 参考文献与链接

### 8.1 心理学 / 社会认知 / 情绪

- [P1] Premack, D., & Woodruff, G. (1978). *Does the chimpanzee have a theory of mind?*  
  Link: https://doi.org/10.1017/S0140525X00076512
- [P2] Apperly, I. A. (2012). *What is “theory of mind”? Concepts, cognitive processes and individual differences.*  
  Link: https://research.birmingham.ac.uk/en/publications/what-is-theory-of-mind-concepts-cognitive-processes-and-individua/
- [P3] Beaudoin, C., Leblanc, E., Gagner, C., & Beauchamp, M. H. (2020). *Systematic Review and Inventory of Theory of Mind Measures for Young Children.*  
  Link: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.02905/full
- [P4] Wimmer, H., & Perner, J. (1983). *Beliefs about beliefs: Representation and constraining function of wrong beliefs in young children's understanding of deception.*  
  Link: https://doi.org/10.1016/0010-0277(83)90004-5
- [P5] Baron-Cohen, S., Leslie, A. M., & Frith, U. (1985). *Does the autistic child have a “theory of mind”?*  
  Link: https://doi.org/10.1016/0010-0277(85)90022-8
- [P6] Ekman, P. (1992). *An Argument for Basic Emotions.*  
  Link: https://sanlab.psych.ucla.edu/wp-content/uploads/sites/31/2016/03/Ekman-1992-An-argument-for-basic-emotions.pdf
- [P7] Scherer, K. R. (2001). *Appraisal Considered as a Process of Multilevel Sequential Checking.*  
  Link: https://academic.oup.com/book/53557/chapter/422115725
- [P8] Lazarus, R. S. (1991). *Emotion and Adaptation.*  
  Link: https://archive.org/download/lazarus_richard-s/lazarus1991_2.pdf
- [P9] Gross, J. J. (1998). *The Emerging Field of Emotion Regulation: An Integrative Review.*  
  Link: https://doi.org/10.1037/1089-2680.2.3.271
- [P10] Decety, J., & Jackson, P. L. (2004). *The Functional Architecture of Human Empathy.*  
  Link: https://doi.org/10.1177/1534582304267187
- [P11] Singer, T., & Lamm, C. (2009). *The Social Neuroscience of Empathy.*  
  Link: https://greatergood.berkeley.edu/images/uploads/Singer_2009.pdf
- [P12] Hatfield, E., Cacioppo, J. T., & Rapson, R. L. (1993/1994). *Emotional Contagion.*  
  Link: https://www.elainehatfield.com/uploads/3/2/2/5/3225640/50._hatfield_cacioppo__rapson_1993.pdf

### 8.2 语用学 / 社会学 / 社会心理学

- [S1] Grice, H. P. (1975). *Logic and Conversation.*  
  Link: https://web.stanford.edu/class/psych205/papers/Grice-1975.pdf
- [S2] Searle, J. R. (1975). *Indirect Speech Acts.*  
  Link: https://doi.org/10.1163/9789004368811_004
- [S3] Brown, P., & Levinson, S. C. (1987). *Politeness: Some Universals in Language Usage.*  
  Link: https://archive.org/details/politenesssomeun00brow
- [S4] Clark, H. H., & Brennan, S. E. (1991). *Grounding in Communication.*  
  Link: https://web.stanford.edu/~clark/1990s/Clark%2C%20H.H.%20_%20Brennan%2C%20S.E.%20_Grounding%20in%20communication_%201991.pdf
- [S5] Goffman, E. (1955). *On Face-Work: An Analysis of Ritual Elements in Social Interaction.*  
  Link: https://doi.org/10.1080/00332747.1955.11023008
- [S6] Goffman, E. (1959). *The Presentation of Self in Everyday Life.*  
  Link: https://archive.org/details/presentationofs00goff
- [S7] French, J. R. P., Jr., & Raven, B. (1959). *The Bases of Social Power.*  
  Link: https://cdn.isr.umich.edu/pubFiles/historicPublications/THEBASESOFSOCIALPOWER_1565_.PDF
- [S8] Ross, L. (1977). *The Intuitive Psychologist and His Shortcomings: Distortions in the Attribution Process.*  
  Link: https://www.sciencedirect.com/science/chapter/bookseries/pii/S0065260108603573
- [S9] Tajfel, H., & Turner, J. C. (1979/1986). *The Social Identity Theory of Intergroup Behavior.*  
  Link: https://archive.org/download/15341_Readings/15341_Readings/Intergroup_Conflict/Tajfel_%26_Turner_Psych_of_Intergroup_Relations_CH1_Social_Identity_Theory_text.pdf
- [S10] Fehr, E., & Schmidt, K. M. (1999). *A Theory of Fairness, Competition, and Cooperation.*  
  Link: https://doi.org/10.1162/003355399556151
- [S11] Berg, J., Dickhaut, J., & McCabe, K. (1995). *Trust, Reciprocity, and Social History.*  
  Link: https://doi.org/10.1006/game.1995.1027
- [S12] Heider, F. (1958). *The Psychology of Interpersonal Relations.*  
  Link: https://garfield.library.upenn.edu/classics1993/A1993KZ42800001.pdf

### 8.3 计算机 / LLM 社会心智 benchmark 与方法学

- [C1] Chen, Z. et al. (2024). *ToMBench: Benchmarking Theory of Mind in Large Language Models.*  
  Link: https://aclanthology.org/2024.acl-long.847/
- [C2] Kim, H. et al. (2023). *FANToM: A Benchmark for Stress-testing Machine Theory of Mind in Interactions.*  
  Link: https://aclanthology.org/2023.emnlp-main.890/
- [C3] Xu, H. et al. (2024). *OpenToM: A Comprehensive Benchmark for Evaluating Theory-of-Mind Reasoning Capabilities of Large Language Models.*  
  Link: https://arxiv.org/abs/2402.06044
- [C4] He, Y. et al. (2023). *HI-TOM: A Benchmark for Evaluating Higher-Order Theory of Mind Reasoning in Large Language Models.*  
  Link: https://arxiv.org/abs/2310.16755
- [C5] Gandhi, K. et al. (2023). *Understanding Social Reasoning in Language Models with Language Models.*  
  Link: https://arxiv.org/abs/2306.15448
- [C6] Jung, C. et al. (2024). *Perceptions to Beliefs: Exploring Precursory Inferences for Theory of Mind in Large Language Models.*  
  Link: https://aclanthology.org/2024.emnlp-main.1105/
- [C7] Wagner, E. et al. (2025). *Mind Your Theory: Theory of Mind Goes Deeper Than Reasoning.*  
  Link: https://aclanthology.org/2025.findings-acl.1368/
- [C8] Wang, Q. et al. (2025). *Rethinking Theory of Mind Benchmarks for LLMs: Towards A User-Centered Perspective.*  
  Link: https://arxiv.org/abs/2504.10839
- [C9] Jones, C. R., Trott, S., & Bergen, B. (2024). *Comparing Humans and Large Language Models on an Experimental Protocol Inventory for Theory of Mind Evaluation (EPITOME).*  
  Link: https://doi.org/10.1162/tacl_a_00674
- [C10] Zhou, X. et al. (2024). *SOTOPIA: Interactive Evaluation for Social Intelligence in Language Agents.*  
  Link: https://arxiv.org/abs/2310.11667
- [C11] Sap, M. et al. (2019). *Social IQa: Commonsense Reasoning about Social Interactions.*  
  Link: https://aclanthology.org/D19-1454/
- [C12] Choi, M. et al. (2023). *Do LLMs Understand Social Knowledge? Evaluating the Sociability of Large Language Models with SocKET Benchmark.*  
  Link: https://aclanthology.org/2023.emnlp-main.699/
- [C13] Jin, C. et al. (2024). *MMToM-QA: Multimodal Theory of Mind Question Answering.*  
  Link: https://arxiv.org/abs/2401.08743
- [C14] Tong, H. et al. (2026). *CogToM: A Comprehensive Theory of Mind Benchmark inspired by Human Cognition for Large Language Models.*  
  Link: https://arxiv.org/abs/2601.15628
- [C15] Bawatneh, A. et al. (2026). *OmniToM: Benchmarking Theory of Mind in LLMs via Explicit Belief Modeling.*  
  Link: https://arxiv.org/abs/2605.26322
- [C16] Chen, R. et al. (2025). *Theory of Mind in Large Language Models: Assessment and Enhancement.*  
  Link: https://aclanthology.org/2025.acl-long.1522/
- [C17] Ma, Z. et al. (2023). *Towards A Holistic Landscape of Situated Theory of Mind in Large Language Models.*  
  Link: https://aclanthology.org/2023.findings-emnlp.72/
- [C18] Sclar, M. et al. (2023). *Minding Language Models’ (Lack of) Theory of Mind: A Plug-and-Play Multi-Character Belief Tracker.*  
  Link: https://aclanthology.org/2023.acl-long.780/
