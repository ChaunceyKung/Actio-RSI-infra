# 费用、凭据与超时边界

2026-10-09 10:11（Asia/Shanghai）读取官方入口、Models & Pricing、Chat Completions 和 Token Usage。前三页字节 hash 与 2026-10-08 审阅相同；没有请求供应商 API。URL、UTC 访问时间、摘录、原始 HTML hash 见 [来源](sources.json)；完整页面只保留本地 `.local/phase1c2b0-sources/`。固定 DSH tag 仍 `183f08e9c6dde7e36cd2318eaee70b0da08fb35e`，16 个先前下载文件逐个重算 hash；MIT 归属见 [原许可](../phase1c2a1/DSH_LICENSE.txt)。

## 单位与保守测算

报价 `deepseek-flash-2026-10-09-peak.v1` 采用 USD、1 USD = 1,000,000,000 nano-USD，全程整数。峰值每 1M token：cache hit $0.006、cache miss $0.30、output $1.20；每项单价存为每百万的 nano-USD。总分子为 `hit×6,000,000 + miss×300,000,000 + output×1,200,000,000`，除以 1,000,000 后**对整个请求向上取整一次**。任何 token 数必须是非负安全整数，浮点不接受。

1M 的价格分母暂按十进制百万用于测算（相比 2^20 分母产生更高估价）；这是一项显式的保守测算约定，**不是已核实的供应商精确定义**。官方上下文只写 1M，而输出明确写 384K=393216；不能由后者擅自证明输入上界。token 页面仅给近似字符比例及未明确绑定当前 Flash 版本的 tokenizer 下载。故不安装不匹配 tokenizer，不把 65,536 bytes 当计费 token 上界。

候选测算包取 `max(1,000,000, 2^20)=1,048,576` 输入、显式最多 64 输出，全按峰值 cache miss 预留：每请求 **314,649,600 nano-USD = $0.314649600**；1 episode/2 请求 **$0.629299200**；2 episode/4 请求 **$1.258598400**。该数是覆盖两种常见单位解释的提案包络，`input_bound_verified=false`，不能称为已证明的最大可计费输入或真实账单硬保证。精确单位、当前模型 token 上界、调价/错误及额外费用仍是 live blockers；小于单次预留的预算会明确显示不足，不自动缩小未知上界。

报价本地复核窗口为 2026-10-09 00:00 至 2026-10-11 00:00（Asia/Shanghai），不是供应商保证有效期。reserve 和 sending 均复核窗口；报价过期或变更需重新查源、冻结合同并重新批准。峰值费率覆盖文档所述半价谷值，不跟随时钟自动打折；动态涨价或未披露收费不能由本机账本约束。

可信 usage 的 prompt 已含 cache hit，因此 miss=prompt-hit；缺缓存明细只按全 miss 保守估算，不擅自给优惠。reasoning 若已包含于 completion 不再重复计费。raw、官方 translator 与 native usage 必须一致，total/cache 自洽，完整 DONE 与有界响应必需。12 输入（hit4/miss8）+5 输出为 **8,424 nano-USD**；无缓存明细的同样 prompt/output 为 **9,600 nano-USD**。length 的完整、可信 usage 允许 settled estimate，场景仍 partial；其他不受支持终态或不完整 usage 保留 unknown。

四类量分列：本系统 sending/一次性资格、可信或模拟 provider usage、冻结报价的 estimated cost/reservation、实际 supplier bill。本轮 model/external requests 与真实费用为 0；USD 数额是本机模拟 usage 的估算，账单字段仍 null/UNVERIFIED。旧 v3 仍用 SYNTHETIC，报告不将两种单位相加。

## 持久权限与未知

沿用 Ledger 四表、BEGIN IMMEDIATE、FULL synchronous 和前缀重放；v4 使用新 schema=2 实验预算库，原任务库及历史账本不原位迁移。reserve 在实际 fetch 前持久提交，sending 再消费一次 wire hash 绑定资格。config/profile/model/endpoint/task/run/op/seat/quote 改动使绑定无效；两独立控制进程共享同一额度权威。

