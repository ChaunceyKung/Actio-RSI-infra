# Codex 执行 Prompt：Phase 1C2C5 供应商流错误诊断与本机故障验收

请实施 **Phase 1C2C5**：交付可运行的、版本化的错误观察与诊断能力，以固定官方DSH和真实Concordia路径上的本机故障注入验证“错误不成为行动、未知费用不变成零、停止证据可交付”，并形成未来完整分块试验的只读计划草案。完成验证后提交并普通推送任务分支及 **main**，独立核对远端SHA。不要只交付设计文件。

项目：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
仓库：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
建议分支：`phase1c2c5-stream-failure-diagnostics`。
C2C4最终基线：`70fce468a229d82f7de1f697b2619a95f8503f4b`；冻结reader：`3750954ea7cc8dff64115039e27bb671fa618d01`。从包含本Prompt的最新origin/main开始，记录实际HEAD、祖先关系、远端和工作树；不覆盖无关修改。

先读AGENTS.md、README、MILESTONES、本次审阅 `docs/reviews/phase1c2c4_review_and_c2c5_plan.md` / `phase1c2c4_review_evidence.json`，以及 C4 CONTRACT / RESULTS / GATES / CLI / DEVELOPMENT / manifest / stop / freeze / local-acceptance / controlled-delivery / report / lineage / decision / comparisons。本Prompt的计划不是已执行事实；自行核对后实施。

## 0. 本阶段范围与已授权事项

本阶段新增真实模型/provider请求、目录GET、外部MCP调用均 **0**；可启动必要的受管本机DSH Worker、Concordia及literal loopback服务，只用内存假凭据。不要读取真实key做模型smoke，不访问TokenKey，不启动C4 live、不补齐95个not_run、不换模型、不建第二真实批次。

这不是恢复零预算或撤销用户无金额上限授权。已有TokenKey项目必要调用与费用授权仍有效；零外部调用是本阶段为解决确定工程问题所选范围，不请求重复费用许可。独立发布扫描可在本机内存读ignored凭据作精确排除，但不可输出密钥、前缀、长度或hash，更不可发送至任何origin。

保留C4：64/128计划、33 sent/response、32 usage/admitted、unknown1、not_run95、16完整episodes、8完整候选pairs、hidden/presentation完整各0。C1为infrastructure_failure、activation=false；历史累计生成172、目录GET1另计。无新candidate/proposer/search、judge、人工标签、训练、部署、晋升、active pointer或controller恢复能力。

完成定义：错误观察可从已绑定证据重算；本机官方链路实测代表性错误与成功对照；失败不准入、账务不伪结算、无重试、停止后缀与清理可验证；旧C4事实精确保留；新包/CLI可核验；未来分块计划仅生成与检查、不执行；代码与文档发布至main。

## 1. 先核对真实停止原因，不把错误流当兼容成功

用固定C4 reader认证受控 `D:/actio-c2c4-live-v1/delivery.json`，只读核对关联v4 `candidates.sqlite` 与导出lineage，读取前后hash相同。受控材料缺失时允许实施合成部分，但历史来源Gate标BLOCKED/public_projection_only，不能宣称完成真实raw认证。不得按artifact的路径或schema动态执行任意源码。

本次审阅已观察到以下结构，需独立复核或保留差异：ep-16的A为第33次发送，HTTP200，raw三帧：普通chunk；data.error(type=api_error)；event:error加data.error(type=upstream_error, code=upstream_stream_truncated)。无DONE、无raw usage；官方adapter为usage(0/0/0)及finish.kind=error、failure.code=PI_AI_ERROR。旧text audit拒绝unsupported SSE field，旧账务原因missing/extra DONE，unknown保持。

中转错误标签仅证明“响应中声明了该错误”，不证明实际上游身份、故障责任、可重试性或账单。response.error=null仅是transport异常字段为空。adapter的0 usage不是可信raw消耗。只移除event行也仍缺DONE，不能承诺支持该字段后就完成旧请求。

