# Codex 执行 Prompt：Phase 1C2C4 可见规则鲁棒性有限真实验证

请实施 **Phase 1C2C4**：将 C2C3 固定诊断集接入已有 DSH/Concordia 真实链路，补齐跨版本评估历史，完成本机验收，首次真实发送前冻结并发布，然后执行一次有限 solver campaign，离线复核并推送任务分支及 **main**。不要只交付设计文件；前置 Gate 不成立时交付精确 NO_GO，保留失败，不强行执行。

项目：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
仓库：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
建议任务分支：`phase1c2c4-visible-rule-robustness`。
C2C3 产品/交付基线：`b50b6da28c25ef34da6a620b2b45a576ead5330f`。
C2C3 实现 reader：`0a66334d61a0de302bbf8f5e15ee1db1b9d2e8fb`，至最终交付产品未变。
C2C2 固定 reader：`3bef7e15b0eb21beeb10888eb508056592b977b0`；最终交付 `6466e2be6f31e0ac5861a379d761d2e7bf39c5eb`。

从包含本 Prompt 的最新 origin/main 开始，记录实际 HEAD、远端、祖先关系与工作树；不重置用户修改。先读 AGENTS.md、README.md、MILESTONES.md、本次审阅 `docs/reviews/phase1c2c3_review_and_c2c4_plan.md` 和证据 JSON，以及 C2C3 CONTRACT / RESULTS / GATES / DEVELOPMENT / CLI / NEXT_EXPERIMENT / manifest / frozen-design / package。再读 C2C2 CONTRACT / CLI / preregistration / report / lineage / decision 和已有执行代码。

## 0. 任务问题、授权与边界

本阶段只回答：在预定的公开限制、自身边界、同分和 options 逆序任务上，原 B0/C1 是否出现可信格式、公开/自身 hard、B 原响应规则的错误，以及本轮观察到哪些行动/展示差异。沿用两个 family 和两步 A→B 信息结构；这是开发集描述性工程验证，不是独立研究、模型排名或能力准入。

用户已有 TokenKey 凭据读取、项目必要真实调用与**无金额上限**授权持续有效，不重复询问首次调用或同一费用许可。新合同显式使用 `uncapped_for_phase1c2c4` 或等价清晰枚举，不用 0、巨大数字或模糊 null 表示无上限。继续保留有限计划、逐请求账务、长度和期限、幂等及清理。

只允许一个 TokenKey `gpt-5.6` route、原 B0/C1、每条件 1 repeat，固定 32 presentations × 2 arms = **64 episodes，最多 128 seat sends**。执行前后不额外做 key smoke、目录 GET、直接 SDK 诊断、模型筛题或第二真实批次；验证 key 的结果已经存在，不重复消耗。没有新候选/搜索/proposer、训练、judge、真人标签、沟通轮次、自动激活或部署。

历史真实生成尝试 139、目录 GET 1 分列，不入新分母。累计只加本轮实际 sent；128 全部发送才可能累计 267。`human_labels=0`、`independent_research_units=0`、`eligible_for_activation=false`。费用币种/单位、账单和上游权重身份未核实；二进制来源映射 unproven、完整 controller 恢复 unsupported，不能由本阶段成功改写。

## 1. 优先复用与新版本接线

复用官方 DSH SDK/runtime `0.1.5rc1`、Windows x64/Python 3.12、官方 pi-ai Chat Completions、现有最终 guard/逐请求账本/受管 Job、真实 Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。不升级 runtime，不替换传输 SDK，不引入新 gateway 或整体 framework fork。

先查：`task_diagnostic_data.py`、`task_diagnostic_policy.py`、`task_diagnostic_analysis.py`、`task_diagnostics.py`、`suite_tasks.py` / `suite_oracle.py`、`evaluation_campaign.py` / `evaluation_tasks.py` / `evaluation_measurement.py` / `evaluation_store.py`、`candidate_evaluation.py`、`database.py` 及 config/host/transport/terminal/verify 的模式分派。公开 CLI 以实际仓库实现为准，不凭本 Prompt 发明可用命令。

