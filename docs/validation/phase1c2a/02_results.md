# Phase 1C2A 实测结果

结论为 **NO_GO（官方 Messages adapter 准入）**。本轮 Prompt 明确允许在固定发行物不支持时，完成必要定位、报告差异及最小备选后停止。没有静默改用 Chat Completions、升级 SDK/runtime 或实现替代 solver。

## 已完成的产品修正

`src/actio/preflight.py` 使用 `pilot-config.v2`：GM 固定 `deterministic_local`，judge/retries/other 固定 `disabled`，远端 calls/tokens/cost 和价格数值为 0，provider/model/credential/报价文本为 null。solver 的 `transport_stub` 配置只允许精确 `127.0.0.1` HTTP origin、任务假凭据引用与合成报价；`future_live` 要求显式字段但始终不能执行。

严格拒绝未知字段、重复 JSON key、bool 代替整数、浮点/非有限数及无效角色组合。金额使用整数最小单位。`configuration_valid` 与 `transport_validated/live_authorized/live_ready` 独立；后三者始终 false。配置校验无 provider client/Worker/网络/真实凭据读取。CLI 仅读取指定配置，所有结果退出 2。

当前修正只改变配置合同。既有 fixture payload 仍有 scripted answer；旧 Engine、任务、verifier、evaluator 没有冒充新的 transport mode。新代码 pins 使用新身份与新库，旧 v1 和旧 pins 不自动迁移。

## 官方发行物定位（全部尝试保留）

| 探针 | 实际本机接收 | 观察与判断 |
|---|---:|---|
| [120113 / 默认 provider](evidence/probe-20261008T120113Z-193e30f2.json) | 1 | 官方 `deepseek-official` 发 `POST /chat/completions`、Bearer 假 key；Messages-only 服务回 404，DSH `HTTP_404`，没有完整 receipt。协议不匹配。 |
| [120331 / 429](evidence/probe-20261008T120331Z-22a0a59c.json) | 1 | 对实际 Chat Completions 路径回合成 429；DSH `RATE_LIMIT`；观察窗口内没有第二次接收。仅局部负例，`PASS_EXPECTED_PROTOCOL_FAILURE` 不等于 Messages 或预算通过。 |
| [120417 / 无效 patch 定位](evidence/probe-20261008T120417Z-17b747e8.json) | 0 | 改已有 entry 的 name 未正确替换插件，落回默认缺凭据错误 `MISSING_CREDENTIAL`；不能据此证明插件不存在。没有读取/提供真实凭据。 |
| [120540 / 正确 disable + insert](evidence/probe-20261008T120540Z-7784d62a.json) | 0 | 禁用旧 provider，再显式插入 API-key Messages 插件。真实 loader 报 `ERR_MODULE_NOT_FOUND`；SDK 初始化在有界 timeout 后失败。构成本轮停止证据。 |

合计 **4 次探针，2 次本机 provider HTTP 接收，0 次外部 provider/真实模型请求，真实费用 0**。两次线上捕获仅为本机合成请求。`llm/stream` 保留 SDK 原始错误；RuntimePort 将没有完整 receipt 的 operation 拒绝为完成。无 Messages SSE 成功、无可信 usage、无行动进入新 transport 事实链。

第二/三次尝试中的 loose-file `import()` 对两个 bundled 包都失败，是解析位置局限，不用于判定包缺失。最终 loader 失败和默认真实 wire 路径是结论依据。最后版本的探针另有精确 loopback URL/最多一次 fetch/禁止 redirect 的出口限制；首次探针尚无此附加限制，依赖显式本机 baseURL 与隔离环境。不能追认首次已执行后加的限制。

## 回归与版本复核

| 范围 | 通过组数 | 性质 |
|---|---:|---|
| preflight | 5 | 新角色/严格配置/零副作用/始终阻断 |
| task | 7 | 既有真实 SDK + Concordia fixture 任务、上下文、campaign、标注回归 |
| runtime | 2 | 既有真实 SDK/binary fixture 路径 |
| reliability | 7 | 既有异常/receipt/回收边界 |
| evidence | 7 | 既有导出与只读反例 |
| schema | 5 | 既有迁移和进程中断 |
| input_binding | 3 | 冻结输入离线反例 |
| sotopia | 3 | 固定抽取 parser/schema 受控回归 |
| evaluation | 8 | 确定性与预置响应评估、子进程审计 |
| 合计 | **47** | 原 42 组相关回归 + 新 5 组；不是研究样本量或新 transport 验收 |

最终 suite 明确列于 [manifest](evidence_manifest.json)，均绑定最终产品与各自测试源码；CLI/安装/Job 复核记录在 manifest 的 `delivery`。另建干净 delivery venv 安装最终源码，执行 core+eval pip check、公开 capabilities 与 preflight smoke。eval-only venv 的 core 依赖本来不全，不将它称为 core+eval pip check。

[固定旧版复核](evidence/legacy-20261008T121101Z-c31e817e.json)：C0 `1e85d8c2fb4a756de81acb333905190df9e97592` 核验原 12 条记录；C1 `af0a88cfff23c22c396fd7c9ef9916f0df8cd21f` 核验原 22 个请求和 25 登记的完整 campaign。标准库子进程禁止网络/runtime/Worker，evaluator 调用 0；当前 pins 明确拒绝全部 34 条旧记录。原目录逐文件 hash 未变。

## 失败、原始材料与限制

首轮 preflight 的审计钩子拦住 canonical 首次加载标准库 UTF-16BE codec：[失败原件](evidence/20261008T120832Z-ff0fbbab.json)。测试改为安装钩子前预热 codec 后通过；未放宽网络/环境/文件/进程限制。一次并行本地包构建遇 Windows `build/lib/actio/common.py` 文件锁，顺序重新安装成功。安装失败日志、测试失败、源码快照和四次探针全部保留并由 manifest 列出。

本轮具名 Jobs 从本轮 worker 表和测试记录独立收集、重新查询 active=0；四个探针服务完成 shutdown/server_close/thread.join。准确数量见 manifest 的 `jobs_inactive`，不复用历史 59 的数字。普通 CLI、评估和迁移子进程由有界 `subprocess.run` 返回/超时 kill+wait；不扫描或终止其他用户进程。

本机原始 SQLite/native journal/配置/log 留在 manifest 所列短根及 `.local/phase1c2a-raw` hash 归档，未上传 venv/二进制缓存或大日志。公开证据含合成 wire、错误、状态和 hash。hash 不是签名，也不证明源码与二进制构建映射。

尚未实施/验证：无答案双 seat 请求与第二步实际行动传播、新 transport 任务负例、500/断流/deadline/畸形响应矩阵、持久 reserve/settle/unknown、并发末额度、重复 attempt、未知 usage 保守结算、新 campaign 对账与只读篡改检测。已有 fixture/配置通过不替代这些项目。
