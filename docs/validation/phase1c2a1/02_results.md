# Phase 1C2A.1 实测结果

**CONDITIONAL_GO，仅本机 transport_stub 工程。** 官方 DSH 0.1.5rc1 Chat Completions 已完成无预置答案双 seat、发送前持久预算与只读对账。最终源码的 **12 个套件 / 59 组**全部通过，runtime、eval-only、全新 release2 安装中的产品文件集合及字节一致；core+eval pip check、公开 CLI smoke 与 preflight 通过预期退出码验收。live / 人工校准 / judge / 研究效度 / 演化晋升继续 BLOCKED。

执行/发布分支 `phase1c2a1-chat-completions-budget`，交接 SHA `2b43ea306bfeaca4b4200b69be65d65a5dc1fee9`，产品基线 `7fb2f682b2726ce3bba9b38bc71ebbf893c5de22`。配置/协议为 `pilot-config.v3` / `chat-completions.v1`；输入为 `scheduling-transport.v1`，profile 为 `sdk-minimal+actio-chat-budget.v1`。旧 v2 Messages 原义保留，旧 C2A NO_GO 原件未改。

完整索引：[manifest](evidence_manifest.json) · [交付对账及清理](evidence/delivery-20261008T152803Z-5dbc98ec.json) · [最终公开 CLI](evidence/cli-20261008T152446Z-2199a31b.json) · [复现](04_usage.md) · [预算生命周期](06_budget.md)。

## 实际计数

下表只计本轮，含中间版本和失败，排除历史 C2A 的 2 次 HTTP。去重单位为独立服务捕获路径与实际预算数据库；`release.sqlite`、`wrong-body.sqlite`、`pending-blocks.sqlite` 等 SQL-only 克隆不计为网络尝试。

| 口径 | HTTP 实际接收 | 持久 sending 事件 |
|---|---:|---:|
| S0 诊断（独立最多一次 fetch，尚无预算库） | 3 | 不适用 |
| 最终源码 transport + budget 两套件 | 46 | 47 |
| 最终干净安装公开 smoke | 2 | 2 |
| 较早正式路径测试及手工/失败 smoke | 139 | 142 |
| 全部预算路径 | 187 | 191 |
| **本轮全部（含诊断）** | **190** | **191（仅预算路径）** |
| **真实模型 / 外部 provider / 真实费用** | **0 / 0** | **0 真实费用** |

最终正式批次有 60 个 seat 登记、55 个 attempt、5 个 not_run；33 settled、17 unknown、5 denied。49 个 sending 与 48 个接收之差来自 sending 提交后、fetch 前的受控 Worker 退出；另有 reserve 后但 sending 前退出的一笔 unknown。它们都不退款或重试。全部预算路径有 236 登记、216 attempt、20 not_run，125 settled、70 unknown、21 denied；4 次 reserve 后中断未产生 sending。

最终正式批次 settled 的合成 usage 为 input=396、output=165，合成金额=561 SYNTHETIC 最小单位（33 请求）；全阶段 settled 为 input=1500、output=625、合成金额=2125（125 请求）。unknown 保留完整预留，最终批次总占额为 input=1,114,508、output=1,253、calls=50、cost_minor=1,115,761；全阶段总占额 cost_minor=4,594,125。占额与合成费用均不是实际账单，未把未知调用当作零费用。

## 行为证据

| 验收点 | 实际结果 |
|---|---|
| S0 官方协议 | attached 和 trailing usage 各成功一次，输出合法非空 propose:morning，SDK/native completed；缺 DONE 探针为预期 incomplete。旧三份诊断 pins 不作为正式 spec |
| 正式 wire | `/chat/completions`、POST、stream=true、include_usage=true、max_tokens=64、thinking disabled；prepared 与 wire 分别 hash，并核对官方字段转换及插件 inventory |
| 双 seat | compatible 达成、conflict 合法未达成、decline 合法拒绝、INVALID 非法行动分开；B 接收到 A 实际公共行动。真实 wire 无 answer/scripted_actions、服务计划、对手私有信息或 judge 内容 |
| 实际预算边界 | 0/耗尽额度发送前拒绝；两个独立控制进程共享最后一次额度只有 1 接收；重复 attempt/票据不能再发；未结算预留即使还有配额也阻断后续 reserve |
| 中断 | reserve 后 / sending 后 fetch 前 / 收到响应结算前退出，接收分别 0 / 0 / 1，均保留 unknown；第二步失败保留第一步世界效果 |
| usage | 最后 usage 对象覆盖先前值；prompt=12 已包含 cache hit=4，native inputTokens=8、cacheReadTokens=4，账本 input=12，未重复加缓存。缺失/负数/浮点/total 矛盾/缓存矛盾/超限全部 unknown |
| 额外 producer | retry/title/MCP/工具/压缩关闭；固定 profile 主动探测 Files、非本机、localhost 共 6 次拒绝，重复 fetch 2 次拒绝；普通两步只有 2 接收。隔离子进程的假 hostile provider/proxy 环境没有生效 |
| 对账 | 所有登记/失败/not_run 保留；改金额、漏登记、改 run/wire/接收归属、重复结算，即使重算外层 hash 仍被拒绝；逐事件重放检查预留峰值 |
| 只读 | 可迁移标准库子进程禁止写入/socket/subprocess/runtime 导入，仍可核验 campaign；不创建 Worker/evaluator/HTTP。deterministic 评估准入，controlled-response 对新 transport 为 insufficient |

