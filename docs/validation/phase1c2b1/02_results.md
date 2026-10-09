# C2B1 实测结果

2026-10-09，TokenKey → 固定官方 DSH SDK/TS loop → 真实 Concordia Sequential 完成两个模型的双场景闭环。工程结论为 **CONDITIONAL_GO**，本轮必要真实调用已完成并停止。账单与上游权重身份仍 **UNVERIFIED**；judge、真人校准、研究与演化晋升保持 BLOCKED。

起点为 `47790607db24a187258035ff990fad544124074d`，已核对产品基线 `f65045a11d1a4728b98b5564623e4827365f91c8` 的祖先关系。所有产品运行使用本轮源码安装；主路径没有 Python OpenAI SDK 回退，没有安装额外 Node adapter、升级 DSH 或改写官方 serializer/translator。实际官方加载证据见 [adapter](06_adapter.md)。

## 正式 DSH / Concordia 批次

| 模型 | 顺序 | A → B 原始行动 | 场景完整性 / 任务结局 | sending / 响应 / 可信 usage | 输入 / 输出 token |
|---|---|---|---|---:|---:|
| gpt-5.6 | compatible | propose:morning → accept | complete / success | 2 / 2 / 2 | 1,121 / 14 |
| gpt-5.6 | conflict | propose:morning → decline | complete / task_failure | 2 / 2 / 2 | 1,011 / 15 |
| claude-sonnet-4-6 | compatible | propose:morning → accept | complete / success | 2 / 2 / 2 | 983 / 5 |
| claude-sonnet-4-6 | conflict | propose:morning → decline | complete / task_failure | 2 / 2 / 2 | 985 / 6 |
| **合计** | **4 episodes / 8 seats** | **每 seat 单次调用** | **4 complete** | **8 / 8 / 8** | **4,100 / 40** |

两次 conflict 的拒绝是合法动作，不是基础设施失败。B 的实际输入包含 A 本次真正产生的公共行动，未预置答案；双方私有约束只发给各自 actor。8 次发送全部 settled、unknown=0、not_run=0、自动 retry=0、额外模型目录/直接诊断=0。每个 episode 有 2 个真实 Concordia 世界记录，合计 8 个；GM 使用确定性规则。

执行说明、实际 CLI argv、原始结果与 Worker 报告：

- [gpt-5.6 执行记录](evidence/live-20261009T042521Z-e92cb80b.json)，[公开只读 campaign](samples/gpt56/campaign.json)。
- [Claude 执行记录](evidence/live-20261009T042704Z-2b9dcbf6.json)，[公开只读 campaign](samples/claude/campaign.json)。

8 次请求均为用户指定的 `https://api.tokenkey.dev/v1/chat/completions`。实际 wire 使用官方 pi-ai 的两条 system/user 消息、stream/include_usage/max_tokens=512；无 DeepSeek thinking/inventory 或其他 producer。每次 raw SSE 的 usage、DONE、stop、model/id 与官方/native 观察一致；requested_model=response_model，但 upstream_identity_verified=false。全部响应均取得实际 HTTP request_id，正文 response_id 另存，system_fingerprint 缺失为 null。

| 模型 / 场景 / seat | headers ms | 首 text token ms | 总请求 ms |
|---|---:|---:|---:|
| gpt / compatible / A | 2,449 | 2,458 | 2,472 |
| gpt / compatible / B | 9,446 | 9,454 | 9,463 |
| gpt / conflict / A | 11,684 | 12,604 | 12,855 |
| gpt / conflict / B | 2,211 | 3,010 | 3,083 |
| Claude / compatible / A | 2,398 | 2,407 | 2,420 |
| Claude / compatible / B | 2,390 | 2,398 | 2,412 |
| Claude / conflict / A | 2,127 | 2,135 | 2,142 |
| Claude / conflict / B | 1,746 | 1,757 | 1,768 |

这是实际 fetch 附近的客户端计时，不能当作供应商推理时间或充分的模型速度比较。开始时间排除了发送前预算 IPC；整 episode 耗时还包含 SDK/Worker 和 Concordia 操作。

