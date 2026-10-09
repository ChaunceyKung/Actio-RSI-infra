# Phase 1C2B0 冻结合同

执行分支 `phase1c2b0-solver-live-readiness`，核实远端交接 HEAD `f5b8f92548184c43d8ab6e6853edb9edc4f7c148` 包含产品基线 `b086cbae97fcebd5c818dce611a0c2a331380cb1` 后创建。只在本机受控服务使用假凭据；公开供应商文档读取不属于 provider API。本轮不读取实际 secret、不请求模型列表/余额/鉴权、不产生真实模型调用或费用，不自动进入 C2B1。

`pilot-config.v4` / `chat-completions.v1` 是新的候选/预演合同，未重解释 v2 Messages 或 v3 loopback。候选为 `deepseek-official`、`deepseek-flash`、`https://api.deepseek.com` + `/chat/completions`、POST、正常 HTTPS/TLS、无 redirect。该候选源自公开资料，**不是用户的 provider/model 选择或费用授权**。默认 `approval=null`、execution budget 全 0、无 authority；非执行测算另列。

预演使用 `mode=priced_rehearsal`、`scheduling-priced.v1`、`sdk-minimal+actio-priced-memory.v1`、`sqlite-priced-attempt.v1`，连接模式也进入 spec pins。仅精确 literal `http://127.0.0.1:<临时端口>`，同样发送请求模型名 deepseek-flash，但只到本机服务；不把这个名字当作已连接真实模型。未来 live_candidate 不能创建执行账本或 Worker。v4 execute 当前始终在凭据解析之前拒绝，不能靠 approved=true、批准字符串、正预算或现成 key 打开。

Windows x64 / Python 3.12，SDK/runtime 0.1.5rc1、exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`、Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db` 不变。只扩充 pyproject 的产品 JSON 打包规则以携带报价；未增加/升级依赖。官方 serializer/SSE translator/agent loop 不替换；仍由 Python Control Plane、官方 SDK、TS Worker 和真实 Concordia Sequential 运行。

仍是 compatible/conflict 两张 authored 卡、两个 seat、顺序两步。actor 只接收自身角色、目标、私有约束、关系、公开场景、实际公开行动历史、冻结 memory 和 ActionSpec；无 answer、服务计划、对手私有信息或 judge 内容。GM 确定性，judge/retries/other 禁用，tools/MCP/Files/image/title/compaction 不启用。测试响应计划仅在服务端，预演不证明模型推理能力。

合同 hash 绑定完整连接、报价来源/hash、limits、具体 authored TaskSpec 提案、产品实现字节、默认批准及预算边界。PROPOSED_A/B 和零 spec hash 明确标记未执行提案，不冒充已分配身份/op/wire；真实运行另建身份、run、数据库，记录官方实际 prepared/wire 两个 hash。B 的完整 wire 只能在 A 行动后冻结，plan 不伪造其结果。

响应必须带一致 request ID，model 仅允许请求 alias deepseek-flash；缺失或不同则 unknown/freeze。记录 response model、request ID、system fingerprint 原值；alias 与 fingerprint 不能证明固定权重版本，immutable weights/binary-source mapping 仍 unproven。无独立供应商访问日志时 supplier_received=null；供应商账单未核对时 supplier_bill_minor=null。

报价与未决单位详见 [费用/凭据/超时](05_cost_credentials_timeouts.md)，公开来源见 [sources.json](sources.json)、固定 SDK/tag 来源见 [upstream.json](upstream.json)。执行入口、批准包与 Gate 见 [CLI](04_usage.md)、[批准包](approval_package.json)、[Gate](03_gate.md)。
