# Phase 1B.1 审阅与 Phase 1C0 行动方案

审阅日期：2026-10-08。产品基线：`bc0c034f997a59161ff79f865ad41098433884b5`。

**建议维持已验证 fixture 路径的 CONDITIONAL_GO，进入 Phase 1C0：离线测量准入与 SOTOPIA 最小复用。** 本轮确认 B1R1–B1R4 已有针对性实现和验收；下一阶段可以开始评估工程，但必须先补一处已复现的“冻结场景输入→实际派发”校验缺口。无需再单独扩展一轮通用可靠性平台，也不开放真实模型费用。

配套：[其他 session 执行的 Codex Prompt](../prompts/phase1c0_offline_measurement_and_sotopia.md)。本轮只交付审阅、证据摘要和 Prompt；未修改产品、安装依赖或执行下一阶段。遵循 [AGENTS.md](../../AGENTS.md)，完成文档验证后提交并推送本轮分支，不合并 main。

## 1. 本次核实范围

| 项目 | 核对结果 |
|---|---|
| 仓库与远端 | 本地和远端 `phase1b1-reliability-and-evidence-export` 均为 `bc0c034…`；开始时工作树干净；远端 main 仍为 `fad04fc…` |
| 当前验收记录 | 8 suites：contract 6、runtime 2、failures 6、processes 4、reliability 7、entry_concurrency 1、schema 5、evidence 7，共 38 组 PASS |
| 源码与测试绑定 | 22 个产品文件、15 个相关测试/fixture 文件的 hash 与登记匹配；各当前 suite 记录的产品 hash 也匹配 |
| 证据文件 | 8 个当前 suite JSON、8 个 raw archive、artifacts、clean-install CLI smoke、delivery 和 bootstrap 日志 hash 匹配 |
| 清理 | 已交付的 66 个受管 Job 清理记录为 active=0；本轮未重新查询所有历史 Job |
| 五个样例 | 20 个样例文件 hash 匹配；实际运行当前离线 verifier，五个结果均与 manifest 一致 |
| 新增定点检查 | 在临时副本做两种重算 hash 的语义变更，均暴露 C0R1；没有启动 DSH/Concordia 或调用模型 |

没有重新运行全部 38 组、重新安装干净环境或重复跑原故障注入；验收/安装/清理属于历史证据核对，五包核验和两项变更实验是本轮实际执行。详见 [审阅证据 JSON](phase1b1_review_evidence.json)。

## 2. 上一轮四项问题可以关闭

| 问题 | 实现与验收观察 |
|---|---|
| B1R1 场景终态 | `scenario_terminal` 与 `terminal_body/validate_sources` 检查 manifest、ordered operations、domain/world 和源事实；第二实体构造失败、真实 Engine callback 失败保持 partial；合法非法 action 拒绝仍可 complete/task_failure |
| B1R2 执行资格 | `begin` 事务内比较规范请求，只有赢家冻结输入；场景入口检查 fresh；Store 的本进程 claim 防止只读 run/epoch 变成执行权；两个入口都有真实双进程竞争记录 |
| B1R3 恢复目标 | recover 先解析目标、核对 run/epoch/owner，清理前后复核 lease/worker；历史或未知目标不回收其他任务 |
| B1R4 replay override | API sentinel 与 CLI 区分未提供参数；冻结 replay 的显式覆盖在创建 run/worker 前拒绝；现有 replay 仍保持新创建身份 |

schema=0→2 迁移到新副本，SQLite backup 覆盖 WAL，旧 spec/pins 与事实不原位改写；旧 complete 保留为历史声明。证据导出使用一致读快照，离线 verifier 无 runtime/作者目录依赖。这些方向继续保留。

这里的“关闭”针对前轮定义的四项行为，不表示所有关联代码已经穷尽验证。新的准入检查在下节独立登记，不改写旧 PASS/FAIL。

## 3. C0R1 / P1：冻结 observation、ActionSpec 尚未绑定到实际派发

位置：[verify.py](../../src/actio/verify.py)，基线第 148 行仅核对 dispatch memory，第 170 行核对 native task 与 dispatch intent；[scenarios.py](../../src/actio/scenarios.py) 中 `External.act` 组装 observations 和 ActionSpec。

当前链路验证了 native task = dispatch intent、dispatch memory = frozen snapshot，但缺少 social 的 observation/ActionSpec 与 frozen manifest 的对应校验。

本次使用已提交 social 样例，分别执行：

1. 只把 frozen input 中 `observations.A` 改为一个从未实际派发的合成字符串。
2. 只把 frozen input 中 `action_spec.call_to_action` 改为一个从未实际派发的合成字符串。