现有 v9 仍绑定原 12 卡、24 episodes、12 pairs。`task_diagnostic_data.task()` 只是纯 result 的最小适配，**不是已获准 live 的完整 TaskSpec**。新增显式版本化 config/profile/task/input/plan/campaign/measurement/delivery 及需要的 evaluation policy，使用代码维护的严格版本分派。版本号按实际仓库避免冲突；不能只换 endpoint、扩大旧卡白名单或让 artifact 指定任意 reader/源码。

新的完整 TaskSpec 映射固定诊断 card 的公开/自身条件、角色、ActionSpec、relationships、A→B 顺序，保留原 Persona、空初始 memory、原候选与 B 响应规则。normal/reversed 精确继承 C2C3 的两 seat options 顺序；别重复逆序或另造排序。数据来源、world/group/presentation/arm/candidate/oracle/hash 仅放在外部绑定，不进入 actor 指令或可见上下文。

新分派必须覆盖计划、输入准备、Worker、最终 fetch guard、Ledger、终态、通道审计、独立 measurement、lineage 和 delivery。既有 suite get/card/validate 和 v8/v9 的允许域不扩张；新 runtime 不把 offline 控制策略或 oracle 计算当真实 solver 答案，不允许回退 fixture。

## 2. 固定输入与有限有序计划

继承 C2C3 原 dataset，不新生成选题、不更改数值、不添加演示答案、不按本轮行为筛卡：

| 固定对象 | 内容 SHA256（sealed 对象取 body，其余沿用 canonical digest） |
|---|---|
| C2C3 dataset | `3e37ca1cb71a90f3bef100a1ec4bff4721d584c19c3442ae04de42207630a02a` |
| C2C3 package manifest | `03f8da8e0318d49a77ab2ad6bdd235604c7cdf902881e2577a793ab74e098091` |
| B0 proposal | `84e9ab99465ada9c47cc17334c305a5f493524f042a218d4be4732c054462fe5` |
| C1 proposal | `e381eb3dd58494dde035b7c301331bdc3f5cde8af18c644bf6e7301087a130b2` |
| B0 scaffold | `9b686045d24438d2544378a515d71915dc92b3eda2a59804607f9d88aa69fbb7` |
| C1 scaffold | `1458fb1db9310b9c54a03c72f32f09045293f789a0f93e3ef9e4cad2fad15c95` |

先从现有对象独立重算这些 hash，区分 body hash、文件 bytes hash 和源码 hash；不一致则停止并解释，不修改历史 pins 来匹配。原 B0/C1 及 parent/artifact/静态 policy 都不改，唯一直接 arm 干预仍是 A 原有三个 checklist 词条。

完整列出 8 groups × 2 worlds × 2 presentations × 2 arms 的 64 个 episode、128 个计划 seat slots、32 个 baseline/candidate pair。每 family 4 组，保留组/世界/展示关系。使用调度 seed `20261013` 生成确定性完整顺序，交错 family，pair 内两臂相邻，baseline-first/candidate-first 在每 family 各 8 对；将 world 和 presentation 的排列也明确封存，不以运行结果改变顺序。调度 seed 不是 provider sampling seed，不消除时间漂移与随机性。

固定精确 endpoint `https://api.tokenkey.dev/v1/chat/completions`、route `gpt-5.6`、`max_tokens=512`，temperature/provider sampling seed 继续省略，不主动请求 reasoning。沿用 C2C2 原期限和起算点：ready30、RPC5、headers60、idle60、total90、result115、drain5、close5、Worker165 秒；活动不得延长 total。关闭所有隐式 SDK/transport 重试，禁止 redirect/cross-origin。

封存新 schema、所有 card/options、candidate/scaffold/Persona、runtime/source、参数与期限、初始状态、完整 schedule、claim namespace、metric/pair/grouping/decision policy、stop 条件和历史基线。数据标记为沿用合成诊断开发集，不能因新 live 命名改成 holdout。64/128 是计划上限，合法跳过 B 或技术停止均不补样。