每份本机预演 authority 使用随机 ID，并以独占创建文件绑定绝对 ledger 路径与合同 hash。该记录先于 DB 创建，初始化中断也保守占用；更换路径、复制数据库或删除旧库后重新建库不能花同一份 authority。该机制不是恶意本机管理员隔离，也不是签名/审批平台；更改 authority root/ID 是另一份合同，不能复用旧批准。live 没有创建 authority 的入口。

reserved/sending/unknown 均占额并阻断新 reserve；进程退出、缺 usage、服务未接收到不构成退款依据。Worker 在 reserve 后、sending 后 fetch 前、结算前退出分别保留事实和占额。不自动恢复或补跑。只在原有 sending 前原子 released 路径可证明尚无消费资格；完整 controller recovery 仍 unsupported。

## 凭据

plan/preflight/verify 不解析 credential reference，不访问用户 provider/proxy 环境。候选仅含 `ACTIO_SOLVER_KEY` 引用，批准为空。C2B0 execute 在任何 resolver 调用之前拒绝，当前不会解析实际 secret；以后真实执行仍需独立人类操作授权及完全匹配合同/期限/额度，不能靠 JSON flag。

预演在内存生成随机 ACTIO_FAKE_ sentinel，经受管 host 启动 stdin 管道传入，再以 SDK 显式 env 注入 TS；不进入命令行或 host-config/profile/SQLite/manifest。父 host 从 clean_env 最小环境启动；预算 IPC 显式另用 clean_env，且 helper 入口拒绝出现 ACTIO_SOLVER_KEY 的环境。官方 SDK 的 env merge 只作用于已隔离 host，不继承用户 provider/代理 fallback。

host 在写日志之前过滤凭据，SDK runtime stderr 在 SDK 内存缓冲；专门的测试插件把 sentinel 写到 runtime stderr 后异常退出，以检验错误诊断路径。服务捕获从建立结构开始就不收集 Authorization 值，只保存 credential_matched 布尔值；不是先落盘再删。测试扫描全部生成文件（含 native/cache/config/stderr/数据库）并导出安全内容；归档仅复制已扫描的数据，不发布真实 key。本轮仅证明固定受信 profile 的这些路径，不承诺任意恶意插件或供应商主动回显 secret 的隔离。

## 分层期限

| 层 | 秒 | 语义 |
|---|---:|---|
| SDK 初始化 / controller ready | 20 / 25 | 继承固定 SDK 启动界限，ready 留余量 |
| SDK JSON-RPC | 5 | session_prompt 的 RPC 收据等待；不是整次模型生成 |
| 首 HTTP 响应 headers | 6 | fetch gate 独立 AbortController；无首响应会中止 |
| 官方 stream idle | 8 | adapter 自有 watchdog，覆盖流迭代无活动 |
| 整请求 | 20 | fetch signal 从发起到响应体读取始终有界，heartbeat 也不能延长 |
| controller result | 35 | 一次 RPC、整请求、两个预算 IPC 的上限合计；正常 IPC 提供处理余量，最坏耗尽时保守中止 |
| drain / close | 4 / 3 | 沿用原生 receipt/barrier 和清理边界 |
| 每 Worker 外层 | 75 | 从启动计时，覆盖 ready/result/drain/close；Job 负责最终回收 |

SDK `client.request()` 计时等待 JSON-RPC response；`subscription.next()` 是独立队列等待，没有共享 RPC timeout。因此不能只提高 request_timeout_seconds；外层 controller 与 fetch 必须同时有界。两个预算 IPC 各最多 5 秒发生在网络发送前，已包含在 result 35 秒中；最坏组合仍可能由外层更早中止并保留 unknown，而不会无限等待。

本机验证延迟 3.5 秒成功（超过旧 fetch3秒），无 headers、流中停顿、持续 heartbeat 不结束分别受界限中止，均无自动 retry。审计 clone 有 65,536 bytes / 128 chunks 上限，沿用先完成有界 capture 再向消费者交付 finish 的修复。门控保留官方 Response/serializer/translator；全局 fetch wrapper 仅适用于该固定可信纯文本 profile，不是通用恶意代码网络沙箱。
