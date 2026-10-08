# Codex 执行 Prompt：Phase 1C1 任务合同与校准就绪

你在 Actio-RSI-infra 项目中执行 **Phase 1C1：任务合同与校准就绪（offline）**。请完成下述有界实现、验收、文档、提交和 GitHub 推送；先核实代码与复用资产，再实施。不要仅给计划，也不要自动进入下一阶段。

## 0. 授权、起点与不可改变的边界

仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。

已验证产品：`phase1c0-offline-measurement` / `1e85d8c2fb4a756de81acb333905190df9e97592`。

本 Prompt 所在交接分支：`docs/phase1c0-review-phase1c1-plan`。目标执行分支：`phase1c1-task-contract-and-calibration`。

1. 读取根 AGENTS.md、状态、remote、已有分支和任何适用的目录规则。保护用户现有修改；有无关脏文件时使用适当隔离 checkout，不 reset、不覆盖、不夹带提交。
2. fetch origin，核对产品基线仍可解析并是交接分支的祖先，记录交接分支的远端完整 SHA。从已核对的 `origin/docs/phase1c0-review-phase1c1-plan` 创建执行分支；目标分支已存在则先检查是否是本任务可继续的工作，不强制重建。若交接远端不可取，明确说明，不能默默从 main 开始。
3. **每轮完成并验证后都要 commit → 普通 push 到 origin 当前任务分支 → 核对远端 SHA 与本地 HEAD。** 用户已持续授权，无需再次询问。禁止默认合并 main、force push 或部署；push 失败保留本地提交并报告精确阻塞。
4. 模型预算 **0**。不调用 live provider，不读取/打印环境中的模型密钥，不以已有登录态或配置作为费用授权。允许获取少量必要的公开源码/文档、安装锁定依赖及 GitHub 推送；所有模型、judge、embedding、训练请求保持 0。
5. Windows x64 / Python 3.12、官方 DSH `0.1.5rc1`、隔离短路径、Python 领域状态和现有 RuntimePort 保持。Concordia 固定 `b71d202750e23444ce1bf28d9f114bcd88aa41db`。本轮不要借机升级依赖。
6. 不重写 DSH loop、不新建第二 solver loop、不接 Raven 晋升或 Letta 状态权威、不运行完整 SOTOPIA 平台/Redis、不触发 Strands 替换。不开放 semantic cancel、原生 resume/fork、mid-run restore、训练或自动版本激活。
7. 旧 Phase 1A/1B/1B.1/1C0 证据、FAIL 记录、campaign 和原始日志不可改写。新 run、新数据库、新证据目录；旧任务保持原有行为。复制源码复用必须保留许可证及来源信息。

## 1. 开工必读与已知事实

先读以下仓库相对路径：

- `docs/reviews/phase1c0_review_and_phase1c1_plan.md` 和 `phase1c0_review_evidence.json`。
- `docs/validation/phase1c0/01_contract.md`、`02_results.md`、`03_gate.md`、`04_usage.md`、`05_sotopia_reuse.md` 和 `evidence_manifest.json`。
- `src/actio/scenarios.py`、`terminal.py`、`verify.py`、`eval_contract.py`、`evaluation.py`、`eval_worker.py`；相关 store/runtime/evidence 代码与测试按依赖追读。
- `docs/planning/03_target_architecture.md`、`08_evolution_architecture.md`、`11_mvp_roadmap.md` 的相关部分。

需要追溯时参考：

- `D:\调研\RSI_AI训AI\Actio_RSI_agentic_evolution_infrastructure_architecture_report.md`
- `D:\调研\RSI_AI训AI\social_mind_agentic_evolution_infrastructure_research_report.md`

C0 已实现离线 admission/measurement，35 组历史验收；审阅重跑 14 组通过，12 当前记录独立复核通过。当前测量包括确定性事实指标与 preset controlled response，**无真实模型判断、无人类校准、独立研究单位为 0**。不要把这些说成社会能力基线。

旧 social manifest 没有目标/初始关系，给它补一张事后说明不构成冻结任务。当前 `validate_spec` 还要求匹配精确当前源码 pins；不能假定改代码后旧 EvalSpec 仍由新 verifier 支持。

## 2. 先做窄复用查验与设计冻结