## 3. 评估历史：在 C2C2 v4 副本追加

先用受信固定 C2C2 reader 认证 `D:/actio-c2c2-live-v1/delivery.json` 和关联原库；本机路径以已绑定材料为准，缺失则报告缺口并阻断主 live，不从公开 JSON 伪造权威 Store。历史 C2C3 portable verify 不替代这一步。

现有 `migrate_evaluation_copy` 仅支持 v3→v4；C2C2 的 `D:/actio-c2c2-live-v1/candidates.sqlite` 已是 v4。建立新目录内的一致 SQLite 快照副本，保留原文件、backup/hash、Store identity、六份原 proposal/decision、所有旧事件、C2C1 reference、C2C2 evaluation/binding/plan/policy/decision。读取 source 不修改；不要只文件复制可能有 WAL 的数据库。记录源前后保全和副本一致性。

在副本追加新的 C2C4 evaluation，原 B0/C1 被新 binding 引用，candidate 的旧 decided/claimed 不重置，旧 decision 不覆盖，旧 claim 不删除、不重领。rehearsal 用另一个隔离副本。schema4 足够就沿用；如确需新 schema，显式复制迁移，保存 backup、失败与版本证据，禁止原库就地升级。

当前 evaluation_store 通过 C2C2 模块和当前源码重建计划，必须做最小可信历史分派。旧对象按其固定版本/source 验证，新对象按新冻结合同验证；旧 plan/hash 不被新源码重算结果替换。历史 reader 由代码信任表/固定 Git 版本选择，artifact 只能引用已知版本，不能携带可执行插件。测试旧 C2C2 evaluation 在本轮源码变化后仍能独立核验且字节/语义绑定不变。

主 live lineage 应至少包含三个 evaluations：C2C1 local reference、C2C2 live、C2C4 live；另有两份 evaluation decision：C2C2 和 C2C4 的 C1。原六份 candidate decision 单独保留；B0 仅为参照，不写能力晋升。若执行前 NO_GO，按实际登记状态报告，不能伪造已运行/已决定记录来凑数。

新 evaluation 与项目固定的 C2C4 live-once claim 都必须一次性；改 root、重启进程、重装环境不得获得第二批。并发领用、重复 execute、错误 plan/schema 应被拒绝且无新发送；这些用本机 fixture 验收。JSON 仅为权威 Store 导出；无 active pointer、CAS 激活或 full recovery 宣称。

## 4. 实际输入边界与三类比较

对每个实际请求从固定 TaskSpec 与本臂事实正向重算 observation、prepared 和 full wire。既核验初始投影，也核验官方 runtime 实际发出的内容、顺序、参数与权限。只允许原有的独立 SDK UUID4 message IDs 归一化，并证明这些 ID 不在 full wire；不能用忽略提示差异的大范围清洗制造输入相等。

1. **同 presentation 的两臂**：A 仅 scaffold 改变；B 只用本臂真实 A 行动。实际 A 相同则相应 B wire 相同；实际 A 不同时，去除经过认证的公开历史后，其余 B 指令、own/public、options、参数、权限必须相同。不能拿 baseline A 填 candidate B，也不复制另一臂动作来提高配对率。
2. **同 group/presentation/arm 的两个隐藏世界**：A 的允许输入和实际 wire 相同，B 的 own 随世界改变；对方 private/标签反事实和来源绑定均核验。相同 A 输入可能产生不同随机输出，输出差异是描述性事实，不是泄漏或技术失败。输入相同是 Gate，输出相同不是 Gate。
3. **同 world/arm 的 normal/reversed**：两个 actor 的 ActionSpec options 都按明确映射逆序；公开/自身语义不变。A 若改变行动，B 公开历史同时改变，这是允许的依赖变化。报告完整 32 个展示对照，不将 B 差异都称为自身 option-order effect。可附实际 A 相同的 B 子集，必须标为条件化描述并保留全部分母。

