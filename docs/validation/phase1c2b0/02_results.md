# Phase 1C2B0 实施结果

2026-10-09（Asia/Shanghai）完成本机接入准备；`local_readiness_engineering=CONDITIONAL_GO`。这不是供应商兼容或真实费用验证。真实模型请求、外部 provider 请求、实际费用均为 **0**；实际供应商接收和账单字段保留 null / UNVERIFIED。全部 Gate 见 [03_gate.md](03_gate.md)。

## 实现与验收

新增 `pilot-config.v4`、`scheduling-priced.v1` 与 `sdk-minimal+actio-priced-memory.v1`；候选为官方 `deepseek-flash` 的 POST `/chat/completions`。固定 DSH SDK/runtime `0.1.5rc1`、官方 serializer/translator、Concordia 及锁定依赖均未升级。复用现有 Ledger、发送 gate、双 seat 和 campaign，新增 USD 整数报价、独占 authority 路径绑定、内存凭据注入、分层期限和默认拒绝的公开入口。源码与 runtime/release 两个安装环境的 **41 个产品文件逐字节一致**，均通过 pip check。

最终 **14 套件、68 组行为测试通过**；加上中间批次及一次失败共 **17 次套件执行、80 个测试执行**，不将重跑计作新增行为覆盖。最终套件依次为 preflight 5、transport_config 3、task 7、runtime 2、reliability 8、evidence 7、schema 5、input_binding 3、sotopia 3、evaluation 8、transport 4、budget 4、readiness_config 3、readiness 6。命令、源码 hash、退出码、完整测试日志见 [交付记录](evidence/delivery-20261009T024051Z-23cdb367.json) 和 [manifest](evidence_manifest.json)。

新版验收覆盖：空批准/零预算/过期或不匹配批准均拒绝，环境与网络访问 guard 下仍能生成 proposal；整数缓存计价、保守 reserve、过期报价和不足额度；独立控制进程分别争抢最后调用和最后金额；Worker 在 reserve 后、sending 后及结算前退出；pending/unknown 重开仍占额且不能更换数据库花费同一 authority；重封后的币种、报价、金额、归属和分母篡改均被离线 reader 拒绝。

官方 adapter 的 attached usage + DONE 通过；成功、冲突卡、非法动作均核对实际 wire，B 只看见 A 已发生的公开行动。400/401/429/500、无首响应、流停顿、持续 heartbeat、不完整/非法/超限 usage、响应 model 改变均保留异常，不隐式 retry。3.5 秒延迟成功，超过旧 fetch 3 秒界限。无首响应/idle/整请求分别由新期限中止。所有失败场景保留已发生的世界效果和原始观察。

`length` 实测 **两个估算 settled，场景 partial / infrastructure_failure，仅 A 的世界效果已发生**；不会因费用可结算而判定任务成功。缺 usage 不补零，超限不截断。受信 profile 范围、精确计费输入界限未核实、完整 controller 恢复未实现等限制见 [合同](01_contract.md) 和 [费用/凭据/超时](05_cost_credentials_timeouts.md)。

## 本轮计数

以下只统计 C2B0 新发生的本机实验；不加入 C2A.1 历史 190 次接收。sending 是一次性资格的持久消费，不是独立服务接收证明。SQL-only 克隆账本不进入请求分母。

| 范围 | 本系统 sending | 本机服务 receives |
|---|---:|---:|
| 新 USD 预演，含中间批次和两次 CLI smoke | 76 | 74 |
| 旧 v3 回归，含失败及重跑 | 86 | 84 |
| **整阶段合计** | **162** | **158** |
| 最终源码批次（上面合计的子集） | 85 | 83 |
| 其中最终 USD 预演 | 38 | 37 |

4 次 sending 与 receives 的差异来自显式发送前中断（新版两批各一次、旧版预算回归一次）及旧版失败批次在实际 fetch 前超时一次。另有 reserve 后但 sending 前中断，不能因未接收而退款；这类记录占额但不计 sending。

USD 预演累计 98 个登记 seat：50 settled、28 unknown、8 denied、12 not_run。模拟可信 usage 合计 600 input / 250 output，按冻结报价计算的已结算估算为 **423,552 nano-USD（$0.000423552）**；含未知预留的账本保留总额为 **8,810,612,352 nano-USD（$8.810612352）**。它们来自多份独立测试预算，不是单次批准额度或真实账单。旧 v3 累计 102 个登记 seat，合成已结算用量 672 input / 280 output、952 SYNTHETIC 单位；不得与 USD 相加。

