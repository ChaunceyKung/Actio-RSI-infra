# F01–F05 审阅闭环

本轮依据真实发行物行为修正 2026-10-05 规划。独立证据索引见 [manifest](evidence_manifest.json)，旧 E001–E042 不重编号、不改写旧测试日期。

| Finding | Evidence | Decision | Changed files | Verification | Remaining risk |
|---|---|---|---|---|---|
| F01 发生身份含 mapper 版本 | `events.json` 7 项；`event-integration.json` 真实 journal 12 条、seq 0–11、24 个语义 slot | occurrence=producer+逻辑 stream 实例+native id/seq；projection 才含 mapper revision；效果键 consumer+occurrence+slot。原子切换 consumer pin，不双消费 | planning 05/10/13；`event_probe.py`、`runtime_cases.py` | 重复投递、v1→v2、一对多、raw hash 冲突、新 stream seq 复用、乱序补齐、commit/ack 丢失通过 | 无真实 physical generation 迁移/远端 outbox/断电验证；新增 slot 必须独立迁移 |
| F02 权限早于 rewrite | `tools.json` 中 pre-execute→rewritten→final-guard deny；`constraints.json` | 前置检查只预检；dispatch 前对最终 schema/scope/hash/tool artifact/policy/run/lease/expiry/budget 校验；任何后续变更使原许可失效 | planning 05/10；`provider_policy.mjs`、`runtime_adapter.py` | allow=1，deny=0；改参、过期、policy/lease/scope/run/toolVersion 错误、缺许可、schema/key scope/budget 错误均0调用 | 仅验证可信冻结 plugin 闭包；没有任意第三方 plugin、热更新或 sandbox 安全结论 |
| F03 Python/TS 审批箭头无实现 | `tools.json`、`policy-isolation.json`；原生 SDK 三方法源证据 | 选择方案1：Python 冻结策略 artifact，TS 本地执行策略并记录决定，Worker 独占 MCP invocation。动态逐调用 Python 审批 unsupported | planning 03/05/10/13/17；相同 plugin/adapter | op→callId→session/seq 对齐，双home同op分别1/0调用；dynamic、missing、过期策略拒绝。静态 timeout/disconnect 仅测试“不可用状态拒绝” | 没有动态往返协议，未声称其 timeout/disconnect/cancel 互操作通过。未来引入需单独协议和测试 |
| F04 源码/SDK/二进制 pin 混淆 | `artifacts.json`、两个 download JSON、`installed-artifacts.json`；取消与消息形态差异 | 分别 pin source SHA、distribution version、wheel hash、exe hash、OS/arch。握手0.0.1/包内0.0.0-dev不作release证明 | planning 02/14/18；requirements.lock、artifact脚本与报告02 | 40个wheel实际hash逐一匹配PyPI；SDK三个文件与固定source文本相同；exe另算hash；真实启动通过 | binary→source SHA 未证，不能因 Python 文本一致推导全部 TS 相同；再分发闭包另审 |
| F05 先冻结全部合同再探针 | 本轮实际顺序与 G0/G1/G2 结果 | B01a主路径→B02a草案→B03/必要B05/B07/B08 probes→B02b最小合同冻结 | planning README/02/11/12/13/14/17/18 | 本轮只安装主路径闭包；完整10 API、full resume/fork不作为G0；无live预算仍完成其余包 | 工程预算不是交付保证；未来产品 slice 仍需运行/恢复验收后才 B09–B11 |

F01 规则需要区分三种“重启”：同一 journal 的进程重启保留发生身份；新创建 session/store 使用新逻辑 stream；格式升级的 physical generation 必须提供沿袭映射。本 wheel 重启同 ID 是拒绝而不是 resume，因此尚无“跨 physical generation 自动接续”的动态证明。实验中的独立新 stream 用显式分配 identity，不靠时间戳推测。

F02 的最终 guard 确实在本轮 rewrite 之后运行，但源码中较新的 cancel 决策不能直接套到本 wheel。保留 [失败记录](evidence/native-cancel-limitation.json)：已有许可的合成只读调用在该分支仍到达工具。最终 profile 在取消前置请求时使用已验证的 deny，精细语义 cancel 留在 G1，未制造“取消通过”的假结果。

C01 由“默认补齐整个生命周期”缩为：先产品化已验证的 B 适配（supervisor、冻结配置、receipt/unknown ledger、flush/cursor 交接）；公开 status/cancel/resume/fork/catchup 只有需求出现时再评估窄 C。上游源码 patch 数为0。
