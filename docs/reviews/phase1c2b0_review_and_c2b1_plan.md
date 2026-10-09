# Phase 1C2B0 审阅与 C2B1 行动方案

审阅基线：`f65045a11d1a4728b98b5564623e4827365f91c8`，已核对本地与远端 main、C2B0 任务分支一致。日期：2026-10-09（Asia/Shanghai）。

**维持本机准备工程 CONDITIONAL_GO。下一阶段建议直接进入 Phase 1C2B1：完成受控执行入口，然后经人类确认做单 episode 的 solver 连接 smoke。** 不再单独开一轮同类 readiness 或扩大 fixture 数量。

用户已在本轮明确选择：**先完成执行入口和批准包，下一 session 首次真实调用前再确认。** 当前仍未授权 provider/model、真实预算或凭据读取。用户也已明确要求成果推送到 main，仓库 AGENTS.md 与新 Prompt 同步了这一交付目标；历史原件不改。

入口：[执行 Prompt](../prompts/phase1c2b1_gated_solver_smoke.md) · [审阅证据](phase1c2b0_review_evidence.json)。

## 复核结果

| 项目 | 本次独立核对 | 适用边界 |
|---|---|---|
| 产品与交付 | 51 个阶段 artifact、41 个产品文件、23 个测试、32 个工具、4 个锁/包配置、2 个入口、1 个中间源码归档、6 个准备日志匹配 | 精确字节 SHA256 |
| 安装环境 | runtime/release 各 41 个文件与当前源码匹配 | 本轮未重装或启动 DSH |
| 已发表验收 | 14 suites / 68 组的最终成功结果与源码、测试绑定一致 | 本次不宣称重跑全部 68 组 |
| 本次配置回归 | 11 项通过：preflight 5、transport_config 3、readiness_config 3 | 真实模型与 HTTP 均为 0 |
| 本机原始材料 | 43 个运行 ZIP、5,269 成员，加 1 个公开来源 ZIP、9 成员，共 13,092,182 bytes | 归档与成员均重算 hash |
| 历史接收/发送 | 从 service 文件与只读 SQLite 重新核算 162 sending / 158 receives；最终子集 85 / 83 | priced 76 / 74，旧 v3 86 / 84；不是新增请求 |
| 当前样例 | success、stall、length、last-money 全通过只读 reader | 有 socket/subprocess/写入拒绝；valid 不等于任务成功 |
| 固定旧版 | C0 12 records、C1 22 records 及 campaign、C2A.1 三个样例通过 | reader 源码与受信 Git commit 比对 |
| 历史文件 | 612 个核对：572 个字节一致，40 个 checkout CRLF/LF 差异 | 40 个分别确认 LF hash 匹配、Git blob 在 f5b8f92 与 f65045a 间不变；未改旧文件 |
| 清理 | 219 个具名 Job 均无活动进程；95 个历史端口无监听 | 不按 PID 杀进程；95 个线程 joined 是已核对的历史记录 |

初次审阅的严格历史字节检查因 checkout 换行失败，失败摘要保留在新审阅 JSON。后续只对列明的 40 个路径验证 Git 内容等价；没有放宽 artifact、数据库、源码、ZIP 或所有文件的 hash 规则。

本轮新增模型请求、外部 provider 请求、本机 HTTP 接收、DSH Worker、evaluator 调用与真实费用均为 **0**。公开官方文档读取及 Git 操作单独计算，不属于模型 API。

## 对当前实现的判断

已完成的预算原子性、未知占额、内存假凭据、官方 adapter、超时和只读对账可以继续复用。旧 v3 TIMEOUT 及同参数重跑保留得当；只能说明发生过时序敏感失败，不能把“当时并行运行”写成已证根因。

当前 `readiness_contract.py:117` 的 execute 无条件抛出 BLOCKED；TransportPort、host 和 Ledger 同时限制 priced_rehearsal 与 ACTIO_FAKE_。因此“默认关闭”已验证，**“批准后能够执行”尚未实现**。这符合 C2B0 范围，并非运行缺陷，但下一轮不能靠填批准 JSON 就宣称功能已经存在。

以下是进入 live 必须补的差异，不构成推翻已限定本机 Gate 的结论：