报价为 `deepseek-flash-2026-10-09-peak.v1`，1 USD = 10^9 nano-USD。1M 的精确定义、当前模型计费输入上界和额外/错误费用未核实，故 `input_bound_verified=false`，live 仍 BLOCKED。候选单次保守包络 **$0.314649600**，1 episode / 2 请求 **$0.629299200**，2 episode / 4 请求 **$1.258598400**。这些只是提案；实际执行预算仍全 0。[批准包](approval_package.json) 绑定具体任务、实现、报价和合同 hash `1afc7cc1d3f9db84538c82e4a338e564fb2adf984d16d11e01abf4f7c411405f`。

## 失败保留与清理

[首次旧 v3 transport 记录](evidence/20261009T023138Z-9254e552.json) 的 500 场景预期 2 次接收，实际 0。A 已持久提交 reserve/sending，随后原生终态为 `TIMEOUT`，`LLM_STREAM_IDLE_TIMEOUT` / `DeepSeek stream idle timeout after 1500ms`；原始响应 status=0、raw 为空。账本保留 unknown，B 未执行。发生时有其他测试与依赖准备并行，但调度压力只是可能原因，未证明根因。

等待其他任务结束后，[原参数顺序重跑](evidence/20261009T023927Z-ea732826.json) 4 组全部通过，再顺序执行预算 4 组通过。没有放宽旧 v3 deadline、删除失败或用重跑替代首次事实。原始超时摘录及文件 hash 见 [失败诊断](evidence/failure-note.json)；测试记录中的命令是 runner 生成的复现命令，后两次实际启动未加 UTF-8 标志，详见 [实际调用注记](evidence/command-annotation.json)。中间新版 5 组通过后，补入提案实现/任务绑定、sending 时报价检查和 stderr 定向测试，再以最终源码验收；初次源码快照与所有实验根保留本地 hash 归档。

共 **45 份逐次假凭据扫描记录**，覆盖配置、SQLite、native/cache、stderr 等全部生成文件。专门的 stderr 测试使上游写入内存中的随机 sentinel 后异常退出，最终诊断为 `[credential omitted]`，服务接收 0；过滤在日志写入之前发生。交付另扫 **5,514 个归档候选/公开文件**，无随机 sentinel。预算 helper 使用显式清洁环境且拒绝带入 key。仅证明固定受信路径，不宣称隔离任意恶意插件。

清理核验 **219 个登记 Job 均无活动进程**，其中 217 有实际 PID、2 为测试登记；95 个服务线程全部 joined，95 个相关端口无残留监听。所有纳入检查的数据库读前/读后 hash 一致。43 份运行根原始归档及公开来源 HTML 归档保存在本地 `.local/phase1c2b0-raw/`，共 44 个 zip，13,092,182 bytes；Git 只公开合成样例、必要来源和摘要/hash，不包含 venv、二进制或原始大日志。

## 可移植交付与历史边界

公开样例：[成功](samples/success/campaign.json)、[流停顿](samples/stall/campaign.json)、[length](samples/length/campaign.json)、[最后金额竞争](samples/last-money/campaign.json)。均由当前只读 reader 重新核验，evaluator 调用 0。标准库 portable 测试明确禁止网络、子进程、写入和 runtime 导入；离线验证不依赖原数据库路径。

[干净环境 CLI 证据](evidence/cli-20261009T023243Z-0ecdeaa2.json) 实测 plan、preflight、execute 拒绝、本机 rehearsal、verify、export 和 pip check。复现命令见 [04_usage.md](04_usage.md)。公开来源访问时间、摘录及 hash 见 [sources.json](sources.json)；精确 DSH tag/SDK 依据见 [upstream.json](upstream.json)。

[历史只读复核](evidence/legacy-20261009T023324Z-20877b5a.json) 用固定 C0/C1 提交验证 12 / 22 records，C2A.1 用固定 `b086cbae97fcebd5c818dce611a0c2a331380cb1` 验证三个公开 sample；artifact 不能选择 reader 源码。所有历史文档、manifest、失败及上游参考 checkout 保持原样。没有真人校准、judge 或独立研究单位。

本轮只交付并普通推送 `phase1c2b0-solver-live-readiness`；未推 main、未部署、未进入 C2B1。Git 提交与远端 SHA 在推送后单独核对，manifest 不自嵌未来提交 SHA。