计划 32 展示实际上只有 16 个不同 A 可见视图；加入两臂为 32 种 A 输入条件，经两个隐藏世界出现两次，共 64 个计划 A 调用。不能声称 64 个独立任务。隐藏世界描述性对照为 8×2×2=32 个，展示对照为 16×2=32 个，候选配对为 32 个，分别命名与统计，勿混为一个 pair 总数。

全 wire 不包含 opponent private、oracle/最优答案、候选/组别标签或其派生 hash。私有信息反事实应覆盖两 family、两 seat、两臂和展示；fixture 可改变实际 A 验证 B 正确继承。对持久 memory/领域事实也核验可见性，不仅检查 prompt 字符串。

沿用 raw SSE→adapter→原生文本双通道审计，只有经认证的 content 可成为 action、B public history、world/memory；reasoning 只作协议结构/一致性证据，不进入下游，不用于事后解释行为，不公开正文。空 content、length、未知通道、raw/native 不一致按冻结规则拒绝，不能 live 后放宽或抽取 reasoning 冒充答案。

## 5. 行为、适用性与报告

复用 C2C3 严格 visible view、合法集合、条件得分多解和独立生产/审计两路径。有限真值的 416 合法组合、128 非法/缺失向量与手算例继续支持新映射；不要用同一函数生成和自证 oracle。控制策略可用于 loopback 和错误分支测试，不能混入真实证据或作为新候选。

| 情况 | 执行与技术分类 | 评价处理 |
|---|---|---|
| 可信、语法合法的两个行动 | 核验 raw/native/账本/领域事实后可完整 | 按原规则算 hard、响应、joint、utility 和诊断 |
| 可信非空、语法非法 A | 保留拒绝 receipt，B 以 task_predecessor_invalid 跳过；按合同结束并继续下个 episode | A format=false；B 和依赖前驱的指标 not_applicable，不假造 B 调用 |
| 可信非法 B，或合法但违反公开/自身 hard | 是已观察行为错误，不自动停止 campaign | 保留 format/hard 错误；非法语法的效用等不适用，不补0 |
| 合法拒绝、世界不可行、同分选择 | 按实际规则评价，不当技术故障 | B 必须满足原“恰在条件满足时接受”规则；本应接受却拒绝仍属响应违规 |
| unknown/timeout/身份、输入、通道或文本不一致 | 首个技术失败停止全 campaign | 未认证文本不评行为；保留 missing 和全后缀，不删除失败样本 |

主报告分列 text_verified、format、domain_executable、public/self hard、B response_rule；另列 conditional_argmax 集合成员、conditional_offer_gap、joint、双方 utility、全知上界/regret。标出工程、可见行为、结果、全知诊断及依赖，不合成总分；B local_hard/response_rule 的同一谓词来源、format/domain 相关性不能计作独立证据。

条件得分是“若提案被接受”的自身收益，不含隐藏先验/接受概率，不解释为期望实际效用。argmax 保留全部同分；不将参考策略具体 tie-break 当唯一正确答案；正 gap 不自动成为原 hard 违规。联合可行但未达成、全知 regret>0 本身不证明 A 错误。

每 metric 满足 assigned=eligible+not_applicable、eligible=defined+missing，布尔项 defined=true+false。每个 baseline/candidate pair 只有两臂该指标都 defined 才算 delta，否则 null 并注明 missing/不适用；不以0替代。执行完成配对与逐指标覆盖分列，不因行为错误或技术停止把 pair 从 assigned 删除。顺序/隐藏世界对照使用同样完整分母，但不得与候选 pair 相加形成研究样本量。

报告 group/world/presentation/episode/seat/arm/route 层次，计划、实际 attempted/sent/response/usage/admitted、可信行为非法、protocol_error、unknown、not_run、not_applicable 均可追溯。跨指标分母不假定相同；技术停止后未运行的 suffix 与行为无效前驱跳过分别列明。先固定枚举与恒等式，再用实际事实重算，不强迫某项等于128。

