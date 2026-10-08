# Phase 1C0 实现与验收

Gate：**CONDITIONAL_GO**，仅准入离线测量工程。预算 0，全部输入为 synthetic fixtures；预置社会分数不证明 judge 效度或 agent 能力。当前结论与命令/hash 见 [独立 manifest](evidence_manifest.json)。

## 输入证据

`terminal.validate_inputs` 同时供在线 seal/finish 与离线 verifier 使用。检查真实角色、B→A 的 action 顺序、必需 memory/observations、own-only policy、完整实际 ActionSpec 和固定环境合同。在线还核对 native accepted task 与 dispatch；离线从清单校验后的同一读取快照获得数据，避免验证后重新打开 evidence 的时序缺口。

原 social manifest 的两字段 ActionSpec 按已固定 v1 adapter 展开 `output_type=choice, tag=null`；新运行显式冻结四字段，删除必需字段失败。固定 Engine 每步先向所有实体送观察，因此 B 行动时为一条、A 为两条相同私有观察。当前证据证明的是行动时的实际输入及其次数/顺序符合固定规则，不证明独立观察交付时间或未行动实体的完整观察历史。

两项审阅反例以及错角色、缺字段、错类型/options/tag、另一实体观察、GM 全量输入、错 policy，共 12 类重算 hash 反例均失败；原 native raw 完全不变，且删除可选旧报告，排除“只比较 stored report”的伪通过。五个原包重新核验为 assistant/social complete+success，rejected complete+task_failure，partial/unknown partial+infrastructure_failure。历史文件原样保留。

bundle format 仍为 `actio-evidence/1`。当前 verifier 为 `actio-verifier.2 / fixture-input.v2`。旧 verification.json 仍受原清单 hash/字节数保护，仅作历史报告；当前结论独立重算。新增字段不构成原包损坏，真正的旧报告/metadata hash 损坏仍失败。

## 测量边界

EvalSpec、EvaluationInput、EvaluationRecord 和 campaign 均使用既有 safe-integer canonical JSON/hash。只开放两个固定本地 evaluator，没有任意代码/宿主文件引用插件。spec 冻结 metrics/rubrics、范围、方向、上下文、代码/依赖/上游 pins、view、错误策略、预算、deadline、dataset hash 与 synthetic split。未实现的范围或 parser 修改明确拒绝；受支持 revision 或数据变化生成新 key，不能复用旧结果。

admission、task_outcome、measurement 三轴分离。封装/事实矛盾拒绝；partial、active、legacy、缺上下文为 insufficient；这些路径 evaluator_calls=0。完整合法拒绝保留 task_failure，并统计非法 action 被正确拦截，未行动 A 没有伪造分数。合法受控输入的非法响应为 invalid_measurement；异常、缺 optional dependency 为 measurement_error；deadline 单列 timeout；都保留 null 结果和诊断，不自动重试。

alias 按冻结 seat 排序产生 `agent_N`，绑定实际 agent/role，与 B→A 行动顺序和 JSON 插入顺序无关。支持单人助手及最多 8 个显式 synthetic seats；三人 parser 回归和反序 alias 不串人。非准入但身份可核验的输入也在 request/campaign 中冻结身份。

view 仅含必要 ordered actions、合法 options、最小 domain/world/tool-result 事实及 occurrence/receipt refs。forced fixture `answer`、private observation/GM/memory、旧 scores 和 candidate 标记不进入 evaluator。actual received view hash 与 EvaluationInput 比较。无静默截断，超限明确拒绝。

助手指标检查真实 native tool-result 的单一成功与 reference 标识；社会指标分报实际动作数、合法数、GM resolved 数、非法行动在 world 前被拒绝数。它们是 fixture 合同指标，不是社会能力评分。原社会包缺 goals/初始关系，controlled spec 对它返回 insufficient。独立封存 synthetic input 才经过真实 SOTOPIA parser 的 goal/relationship 结构路径。

记录包含可迁移的源包文本快照、必要 source/content/manifest、spec/campaign/view/alias/pins、原始响应 hash、三轴结果、来源与调用数。离线 verify-record 重算源准入、输入和确定性/严格 envelope 结果，不调用 evaluator、不依赖作者 DB/目录或 optional packages。hash 不认证作者或 parser 执行；异常/审计计数是本地执行记录。exact source pins 不支持的早期 C0 记录仍保留作历史，当前报告明确选定最终 pins。