旧C4停止点、计数、verdict、usage=null、报告、decision、claims一律不改。新增sidecar引用原attempt、冻结commit、raw/adapter/native证据hash和旧结果，同时提供新版观察；不是重评分、结算、恢复或新evaluation。公开只保留结构、受限错误标识和摘要，不复制error.message、raw reasoning、HTTP秘密、请求全文或数据库。

## 2. 复用边界与实现位置

先查 `channel_audit.py`、`stream_audit.strict_json`、`candidate_measurement.classify/facts`、`gateway_contract.trusted_usage`、`budget.Ledger.finish/verify_snapshot`、`transport.TransportPort.submit`、`plugins/transport.mjs`、`pilot.run_unit/execute`、`robustness.verify` 和现有TaskSpec/独立oracle。复用 `tests/gateway_stub.py` / `chat_stub.py`、`test_candidate.py` 的双通道用例、`test_robustness_runtime.py` 的真实A历史/前驱/停止库存/清理机制。

固定Windows x64/Python3.12、官方DSH SDK/runtime0.1.5rc1、官方pi-ai Chat Completions、Concordia固定来源与既有Worker管理。不升级runtime、不替换官方parser/serializer、不引入新gateway、不整体fork框架。

可读 `../../codebase/01_deepseek-harness/repo/packages/llm/llm-pi-ai/src/stream.ts` 与相应测试核对error→usage/finish映射；本次参考checkout为 `5badb15009ae1756c3afe0ae0cef1faafc290ccc`，读取时记录实际版本、hash与许可。它只是参考源码，不能宣称等于当前二进制构建；真正兼容性依赖本机固定发行物实测。

新增最小独立纯模块及CLI，例如failure_observation/transport_diagnostics，具体命名按仓库风格。不要改写旧v1/v2成功审计的允许域、输出或旧版本分派。失败观察是附加视图，不能为成功audit绕过严格性；如需把观察挂到新运行结果，使用新schema/明确新版本入口，旧对象用旧reader，新对象用代码维护的可信分派。

注意现有implementation()扫描全部产品源码：即使只添加模块，也会改变“当前源码生成的C4计划”。不能刷新历史preregistration/pins来让旧包迁就新实现。创建代码选择的固定C4 reader闭包（Git归档/可信白名单与source hash），在只读guard下复核原包；不得让artifact提供脚本。C2C2/C3旧reader仍保留。当前evaluation_history只固定C2C2，别宣称已天然支持任意新evaluation。本阶段不新建评估和权威Store，不因增加诊断强行迁移schema或再实现通用历史框架。

## 3. 冻结多层失败观察合同

实现前提交设计合同；正式故障矩阵前封存用例、断言、版本、上限和工具源码。开发探针、失败、修复及时间顺序单列，不能事后声称完全盲化。新schema名称可定为 `transport-failure-observation.v1`，至少包含以下独立层次与证据绑定：

| 层次 | 需要表达的事实 |
|---|---|
| identity/source | config与reader版本、attempt/operation/seat、实际request/raw/adapter/native内容hash和归档来源；跨attempt错配必须失败 |
| transport | 是否记录sending、HTTP状态、捕获异常、deadline触发/原生代码、结束/截断证据及可观测性 |
| protocol | bytes与UTF-8一致性、帧边界、event名、data类型、DONE/finish/usage是否存在及顺序/冲突 |
| provider-declared error | 有无结构化error对象、类型/code允许值、出现顺序与来源；未知type可按严格结构表示未分类，不推测原因 |
| adapter/native | usage与finish.kind/failure.code、native终态、有无content前缀及一致性；仅事实，不从默认usage构造可信用量 |
| admission/domain | 原成功审计verdict、是否存在可信完整行动、是否实际准入/产生领域receipt；识别错误不增加准入 |
| accounting | 原账本状态、raw/adapter/native usage是否可核验、实际账单状态；unknown与费用未知保留 |