最终传输故障矩阵每案均已先完成 A，再对 B 注入；每案实际为 **2 sending / 2 接收**，无隐式重试。以下是实际官方 chunk 的错误码，不把它们统一 mock 成理想错误：

| B 输入/故障 | 官方 finish / error | 场景 / 账务 |
|---|---|---|
| HTTP 429 | error / RATE_LIMIT，status=429 | partial / A settled、B unknown |
| HTTP 500 | error / SERVER，status=500 | partial / A settled、B unknown |
| 缺 DONE | error / STREAM_CLOSED | partial / A settled、B unknown |
| 空响应 | error / EMPTY_RESPONSE | partial / A settled、B unknown |
| 畸形 SSE | error / MALFORMED_RESPONSE；审计 clone 另记录 consumer stopped | partial / A settled、B unknown |
| deadline | error / TIMEOUT，idle=1500ms | partial / A settled、B unknown |
| redirect | error / TRANSPORT；fetch failed | partial / A settled、B unknown，无重定向接收 |
| 缺 usage | stop；usage missing | complete/success / B unknown |
| 负数 / 浮点 / total矛盾 / cache矛盾 / 超限 | stop；保留各原数值及拒绝原因 | complete/success / B unknown |

任务行动完成与预算结算是两轴。带不可信 usage 的合法行动仍保留事实和世界效果；没有据此伪造 rollback 或零消费。本轮未运行 400/401 或外部网络故障，未宣称覆盖全部 provider 错误。

## 最终套件与历史

| 套件 | 组数 | 主要行为 |
|---|---:|---|
| transport / budget / transport_config | 4 / 4 / 3 | 官方本机协议、实际发送边界、并发/中断、版本隔离、WMI fallback |
| preflight / task / runtime | 5 / 7 / 2 | 角色预算、无 live 开关、原任务与真实运行回归 |
| reliability / evidence / schema | 8 / 7 / 5 | 异常前缀、Job回收、磁盘竞态、离线证据、只读/迁移 |
| input_binding / sotopia / evaluation | 3 / 3 / 8 | 冻结输入、既有 parser/schema、离线测量准入与失败 |

每条实际命令、测试方法、运行根、退出码和最终 source/test/helper hashes 均在 manifest 选定的 suite 记录内；旧的中间 PASS 不冒充最终源码验收。固定旧版复核 [记录](evidence/legacy-20261008T152125Z-491933d6.json) 通过 C0 12 记录、C1 22 请求/25 登记，当前源码 pins 明确拒绝旧记录。相对交接提交核对了 537 个历史文件（含 C2A、审阅/Prompt、锁文件、pins/vendor）未变，较新的原参考 DSH checkout HEAD 与文件也未变。

## 失败保留与修正

1. 初期手工 smoke `D:/actio-c2a1-smoke/146642ba00cc` 收到 1 请求，DSH 在消费者收到 finish 后正常取消 signal，审计 clone 误记录 consumer stopped；A 的账务 unknown 阻断 B。已改为在向消费者交付 finish 前等待有界 clone。原始 result/账本及完全匹配该 run pins 的源码 ZIP 保留，没有重封它。
2. 旧任务首次 setUpClass 失败（[原记录](evidence/20261008T150349Z-3e535bd8.json)，[根路径/来源](evidence/failure-task-start.json)），运行组数=0。WMI 查询偶发失败时，隔离环境缺架构 fallback；按当前 CPython AMD64 构建标识补齐非敏感字段，不读取 ambient provider 环境。新增强制 fallback 的真实子进程检查，并重新跑最终套件。
3. 干净安装首次公开 smoke [记录](evidence/cli-20261008T151724Z-339e0474.json) 收到 2 请求，扫描已被原生原子替换的 `.tmp` 文件时 FileNotFoundError，B 保留 unknown。磁盘计数仅忽略已消失项，其他 I/O 错误及超限继续拒绝；新增确定性竞态回归，重做干净 release2 安装及所有相关验收。该失败 run pins 与修复前 ZIP 逐文件匹配。
4. 交付汇总首次 [失败](evidence/delivery-20261008T152738Z-baff2401.json) 错把 0 接收的服务当作应有 receives.json。helper 实际在第一次接收时才写文件；汇总现在仅在 service.json 明确计数 0 时接受文件缺席。此修复只改交付工具，没有重跑模型/HTTP。首次 seal 另发现相对路径转 manifest 引用的问题（[记录](evidence/seal-relative-path-failure.json)），统一 resolve 后修正；失败时尚未写 manifest。

## 清理与保存

从本轮全部根的 worker 表去重得 **298 个受管 Job 名称**，其中 **294 有记录 PID**、4 个为受控未启动行。逐一 Win32 查询均 active=0（或 Job 对象已不存在）；没有复用历史 Job 数。**117 个服务线程已 join**，115 个去重服务端口（两次临时端口重用）逐一检查无监听。没有终止无关进程。

73 个本地原始归档 ZIP 合计 15,524,688 字节，位于 `.local/phase1c2a1-raw/`，逐文件/归档 hash 在 manifest；数据库、原生日志、失败插件及源快照保留本地，未提交 venv/二进制缓存。公开材料只含合成证据及必要来源/hash。三个样例：[success](samples/success/campaign.json)、[missing-done](samples/missing-done/campaign.json)、[last-call](samples/last-call/campaign.json)。

尚未验收：真实模型质量、真实计费硬上限、任意恶意插件网络隔离、完整控制进程崩溃恢复、上游二进制可复现构建。详细限制及未来字段见 [Gate](03_gate.md)。