| 编号 | 缺口 | 下一轮验收要求 |
|---|---|---|
| B1-01 | 当前 BLOCKERS 把人类授权、计费假设、供应商兼容、未实现入口混在固定列表 | preflight 分开“发送前必须满足”与“本次 smoke 要观察”；供应商兼容和账单对账不能反过来成为首个 smoke 的循环前提 |
| B1-02 | 报价/上界仍有假设，tokenizer 映射与 context 上界被同时列为 blocker | 接受有依据的上界方法之一；未证实部分保留 conservative_assumption，由具体批准包说明，不能篡改 input_bound_verified 或宣称绝对硬封顶 |
| B1-03 | candidate 带两张占位身份卡，尚无 live episode 队列及批准后的发送检查 | 默认只建议 compatible 一张卡、1 episode、A→B；冻结具体身份/spec/memory 与 episode ID，每次 reserve/sending 复核批准 hash、期限、权限和剩余额度 |
| B1-04 | 现有 export/analyze 依赖本机服务 receives，且只支持 stub/rehearsal | 新 live 模式用客户端原生观察、响应 ID/usage 对账；不生成假的供应商服务日志，无独立接收数据时保持 null |
| B1-05 | 当前接收 model 列表只有请求别名；128 个 adapter chunks 是旧本机配额 | 查明官方响应标识示例与长度范围；批准时冻结有限 allowlist/边界，未知实际响应就停，不在付费失败后自动放宽并重跑 |
| B1-06 | request 级 usage 可 settled，但结果/协议异常的 campaign 停止仍需独立控制 | length、unknown、协议错误等由 run/campaign 控制阻止后续发送；账务 settled 不能自动解除运行停止条件 |
| B1-07 | 新授权的权限与账本生命周期尚未存在 | 同一批准只能绑定一个 authority/ledger/固定 episode 队列；崩溃后只报告和阻断，不换库恢复预算、不自动重试 |

凭据过滤的现有测试证明固定受信路径没有随机 sentinel 落盘；它不是任意输出内容的机密隔离证明。下一轮只为新增真实凭据解析入口补相应检查，检查分段诊断输出、异常和日志路径，不重做通用 secret 管理平台。

## 报价与预算决策

本轮重新读取 [Pricing](https://api-docs.deepseek.com/quick_start/pricing/)、[Chat API](https://api-docs.deepseek.com/api/create-chat-completion/)、[Token Usage](https://api-docs.deepseek.com/quick_start/token_usage/)。三页 hash 与 C2B0 来源相同；页面仍以 1M 表示上下文，token 页仍给近似字符比例和未明确绑定当前 Flash 的 demo tokenizer。精确单位/计费输入上界没有新增证明。

当前提案以 1,048,576 输入、64 输出、缓存未命中/峰值价计算：

- 每次预留 **$0.314649600**；
- 1 episode / 最多 2 次发送的保守估算合计 **$0.629299200**；
- 可在下一 session 提出 **1 USD** 作为这次试运行的本地记账限额，但它现在不是实际执行预算，也不是已获批准的费用。

不要把“不存在未来调价或任何额外收费”当作能由离线工程绝对证明的命题。应该明确列出供应商公开合同支持的内容、保守假设、价格窗口和异常停止策略，让用户对具体的一次试运行作决定。若用户要求真正不可突破的供应商账单硬上限，则需供应商侧确证的额度约束；单靠本地 SQLite 或上述 1 USD 配置不能承诺这一点，也不自动充值/创建账户。

对仍有假设的路径，批准包须明确请求用户接受相关残余风险；不能把泛泛的“开始下一阶段”当成接受。若用户不接受或缺乏足够依据，则保留 BLOCKED。这样无需无限等待 tokenizer 完全匹配，也不会伪造保证。

## 下一阶段顺序与停止点

1. **完成入口**：新增明确 live 模式及版本分派，复用现有 SDK/Worker/Ledger/Concordia；先做零外部调用的本机验收。
2. **完成具体批准包**：冻结 compatible 卡、1 episode、最多 2 次 solver 尝试、候选 deepseek-flash、明确 URL/报价/credential reference/timeout/停止规则；初始实际批准为空。
3. **发布准备成果到 main**：验证代码与文档后 commit、普通 push，并核对远端。准备阶段也应有完整交付，不等到用户答复才发布。
4. **首次真实调用前确认**：按用户本轮明确要求，展示最终合同 hash、费用测算及假设，询问是否执行这一份批准包。只在确认后读取指定 credential reference。无确认时结束在 AWAITING_APPROVAL，真实调用 0。
5. **若确认并满足发送条件**：首 seat 同时作为连接检查，不另开未记账探针；A 成功且账務可信后才运行 B。任何 unknown、协议错误或额度到达就停，不凑成功补跑。任务合法未达成与基础设施故障分开报告。
6. **发布本次观察**：运行结果、失败、计数、估算与实际账单状态、清理证据另行提交推 main；停止于单 episode。judge、人工校准、研究效度、演化晋升仍 BLOCKED。

源代码到二进制的完整构建映射、完整 controller 恢复继续单列 unproven/unsupported；不声称已解决，也不以此为借口扩成本轮重建项目。

## 发布范围

本轮只新增审阅报告、审阅证据、下一 session Prompt，并更新 AGENTS.md 的 main 交付与首次 live 确认约定。产品、测试、依赖和历史 validation 不改。新 Prompt 中明确覆盖旧文档的“只推任务分支”默认，要求正常推送到用户指定的 [main](https://github.com/ChaunceyKung/Actio-RSI-infra/tree/main)，不 force push、不部署。
