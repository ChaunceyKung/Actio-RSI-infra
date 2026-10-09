# 模型选择与证据边界

当前接入只声明 TokenKey 的两个模型路由标签：`gpt-5.6` 为 solver 基线，`claude-sonnet-4-6` 为跨模型候选。二者使用同一官方 pi-ai adapter、512 max_tokens、纯文本 ActionSpec、compatible→conflict 有限计划。temperature/seed/reasoning 不显式请求；GM deterministic，judge 禁用。正式执行逐 seat 的结果、usage、客户端分层耗时见 [结果](02_results.md) 和对应公开 campaign。

这次每个模型只有两个小型合成 episode，未作重复试验、功效分析或独立研究单位认定。客户端 headers/首 token/总时长包含网关路由与网络影响，不能以一次较快响应推断总体速度或质量优势。requested_model/response_model 一致仅证明观测到的标签一致；上游权重身份、模型家族与网关路由混杂均未解除。

## 已有探索的使用方式

下表引用前置 [直接诊断](../../reviews/phase1c2b1_key_check_and_prompt_update.md) 与 [原始脱敏证据](../../reviews/phase1c2b1_tokenkey_evidence.json)。本轮没有重复遍历 109 个目录标识，也没有用直接 API 探针充作 DSH/Concordia 成果。

| 路由标签 | 已有证据 | 当前用途 / 下一步 |
|---|---|---|
| gpt-5.6 | 用户示例；普通与 SSE smoke、两步约束任务均通过 | 固定本轮 solver 基线；本轮 DSH 结果独立记录 |
| claude-sonnet-4-6 | 直接两步约束任务通过 | 验证同一 DSH 合同的跨模型候选，不据小样本排名 |
| gpt-5.6-luna | 直接两步通过，曾有较长单次耗时 | 后续吞吐候选；需独立测量质量、时延、价格 |
| qwen3.8-flash | 直接两步通过，部分 usage 含 reasoning | 后续另一模型族候选；reasoning 不重复叠加到 output |
| deepseek-flash | 直接生成通过，但跨请求 response_model 变化；一次 SSE ReadTimeout | 先隔离路由、参数、期限原因；不作为稳定严格对照 |
| gemini-3.1-pro | 目录可见，该 Chat Completions 路径 HTTP400 unsupported_model | 本协议暂不选；不推广为整个 Gemini 家族或 key 无效 |

前置诊断为 14 次生成尝试、12 个 usage 响应、1 次目录 GET，1 次 unsupported_model、1 次 timeout。它没有 DSH Worker、Concordia episode 或产品 Ledger；费用与正式执行分账保留。过去 JSON 的 request_id 来自正文 id；C2B1 将正文 response_id 与实际 HTTP 请求头 request_id 分开，缺失为 null。

## 后续准入

后续可以预注册更广的固定任务集、重复次数、提示/输出额度、可用 seed/参数、稳定 route/cohort，以及格式、约束、任务结局、usage、时延、成本和不确定性指标。先核实 TokenKey cost 的币种/单位/覆盖及账单，再讨论每成本表现；不能使用官方零售价替代该网关实际价格。

未来 judge 候选仅为角色规划，不在本轮发起 judge 调用。独立人工标注、评估器校准与研究晋升另设 Gate。无金额上限仅使必要实施和有依据的有限诊断可推进，不授权无限探索或重试到满意答案。
