# Phase 1C2A.1 Gate

**CONDITIONAL_GO：仅固定 Windows x64 / DSH 0.1.5rc1 的本机纯文本 transport_stub 工程准入。** 官方 Chat Completions 成功流、无预置答案双 seat、发送前持久预算、异常保守占额、并发最后额度及离线 campaign 对账均已实测通过。结果与失败见 [02_results.md](02_results.md)，最终来源与计数见 [evidence_manifest.json](evidence_manifest.json)。

| Gate | 状态 | 边界 |
|---|---|---|
| transport_stub | CONDITIONAL_GO | literal loopback、固定纯文本 profile、两 seat/两步、合成计划与价格 |
| live provider | BLOCKED | 无真实费用授权、真实 tokenizer/报价/账单硬上界证明 |
| 人工校准 | BLOCKED | 没有真实标签与校准数据；旧盲化模板不等于已校准 |
| live judge | BLOCKED | 只保留既有离线 deterministic/controlled-response；新 transport 对 controlled-response 为 insufficient |
| 研究效度 / 演化晋升 | BLOCKED | 合成 stub 没有模型推理能力证据，独立研究单位为 0 |

`pilot-config.v3` 明确使用 `chat-completions.v1`；旧 v2 的 Messages 含义保留，新执行拒绝 v2。preflight 仍返回 BLOCKED/退出 2，即使正预算、批准字符串或字段齐全也不解锁 live；工程 Gate 来自本轮行为证据，配置文件本身不授予执行权限。

限制必须连同结论使用：官方源码固定为 `183f08e9c6dde7e36cd2318eaee70b0da08fb35e`，二进制可复现映射仍 unproven；全局 fetch wrapper 只证明受信固定 profile 的发送边界，不覆盖任意恶意插件或其他网络 API；输入 byte quota/整数价格只是合成配额，不承诺真实 token/账单封顶；控制进程整体崩溃后未实现完整恢复，reserved/sending/unknown 持久占额并阻断后续发送。

真实模型请求、外部 provider 请求、真实费用均为 0。本轮仅普通 push `phase1c2a1-chat-completions-budget`，不合并 main、不部署、不自动执行 C2B。

未来 1–2 个 baseline episode 的连接 smoke 仅保留 [字段清单](c2b_connection_fields.json)。需要明确 provider、model、endpoint、适用协议/参数、数据范围、episode 数、输入/输出/调用及金额上限、币种、报价版本与来源、仅引用的 credential reference、独立费用授权与停止条件。不要把 secret 放入 Prompt；填写该清单不会发起调用，也不是费用授权。本轮没有提供 live 执行 CLI。
