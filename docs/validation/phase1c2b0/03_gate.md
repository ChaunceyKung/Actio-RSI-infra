# Gate 与停止点

| Gate | 状态 | 含义 |
|---|---|---|
| local_readiness_engineering | CONDITIONAL_GO | 仅本机 USD 计价预演、默认拒绝、内存假凭据、期限/并发/对账工程；以最终结果及 manifest 为据 |
| provider_compatibility | UNVERIFIED | 未调用供应商，API 文档不等于实际兼容 |
| live_authorization / live_execution | BLOCKED | 本轮无费用授权；execute 始终在凭据解析前拒绝 |
| billing_reconciliation | UNVERIFIED | 没有供应商账单，supplier_bill_minor=null |
| human_calibration / judge | BLOCKED | 没有真人标签、live judge 或校准运行 |
| research_validity / evolution_promotion | BLOCKED | 本机计划响应不证明推理能力，没有独立研究单位 |
| binary_source_mapping | unproven | 固定 tag 与发行物未证明可复现构建 |
| full_controller_recovery | unsupported | 未结算记录阻断，不自动恢复/重试 |

[批准包](approval_package.json) 是可审阅的具体提案，包含两张 authored 卡、源实现/报价/合同 hash、精确候选 URL/model、期限、credential reference、每次和 1/2 episode 费用测算。默认批准为空，实际执行预算为 0，建议额度不写入实际预算。用户尚未选择 provider/model，也未授权真实预算；不需要等待这些选择才能交付本机准备。

输入 1M 的精确单位、价格百万分母、当前 tokenizer 绑定、调价与额外/错误费用仍未核实。保守测算明确列出假设，不能宣称真实 token/费用硬封顶。future live 需要独立批准和新的执行 gate，不把本阶段完成叫作 live 已验证。

未来 C2B1 只建议 1–2 baseline episode、最多 2–4 solver 请求；所有诊断也计入总额度，首 seat 可同时作连接检查，不另建免记账 probe。任何 unknown、首个协议错误或上限到达即停，无自动 retry/补跑；任务未达成可作为合法失败，不绕过 ActionSpec，也不补答案。本轮没有执行该建议。

交付仅普通 push `phase1c2b0-solver-live-readiness`，核对远端 SHA；不推 main、不部署，停止于 C2B0。结果见 [02_results.md](02_results.md)，复现见 [04_usage.md](04_usage.md)，证据见 [manifest](evidence_manifest.json)。