不要把这些压成一个会掩盖信号的reason字符串。可给主分类及并存signals，明确证据强度、缺失、矛盾与优先级。结构化error与adapter error一致可标 `provider_error_observed`；这不表示success、可靠上游归因、无需付费或已修复。不支持/不完整/损坏/矛盾证据继续拒绝或unclassified，不能以“检测到error”掩盖错误绑定。

分类器不得按error.message的自由文本关键词决定timeout、rate_limit、无费用或自动重试；使用实际HTTP、代码字段、已记录deadline/native事件。官方adapter本身可能从message映射PI_AI_ERROR等，报告其来源，不把它升级为独立原生事实。message只留受控归档；公开type/code需限定形状和长度，任意未知原文不进入公开报告。

错误流中出现usage时仍单独核验来源与一致性，不由诊断层决定settlement或清空已核验usage。对于本次C4缺raw usage情形，adapter零值不能被计为可信0、released或settled。账单永远不能由解析器认证。发现现有账务与错误结构不一致时报告精确缺口，必要修复限于新本机合同并保留旧语义，不顺带开放live计费或新重试政策。

## 4. 严格的负面协议读取与证据完整性

窄复用已有strict JSON、size/chunk limits、sealed hash和只读guard。负面观察可理解event/data/comment帧结构，但不成为新的通用生产SSE解析器，也不扩大成功profile。明确并测试：CRLF/LF、分段UTF-8、有限multiline data和空帧的处理边界；不支持项显式标记，不能静默丢弃。

所有输入有字节/帧/深度/字段/长度上界，JSON重复key、非有限值、无效UTF-8/base64、身份冲突和错attempt绑定拒绝。event字段与data.error都要保留，不能只看event:error，也不能把普通content中提到“error”或注释当错误对象。对比structured data和官方adapter/native：数据说error但adapter说success、相反情况、error后又有成功finish/DONE、重复terminal、末尾多余内容应报告矛盾或拒绝，绝不优先挑成功部分。

有效content前缀之后遇错误，不能取前缀完成行动；补DONE/usage、去error帧、重写finish、从reasoning提取答案均禁止。原始与合成不同来源分列。对历史真实响应只做受控只读回顾；本机服务使用人工构造、保持结构的合成替身，不复制原error.message/IDs/私有原文。fixture不得查询key或外网。

新版包须绑定原始证据hash、解析器/合同/fixture实现、expected与observed各自来源。公开portable包只含可重算合成输入及脱敏历史摘要；它验证自身结构与合成逻辑，不冒充对C4原始来源重新认证。artifact数据可引用已知reader，不授予执行权。

## 5. 有限本机故障矩阵

不要重跑C4完整64/128正常主矩阵。用现有run_unit、官方adapter、Ledger、TaskSpec与真实Concordia作窄适配，在新的本机诊断root/命名空间运行必要场景，调用者只接受literal loopback与内存假凭据，明确拒绝外部origin、真实credential_ref和live标志。不得把新本机结果登记成C4的历史执行或候选能力评估。

正式runtime矩阵固定为下列9个场景，正常路径合计最多12次本机发送；如有必要额外一项针对修改部分的超时/清理测试，先写入合同，**正式矩阵总上限16次loopback sends**。纯解析器恶意向量不启动Worker。若实现需要不同最小映射，应在正式验收前记录原因与完整上限，不能临时无限扩跑；所有开发/失败发送另外保留累计。

| 场景 | 预定发送上限 | 必须观察 |
|---|---:|---|
| 排期正常text成功对照 | 2 | 原成功audit与可信usage准入，A→B真实历史正确 |
| 议价text+reasoning正常对照 | 2 | 双通道一致，只有content进入world/memory，reasoning不传播 |
| C4结构替身：普通chunk、两个error对象、无DONE/usage | 1 | 原audit拒绝；新观察报结构化错误；unknown保留；B无发送 |
| 无event字段，只有data.error | 1 | 仍观察供应商声明错误，不误称未知event是唯一原因 |
| content前缀后error | 1 | 无完整行动/领域准入，前缀不进入B或memory |
| A正常、B返回结构化error | 2 | B使用实际A；保留已完成A事实，不伪造最终world结果或回滚成未发生 |
| HTTP429的有限错误body | 1 | HTTP错误与SSE解析分别处理，停止无重试，账务不猜0 |
| HTTP503的有限错误body | 1 | 同上，不自动换route/backoff重发 |
| 没有error对象的中途截断 | 1 | incomplete/unclassified，不能伪造成明确provider error |

