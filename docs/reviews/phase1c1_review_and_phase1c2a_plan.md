# Phase 1C1 审阅与 Phase 1C2A 行动方案

审阅日期：2026-10-08。基线：`af0a88cfff23c22c396fd7c9ef9916f0df8cd21f`。本地、远端 `main` 与 `phase1c1-task-contract-and-calibration` 均已核对到该提交，开始时工作树干净。

**维持 Phase 1C1 的 CONDITIONAL_GO，下一轮进入 Phase 1C2A：solver 传输与调用预算的离线准入。** 不继续扩大固定任务卡数量，也不把当前预置分数包装成评估进展。先移除模型输入对预置答案的依赖，复用官方 provider 适配器，通过本地协议服务验证真实 DSH 请求、返回、错误和请求级预算。真实 provider/模型尚未指定，当前费用预算仍为 0。

本轮只交付审阅、[核验记录](phase1c1_review_evidence.json)和[其他 session 执行 Prompt](../prompts/phase1c2a_solver_transport_and_budget.md)。未修改产品、历史证据、依赖或数据库，未执行 C2A。此前 main 发布已完成，本轮按 [AGENTS.md](../../AGENTS.md) 发布独立文档分支；不从历史 main 发布说明推导本轮默认合并授权。

## 1. 核验结论及范围

| 项目 | 本轮结果 |
|---|---|
| 证据绑定 | 739 项文件 hash 比较全部匹配：33 个产品文件、188 个阶段 artifact、8 个当前 suite 的源码/测试绑定、锁文件、工具、准备日志、24 个原始归档及已安装 release 包；包含跨 suite 重复比较 |
| 历史验收 | 8 suites、42 组 PASS 的记录及源码绑定成立；本轮未重新运行整套真实 runtime/恢复/迁移验收 |
| 实际重跑 | input_binding 3、SOTOPIA 3、evaluation 8，共 14 组 PASS，使用当前源码和已安装隔离环境 |
| 当前 campaign | 实际执行只读 verifier，25 登记、10 evidence identity、22 唯一测量请求；计数与 manifest 一致，零 evaluator 调用 |
| 标注 | 实际验证 registry 与 3 个公开 case 一致；空白标签导入正确拒绝，accepted 为空；没有新增人工标签 |
| 旧记录 | 校验已封存 C0 源码副本的 hash 后，以固定 `1e85d8c…` 源码在 `-I -S` 子进程重新复核 12 记录，全部通过 |
| 清理/安装 | 历史交付记录：59 Jobs active=0，core+eval pip check/CLI/安装通过；本轮未重新查询历史 Jobs 或重做安装 |
| 上游查验 | DSH 本地固定 `5badb150…` checkout 干净；GitHub 同 SHA 的 provider README、retry README、mock-server.ts 与本地 LF 规范化后相同 |

本轮未启动 DSH/Concordia runtime，模型请求 0。当前 campaign admitted/rejected/insufficient=15/2/5，valid/invalid/not_run=14/1/7；task_failure/infrastructure_failure=8/2。三轴不能相加；独立研究单位仍为 0。

## 2. Phase 1C1 可以接受的部分

- TaskSpec 的两个固定卡、真实 seat/spec、目标/约束/初始关系在运行前冻结；第二 actor 的观察包含第一 actor 实际公开行动。旧合同没有被放宽成任意任务 DSL。
- `task_result` 按共同可用时间与实际 accept/decline 判定；合法 accept 在 conflict 卡不等于达成。第二步非法不抹去第一步效果，partial 不补第二步分数。
- campaign 完整性相对于冻结 dataset 和明确 inventory 计算；登记、source/spec/view、claim/pointer、去重和状态分母一起核验，historical 不进入当前统计。
- 原 C0 记录由固定版本复核；新实现明确不支持旧 pins。没有重封历史记录或执行记录指定代码。
- 标注接口只交付待标包和绑定检查，不把 `provenance=human` 字符串当成人类真实性证明。人工校准、研究效度与演化保持 BLOCKED。

