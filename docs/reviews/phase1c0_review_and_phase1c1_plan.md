# Phase 1C0 审阅与 Phase 1C1 行动方案

审阅日期：2026-10-08。产品基线：`1e85d8c2fb4a756de81acb333905190df9e97592`，分支 `phase1c0-offline-measurement`。

**维持 CONDITIONAL_GO（仅离线工程），进入 Phase 1C1：任务合同与校准就绪。** 本次审阅未发现要求撤销当前 Gate 的新阻断项；C0R1 的冻结输入绑定缺口可以按原定义关闭。下一步应把“固定 cooperate 的流水线”推进到“有目标、约束与可判定结果的最小社会任务”，为真实评估准备数据和标注接口。当前证据仍不支持社会能力、测量效度或演化晋升。

本轮交付审阅、[核验记录](phase1c0_review_evidence.json)和[下一 session 的执行 Prompt](../prompts/phase1c1_task_contract_and_calibration_readiness.md)。未修改产品代码、历史证据、依赖或数据库，未运行 Phase 1C1。按 [AGENTS.md](../../AGENTS.md) 提交并推送本轮文档分支；不合并 main。

## 1. 本轮核实了什么

| 核实项 | 结果与证据边界 |
|---|---|
| Git 基线 | 本地及远端产品分支 SHA 一致；初始工作树干净；远端 main 仍为 `fad04fcf0d14ded6684d54dc0633f4ee213276f3` |
| 文件绑定 | 428 项 hash 比较均匹配，包含 29 个产品文件、146 个阶段 artifact、当前 suite/相关测试/原始归档、工具、锁文件、准备日志与已安装 eval 包；428 包含跨 suite 重复检查，不是 428 个不同文件 |
| 历史验收 | 7 个当前 suite 共 35 组 PASS，suite JSON 与相关源码/测试绑定一致；没有重跑全部 runtime/恢复/迁移测试 |
| 本轮实际重跑 | 当前源码下 input_binding 3、SOTOPIA 3、evaluation 8，共 14 组通过；使用已有隔离 eval 环境，未安装依赖，未启动 DSH 或 Concordia runtime |
| 记录独立复核 | 12 个当前记录全部通过当前 `verify_record`；另重算 14 项登记的 dataset→entry→source→spec→record 关联、aliases、cluster 和计数，均一致 |
| 上游复用 | `extract_sotopia.py --check` 从固定只读 checkout 重建 11 个定义通过；另读取 GitHub 固定 SHA 的 profile/schema 和数据集注册表，与本地 LF 规范化后相同 |
| 清理与安装 | 已交付的 clean-install/CLI/core+eval pip check 记录为 PASS，28 个受管 Job 的历史清理记录均 active=0；本轮没有重新枚举这些 Job 或再次做干净安装 |
| 费用 | 本轮模型请求 0；只发生 GitHub 只读访问、离线测试及文档交付 |

统计复核：14 registrations、10 unique evidence、12 unique measurements；admitted/rejected/insufficient 为 7/2/3；valid/invalid/not_run 为 6/1/5；task_failure/infrastructure_failure 为 1/2。这些是不同轴，不能相加当总样本数。**独立研究单位仍为 0**。其中 controlled_response 只有两个 admitted synthetic 请求，一条合法、一条非法；不是两次真实 judge 实验。

## 2. 可以保留的实现选择

1. `terminal.validate_inputs` 同时用于在线终态和离线核验，检查冻结角色、调度、观察策略、memory 与完整 ActionSpec。12 种重算 hash 的内部矛盾被拒绝；真实 Engine 中 B 一次、A 两次同值观察的历史保持原样。
2. admission、task outcome、measurement status 分离；缺上下文/partial 不调用 evaluator，合法拒绝保留 task_failure，非法响应不修成零分或有效分数。
3. evaluator 接收白名单 view，原始严格类型检查先于上游 parser；alias 按冻结 seat 明确绑定，不按返回顺序猜身份。
4. SOTOPIA 的实际 parser/schema 复用成立；完整 EpisodeLLMEvaluator 的兼容性失败及身份重排问题被如实保留，继续不采用整套 evaluator/平台。
5. 不可变记录、无覆盖发布、request claim 与超时后不自动重试适合当前离线切片。hash 和 audit 只能支持内部一致性及本地执行观察，不能冒充签名或外部执行证明。