## 费用与前置诊断

本轮 gpt-5.6 为 2,132 输入 / 29 输出，Claude 为 1,968 输入 / 11 输出。只有 gpt conflict 的两个响应含 `usage.cost`，原始 Decimal 文本为 `0.001864` 与 `0.0024799999999999996`；其余 6 个 cost=null。币种、单位与覆盖范围未证实，没有合成 USD 总价或将缺失补零。estimated_cost、supplier_bill、supplier_received 均为 null；未读取账户余额或修改预算/权限/充值。

前置 [直接 API 诊断](../../reviews/phase1c2b1_tokenkey_evidence.json) 另有 **14 次生成尝试 + 1 次目录 GET**、12 个 usage 响应（1,362 输入 / 364 输出）、1 次 HTTP400 unsupported_model、1 次 ReadTimeout。它没有产品 Ledger/DSH/Concordia，不能混入正式 episode 分母。两阶段可见生成尝试累计为 **22**，另有 **1** 次目录 GET；失败/超时费用仍未知。本轮未重复这些模型探针。更详细语义见 [账务](05_accounting.md)。

## 本机验收与真实失败

当前实现 **16 suites / 75 组全部通过**。其中新增 gateway 5 组、gateway_lifecycle 2 组；旧路径 68 组，覆盖 preflight/config、transport/预算、C2B0 readiness、任务合同、runtime、可靠性、证据/迁移/输入绑定、SOTOPIA 与离线 evaluation。suite 并行度为 1，实际 argv 和源码 hash 逐份保留。

新增检查实际覆盖两模型×双场景、无预置答案、原始 wire/usage/native 对照、Decimal cost、HTTP400/401/429/500、缺 DONE/usage、非法 token 数、模型标签变化、length 与非法动作、分层 timeout、分段 stderr 凭据过滤、跨 origin/额外 fetch 拒绝、两个独立 controller 同 run 竞争、重复请求不发送，以及 reserve/sending/settlement 前中断、authority 不能换库、只读 reader 与重封篡改拒绝。

**首轮 gateway suite 失败仍保留**：[20261009T040009Z-740ca99d](evidence/20261009T040009Z-740ca99d.json)。当时运行 5 组，1 个成功记录、13 个错误记录（含 subtests）；新辅助函数 `allowed` 被旧 verifier 局部列表同名遮蔽，导致导出/核验异常。已完成的本机发送没有删除。修正为 `cap_allows`，并将计时起点放到实际 fetch 前；修正前源码归档 `.local/phase1c2b1-before-cap-fix.zip` 的 hash 纳入 manifest。没有改变旧配置的实现 hash 来伪造它由当前版本执行。修正后 [gateway 5 组](evidence/20261009T040829Z-c42189b5.json) 和 [lifecycle 2 组](evidence/20261009T040919Z-0384a7fc.json) 全通过，再完成旧路径回归与干净安装，之后才调用真实模型。

其他失败均为本机受控反例，保留 unknown、已发生世界前缀和 not_run，不重试、不退款、不补零。官方源码检索中的 `src/types.ts` 返回真实 404；所需定义已在固定 tag 的 config/catalog 中查到，不影响 loader 验证。

首次只读归档进程因串行扫描约 35.8 万文件耗时而主动停止，未观察到验收错误，也未再次运行模型；[未完成记录](evidence/collection-interrupted-20261009T043733Z.json) 与原采集脚本快照保留。采集工具改为最多 8 个只读目录扫描线程后重新收集。此并行仅用于磁盘读取；构建、安装、runtime suite 与真实批次仍全部顺序执行，产品源码未因此改变。

首次 manifest seal 使用相对路径时，工具的 `Path.relative_to` 与绝对 DOC 路径不兼容，退出 1 且未生成 manifest；改为先 resolve 输入路径后再封存。[工具失败记录](evidence/seal-relative-path-failure.json) 保留，不影响已通过的 delivery/产品或真实批次。