未发现要求撤销现有 fixture 工程 Gate 的新阻断项。下面一项配置缺陷应在接入阶段先修复；其他列为明确扩展门槛。

## 3. C2R1 / P2：确定性和关闭的角色被要求配置正预算

位置：[preflight.py](../../src/actio/preflight.py) 的 `preflight`（基线第 36–37 行）。当前对 solver、GM、judge、retries、other 一律要求 calls/tokens/cost 大于 0，并要求报价。

本轮构造纯内存配置：solver/judge 用合成正数预算，GM 声明 deterministic-local/common-slot-accept，retries/other 为 0；没有读凭据、建客户端或调用模型。实际结果 `configuration_valid=false`，包含：

```text
gm_zero_budget, gm_price_unconfirmed,
retries_zero_budget, retries_price_unconfirmed,
other_zero_budget, other_price_unconfirmed
```

这与 [pilot 草案](../validation/phase1c1/06_pilot.md) 的“GM 可确定性、不伪造预算、默认不重试”矛盾。目前 live 始终 BLOCKED，没有造成支出；但不能通过为关闭的角色填假预算解决。

下一轮应采用显式角色模式（disabled / deterministic_local / transport_stub / future_live 或同等严格语义）：关闭或本地确定性角色允许且要求相应远端预算为 0，拒绝携带不适用的 provider/secret 配置；只有启用的未来远端角色检查真实报价、授权与正上限。`configuration_valid`、`transport_validated`、`live_authorized`、`live_ready` 分开，不能因为配置齐全就自动解锁。

## 4. 下一个真正的接口断点

| 缺口 | 基线事实 | 对下一步的要求 |
|---|---|---|
| Solver 输入仍有答案 | [scenarios.py](../../src/actio/scenarios.py) `run_engine` 把 `answer` 送到 RuntimePort；[task_contract.py](../../src/actio/task_contract.py) 要求 dispatch 等于 scripted_actions；fixture provider 直接返回 task.answer | 新传输合同的 actor payload 只含角色、实际可见观察、memory 和 ActionSpec；答案只来自响应。旧 fixture 合同保留，不能删旧证据中的字段后称为同一次运行 |
| 官方 adapter 尚未走通 | 现有 RuntimePort 禁用官方 provider、注册自有 fixture | 用真实安装的 `0.1.5rc1` 二进制和官方 adapter 指向本地协议服务；源码只能指路，不能证明该发行物已有相同能力 |
| 请求不等于行动 | 上游 LLM service 也服务 title/compaction；可选 retry 会再次发请求 | 预算计数放到实际 provider attempt 边界；关掉不需要的隐藏调用，以本地服务请求记录核对。不能用两步任务推定恰好两次请求 |
| 无独立预算账本 | C1 preflight 是静态阻断，没有 reserve/settle/unknown 生命周期 | 新的本地实验账本先持久保留调用额度，再允许请求；未知结果不自动退款重试。只验证合成单位，不冒充真实账单 |
| 两个符号动作不足以判断关系 | rubric 已允许人工 cannot_judge，但 controlled score envelope 必须给数字 | C2A 只测 solver 传输和确定性任务结果；不接 live judge，不由达成率推导关系分，不为了评分扩成多轮社会模拟 |

目前 conflict 卡本身不可达成；合法失败不是模型能力差的证据。之后的小型 smoke 也只能证明连接、输出合同与成本记录，不能证明社会效度。

## 5. 优先复用资产

