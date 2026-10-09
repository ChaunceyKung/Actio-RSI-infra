# 无金额上限与可核验账务

`spending_policy=uncapped_for_phase1c2b1`、`cost_limit_minor=null`、`authorization_basis=explicit_user_instruction_2026_10_09` 共同表达本轮明确授权。缺字段、未知 schema、其他策略、0、负数、浮点、NaN/Infinity 或巨大整数不代表无上限。单批调用数来自具体 episode/seat 计划，不是暗中新增的全项目费用/两次调用限制；必要新诊断另登记有限批次并累计保留。

复用 Ledger 的四表和 BEGIN IMMEDIATE，v5 新库 user_version=3 / attempt-ledger.v3；旧库不迁移。每一资格绑定 campaign/run/op/seat/agent/task/config/profile/model/实际 prepared 与 wire hash。reserve 记录 calls=1、input_tokens=null、output_tokens=512、cost_minor=null，表示在途登记和输出约束，**不是 0 成本或证明了最大账单**。金额未知在 totals 中仍为 null。

同一批有 reserved/sending/unknown 时阻断后续 reserve；资格只能消费一次。authority 独占文件绑定精确 ledger 路径与 config hash，不能复制/换库花同一资格。并发控制进程由既有 Store 原子 request claim 决定同一 episode 的唯一运行者。完整控制进程崩溃恢复仍 unsupported。

四类量明确分列：

1. sending 是客户端持久消费发送资格；live observed_responses 是实际取得 HTTP 状态的观察，不是服务端完整访问日志，supplier_received=null。
2. verified usage 要求完整原始 SSE、单次 usage、DONE，prompt/output/total/cache 自洽、官方 pi-ai/native 映射相符、响应 model/id 一致。reasoning 已包含在 completion 时不额外相加。已核验 usage 的 settled 不表示费用已核对。
3. TokenKey `usage.cost` 使用 Decimal 从原始 SSE 解析，保留十进制文本、来源；币种/单位/覆盖未核实。缺失为 null，不补零，不采用官方厂商零售价冒充网关报价。pi-ai catalog 中的 NO_COST 元数据不参与账单结算。
4. supplier_bill_minor=null、billing_reconciled=false。没有查询账户扣款、余额或账单，也未修改账户侧限制。

raw 响应为字符串原样保存，因此 usage.cost 的小数不会被受限 canonical JSON 浮点规则丢弃；可核验的结构化 cost 值是文本。price estimate 仍 null。缺报价或精确 tokenizer 不阻断已授权 uncapped 的发送；协议矛盾、输出越界和身份异常仍停。

任务状态与账务状态独立：非法动作可以有合法 usage；length 可有完整 usage，但原生非 completed 使任务 partial。网络失败、缺/坏 usage、响应身份变化保留 unknown 和原始观察，停止 episode/批次，后续 seat not_run。401/403/402 停该路径，429 保留返回信息且不隐式重试；没有新证据时不反复请求。

新诊断批次可以在旧 Worker 回收后推进，不将历史 unknown 永久扩大成全项目死锁；CLI predecessor 引用保存旧 result hash 和理由。所有 live intent 在读取凭据前登记，阶段 manifest 汇总本轮每份实际 ledger 与失败，并关联前置直接诊断的 14 次生成尝试/1 次目录 GET；它们不混入正式 DSH episode 分母，也不把历史 C2B0 零真实调用改写。