与旧期限相同：ready30/RPC5/headers60/idle60/total90/result115/drain5/close5/Worker165及原起算点，活动不延长total。保持SDK自动retry关闭和一次fetch guard。本机HTTP status/error替身不需要外部model catalog或模型请求。

每场景自身遇到预期技术错误要停止该场景、保留未运行后缀，不能自动重试；诊断套件可按预先列明顺序进入下一个独立fixture，这是故障验收，不是让真实campaign忽略失败继续。明确scenario与suite两个层次，报告每层expected/observed/PASS/FAIL，不把“出现预期失败”称solver成功。

runtime证据必须来自真实官方adapter返回，不用手写adapter/native chunks冒充实测；纯分类器向量可以显式合成，两者分列。核验收发/usage来源/unknown/operation/domain/memory、Worker退出、服务join、端口及无活动sending/authority。对A和B失败各自保留完整计划slots与not_run，不把技术失败计作行为违规。

纯函数向量另覆盖：正常内容中的error字样、comment/无害frame、错误标签缺失或未知、重复error、error后DONE、先成功后error、假0 usage、有usage但finish不符、raw/adapter/native矛盾、native缺失、伪造deadline、字节/身份/摘要篡改、资源上限和未知schema。按行为等价类选择最小数量，不追求测试数。

## 6. 停止交付、扫描与历史兼容

先保存attempt、原Ledger、raw/native路径清单、停止位置、完整未运行后缀和清理状态，再做可复算导出及敏感材料扫描。诊断本身失败须保留原失败、诊断失败和精确缺口，不以新版reason覆盖原异常，也不丢失provider/adapter的多层证据。

C4曾在完成128次本机发送后被7200秒包装器终止于扫描，缺一份join收据；保持历史事实。新本机驱动用try/finally及时结束Worker/服务，记录扫描范围、进度及实际文件清单，生成材料与只读依赖缓存区分。不能通过跳过实际生成的日志/DB/native材料来声称凭据扫描通过，也不必反复扫描未变化的整个依赖缓存。扫描未完成则scan/export Gate为INCOMPLETE，保留已落盘运行证据；不因扫描失败自动重跑模型路径，不宣称完整controller恢复。

给出只读CLI，例如plan/analyze/verify和一个明确local-only run；名称以实现为准。plan/analyze/verify须guard实测不读key/env、不联网、不import runtime、不启动子进程、不写文件。历史固定reader的启动是外层受信review harness行为，与内部纯reader guard分开记录。会写包的export/run仅向指定新目录写，已有目录拒绝覆盖。

验证完整C4结果、v4原库与19个登记claim前后不变；旧C2C2/C3数据与raw reader继续使用原固定源码。C5不修改已发布validation目录、旧pins、olddecision或once-only标志，也不创建新candidate evaluation来表示故障分类完成。新模块改变当前产品hash时，明确记录旧包需固定reader，而非用新源码刷新旧hash。

已发布C4十项验收绑定产品版本，但部分测试/启动工具是不同历史快照。新的最终验收必须准确绑定实际运行的产品与工具；若修改测试或harness，只对受影响项重新验证并列出复用范围，不把旧快照改标成最终源码PASS，不无理由重跑所有长矩阵。

## 7. 未来分块计划：只读生成，不执行

用C3原32展示和原B0/C1，生成一个新版本的未来顺序提案。卡内容、信息结构、候选、route、参数、原约束指标不变；只调整调度，明确这也是合同变化。选择理由来自前缀对照覆盖，不来自C4两对正负delta或错误卡，不能筛选已成功/未运行卡。

