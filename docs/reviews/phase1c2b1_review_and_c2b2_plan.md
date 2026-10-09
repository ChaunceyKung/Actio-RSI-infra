# Phase 1C2B1 审阅与 Phase 1C2B2 行动方案

日期：2026-10-09（Asia/Shanghai）。审阅基线：`1e00535408e3a3dd12356dbb2cdf934134fb68e4`。本地 main、远端 main 和 `phase1c2b1-gated-solver-smoke` 已核对一致。

**维持 C2B1 已限定的工程 CONDITIONAL_GO；下一阶段建议 Phase 1C2B2：测量完整性修复＋预注册工程 pilot。** 不应把供应商账单和上游身份未证实变成整个项目的无限等待，也不应直接用当前两个场景的 task_success 给模型排名或做演化晋升。正式测量前，先补本次已确认的两处语义边界。

入口：[完整执行 Prompt](../prompts/phase1c2b2_measurement_integrity_and_pilot.md) · [本次审阅证据](phase1c2b1_review_evidence.json)。本轮仅审阅、离线检查和规划，没有产品代码改动，也没有新增模型调用。

## 已独立核对的内容

| 项目 | 本次核对结果 | 边界 |
|---|---|---|
| 版本与文件 | 51 个阶段 artifact、43 个产品文件、26 个测试、40 个工具、4 个入口、3 个锁文件匹配 | 同时核对工作区和已提交 Git 字节；entry 使用 manifest 已列出的本机/Git hash |
| 安装一致性 | runtime/release 两套各 43 个产品文件匹配 | 未重装、未升级 SDK |
| 已发表验收 | 当前 16 suites / 75 组的成功记录与源码/测试绑定一致；17 次 suite 执行历史仍在 | 本轮没有重跑全部 75 组 |
| 原始证据 | 49 个 ZIP、5,042 个成员、12,782,056 bytes 匹配 | ZIP 与每个成员逐一 hash |
| 准备与旧版本 | 6 个准备日志、2 个源码/工具快照匹配；650 个历史保护文件未变 | 不重新封存历史证据 |
| 账本普查 | 88 个 SQLite 只读重算，数据库前后字节未变 | live sending=8、usage=8、输入4,100/输出40，cost 字段2 |
| 本机接收 | 86 个 service 记录重算152次，另有 loader probe 1次，共153次 | 9个零接收服务无 receives.json，与其零计数一致；不是新增请求 |
| 公开 campaign | GPT、Claude 两份都通过原 reader | 子进程禁止网络、进程创建、runtime import、写入、key读取及 env访问 |
| 纯 plan | 两个模型 plan 通过相同零副作用约束 | 不读取凭据、启动 Worker 或发请求 |
| 新附加文本检查 | 8条真实记录的 raw文本与adapter最终文本均一致；原reader绑定到native action | 本轮新增离线语义检查，不能说旧reader已自动包含此检查 |
| 清理 | 215个登记命名Job均无活动进程；87个端口无监听 | 未按PID终止进程；未启动新Worker |

C2B1 的确是固定官方 pi-ai adapter → DSH → Concordia 的真实闭环；不再需要反复证明插件存在或重新搭建 provider stack。两模型各完成 compatible/conflict，8次发送全部 settled，无新增unknown，支持现有工程结论。

本轮复核器有三次可见执行问题，均发生于审阅工具而非产品：旧v3配置没有顶层mode；零接收服务未生成receives.json；Windows子进程默认编码与父进程UTF-8不符。分别按既有旧版语义、明确零接收事实和显式 `-X utf8` 修正后通过。失败摘要进入新审阅证据，没有重跑模型或修改原始文件。

## B2R1：离线核验未闭合 raw文本到原生行动的语义链

位置：[gateway_contract.py](../../src/actio/gateway_contract.py) 的 `trusted_usage`（基线第73行起），[transport_campaign.py](../../src/actio/transport_campaign.py) 的 `analyze`（第54行附近）。

旧核验检查原始SSE的usage/finish/id/model，并比较adapter最终文本与native answer；**没有比较 raw SSE 的 delta.content 与adapter文本**。本次在内存副本中改变第一段非空raw文本、同步更新重复审计事实和结构hash后，原usage核验、bundle与campaign分析仍接受。原件、原manifest、原账本均未修改。

这是内部一致性核验缺口，不是“hash无法证明供应商真实性”这一已声明边界的同义复述：已有不同层级记录之间的文本矛盾应当被拒绝。新测量不应依赖尚未闭合的证据链。

重要限制：原8条实测记录重新逐条提取raw文本后，与adapter/native行动全部相符，**没有证据说明已发表行动被改写或实测无效**。下一阶段应新增严格、有限协议范围的审计检查和行为反例，并给旧记录追加只读sidecar，而不是修改历史报告或替换官方生产translator。

## B2R2：完整任务hash进入actor，破坏隐藏变量不变性

位置：[task_contract.py](../../src/actio/task_contract.py) 的 `actor_observation`（基线第78–81行）。

在固定A身份/spec/自身约束、公开内容和行动历史时，只改变B私有可用时间，A可见观察仍有一个字段变化：`task_hash`。它来自包含双方私有状态的完整TaskSpec。本次没有发现对手私有明文进入actor，也不声称hash被模型解码；问题是**隐藏信息变化会改变模型输入**，后续反事实实验无法将差异单独归因于允许的可见干预。