不作模型排名、显著性检验、推广置信区间、稳定位置偏好或因果能力提升结论。单次展示差异只是本轮观察，可能混合采样与时间变化。零差值不证明等效/无效，正差值也不证明可泛化。

## 6. 必要本机验收与首次发送前发布

在调用真实 provider 前完成：

1. 原 dataset/proposal/旧证据 pins 与新 TaskSpec 映射；完整 64 episodes/128 seat slots 的 schedule、分组、来源与仅允许输入；未知版本、漏项、重复项、错 arm/候选/世界绑定拒绝。
2. v4 一致副本、C1/C2 历史保全、C4 注册/一次 claim/决策绑定、重复执行拒绝、source 变化后旧 evaluation 可信复核；只对受控副本操作。
3. **全 64 episodes 的真实 DSH/Concordia loopback rehearsal**，两个 family、所有展示和两臂；正常主矩阵用语法合法 fixture 完成128个 seat slots，实际发送/接收另据日志报告。额外必要行为/技术错误分支独立统计，不能混成主矩阵或真实费用。
4. prepared/full-wire 反事实、B 本臂 A 继承、两通道、合法拒绝/错误拒绝/非法 A 跳 B、timeout/unknown 停止与后缀、清理、只读 guard。历史机制已验的无关长测试不重复跑；新接线与风险分支必须有实际行为验收。
5. 干净安装或明确可复现最小环境，源码与 installed package 一致；真正执行公开 plan/preflight/analyze/verify/lineage 和本机 execute CLI，保留 argv/source/exit/hash。plan/preflight/verify 保持 key/env/network/process/runtime/write guard；会写输出的操作限制到指定新目录，不声称写命令是纯只读。
6. 固定旧 reader 复核 C2C2 及 C2C3 包、旧 proposal/decision/停止点/unknown/claims 保全。源码变化不能通过刷新历史 hashes 来“修复”测试；失败记录绑定当时源码，新最终验收不能引用旧快照冒充。

本机通过后冻结完整预注册和执行实现，连同本机准入证据提交，普通推送任务分支及 main，独立 `ls-remote` 核对两个远端 SHA 与本地，工作树干净、安装源码匹配。记录已提交计划文件、冻结提交、发布核对先于首次 intent/send 的本机证据；不要做自引用 commit hash。若需要包含发布收据，放于受控运行包并绑定已发布提交，不为补收据修改冻结产品。

只有新版专用 execute 在核验上述前提后读取 ignored `.local/credentials/token_key.txt` 并内存注入；缺项目副本时才从已授权 `D:\调研\CausalEngine\api_key\token_key.txt` 复制到忽略目录。不要在聊天/日志/证据中输出密钥、前缀、长度或哈希；不将 key 发给其他 origin。

静态或 runtime Gate 不成立，先修复并重新完成受影响的本机验收与冻结；始终0真实调用。无法在本阶段成立则交付 NO_GO。首次真实调用后发现冻结合同需修改，应停止并作为后续阶段问题，不在同一批中修合同、补冻结、换模型或再跑。

## 7. 一次真实执行、停止、账务与清理

建立新的 Windows 短路径受控 root，隔离各 episode 的 home/session/Ledger/Store/authority。沿冻结顺序串行运行 A→B、两臂，不并发增大范围。claim 与计划双重限制最多128发送；第一次实际发送消耗本阶段唯一批次资格，输出目录变化不恢复资格。已 claimed 的意外退出也不能偷偷清除 claim 续跑。

首个完整 arm block 只检查证据完整性与清理，不依据效果重新筛卡；后续每个 unit 按合同核验。首个技术 unknown/timeout、协议/文本/身份/输入绑定冲突停止全 campaign，完整登记剩余 not_run。可信行为错误继续并按前驱语义跳过 B，无答案修复、retry、补样、第二批、key smoke 或外部诊断调用。

