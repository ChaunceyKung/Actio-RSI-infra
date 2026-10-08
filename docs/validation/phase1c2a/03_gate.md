# Phase 1C2A Gate

| Gate | 状态 | 依据 |
|---|---|---|
| C2R1 角色配置修正 | PASS（仅配置） | 零预算本地/关闭角色合法；严格类型；live 始终 false；5 组新增检查 |
| transport_stub 工程 | **NO_GO** | `0.1.5rc1` 默认为 Chat Completions；所要求的官方 Messages 插件实际 loader 无法加载。未通过完整传输/无答案/预算验收 |
| live provider | **BLOCKED** | 无执行入口、无选定并授权的真实 provider/model/calls/tokens/总费用；C2A 未通过 |
| 人工校准 | **BLOCKED** | 真实人工标签 0；受控评分不等于人工校准 |
| 研究效度 / 演化晋升 | **BLOCKED** | 真实模型与独立研究单位 0；没有有效研究数据或晋升证据 |

冻结 Prompt P0 的停止条件在正确 loader 探针触发，因此没有继续 P1–P3 的新传输实现。保留 47 组配置/既有路径回归通过，不提升 transport Gate。C1 的 CONDITIONAL_GO 仅属历史 fixture 工程，不能继承成新协议通过。

## 最小备选，需要下一轮明确选定范围

1. 保留 `0.1.5rc1`，另行批准将协议目标改为它实际附带的官方 Chat Completions；先查验对应版本源码/许可/serializer/SSE/usage，再修合同、探针和预算 seam。当前仅观察到错误响应，不能宣称它的成功链路已经可用。
2. 保留 Messages 目标，另行批准升级到经验证附带 Messages adapter 的 SDK/runtime 组合，锁定新 wheel/exe 与对应源码后重做探针、回归和所有 P1–P3 准入。此文不指定未经检查的升级版本。

本轮没有选择或执行上述备选。它们都要求先补齐 C2A，不直接解锁 C2B live。

## 后续 C2B 草案（本轮不执行）

C2A 重做通过后，单独授权 1–2 个 baseline episode 的真实 solver 连接 smoke。GM 确定性，无 judge/工具/重试。需确认 provider、精确 model/version、protocol/endpoint、可发送的 data scope、授权引用、总 calls/input/output token/总费用/币种/报价版本、单请求 deadline 和遇 unknown 的停止规则。[future-live-config.json](future-live-config.json) 留空待确认，不使用 placeholder 自动补齐付费参数。

目前唯一可复制命令是 `python -m actio.preflight <审核后的配置.json>`，它仍返回 BLOCKED/2。没有可执行 live smoke 命令；下一轮先完成明确版本的执行合同再发布该命令。连接 smoke 可以先于社会评分人工校准，但只能证明连接与工程行为，不能支持能力结论。
