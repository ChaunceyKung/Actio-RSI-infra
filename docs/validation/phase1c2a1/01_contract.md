# Phase 1C2A.1 合同

执行起点是远端交接 `2b43ea306bfeaca4b4200b69be65d65a5dc1fee9`，已核对产品基线 `7fb2f682b2726ce3bba9b38bc71ebbf893c5de22` 为祖先。执行/发布分支 `phase1c2a1-chat-completions-budget`，不推 main、不部署。用户本轮明确选择保持 DSH `0.1.5rc1`，将协议改为发行物的官方 Chat Completions；旧 Messages NO_GO 原件不变。

版本分派：`pilot-config.v3` / `chat-completions.v1` / `scheduling-transport.v1` / `execution_mode=transport_stub` / `sdk-minimal+actio-chat-budget.v1` / `sqlite-attempt.v1`。官方 route 为 `deepseek-official`，model 为专用假标识 `actio-synthetic-chat-model`，插件是发行物的 `@deepseek-ai/dsh-llm-deepseek` `0.1.5-rc.1`。新 spec 显式冻结这些 pins；旧 `pilot-config.v2` 仍是 Messages 语义，新 transport 执行明确拒绝 v2。

Windows x64 / CPython 3.12.10，固定 SDK/runtime 0.1.5rc1、exe SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`、Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db`。核心和 eval 锁文件不变，参考 checkout 不改。模型请求、外部 provider 请求和真实费用均为 0。

只用原 compatible/conflict 两张 authored 排程卡、两个 seat、固定两步真实 Concordia Sequential。actor 输入只含公开场景、自身角色/目标/约束/初始关系、实际公开行动历史、冻结的自身 memory、完整 ActionSpec 和关联 ID。服务响应计划留在测试控制侧；输入没有 answer/scripted_actions、对手私有内容、GM 私有内容或 judge 内容。B 的最终观察含 A 的实际公开行动。既有 fixture 入口保留原合同，不通过放宽校验获得新模式。

独立新预算库使用 schema=1，不迁移任务库 schema=2 或历史 DB。Python 冻结 campaign/config/profile、两 seat 登记与 operation 授权；受管 TS Worker 的最终 fetch 门控在调用官方 fetch 前，经独立 Python 子进程提交 SQLite reserve 和 sending。相同预算的独立控制进程共享这份权威账本。DSH 仍拥有 serializer、SSE translator、错误处理和 agent loop。

只允许精确 `http://127.0.0.1:<临时端口>/chat/completions`、POST、纯文本、64 max_tokens、thinking disabled；每次发送资格绑定 prepared request、实际 wire bytes、actor task、run/op/seat/config/profile。关闭 retry、session-title、MCP/工具和压缩；拒绝重定向、Files/image/非本机或未绑定调用。使用任务假 key；隔离环境不继承 provider/proxy 配置或真实凭据。全局 fetch wrapper 仅适用于这个固定、受信纯文本 profile，不是任意插件的恶意代码沙箱或通用网络防火墙。

单请求 fetch deadline 3 秒、provider idle 1.5 秒；请求/响应各 65,536 字节、观察 chunk 最多 128；外层 RuntimePort/Job/journal/stdout 继续原有界限。完整官方终态、领域结果、账务状态分别保存。缺 usage/非法 usage 即便已有合法行动也保留 unknown 预留；不删事实，不补零，不自动重发。只读 campaign 绑定登记、bundle、spec/view/wire、attempt、预算事件与独立服务捕获。

scope 限制：只有本机合成请求准入；没有真实 tokenizer/账单上界、live judge、人工标签、独立研究单位、训练或晋升。本阶段结束后不自动启动 C2B。