异常时优先保存计划、entries、pilot、账本清单、实际 prefix、未知状态及完整 suffix，再尝试 verifier；verifier 失败另存明确缺口，不删除原错误，不把 controller 中断标为完整恢复。离线 reconcile 不能把 unknown 仅凭推测改成未发送或零费用。

逐请求保留发送尝试、实际 HTTP/响应/usage 可信度、raw cost 原值及来源。未知币种/单位和账单仍 UNVERIFIED，不从模型名或 route 断言上游身份，不估算无依据 USD，不用0填未知费用。计划范围有限与金额 uncapped 可以同时成立。

本机开发批次（含失败/诊断）、正式 rehearsal、正式 live 和历史139/目录GET1分列，避免只公布最终成功批次。所有实际创建的具名 Job、Worker、服务、端口和发送状态有清单；结束后验证 inactive/reaped、join、无残留监听、无活动 authority/reservation/sending。历史 unknown 与永久 claim 保留；没有本轮对象则如实说明，不拿历史清理数充数。

## 8. 独立离线核验、Gate 与交付

受信 verifier 从固定输入、raw/adapter/native、领域事实、账本、完整计划和谱系重算报告；报告不能自证。固定源码版本/版本白名单，无任意代码加载。完整受控 delivery 保存在本地，不公开 raw reasoning、密钥、数据库或巨大原始日志；Git 仅发布脱敏事实、行动、manifest、来源与必要审计摘要。若提供可移植包，明确内部重算与受控 raw 来源认证两种范围。

Gate 分列 dataset/task admission、runtime/wire integrity、history preservation、channel/measurement、denominator、cleanup、publication，另报告行为约束与推断边界。决策优先级固定：

- 静态不合法：reject/no send；不重新解释旧六份 proposal/decision。
- 技术证据不完整：本 evaluation 为 infrastructure_failure，保留已观察行为事实；不把缺失当通过。
- 技术完整且 C1 有已观察格式或原公开/自身 hard（含原 B 响应规则）违反：reject，仅限本开发集约束。
- 其余：insufficient_evidence，无论正负/零 delta；没有 capability pass，`eligible_for_activation=false`。

baseline 的错误单列，不写其晋升决定。C2C2 和更早决策保持不变。研究有效性 UNESTABLISHED，真人校准/judge/能力晋升/生产激活保持未解锁。工程结果可以 PASS、停止或 NO_GO，不能把真实行为全通过当成研究有效性。

交付 `docs/validation/phase1c2c4/` 的 CONTRACT、preregistration、RESULTS、GATES、CLI、DEVELOPMENT、evidence_manifest，必要版本映射、逐 seat/指标/配对与三类比较报告、评估谱系/决策、实际 argv/源码绑定验收、冻结发布与清理证据。新增文件按项目风格命名，但链接和公开命令必须真实可用。README 更新当前入口/状态，保留整体项目介绍；MILESTONES 顶部追加实际完成或停止事实，不覆盖历史。

全部验证后提交，普通 push 任务分支，安全合入并普通 push main，独立核对两个远端 SHA 与本地一致和工作树干净；有并发先读取/整合/验证，不 force push、不覆盖无关修改。推送授权已明确，无需再次确认。发布前做精确凭据及敏感材料扫描。网络失败有限正常重试，保留本地提交并准确说明未发布，禁止关闭 TLS 校验或声称成功。

最终中文报告：冻结与最终提交、各 Gate、实际计划/发送/完成/配对分母、行为违规与适用性、候选/展示/隐藏世界三类描述、历史加实际累计、费用/来源限制、失败与清理、测试及 CLI 范围、RESULTS/manifest/CLI 和远端核对结果。

**停止于 C2C4。** 若出现可信可见规则错误，后续先定位具体条件；若继续零违规/零差值，保留开发观测并另设计信息获取/期望效用合同，不为寻找候选正收益重跑本批。不自动启动 C2C5、候选搜索、研究晋升或下一批真实调用。
