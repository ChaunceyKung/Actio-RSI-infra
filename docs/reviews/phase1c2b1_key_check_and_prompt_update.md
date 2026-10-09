# Phase 1C2B1：TokenKey 实测与执行 Prompt 修订

日期：2026-10-09（Asia/Shanghai）。文档起点：`d98591acbad61fbe67adc596e35b11c2e6c429a7`；产品仍为 C2B0 基线 `f65045a11d1a4728b98b5564623e4827365f91c8`。

**API key 可用，用户给出的 TokenKey / gpt-5.6 组合已真实返回内容。** 已将指定 key 文件复制到项目的 `.local/credentials/token_key.txt`，该路径被 Git 忽略且未跟踪。没有输出密钥、片段或密钥摘要。

下一 session 使用 [修订后的完整 Prompt](../prompts/phase1c2b1_gated_solver_smoke.md)。[脱敏证据 JSON](phase1c2b1_tokenkey_evidence.json) 收录模型目录、每次已观察的结果、失败、usage 和源码参考；本轮只做直接 API 诊断及文档修订，**未实现或运行 C2B1 的 DSH/Concordia live 闭环**。

## 用户授权与实际改动

用户最新要求“api key 不设置预算上限，以推进项目为准”，随后指定凭据来源、`https://api.tokenkey.dev/v1` 和 `gpt-5.6` 示例。这覆盖前轮“先准备，首次调用再确认”的约束，已在 AGENTS.md 与新 Prompt 写明。必要的 key 验证、solver 基线和有依据的诊断无需重复请求同一费用授权。

Prompt 要求下一 session 新增显式 uncapped 模式，保留使用量与未知费用记账、请求级长度/超时、有限批次、幂等和进程清理。旧 limited 模式和历史证据保持原义；不以极大整数、0 或含义不明的 null 模拟无上限。缺少精确计费输入上界或最新单价，不应再次成为已授权 uncapped 模式的全局发送阻塞。

**当前修改的是执行要求，尚未修改现有产品的预算实现。** 未设置或改变 TokenKey 账户侧限额、余额、权限或充值；账户余额不足等仍可能成为供应商侧限制。judge、人工校准、训练/演化、研究晋升与部署继续由各自阶段决定。

## Key 与协议实测

调用目标均为用户明确指定的 `https://api.tokenkey.dev`，使用正常 TLS，禁用重定向、环境代理和自动重试。只有合成场景/短提示发送给网关，未发送本地项目文档或他人私有数据。

| 检查 | 结果 | 能证明的范围 |
|---|---|---|
| 鉴权与 GET /v1/models | 成功，109 个模型标识 | 该 key 可以访问模型目录；不保证所有列出的模型都能调用 |
| gpt-5.6，普通 Chat Completions | 返回 OK，finish=stop，usage 11 输入 / 5 输出 | 用户示例的 key、base URL、模型与 max_tokens 参数可用 |
| gpt-5.6，流式 Chat Completions | HTTP 200，OK，stop，4 个 SSE 事件，1 个 DONE，有 usage | 直接网关流式协议可用；尚非 DSH adapter 验证 |
| deepseek-flash，流式诊断 | 45.969 秒后 ReadTimeout；未取得响应头状态 | 该次参数组合失败；是否已被上游执行和收费未知 |

普通 smoke 使用 `max_tokens=64`；流式诊断使用 `max_tokens=128`、`stream_options.include_usage=true`。DeepSeek 流式额外传入 `thinking.type=disabled`，本轮未分离模型路由、参数兼容和服务时序各自的影响，不能归因为“DeepSeek 不支持流式”。

## 六个模型的约束任务探索

采用同一小型合成冲突场景：A 只能参加下午，输出提议；B 只能参加上午，接收 **A 的真实行动** 后输出接受/拒绝。每个 seat 单次调用，要求仅返回 `{"action":"..."}`。每请求 `max_tokens=256`，不显式设置 temperature、seed 或 reasoning；B 只在 A 的输出可解析且 stop 时运行。

| 请求模型 | 发送尝试 / 成功生成 | 严格 JSON / 约束正确 | A+B 耗时 | 建议 |
|---|---:|---:|---:|---|
| gpt-5.6 | 2 / 2 | 2 / 2 | 9.422 秒 | 首个 solver 基线，另有普通/流式 smoke 支持 |
| claude-sonnet-4-6 | 2 / 2 | 2 / 2 | 3.328 秒 | 首个跨模型对照候选 |
| gpt-5.6-luna | 2 / 2 | 2 / 2 | 15.860 秒 | 后续轻量模型/吞吐候选，实际价格与性能需测量 |
| qwen3.8-flash | 2 / 2 | 2 / 2 | 6.313 秒 | 另一模型族候选，注意 reasoning usage |
| deepseek-flash | 2 / 2 | 2 / 2 | 6.906 秒 | 先查明返回标识变化及流式超时，再作严格对照 |
| gemini-3.1-pro | 1 / 0 | 0 / 0 | 0.782 秒（仅失败 A） | 此 Chat Completions 路径返回 unsupported_model，B 未运行 |

JSON/约束两列各自为通过次数，不是质量分数。模型探针最多两个模型并发，各模型内部 A→B 顺序执行。耗时是单次客户端观察，未控制负载或缓存；没有统计效力，不能据此认定某模型整体最快、最便宜或最擅长社交推理。

`deepseek-flash` 两次响应的 model 分别是 `deepseek-v4.1-flash` 和 `deepseek-v4-flash-ga-260731`。这是**响应模型标签变化**的事实，尚不能证明底层权重确实不同。正式实验必须保存 requested/response model，明确 route/cohort；不能把不同标识静默汇总成稳定型号。