固定seed `20261014`，每个family的4个结构组作确定性shuffle，再将两个family各一个组组成4个macro blocks。每组包含2world×2presentation×2arm=8 episodes；每块16 episodes/32席位。块内按完整candidate pair交错family，同pair两臂相邻；world/presentation顺序在设计中明确一次封存，每family总baseline-first/candidate-first各8对，组内亦尽量平衡。保留所有64 units和128slots及原32/32/32三类关系。

每完成16-episode块，候选、隐藏世界、展示对照应分别新增8个；全64后各32。不执行这个计划、不领live claim、不为它新建evaluation，不将其日期/seed视为未来预约。为0..64每个前缀计算三类完整对照数，输出旧/新完整曲线与关键切点，测试不丢卡/重复、来源/arm绑定、pair邻接和平衡。曲线假定所列前缀都成功完成，不能伪装实际测量或成功概率。

原C4前16完整episode的8/0/0、首次hidden对照需17、首次展示对照需21保留；新顺序不保证任意短前缀都更好。说明块内时间相关与分组聚集取舍，独立研究单位仍0；不将改善覆盖等同因果识别或提高provider可靠性。

在NEXT_EXPERIMENT中只写一个后续决策草案：先审阅C5分类与故障验收；若再做真实验证，另冻结新合同/evaluation/claim、按新完整计划发布后运行，不接续C4缺失后缀、不合并新旧数据作单一campaign。原无金额上限授权仍有效；本阶段不自动启动下一次provider请求。

## 8. Gate、交付和发布

分列：historical_source_authentication、failure_observation_integrity、success_admission_unchanged、accounting_nonfabrication、runtime_fault_matrix、stop_evidence_and_cleanup、offline_portability、future_schedule_integrity、publication。故障被准确识别可为诊断工程PASS，但provider_availability=NOT_RETESTED、C4=INCOMPLETE、C1旧decision=infrastructure_failure、研究UNESTABLISHED、activation=false。

若错误结构不能与实际adapter/native一致解释，保留BLOCKED/PARTIAL和原始证据；不要扩张成功合同、延长期限、重试或调用真实模型来替代诊断。成本币种/单位/账单和上游权重身份仍UNVERIFIED，binary_source_mapping=unproven，full_controller_recovery=unsupported。

交付 `docs/validation/phase1c2c5/` 的CONTRACT、RESULTS、GATES、CLI、DEVELOPMENT、NEXT_EXPERIMENT、evidence_manifest，错误sidecar/字段来源表、合成fixture与预期、runtime实测与各分母、纯解析器拒绝用例、历史认证、停止/清理/导出扫描收据，以及未来分块计划和前缀覆盖曲线。CLI必须实际执行，最小安装或干净环境源码一致；独立verifier可移址重算合成包，明确历史raw认证边界。不要只增加文档或把未经核验的provider message直接写成根因。

README维持项目整体入口，只更新当前进展、限制和使用方法；MILESTONES追加实际阶段完成/停止事实，保留旧记录。不要用新阶段诊断PASS覆盖C4实际INCOMPLETE。

每轮完成并验证后提交并普通push任务分支，安全合入main并普通push origin/main，独立核对两远端SHA与本地一致、工作树干净。无分叉优先快进；有并发读取、整合并验证，不force push、不覆盖无关修改。发布授权持续适用，无需再询问。扫描精确凭据及raw reasoning等敏感材料，禁止提交缓存、venv、数据库、大raw或秘密。网络失败有限正常重试，保留本地提交并报告精确未发布状态，不关闭TLS验证、不虚报成功。

最终中文报告给出：C4停止原因的结构证据与不能推断的部分、新诊断/失败准入/账务关系、实际本机矩阵与失败/清理分母、各Gate、纯测试/CLI/历史认证范围、未来顺序覆盖改进及限制、真实新增0/历史172/目录GET1、最终提交与远端核对、RESULTS/manifest/CLI链接。**停止于C2C5，不执行未来live计划。**