限定查验这次任务必需的资产，不重做 21 份规划：

- 本地 SOTOPIA：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\18_sotopia\repo`，固定 SHA `a0aaafb440e570e5e61b7c44a44e5e417c545383`。查 `sotopia/database/persistent_profile.py` 的 scenario、agent_goals、relationship/background_story，与已提取 parser/schema 的接口。
- 在 GitHub 相同 SHA 核对实际拟复用定义/数据出处；记录 URL、commit、文件 hash、许可、采用字段、必要改动及不采用原因。本地参考 checkout 只读，不 pull 改写。
- 代码 MIT 不等于数据 MIT。注册表中的 SOTOPIA 数据为 CC-BY-SA 4.0，其他数据另有许可证；采用具体样例前核对数据卡、版本和再分发条件。`tests/envs/test_background.json` 中 scenario 为 `<missing_info>`，不能原样当作完整任务。
- 优先复用合同语义和已提取组件。没有许可清楚、字段完整、可离线使用的小样例时，创建两个明确标为 Actio authored synthetic fixture 的任务卡，记录区别；无需下载 RDB/整套 benchmark 或补入 Redis/litellm。

将窄设计写到 `docs/validation/phase1c1/01_contract.md`，然后直接实施。常规实现选择自行判断；遇到 live 或人工数据依赖时标 BLOCKED 并继续其他已授权工作。

## 3. 唯一的任务范围：两人共同排程

实现一个任务族、两个任务卡、两个 seat、固定两步的社会任务：第一人提出时间，第二人看到公开提议后回应；双方各自有冻结的可用时间/偏好/目标，关系基线明确。两个卡分别覆盖可达成与约束冲突，仍只是工程 fixture。

允许据代码选择具体合法动作编码，但任务必须有非恒真的判据，至少能区分共同约束下达成、合法但未达成、非法动作拒绝和未完成。不得把“Worker 成功退出”“选择 cooperate”或 preset answer 等同任务成功。

### 3.1 TaskSpec 和冻结顺序

新增明确版本的 TaskSpec/输入合同，至少包含：

- schema/version、task/family/variant 标识、来源/许可或 authored-fixture 标记；规范内容 hash。
- 公共场景、seat→真实 agent/spec 绑定、各 seat 目标/私有约束、初始关系与必要背景。
- 每步可见范围：公共信息、自己的私有信息、此前实际公开行动；memory as-of 与来源范围。judge 可读哪些目标/关系由 metric view 明确授予，不能直接传完整审计包。
- 实际 ActionSpec 全字段、行动顺序、最大步数、seed、终止条件、成功/失败判据和确定性任务结果规则版本。
- 执行模式 `fixture` 以及工程分组信息。脚本化输出/期望测试答案单独标明并从 evaluator 和标注 view 排除。

必须先校验和冻结，再创建 run 或 Worker；同 key 重试和 replay 的输入约束继承原规则。不能把刚从数据库读出的可变目标放到末尾再 hash。

本轮默认不增加 DB migration：优先使用现有 manifest 与不可变内容文件。旧 v1/v2 输入的固定解释保留，新合同单独分派，不通过放宽旧校验兼容新动作。代码 pins 改变时使用显式新身份/spec 做新实验，不原位刷新旧身份的 pins。

### 3.2 经真实 runtime/Engine 运行

复用现有 RuntimePort、受管 DSH、官方 SDK、Concordia Sequential/Entity/ActionSpec 和事实链。扩展现有 adapter 即可，不另造调度器或用纯 Python 模拟执行替代验收。

- 至少真实跑通新任务的成功与合法未达成路径；补相应非法动作和中断/partial 验收。
- 第二 actor 确实收到第一 actor 的公开行动；对手私有约束和 GM 私有上下文不泄漏。观察次数/顺序按真实 Engine 记录，不假定每个 actor 恰好 observe 一次。
- 冻结 TaskSpec→每步有效 view/ActionSpec→dispatch intent→native task→返回行动→世界/领域结果→终态完整绑定。
- 领域成功由冻结约束与实际行动重算，独立于运行状态；非法行动在世界效果前拒绝；缺第二步保持 partial，不补造回应或分数。
- 在线 seal 与离线 verifier 共享版本化语义检查。旧证据原样保持，新负例使用临时副本验证内部一致性。

## 4. 评估、分组与只读 campaign 核验

### 4.1 新任务输入到现有评估链

保持 admission / task_outcome / measurement 三轴。新完整任务包的 goal/relationship 只能从运行前冻结的输入派生；实际行为、任务结果和依据来自证据。actor view 与 judge view 分开。

复用 deterministic 和 controlled_response 模式：确定性任务结果需引用事实；goal 0..10、relationship -5..5 的 preset 响应仍只做 parser/schema/dataflow 验收。为新任务冻结具体 rubric/anchors/上下文及版本，不将旧泛化文字冒充已校准 rubric。alias 按 seat 显式绑定，反序 JSON 不换身份，角色交换需新绑定。

缺失输入拒绝或 insufficient，损坏拒绝；非法响应、缺依赖、内部错误、timeout 保留原错误语义；不自动重试、不静默零分。旧 social 包仍缺上下文，不准事后补目标后升级其状态。

### 4.2 分组规则

明确区分 family、任务卡、episode、repeat/replay、baseline/candidate arm（此轮不执行 candidate），以及 evaluation request。

- 同 family 的任务变体、角色置换、重复运行和 replay 必须留在同一开发/校准准备分组，不按随机 run ID 分开。
- 同内容不同导出、同 source/spec/response 请求应按合同去重；不同 response/spec 是不同测量请求，但不是新的研究单位。
- 冻结分组清单、分配规则/seed/hash；两个实际任务卡可都在开发组。用单独合成注册负例验证跨组冲突，不为凑 split 伪造独立任务族。
- 数据清单可使用 `development` / `calibration_pending`；公开或作者看过的内容不得称为 sealed holdout。独立研究单位数继续 0。

提供独立只读 `verify-campaign` 等效公开 CLI，**不能调用 campaign 执行入口来代替验证**。至少检查：dataset/spec/record/source/alias/view 关联、登记 ID 完备且唯一、缺失/多余/错属记录、文件清单 hash、重复请求、family 分组冲突、各状态统计分母、fixture/live 标记和预算；完整合法数据不产生新测量。完备性相对于冻结 dataset 和明确文件清单判断；目录中已标为 historical 的旧记录可以保留，但不得混入当前统计。保留失败、不挑选有效记录后报成功率。

### 4.3 旧记录的版本路径

选择最小明确方案：保留 C0 固定提交/隔离环境的复核命令及源码锁定说明，新实现对不支持的旧 pins 明确报 unsupported；或实现并验收有限版本分派。无需为此建设通用插件系统。

不得去掉源码 pins 检查、修改旧 record/spec/hash 或导入记录指定的任意代码。验收中用固定 C0 实现复核原 12 记录，并用新实现复核新记录；报告清楚哪个版本验证了哪个集合。代码 hash 发生变化后，最终证据必须对应最终源码和实际安装包。

## 5. 人工校准接口：做好交接，但不捏造标签

导出可读 Markdown/JSONL 标注包与结构化输入模板；明确目标、基线、完整可见交互、维度锚点及无法判断原因。隐藏模型/provider、candidate/arm、历史分数、preset answer 和期望结果；显示稳定匿名 seat，内部保存可追溯映射。

实现标签导入校验，绑定 task、episode/trace、rubric、view、alias、分组版本和标注来源；缺标、重复/冲突标签、错版本/错 seat 不静默接受或补零。盲化后的实际内容与 hash 必须对应，不能只有模板名。

无真实标注者时交付空白模板、待标队列和 `human_calibration=BLOCKED`。可以用明确 `synthetic_label_fixture` 测试解析、缺标及分歧处理；不得将 Codex 生成的分数称为人工 gold 或专家共识。真实分数若未提供，不需要停下来索要才能完成工程交付。

文档给出未来双人独立标注、分歧裁决、维度分开计算一致性、缺失率和有序分数的校准比较方案。没有真实数据时不报告实测相关系数、显著性、置信区间或校准通过，不自动联系标注者。

## 6. Provider / pilot 准备：当前始终 BLOCKED

本轮不实现或启用网络 transport。写配置合同、pilot 预注册草案及可执行只读 preflight，配置不包含 secret。

- 未来 solver/judge 的 provider、精确模型版本、参数、工具权限、数据发送范围、独立进程/上下文及 judge 与 solver 的依赖关系都需显式指定。独立上下文不等于独立统计判断。
- 分列 solver、GM、judge、重试与其他调用的次数/token/费用上限、失败率口径、停止条件和账本归属；无法报价时标待确认，不能编造当前价格。
- 给出小规模 pilot 的建议单位/重复数与理由、校准方案和之后样本量决策方式；建议不是支出授权或效度证明。
- `preflight` 在预算 0、缺显式授权或缺必要配置时返回结构化 BLOCKED/原因和非成功退出码，并在读取凭据、创建客户端、启动 Worker 前停止。即使传入正数预算也不能把此轮实现切换成 live。
- 能力报告不得把尚未实现的 live 路径标为 ready；工程配置检查通过与真实 provider 兼容通过分开。

## 7. 必须完成的行为验收

测试按行为设计，不为凑数字镜像实现。至少覆盖：

| 范围 | 必须证明 |
|---|---|
| 冻结与资格 | 缺/错任务字段在创建 Worker 前拒绝；重复 key 不产生第二执行；显式 replay 覆盖拒绝；新旧合同区分 |
| 实际运行 | 新任务在真实 DSH + Concordia 上成功/合法未达成；公开行动交付正确、私有上下文不跨 seat；非法动作不改变世界；partial 不伪装 complete |
| 内部一致性 | 对冻结目标/关系/约束/公开行动/实际 ActionSpec/seat/world 结果做临时不一致变更，即使重算包装 hash，仍被拒绝；原生事实及历史样例不改写 |
| 评估 | 缺上下文零 evaluator 调用；视图仅包含规定信息；结果引用事实；反序 alias、严格原始 envelope、null 错误结果与无自动重试保持 |
| 分组与 campaign | 同族变体/replay 不跨组；去重不丢失败；删登记/少记录/错 source 或 spec/错分母不能通过只读 verifier；零 evaluator 调用独立重算 |
| 标注 | 空模板无分数；合成标签显式标记；正确绑定通过，错 view/rubric/trace/alias、重复冲突、缺标均诚实报告 |
| 费用与版本 | zero-budget preflight 在任何 secret/client/worker 动作前阻断；旧 12 记录有固定 C0 验证路径，新记录对应最终 pins；无 live 调用 |
| 回归与发布 | 运行与修改范围相应的旧输入绑定、SOTOPIA、evaluation、runtime/可靠性/证据回归；干净安装/CLI、core+eval pip check、安装包源码一致和本轮所有受管 Job 退出 |

保留所有失败和修复记录；最终 manifest 区分真实 runtime、受控 fixture、合成标签和仅文档检查。不要把测试中 mock 通过说成 provider/完整上游 evaluator 通过。

## 8. 文档、Gate、推送和停止点

交付 `docs/validation/phase1c1/`，至少包含：合同/复用来源、验收与证据 manifest、Gate/限制、可复制 CLI 使用说明、标注指南/模板、pilot 与 live 配置待确认项。更新根 README 链接，不回写旧阶段统计。

最终分列：

- 工程 Gate：上述绑定和流程通过才是 CONDITIONAL_GO；有关键合同失败则 NO_GO，不能缩小措辞掩盖。
- 人工校准：无真实独立标注时 BLOCKED。
- Live provider：预算 0，BLOCKED。
- 研究效度/演化晋升：BLOCKED，不自动创建 candidate、激活版本或声称能力提高。

完成必要检查后检查 diff 和敏感内容，只 stage 本轮文件，提交并普通 `git push -u origin phase1c1-task-contract-and-calibration`（若已在同任务分支继续则推送实际当前任务分支）。验证 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/<当前分支>` 一致，报告工作树状态。网络/鉴权/远端并发阻塞时保留提交和精确失败，不强推。

最终用中文给出：交付内容、Gate、真实验收/未验收界限、模型请求数、Job 清理、GitHub 分支/提交链接及远端 SHA 核对；链接结果、证据和复现入口。停止在 Phase 1C1，不自动运行 Phase 1C2，不合并 main、不部署。