这些判断限于已读代码和上述验收范围，并非穷尽审计。

## 3. 进入下一阶段前必须理解的缺口

| 编号 | 当前边界及代码位置 | 下一阶段处理 |
|---|---|---|
| C1D1 任务语义缺失 | [scenarios.py](../../src/actio/scenarios.py) 的 `social_manifest/run_engine` 固定 cooperate/wait，没有冻结目标、初始关系和真正的任务结果判据；[evaluation.py](../../src/actio/evaluation.py) 的 `prepare` 正确地拒绝给旧 social 包做 controlled 社会评分 | 新建版本化任务合同，在运行前冻结；用新 run 产证据，不倒填旧包 |
| C1D2 研究单位尚未建立 | 当前 cluster 是起点内容的工程分组，campaign 明确 independent_units=0 | 定义 scenario family、变体、episode、repeat/replay、arm 的关系；实现按 family 分组的开发/校准准备清单，仍不声称统计独立或封闭 holdout |
| C1D3 校准与调用未准入 | preset response 只验证数据流；没有人工标签、live solver 或独立 judge | 交付盲化标注导出/导入、人工校准方案和可执行的零预算 preflight；真实标注与模型调用分别保留 BLOCKED |
| C1D4 版本可复核边界 | [eval_contract.py](../../src/actio/eval_contract.py) 的 `pins/validate_spec` 要求记录匹配当前精确源码；正常改代码也会使旧 EvalSpec 不再被当前实现接受 | 新旧版本显式区分；提供固定 C0 SHA 的离线复核路径，或经过验收的窄兼容实现。不得删除 pins 检查、重封旧记录或动态执行包内代码 |
| C1D5 campaign 审计入口 | 当前 `campaign` 是执行/生成入口；`verify-record` 不等于完整 campaign 核验。本次完整关联检查由审阅脚本完成 | 提供不启动 evaluator 的离线 campaign verifier，验证清单完备性、归属、分组、统计分母和重复处理 |

C1D1–C1D5 是扩展门槛，不登记成 Phase 1C0 承诺未兑现的缺陷。尤其 C1D4 已在 C0 文档明确披露，不能把当前版本可复核误写为跨任意版本可复核。

## 4. 复用方向不变，数据另行审查