每次仅更新依赖的 `run.input_hash`、终态凭据的 `manifest_hash` 以及文件清单 hash；实际 dispatch audit、native raw occurrence、回答和 world 保持原样。新包省略可选的 `verification.json`，要求 verifier 独立重算，而非因旧结果文件不同而拒绝。

两次实际输出均为：

```json
{"bundle_integrity":"valid","facts_consistency":"consistent","scenario_completeness":"complete","task_outcome":"success","errors":[],"missing":[]}
```

这是内部事实不一致仍被接受的问题，与“hash 不能证明作者身份”不同：包内已包含两个互相矛盾的输入，verifier 应识别。它不表示历史真实运行输入已经被修改。

**下一轮第一步**：为当前固定场景补齐 manifest→Entity/step→dispatch→native task 的校验，包括角色到真实 agent 的映射、observation 策略、完整 ActionSpec、必要 memory 字段及其他必需输入。复用一个明确版本的场景输入合同，使在线 seal 与离线校验保持一致；避免为了修一条字符串比较而创造第二个 Engine。

注意实际 social 样例中 B 的 observations 有一条，A 有两条同值 observation；这是 Engine 的观察调用历史。不能假定每个实体恰好收到一次，也不能为通过新验证改写旧 raw 事件。应核查固定 Engine/调度合同，保留真实次数和顺序；如旧证据不足以证明次数，明确降低那一维的可证范围。

**验收**：以上两种修改及缺字段/错 agent/越权观察/ActionSpec 选项或类型漂移不进入测量；原五包保留历史记录并给出当前重新核验结论。新版本 verifier 的旧报告比较规则必须明确，不能为升级删除历史文件后假称原包未变。

## 4. 从“完整轨迹”到“有效测量”还缺什么

证据完整性、任务结果、测量状态应分开。下一轮不直接复用 Phase 1A 的一个字符串分类器，也不把 tool success 或固定 cooperate 当作社会智能分数。

| 输入 | 离线准入/测量处理 |
|---|---|
| 完整助手或完整 social fixture | 可做其冻结任务合同支持的确定性指标；输出标注 fixture |
| 完整、合法记录的非法 action 拒绝 | 保留 task_failure，进入对应约束/失败率统计；不能从数据集中删除，也不补造缺失 agent 的社会评分 |
| partial/unknown 且已有基础设施失败证据 | 保留 infrastructure_failure，禁止调用 judge；评分值为空，不当 task zero |
| 缺事实、legacy_unverified、活动前缀 | insufficient_evidence/不准入，禁止调用 judge；仍保留登记和原因 |
| hash/内部关联冲突 | 证据无效，不准入；不尝试评分后“平均掉” |
| 完整输入，但受控 judge 返回坏类型/错身份/缺维度 | invalid_measurement，与任务结果分开，保留原响应 hash 和错误原因 |

Phase 1B.1 的 social manifest 没有独立冻结的 social goals 或初始关系量表。它能证明 action 合法、观察按策略隔离、GM 裁决闭环，不能支持“目标达成 8 分”“关系提升 6 分”等真实测量。后续 goal/relationship 合同必须要求相应前置输入；缺失时拒绝该指标，不依据结果倒填目标。

建议本轮交付两条有清晰标签的路径：

- **真实证据的离线确定性指标**：助手的工具合同结果、社会行动合法性/约束/完成情况，均从可核对事实派生并保留来源。
- **受控响应的解析与 envelope 验证**：专门的合成 EvaluationInput 有明确目标、角色、维度、范围和输入视图；judge 输出是预置数据。验证解析器、身份映射和记录链路，不宣称发生了模型评审或验证了效度。

## 5. SOTOPIA：复用 parser/schema seam，先查验 evaluator 兼容性

本轮已静态读取本地干净参考仓库，未执行 SOTOPIA 或安装它：

`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\18_sotopia\repo`

固定 SHA：`a0aaafb440e570e5e61b7c44a44e5e417c545383`，项目 metadata `0.1.5`，MIT。相关文件为 `sotopia/generation_utils/output_parsers.py`、`sotopia/envs/evaluators.py`、`sotopia/database/evaluation_dimensions.py`、`base_models.py` 及对应 tests。