首次暂存字节核对发现未修改的 AGENTS.md 本机 CRLF 与 Git LF 不同；已验证它与起点 Git 对象完全一致，且本机仅行尾不同。保留 [核对失败](evidence/publication-line-ending-failure.json) 和 [首次 seal](evidence/manifest-before-git-audit.json)，最终 manifest 分列 entry 的本机/Git hash。所有本轮变更仍强制暂存字节与本机完全相同，未修改产品或重跑真实调用。

本轮创建 runtime 与 release 两个隔离环境，全部产品文件字节与源码一致；两环境 pip check 通过。公开 CLI 的 plan/preflight 为零 key/网络/Worker，缺执行标志拒绝，旧 C2B0 execute 拒绝；release 环境本机 smoke 实收 2 次请求，并完成只读 verify。见 [CLI](04_usage.md)。历史 C0 固定 reader 的 12 个记录、C1 的 22 个记录、C2A.1 的 3 个样例和 C2B0 的 4 个样例全部通过，历史 validation/reviews/prompts、锁文件和 pinned source 未改写。

完整本机接收数、跨失败与成功的账本普查、清理数、原始归档与所有文件 hash 由 [manifest](evidence_manifest.json) 及其 delivery 记录给出。下节汇总这份只读普查。

## 全轮普查与清理

[最终 delivery](evidence/delivery-20261009T043751Z-4fb06664.json) 为 PASS，收集所有成功及首轮失败 suite 的运行根、官方加载 probe、公开 CLI smoke 与两份真实批次。它用只读 SQLite 查询保留中间实现的账本，而没有用当前合同重封旧库。

| 类别 | sending | 独立本机服务接收 | 观察到响应 | 可信 usage / settled | unknown |
|---|---:|---:|---:|---:|---:|
| 新 TokenKey 本机 rehearsal（含首轮失败） | 72 | 71 | 69 | 51 | 22 |
| 旧 priced_rehearsal 回归 | 36 | 35 | 33 | 23 | 14 |
| 旧 transport_stub 回归 | 47 | 46 | 43 | 31 | 17 |
| 官方 adapter 加载 probe | 不使用产品 Ledger | 1 | 单独 probe 记录 | 单独 probe 记录 | 不适用 |
| 正式 TokenKey live | 8 | null | 8 | 8 | 0 |

本机 HTTP 接收合计 **153**（71+35+46+1），并非真实模型请求。reserved 后中断可以 unknown 而未 sending；sending 后中断可以尚未到服务端；这说明各列不能互相替代。未注册的后续 episode 与已注册但未运行的 seat 按各 execution/result 记录，不能从单列差值推断完整计划。controlled unknown 在账本中保留，不能解释成真实供应商欠费。

验收历史为 17 次 suite 执行 / 80 个顶层组次，其中首轮 5 组失败尝试和当前 75 组均保留。当前 75 组通过并不抹去过去错误。原始本机归档 **49 份、12,782,056 bytes**，含 48 个运行根和固定上游源码摘录，保存在 `.local/phase1c2b1-raw/`，逐归档及逐文件 hash 进入 manifest；重复 node_modules/.cache 不打包。修复前源码与采集中断脚本另有快照。

全扫描覆盖 **358,129 个文件检查**（含生成目录及当时公开材料），实际 key 与假 sentinel 均未发现；所有将提交文件还需在暂存区做一次精确 key 扫描。key 副本仍 Git ignored/untracked。两个正式批次各扫描 6,712 个生成文件，未把密钥值、前后缀、长度或 hash 输出到公开材料。

清理普查去重 **215 个 Worker 记录**，均 state=reaped 且对应命名 Job active=0，其中 **213 个有 PID**，另 2 个是未分配/受控恢复记录，不冒称真实启动了 215 个进程。正式 live 为 8 个受管 Worker。**87 个本机服务记录（含 probe）**确认线程已结束，所记端口无监听。数据库只读扫描前后 hash 一致；650 个历史受保护文件未改变。未执行部署、账户侧设置、judge 或真人校准。