`gemini-3.1-pro` 列表可见，但实际 HTTP 400，code=`unsupported_model`、type=`invalid_request_error`。仅该协议/模型组合未通过，不等于整个 Gemini 家族或 key 无效。

推荐先固定 `gpt-5.6` 完成 compatible、conflict 两个真实闭环，再以 `claude-sonnet-4-6` 验证同一合同。未来选 judge 需要独立校准，不能因为本次格式正确就宣称评估器有效。其余模型按明确假设补测，无需逐个调用目录中的 109 个标识。

## 请求与费用核算

| 类别 | 本轮数量 |
|---|---:|
| 模型目录 GET | 1 |
| 普通凭据 smoke 生成尝试 / 完成 | 1 / 1 |
| 六模型约束探针生成尝试 / 完成 | 11 / 10 |
| 流式诊断生成尝试 / 完成 | 2 / 1 |
| **生成尝试 / 成功生成** | **14 / 12** |
| **TokenKey HTTP 尝试（包括目录）** | **15** |
| HTTP 400 / ReadTimeout | 1 / 1 |
| 自动重试 | 0 |
| DSH Worker / Concordia episode / judge / 独立研究单位 | 0 / 0 / 0 / 0 |

12 个完成响应均含 usage，报告值合计为 **1,362 输入 token、364 输出 token、1,726 total token**。这是网关报告值的机械汇总，未验证所有模型的 tokenizer、reasoning/cache 子字段口径；不要再把 reasoning 加到已经包含它的输出总数里。失败/超时的 usage 和费用保持未知。

只有 **5 / 12** 个完成响应包含 `usage.cost`。脱敏证据保留原始数值，未验证其币种、单位及覆盖范围，**没有将其合计为 USD 账单**，也没有把缺失 cost 或失败请求补零。供应商实际接收数、账户扣款和账单均未独立核对。

本轮直接 API 探针没有产品账本，不能声称已由 C2B0 Ledger 结算。保留这组诊断的独立计数，下一 session 新账本须关联它作为前置诊断，不能重写历史阶段“当时真实调用为 0”的证据。

本轮无本机 HTTP 服务、无 DSH 受管 Job；诊断客户端均关闭，模型比较线程池已回收。未重新执行全部 C2B0 产品验收，也未将既有历史 Job 清理数计成本轮成果。

## 复用调查对下一步的影响

查询固定 DSH 源码 `183f08e9c6dde7e36cd2318eaee70b0da08fb35e`（`dsh-v0.1.5-rc.1`），找到官方 `@deepseek-ai/dsh-llm-pi-ai` 包。它支持手工声明的 OpenAI-compatible gateway，可设置 `api=openai-completions`、`baseURL`、`apiKeyEnv` 和有限模型目录。下一 session 应优先验证这条官方路径。

已读取并记录 hash 的来源：

- [llm-pi-ai package.json](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm-pi-ai/package.json)
- [llm-pi-ai README](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm-pi-ai/README.md)
- [sdk-minimal composition](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/bundle/sdk-minimal/cordis.patch.yml)

README 默认 retryPolicy 可重试五次，省略 apiKeyEnv 可能走环境凭据发现；这些都必须显式配置。sdk-minimal 默认选择 llm-deepseek。**源码存在不证明当前发行物能加载 pi-ai**；先以 fake key/loopback 检验 loader、依赖、实际 route 与发送守卫，然后才进入真实调用。缺包时评估同版本官方包/依赖闭包，避免再次陷入只改配置却未验证加载的问题。

新供应商身份为 TokenKey，不能把 GPT/Claude 调用标记成 `deepseek-official`，不能拿 DeepSeek 直连零售价当 TokenKey 实际账单，也不能以 Python OpenAI SDK 探针取代 DSH 生产 solver 后宣称架构完成。

OpenAI 官方 [GPT-5.6 Sol 模型页](https://developers.openai.com/api/docs/models/gpt-5.6-sol) 将 `gpt-5.6` 列为该模型别名，支持 Chat Completions 与 streaming；这仅描述官方服务，**不认证 TokenKey 的上游模型身份**。[Chat Completions 参考](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) 推荐 max_completion_tokens，包含可见输出及 reasoning；TokenKey 在本轮接受用户示例的 max_tokens。下一 session 需按 adapter 实际 wire/模型兼容验证，不机械替换字段。

## 证据边界与交付

脱敏 JSON 内嵌本轮 observations 及模型目录，可离线重算上表；保留本机来源文件 hash。比较任务的共同 system 指令和用户 payload 均已记录。流式探针只保存汇总、内容和 usage，没有完整 SSE 字节归档，因此尚不能进行独立的逐字节协议重放。

早期探针中的 `request_id` 字段来自响应正文的 `id`，不是 HTTP 请求头。JSON 的字段说明明确这一点；后续产品合同应区分 response_id 与 HTTP request_id，缺失的字段保持 null。

历史 C2B0 审阅与批准包保持原样。其“首次调用待确认”“预算 0/1 USD”是当时约束，由本次新授权和 Prompt 覆盖，不能再拿来阻塞当前范围。

本轮交付仅包含 AGENTS.md、执行 Prompt、本审阅报告和脱敏证据；不改变产品源码、测试、依赖或历史 validation。完成文档/JSON 校验、密钥扫描与 Git 检查后，普通提交并推送 main，核对远端 SHA。目标 Gate 是 **KEY_AND_DIRECT_API_OK；DSH_LIVE_INTEGRATION_NOT_RUN**，不是 C2B1 已完成。
