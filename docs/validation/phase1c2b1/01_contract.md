# Phase 1C2B1 TokenKey 执行合同

2026-10-09 从 `origin/main=47790607db24a187258035ff990fad544124074d` 创建 `phase1c2b1-gated-solver-smoke`；已核实产品基线 `f65045a11d1a4728b98b5564623e4827365f91c8` 为祖先。用户当前 Prompt 明确授权必要凭据读取、TokenKey 模型验证、solver 基线及有依据的诊断，且无金额上限；覆盖旧阶段零预算、固定金额和首次调用再次确认门槛。授权不包含账户预算/余额/充值/权限修改、部署、judge、真人校准或研究晋升。

新配置 `pilot-config.v5`、任务输入 `scheduling-tokenkey.v1`、profile `sdk-minimal+actio-tokenkey.v1`，区分 `tokenkey_live` 与 `tokenkey_rehearsal`。旧 v2/v3/v4 保持原义，C2B0 execute 继续无条件拒绝。live 精确 base URL 为 `https://api.tokenkey.dev/v1`，POST `/chat/completions`；不追加第二个 `/v1`，不向其他 origin 发送 key。TLS 默认验证，redirect=error。

网关身份为 TokenKey，官方 adapter 为 `@deepseek-ai/dsh-llm-pi-ai` `0.1.5-rc.1`，DSH 内部 route 为 `actio-tokenkey`；不能称为直连 OpenAI/Anthropic/DeepSeek。requested model 仅允许 `gpt-5.6`、`claude-sonnet-4-6`。响应 model 必须与该批请求标签一致；标签相同也不证明实际上游权重，`upstream_identity_verified=false`。正文 id 存为 response_id，HTTP x-request-id/request-id 单独记录，缺失为 null；fingerprint 原值保留。

Windows x64、Python 3.12、DSH SDK/runtime `0.1.5rc1`、exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`、Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db` 固定。Python Control Plane → 官方 SDK → TS loop → 真实 Concordia Sequential 不变。官方 serializer/stream translator 不重写；不存在 Python SDK 生产 solver 备选环。

每个模型单独登记有限批次：compatible episode 正常闭环后执行 conflict episode，每 episode A→B 顺序两步，每 seat 最多一次请求。无独立免记账连接探针。每个实际任务冻结 TaskSpec、agent/spec、memory、输入构造与配置/源码 hash；B 的 wire 在 A 真正行动后冻结。actor 仅见自身合成约束/目标、公共场景及真实公开行动，未注入答案、对手私有信息或 judge 内容。GM deterministic；拒绝/未达成可以是合法 task_failure。

请求输出上限 512（可包含网关的 reasoning 消耗），明确 max_tokens；temperature/seed 不设置，reasoning 不请求。profile 的 reasoningEfforts=false 仅控制 adapter 不发 reasoning 参数，不声称网关内部无推理。两条显式模型 entry 的 contextWindow=32768 是本地 catalog 容量声明，不是已验证 TokenKey 计费输入上界；请求体另限 65,536 bytes。响应限 262,144 bytes / 1,024 adapter chunks。实际 wire 必须只有 model、system/user messages、stream、stream_options.include_usage、max_tokens，与 prepared task 完整对应。

分层期限：ready30s（SDK initialize20s）、RPC receipt5s、headers45s、官方 stream idle30s、整 HTTP 请求90s、controller result115s、drain5s、close5s、Worker165s。result 留出网络90s、预算 IPC各5s、RPC5s及10s处理余量；外层覆盖启动/结果/清理。官方 idle 同时可能在首 headers 前触发，实际有效期限为各层最先到达者。timings 分列客户端 headers/首 text-delta/总请求毫秒；均不等于供应商推理时间，前置非流式总耗时也不冒充首 token。

固定可信 profile 禁用旧 DeepSeek adapter、专有 API 扩展/inventory、session-title、llm-retry、工具/MCP/Files/image/compaction；pi-ai retryPolicy 明确 maxRetries=0。fetch gate 对每 op 仅允许一次精确目标请求，先持久 reserve/sending 后调用原 fetch；helper 用最小 clean_env，无 key。门控范围是该固定可信 profile，不是任意恶意插件沙箱。

plan/preflight/verify 不读 secret、不联网、不启动 Worker/evaluator。显式 execute 验证 config/有限计划/实现 hash 后才解析 `.local/credentials/token_key.txt`；CLI 操作标志确认执行本轮已有授权，JSON 自身不是授权来源。key 经受管 stdin → host 内存 → SDK 显式 env 注入，不进入命令行、磁盘配置/账本/manifest。缺副本才从用户指定源文件复制；不覆盖已有未知内容。分段 stderr 在 host 写盘前合并过滤；本机假 sentinel 和本轮真实生成文件均检查，不打印 key、前后缀、长度或 hash。

账务与异常规则见 [05_accounting.md](05_accounting.md)，官方加载证据见 [06_adapter.md](06_adapter.md)。完整 controller 恢复不在本轮支持范围；旧 unknown 不退款、不补零、不重用 attempt。新诊断需说明前次失败和变化、确认旧 Worker 回收，并在阶段汇总保留所有批次。