写入先 exclusive claim，再写入 fsync 的临时文件，以同目录 hardlink 原子发布、不覆盖已有 inode；request 指针绑定最终 record。同请求读取原结果；未完成 claim 不自动重跑。CLI 在文件读取的硬字节边界之外返回结构化请求错误；已准入执行的无效响应/内部错误保存 EvaluationRecord。没有任意 evaluator 插件、provider 或重试选优逻辑。

## 当前 campaign

当前 [报告](campaign/reports/8f58df3b4b00d583130797981ec7c8c808446a1991b430f353d2324b1ed0b5e3.json) 与 [dataset](campaign/datasets/7843afb624ca1b783b90b87822fb85efdd82985889a8463225a88837719ea9af.json) 包含全部登记。早期报告为中间实现 pins，未覆盖或删除。

| 计数 | 当前值 | 分母/含义 |
|---|---:|---|
| 登记 | 14 | 包含同包重复、同 run 改 export metadata |
| 唯一证据输入 | 10 | 9 个 evidence 身份（含两项矛盾变体）+ 1 个 synthetic input |
| 唯一测量请求 | 12 | 同证据不同 spec/response 分开；两项重复不重评 |
| admitted / rejected / insufficient | 7 / 2 / 3 | 分母 12 |
| valid / invalid / not_run | 6 / 1 / 5 | 分母 12；不以缺失填零 |
| task_failure / infrastructure_failure | 1 / 2 | 分母 12，与准入/测量轴可重叠 |
| measurement_error / timeout | 0 / 0 | campaign 分母 12；独立故障测试另有保留记录 |
| 独立研究样本 | 0 | 所有 split 都是 synthetic engineering fixture |

deterministic：9 个唯一请求，5 个准入且有结果。其中助手 reference 指标适用 1 个完整助手；social constraints 指标适用 4 个完整社会 episode（含合法拒绝、实际起点 replay）。controlled_response：3 个请求，历史社会缺 goals 的 1 个不准入，synthetic 的 2 个准入，其中有效 1 个、无效 1 个；有效结构只有 2 位 synthetic agent 的各两维预置分数，不是研究观测。所有未准入和无效输出都在登记表中。

真实 `c0-social` 与 `c0-replay` 使用新身份 C0_NORTH/C0_SOUTH、真实 DSH/Concordia、不同 run/native session；冻结起点 cluster 相同。保留两个记录，不作为两个独立样本。

## 实测

| suite | 聚合行为组 | 实际边界 |
|---|---:|---|
| input_binding | 3 | 12 类反例、五包新结论、旧清单损坏 |
| sotopia | 3 | 原定义 parser/schema、context/repair/coercion、完整 evaluator 失败刻画 |
| evaluation | 8 | 准入零调用、两个指标、严格错误谱、幂等、异常/真进程 deadline、portable 标准库、audit hook 真拒绝 |
| runtime | 2 | 原真实双场景/replay/privacy、同 host 两 turn |
| reliability | 7 | 原 seal、首步后故障、replay、执行资格和目标恢复 |
| evidence | 7 | 原真实导出、重算 hash 矛盾、快照、只读与 portable |
| schema | 5 | 原旧库/迁移副本/中断及 incompatible pins |

共 35 组行为验收，不是样本量。另有新 runtime CLI smoke、干净 eval-only install、公开 spec/run/verify-record/campaign 和 core+eval `pip check`。原 runtime 回归绑定所有未变核心文件；随后仅调整评估 alias 元数据与 builder 复制，最终 eval suites 绑定最终全部产品代码。无需因此重跑无关的原故障/竞争套件。

worker 是有 deadline 的一次性隔离 Python 子进程；安装 audit hook 后才导入 optional seam。网络、子进程、runtime/Redis/provider 导入和写入被拒绝，测试真实触发前三类拒绝；正常评估记录各计数为 0。eval-only 环境根本未安装 DSH/Concordia/Redis/litellm/openai。`-I -S` portable record 验证无原目录和 optional 依赖仍通过。缺 optional dependency 的受控路径明确记录 PackageNotFoundError，标准库 verifier 仍可用。

本阶段所有独立测试尝试均保留。上游 nested shape/身份/history 失败、受控非法响应和内部异常/超时是预期负例，未改写为成功。首个 delivery 收集器误将构建生成的 egg-info 当产品文件，检查失败；收集范围修正为 src/actio 后重新验收通过，原失败记录保留。最终检查 28 个登记 Job 均 active=0，12 个当前 campaign 记录全部离线复核通过。

原 Phase 1A/B/B.1 证据、41 wheel lock 与 Concordia pin 不变。完整 raw/源码中间归档和 bootstrap 日志只留 ignored 本地，hash 登记在 manifest；公开 Git 仅合成包、必要日志摘要和小型 JSON 记录。
