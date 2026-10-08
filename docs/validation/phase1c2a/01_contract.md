# Phase 1C2A 冻结设计与边界

**最终状态：P0 协议准入 NO_GO。** 下文记录探针前冻结的目标；其中 `scheduling-transport.v1`、双 seat 无答案 payload、每次发送前预算 reserve、transport campaign/verifier 均未实施。实际交付仅角色配置修正、官方发行物有界定位、回归和证据；不能把设计陈述视为已实现能力。结果及停止原因见 [结果](02_results.md) 和 [Gate](03_gate.md)。

从远端交接 `a06729e01526def46195c0f3fdd157ebb7e780a8` 开始，产品基线 `af0a88cfff23c22c396fd7c9ef9916f0df8cd21f` 已验证为祖先。执行分支 phase1c2a-solver-transport-and-budget。只推本分支，不推 main；无部署。真实模型/外部 provider 请求及费用为 0，允许本机临时 HTTP/SSE 服务。

先修 C2R1：pilot-config.v2 明确 disabled、deterministic_local、transport_stub、future_live。GM 仅本地确定性，judge/retries/other 关闭，零远端额度且不配置 provider/报价/凭据。solver stub 独立合成预算；future_live 需要显式字段，但任意批准字符串/正数预算均不构成 live 授权。金额只用整数最小单位；严格拒绝未知字段、重复键、bool 充数和 float/nonfinite。

先用固定发行物 0.1.5rc1 实测官方 deepseek-official Messages adapter → 127.0.0.1 临时端口。不改 SDK/adapter 的序列化或 SSE 解析；不升级发行物。源码固定 5badb15009ae1756c3afe0ae0cef1faafc290ccc，只读核对必要文件与 GitHub。若能力不支持，记录 NO_GO 与发行物差异，停止在最小定位，不以自有 provider 模拟官方链路。

新 scheduling-transport.v1 独立于旧 fixture。模型只见 own frozen TaskSpec view、历史实际公开动作、memory、完整 ActionSpec 和必要关联 ID。无 answer/scripted_actions/服务计划/期望结果/对手私有上下文/GM/judge。两个旧 authored 卡和两步 Engine 保持。服务控制侧保存固定响应计划，不能从请求取预置答案回显；mode 明确 transport_stub。

预算权威采用新实验独立 SQLite 账本，Python 冻结 config、campaign/run/op、合成价格与上限。最终发送门控必须在实际 TS provider attempt 之前验证并持久 reserve；实际接收与控制面事件分别留证。重复 attempt 不重发，并发末额度仅一个赢家。发送后任何断流/usage 缺失/中断不退款，保留 unknown/reserve；只有可证明未发送才显式释放。调用数硬上限与合成估算/usage/真实收费能力分开，不声称真实费用硬封顶。

关闭 retry、title 模型、compaction、工具/MCP 与其他非必要 producer，并用实际计数核对。限定本机精确 URL/POST Messages 路径、任务假 key、清空环境回退，禁止重定向。请求/响应/SSE/日志/进程均有界；继续 Job 清理和原生事实链。

新证据独立登记 campaign/run/source/spec/view/attempt/reserve/捕获及全部失败。只读核验不建 Worker/evaluator/HTTP；新模式仅显式版本分派，历史不改写。C0 12 与 C1 22 请求分别以固定版本源码离线复核。工程 Gate 需真实链路、无答案和预算对账全部通过；live、人类校准、研究效度、演化晋升保持 BLOCKED。