| 资产 | 本轮确认与下一轮复用 |
|---|---|
| DSH SDK/session、受管 Worker | 保留官方 `0.1.5rc1`、短路径和现有 RuntimePort；只扩展 fixture 输入，继续由 DSH loop 执行，不另写 solver loop |
| Concordia Sequential/Entity/ActionSpec | 保留 `b71d202750e23444ce1bf28d9f114bcd88aa41db`；扩展现有外部 Entity/GM adapter，验证公开行动到下一 actor 观察的交付；不重造调度器 |
| SOTOPIA task/profile 字段 | 固定 [persistent_profile.py](https://github.com/sotopia-lab/sotopia/blob/a0aaafb440e570e5e61b7c44a44e5e417c545383/sotopia/database/persistent_profile.py) 已有 scenario、agent_goals、relationship、background_story。借鉴这些语义，与现有严格 parser/schema 组合；不导入 Redis/provider 闭包 |
| SOTOPIA 示例/数据 | `tests/envs/test_background.json` 的 scenario 是 `<missing_info>`，不能直接当完整任务；[published_datasets.json](https://github.com/sotopia-lab/sotopia/blob/a0aaafb440e570e5e61b7c44a44e5e417c545383/sotopia/cli/install/published_datasets.json) 登记 SOTOPIA 数据为 CC-BY-SA 4.0、另一数据集为 AI2 Impact License。登记表不是最终许可批准，采用具体数据还需核对数据卡、revision、再分发条件 |
| Raven / Strands / Letta | 本轮不扩大接入。评估尚未校准，不启动 Raven 晋升；G0 主路径未失败，不触发 Strands；不增加第二状态权威 |

下一轮只做针对新任务的窄复用查验。优先使用现有字段、schema 和 fixture 机制；若没有可直接使用且许可明确的完整小样例，可编写两个明确标注 Actio authored fixture 的任务卡。不能声称这是 SOTOPIA benchmark，不能下载整套数据库来绕过缺字段。

## 5. Phase 1C1 的具体交付

**一个任务族、两个任务卡、两个 seat、固定两步。** 推荐成人邻里共同排程：每个 seat 有自己的时间约束与目标，初始关系明确，先行动者提出时间，后行动者收到公开行动后响应；结果由双方约束和实际行动决定。两个卡用于覆盖可达成/冲突条件，不代表两个独立研究样本。

| 顺序 | 要做的工作 | 可检查的完成标准 |
|---|---|---|
| P0 合同与复用决策 | 冻结 TaskSpec、可见性、合法动作、终止/成功/失败条件、任务来源；明确 schema 与旧证据兼容策略 | 数据许可/来源逐项登记；缺目标/关系/约束或错身份在创建 run/worker 前拒绝 |
| P1 真实运行切片 | 新合同经现有 DSH 和真实 Concordia 执行；记录 TaskSpec hash、起点、每步可见观察、实际 ActionSpec、公开行动和领域结果 | 成功、合法但未达成、非法动作拒绝、部分失败均有诚实结果；在线终态和离线 verifier 共用语义检查；preset 输出不进入 judge view |
| P2 数据与测量联结 | 新完整包的目标/关系来自冻结输入，领域结果来自事实；保留确定性指标与 controlled response 两类测量 | 新包可测量；旧包缺上下文仍 insufficient；单次证据、repeat/replay、不同 arm 不重复计为独立样本 |
| P3 标注与 campaign 复核 | 导出可读的盲化任务包和结构化标签模板；实现标签导入及只读 campaign verifier | 标签绑定 task/trace/rubric/view/alias/split；缺标/分歧保留；默认没有人工分数；零 evaluator 调用即可复核完整清单与计数 |
| P4 live 准备 | 预注册未来 pilot：provider/model、judge 独立性、预算分项、失败率口径、样本/重复方案、停止条件；实现只读配置 preflight | 当前返回 BLOCKED，且在读取凭据/构造客户端/启动 Worker 前停止。方案是建议，不是支出授权 |
| P5 交付 | 新证据、相关回归、干净安装与 CLI smoke、进程清理、文档、普通 Git push 和远端 SHA 校验 | 本轮工程 Gate 与人工/live Gate 分列，停止于 Phase 1C1，不自动演化/激活/合并 |

受管运行放在新隔离数据库/短根，Phase 1C0 的原证据和 fixture 入口保留。无需提前做数据库迁移、多环境平台、自由多轮对话或通用任务 DSL。新合同若能存入已有 manifest 和不可变 artifact，就继续使用这两者。

## 6. Gate 与后续顺序

- Phase 1C1 工程 Gate：合同→实际运行→事实→只读测量/标注导出完整绑定，负例可靠拒绝，所有相关验收通过，可为 CONDITIONAL_GO。
- 人工校准 Gate：没有真实独立标注时为 BLOCKED；不能让执行 Codex 填一批分数并称为人工 gold。
- Live Gate：预算仍为 0，provider/model/judge 配置和授权未完成时为 BLOCKED；不能因 GitHub push 获授权就推定模型费用获授权。
- 研究/演化 Gate：继续 BLOCKED。公开 fixture、同族变体、replay 和合成标签没有封闭 holdout 或统计准入意义。

后续 Phase 1C2 才在单独确认配置与预算后开展小规模真实 solver/judge、人工对照和 pilot；根据结果冻结正式评估方案。再之后接单 seat 候选、配对评估与 lineage。不要用更多 fixture 分数绕开测量效度，也无需等待原生 resume/fork 全面开放才完成上述离线切片。

## 7. 发布和下个 session 起点

本轮分支：`docs/phase1c0-review-phase1c1-plan`，基于上述 C0 产品 SHA。下一 session 从该文档分支的**已核对远端 HEAD**创建 `phase1c1-task-contract-and-calibration`，并将解析出的完整起点 SHA 写入新的证据 manifest。不要从只含旧规划的 main 开始。

每轮验证后提交并普通推送当前任务分支到 origin，核对 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/<branch>` 一致。若无法 push，报告本地提交与精确阻塞，不宣称已交付到 GitHub，不 force push。