DSH 固定源码：`5badb15009ae1756c3afe0ae0cef1faafc290ccc`。本地根：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\01_deepseek-harness\repo`。

| 资产 | 查验与采用方式 |
|---|---|
| [llm-deepseek](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/llm/llm-deepseek/README.md) | 固定源码支持 Messages-compatible `baseURL`，官方配置不是任意 OpenAI chat-completions。优先验证已安装 adapter 的实际配置与 SSE 映射，不自己重写 provider 协议栈 |
| [本地 mock server](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/llm/llm-deepseek/tests/mock-server.ts) | 已有 SSE、HTTP error、提前断流的测试结构；只拆必要脚本行为/fixture，保留 MIT 来源，服务绑定本机临时端口 |
| [llm-retry](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/llm/llm-retry/README.md) | 固定源码默认 normal 可重试五次；启用与否由 composition 决定。下一轮必须用错误返回测实际次数，不能只看配置声称禁用 |
| 现有 RuntimePort/Job/事实链 | 继续使用官方 SDK 和 DSH loop，经新的版本化 profile/payload 接入；Python 保有任务和预算权威，TS 做最终调用检查，不生成第二个 solver |
| 现有独立 verifier/标签接口 | 扩展必要的 execution_mode/来源和账本绑定，保留旧版复核路径。标注和真实 judge 留待外部输入，不再堆合成评分 |

上述 GitHub/source 查验不证明二进制构建映射，也没有选定用户未来付费 provider。协议路径本轮通过本地服务实测；若官方发行物不支持，保留失败并写最小替代选择，不能静默升级或换框架。

## 6. Phase 1C2A 的有界交付

| 顺序 | 交付 | 停止条件/验收 |
|---|---|---|
| P0 | 修复 C2R1；冻结新输入、角色模式与预算合同；查验复用 seam | 零预算远端入口先于凭据/客户端/Worker 阻断；不执行真实调用 |
| P1 | 原有两个排程卡走新 actor payload，官方 DSH adapter → 本地 SSE 服务 → 官方 SDK 返回 | 捕获实际请求证明无 answer/script/期望结果/对手私有信息；固定返回仅由测试服务控制，明确 transport_stub |
| P2 | 本地请求预算台账：原子 reserve、attempt、settle/unknown 和关联证据 | 重复/并发末额度、崩溃窗口、丢 usage、HTTP/断流/超时均有界；无隐式重试；子进程退出 |
| P3 | 新任务证据与预算/请求捕获的只读核验 | 本地接收次数与 attempt 对账，任务结果仍由冻结约束判定；新模式不能伪装 live/研究样本 |
| P4 | 相关回归、独立旧版核验、CLI/干净安装、新证据与 handoff | 普通提交推送任务分支并核对 SHA；不合并 main、不部署，不扩大到 judge/演化 |

采用一次只跑一个 campaign、受限并发的最小方案即可，不做多供应商网关、UI 或通用计费平台。预算账本只负责这次调用治理，旧任务库不原位迁移。真实费用为 0；本地 HTTP 请求和合成预算使用量另列，不能将它们也写成 0 来掩盖实际测试流量。

## 7. 下一步何时可以真正调用模型

工程准备与测量效度分开排队。C2A 通过后，C2B 可以在另行明确授权后先做 **1–2 个 baseline episode 的真实 solver 连接 smoke**：确定性 GM、无 judge、无工具、无重试，实际 provider/model/数据范围及 calls/tokens/currency/cost caps 在运行前冻结。这个工程 smoke 不必等待社会评分完成人工校准，但也不能产生能力或晋升结论。

随后再处理人工标签、独立 judge、适合目标构念的任务数据和校准 pilot。两步符号任务的 relationship 可以一直是不可判断；不能为了填满表格强行量化。只有测量有效性得到支持后才进入候选配对和演化准入。

当前缺少真实 provider/模型/收费上限和真实标注；执行 Prompt 以预算 0 为硬边界。未来用户需要明确的是：provider/endpoint 协议、精确模型版本、允许发送的合成字段、总 calls/输入输出 tokens/费用与币种、报价时间、超时及失败处理、凭据引用方式。不要在文档或聊天中要求粘贴 secret。

## 8. 下一 session 起点与发布

本轮文档分支 `docs/phase1c1-review-phase1c2a-plan`，基于 `af0a88c…`。从其已核对远端 HEAD 创建 `phase1c2a-solver-transport-and-budget`，记录完整起点 SHA。main 当前已有产品，但从交接分支开工才能同时携带此次审阅要求。

每轮验证后 commit → 普通 push 当前任务分支 → 核对远端 SHA 与本地 HEAD。保留历史失败和用户修改。push 阻塞则报告本地提交与精确原因，不 force push；不自动再推 main。