下一版本应将全任务hash保留在Control Plane/Ledger的外部绑定中，模型侧仅保留允许视图及必要的视图hash。对完整prepared/wire做隐藏状态变动测试；不仅观察字段，还要审查op/task/spec/memory标识、场景名和group标签。身份与实际输入绑定继续保留，不能通过删除所有审计信息来“修复”。

## 另外两项测量设计缺口

**当前task_failure表示共同目标未达成，不等于actor错误。** 本次独立按集合约束复算GPT样例：

| 场景 | A自身约束 | B本地回应 | 共同时间是否可行 | 既有领域结局 |
|---|---|---|---|---|
| compatible | 遵守 | 正确接受 | 可行 | success |
| conflict | 遵守 | 正确拒绝 | 不可行 | task_failure |

Claude观察也是相同行动组合。下一阶段需要独立指标：格式、A自身约束、B按自己信息回应、joint_feasible、共同结果、证据完整性。评估器不能把全知信息当成actor已知信息，也不能为提高“达成率”奖励接受不可用时间。领域原结局保持；另增测量层。

**当前计划只覆盖固定两场景，尚不适合完整实验分母。** `gateway_contract.validate`（第39行）只允许compatible或compatible→conflict；Ledger在episode开始时才注册，未启动的后续episode通过execution结果另记。C2B1范围内已披露，但更广pilot必须在调用前枚举全部planned units，并验证计划→实际→not_run完整对应；仅从“已注册attempt”聚合会漏掉未启动单位。

## 为什么下一步不只做TokenKey账单调查

本轮对 [TokenKey公开站点](https://tokenkey.dev/) 的无鉴权抓取得到HTTP200，但页面只是前端入口；搜索和静态内容没有取得可引用的cost币种、单位、账单映射或稳定上游路由证明。API根地址在浏览工具中不可达，不代表已验证的Chat Completions服务失效，也不证明供应商不存在相关文档。

应继续有限查证公开说明、可见文档与已明确只读来源；记录provider claim、quote、raw cost、estimated cost、billed cost及其证据等级。2/8的cost返回覆盖不支持完整USD账单，标签相同不证明上游权重。

但用户已明确无金额上限。费用未知只阻止按成本排名/账单结论；上游身份未知只限制结论为TokenKey route在特定时段的观察。独立确定性测量、输入隔离、任务矩阵与solver工程pilot可以继续，不能再等待一个无法保证获得的“绝对身份或计费上界证明”。

本轮真实模型新增请求、凭据API请求、本机HTTP、DSH Worker和evaluator调用均为0；公开网页/搜索与Git访问另计。密钥仅在交付前用于本地精确内容扫描，不发出认证请求。

## C2B2具体行动方案

1. **修复与版本化**：B2R1文本语义链、B2R2模型可见性；新增task/config/measurement版本，保留旧reader。
2. **实现独立测量**：从冻结约束与实际行动重算基本谓词，复用source_bundle/seal/只读reader，用独立真值表验收。无live judge、无伪造真人标签。
3. **建立完整预注册计划**：4个A/B可用时间参数实例 × 2个选项顺序呈现 × 2个模型 × 2次重复，共32 episodes、最多64次seat发送。模型交错，初始memory固定，B依赖A真实输出。
4. **先发布后调用**：实现/本机检查/任务/指标/运行顺序/停止规则冻结，提交并推送main后再做首次pilot调用。该步骤不新增费用确认。
5. **完成有限工程pilot**：按计划执行，保留全部错误/not_run；不得重试到满意、看到分数后改计划或补样到显著。诊断另有版本/前驱/原因。
6. **结果与下阶段**：描述性分维度报告和相关性分组，发布结果/manifest/CLI与Gate，停止于C2B2。C2C再推进有来源、更多样且有区分度的任务与独立校准，再连接单seat候选/谱系。

这里64次是预定工程设计上界，**不是新增金额预算**。最多只有4个参数实例、2类镜像结构和1个任务family；重复、呈现变体、两模型配对与消息数不创造独立研究单位。保持independent_research_units=0，不做显著性排名或推广性区间。小任务满分也只说明这个有限矩阵通过，需要更丰富任务才能研究社会行为或演化收益。

## 当前Gate与交付边界

| Gate | 审阅结论 |
|---|---|
| 已完成的C2B1固定工程闭环 | CONDITIONAL_GO，原样例与计数通过本次复核 |
| 新正式测量准入 | 先补B2R1/B2R2和独立指标/完整计划；暂不直接放行 |
| C2B2预注册工程pilot | 推荐下一session实施；明确无金额上限，任务与停止点有限 |
| 账单/上游模型身份 | UNVERIFIED，不能伪造为已确认 |
| judge/真人校准/正式研究/演化晋升 | 继续BLOCKED |
| binary_source_mapping / full_controller_recovery | unproven / unsupported，不在本轮顺带扩建 |

本轮只新增本报告、审阅证据和C2B2执行Prompt；产品、依赖、旧validation/manifest、AGENTS.md和C2B1 Prompt保持原样。按用户持续交付要求，检查后commit并普通push main，核对远端SHA和工作树。
