# 预算生命周期与对账

`attempt-ledger.v1` 新库含 meta、registration、attempt、event 四表，schema=1，SQLite `BEGIN IMMEDIATE` 和 `synchronous=FULL`。任务 SQLite 不迁移；两份库分别拥有实验预算与既有领域事实，campaign 通过冻结 ID/hash 对账，不成为第二个世界状态权威。

| 状态 | 含义与支出处理 |
|---|---|
| 登记但 not_run | 两 seat 预先登记，前一步非法或失败可能让后一步没有 operation；保留分母 |
| authorized | Python 创建 op 后登记正确 actor/task/config/profile 的一次性资格；尚无预算预留或发送许可 |
| denied | reserve 前类型、归属、未知账务或额度不足；无发送资格、无消耗 |
| reserved | 每请求原子预留 calls=1、合成输入上界 65,536、输出上限 64、合成金额 65,600；持久提交后才允许下一步 |
| sending | 另一个持久事务消费 wire hash 绑定资格，再进入 official fetch。它是**发送尝试**，不意味着服务已接收 |
| settled | 官方完整 stop/DONE、raw usage、translator usage 与 native usage 一致，按合成实际 usage 结算；不重复加缓存 |
| unknown | 缺终态、断流、超时、非法/缺失 usage 或 Worker 中断；保留整笔预留，阻断后续 reserve，无退款/重试 |
| released | 只有在 sending 尚未提交前原子释放，令后续 ticket 失效；authorized 且无 reserve 的终止也可确认从未获得发送许可 |

硬调用上限在每次真实 fetch 前执行，重复 attempt/票据不能发送。同账本保守地只允许一个未结算发送：reserved/sending/unknown 任一存在均阻断新 reserve，即使总配额还有余额。并发测试使用两个独立 Python 控制进程、独立任务库、共享预算库争抢最后 1 次额度，实际只收到 1 请求。Worker 在 reserve 后、sending 后但 fetch 前、收到响应但结算前退出，分别保留 unknown；其中 sending 后退出的发送尝试为 1、接收为 0。发生控制进程整体崩溃时，未终结的 reserved/sending 保留占用并阻断新发送，不能自动释放或重跑；本轮没有实现完整控制进程恢复。

prepared request hash 与 wire-body SHA256 **分开**。pure text mapping 核验 system/user 内容相同；官方转换删除 source/id，添加 model/stream/thinking/max_tokens/plugin inventory。`X-Actio-Attempt` 只在 HTTP header，用于独立服务捕获归属，不进入模型上下文。重复/错归属/错 body、缺登记、金额/次数篡改和重复结算由只读 verifier 拒绝；它重放全局 reservation 前缀检查并发峰值，不只看最终总额。

usage 取官方规则下最后一个附带/尾部对象。`prompt_tokens` 已包含 cache hit；DSH `inputTokens = prompt_tokens - cacheReadTokens`，本账本输入扣额为原 prompt_tokens，缓存只计一次。要求整数非负，total 自洽，cache hit/miss/details 相容，映射与 native 相同，且不超过预留。原始响应和可能非法的 translated/native 数值以原始 JSON 文本保留，避免转成 0 或为编码而截断。

合成价格标识 `synthetic-byte-upper.v1`，输入/输出各 1 SYNTHETIC 最小单位。输入 byte quota 是本机实验的保守配额，不是对真实 tokenizer 的证明。settled 是合成 usage 结算；unknown 保守冻结，不表示发生了等额真实消费。没有真实收费硬封顶承诺；真实模型请求、真实费用均 0，live 永远 BLOCKED。

预算不能抹掉已发生的事实。第二步 usage 不可信但 SDK 已给完整合法行动时，场景可能 complete/success，而账务仍 unknown；第二步传输失败时场景 partial，第一步的世界效果保留。两轴在报告中分列。