| 静态发现 | 下一轮需要实际验证/适配 |
|---|---|
| `PydanticOutputParser.parse` 有 JSON repair/`value` 展开/`properties` 分支，context 与无 context 路径使用不同的校验输入 | 原始输出必须保留；严格准入不能被修复、数字字符串或 bool 的隐式转换绕过；正常和异常两条路径都测 |
| `EpisodeLLMEvaluator` 对 `evaluations.values()` 枚举后重新分配 agent_1/agent_2 | 字典顺序不应决定真实身份；Actio 使用封存 alias→agent/role 映射，倒序键必须不串人 |
| evaluator 用 `model_dump()[dimension][1]/[0]`，而当前标准维度为 `{reasoning, score}` 对象 | 静态可见返回形状不一致风险；下一轮用真实上游受控调用刻画，不能先宣称整个 evaluator 可直接用 |
| 异常会返回 `[]`；仅 history 且无 messages 时参与 agent 数为 0；默认过滤含 “did nothing” 的消息 | 空列表不成功；显式参与身份与输入完整性；保留不行动记录或把过滤规则版本化 |
| `relationship`、物质收益是 -5..5；secret/social_rules 是 -10..0；goal 等是 0..10 | 旧 Phase 1A 把两个维度都按 0..10 检查，不能作为 SOTOPIA 量表；本轮按选定 schema 冻结真实范围 |
| 顶层导入牵涉 generation、redis-om、litellm 等，pyproject 有额外完整平台依赖 | 先核查最小导入闭包；优先隔离 adapter；必要时按 MIT 可追踪提取少量源码，不能为 parser 自动部署 Redis/整个模拟平台 |

目标是实际执行固定上游 parser/选定 schema 或可追踪的最小源码提取，再实现 Actio 自有严格输入/结果 envelope。完整 evaluator wrapper 若无法满足身份/形状合同，可只保留为兼容性实验并明确不采用；这不阻断 parser 复用，但必须有真实执行证据。不能写同名假 parser 后称为上游已验证。

## 6. Phase 1C0 的实施顺序与终点

| Slice | 交付 | Gate |
|---|---|---|
| C0.0 输入合同补齐 | C0R1 修复、旧报告/新 verifier 版本规则、重算 hash 反例回归 | 冻结 observation/ActionSpec 与实际 dispatch/native 不一致时拒绝准入 |
| C0.1 测量合同和输入包 | 最小不可变 EvalSpec、Evidence admission、EvaluationInput；真实身份映射与可见范围 | 准入前不调用 evaluator，partial/invalid/legacy 保留原因，输入 hash 可复算 |
| C0.2 SOTOPIA 复用及严格 envelope | 固定 parser/schema 执行、上游行为刻画、薄 adapter；修复旧 scores 四类坏类型 | 反序键不串人；错误类型/范围/维度不被 repair/coercion 提升为有效结果 |
| C0.3 两条离线路径 | 真实包的确定性指标；合成受控 judge response 的结构验证 | 本地费用 0、无网络/模型调用；结果含证据/合同/parser/输入/响应链路 |
| C0.4 数据登记与交付 | 一个小型冻结 fixture campaign，保留全部准入/失败结果；必要测试、文档和 GitHub | 重复证据不重复计数，同源 replay 标关联；不做统计提升/自动晋升 |

不需要新 HTTP 服务、前端、全量 evaluator 框架、第二数据库权威或数据库大迁移。可以把评估产物保存为版本化不可变本地文件，原证据包只读。生产 artifact pins 保持旧语义，别为运行新 evaluator 自动更新既有 AgentSpec。

campaign 在此只封存 EvalSpec、输入集合/split、版本和去重单位。五个公开样例是工程 fixture，不能宣称形成科学 holdout；同一 scenario 的起点 replay 也不是独立样本。真实 pilot 的单位、样本量、效度/偏差、人评对照和预算计划可写出，当前不执行、不过度承诺。

## 7. 明确保留的后续工作

Phase 1C1 才考虑：新任务/社会目标数据集、模型/评委实际接入、小规模 pilot 与有效性分析。须另外明确 provider/model、凭据来源、请求/输出/费用上限；当前预算 0 不阻塞 C0 的离线工作，也不授权 C1。

单 seat 演化仍在可靠测量与独立准入后，再迁入 Raven C02/C03；允许所有候选被拒绝。跨版本稳定 AgentVersion、真实成本/延迟遥测、binary-source provenance、完整恢复、写效果工具和规模能力各自后置，不能因开始评估就悄悄开放。

本轮文档分支为 `docs/phase1b1-review-phase1c0-plan`，包含 `bc0c034` 与本交接文件。下一 session 优先从该分支已推送 HEAD 创建实现分支；每轮完成后验证、提交、普通 push 并核对远端 SHA，不默认合并 main。
