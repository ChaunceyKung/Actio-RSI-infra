# Gate 与停止边界

**Phase1B CONDITIONAL_GO**：仅 Windows x64 / Python 3.12 / DSH SDK 与 runtime-bin 0.1.5rc1 / 冻结受信只读 profile / 合成 fixture / 单 store 单活动 run。B1.1–B1.4 的身份持久化、受管执行、真实 facts 链、最小 memory、助手与两实体社会场景，以及关键失败核对成立。逐项实际命令、源码 hash、退出码和限制见 [manifest](evidence_manifest.json)，实现解释见 [结果](02_results.md)。

准入的是这条有限产品路径，不是完整 MVP、生产就绪、社会测量效度或能力提升。真实 SDK、TS loop、MCP stdio、native journal、Concordia Engine/ActionSpec/GM 边界已运行；provider/GM 输出均为固定 fixture。没有切换 Strands 或改造上游代码。

## 能力状态

| 能力 | 本轮状态 |
|---|---|
| 稳定 Agent / 不可变 spec / 重启查询 | 支持；同 key 同输入不重新派发，输入冲突拒绝 |
| 新 native session / 当前 host 两个受限串行 turn / 只读 MCP | 支持；每 run 最多两个 turn，单个 worker 顺序使用 |
| 本地台账 status / bounded stop | 支持；stop_requested 独立，强停保留 incomplete/unknown |
| 受管 journal 的只读 reconcile | 支持；补 facts 不补造未知效果、不自动重试 |
| episodic memory / 默认 branch / 私有 namespace / 显式跨环境共享 | 支持；CAS、来源、effect receipt 原子提交 |
| 冻结社会场景起点重执行 | 支持；新 run/creation/stream；只比较 world 语义；不回写原 memory |
| native reopen / resume / fork / online catchup / semantic cancel | unsupported；CLI require 明确拒绝 |
| mid-run 完整 world restore / 动态逐调用审批 / 写效果工具 | unsupported |
| live provider / SOTOPIA 真实 evaluator / 演化与训练 | 未执行；预算 0；产品 evaluator=false |

## 不能外推

未执行：SDK 解码前精确 wire 字节丢失、disk-full、系统断电/设备缓存持久性、physical generation migration、Linux/WSL、100-agent scale、远端 exactly-once。部分验收属于 controlled envelope：Job 分配失败注入、canonical 前异常 rollback；它们不等于真实断电。

官方二进制与已审阅 DSH source `5badb150…` 的构建映射仍 **UNPROVEN**。MCP 只验证官方 Python SDK 1.26.0 / stdio / 实际协商 `2025-11-25`；未验证其他 transport/version 组合。SDK 内部队列仍无界，依靠受管资源/时间上限，不宣称原生 backpressure 修复。SQLite FULL/WAL 和真实 flush 不是断电认证。

安装依赖仍需要 Windows x64 的对应 wheel；无缓存全量下载曾超时，缓存哈希验证与新虚拟环境安装已执行。GitHub 固定 Concordia 归档已下载并精确验证。完整日志留在 ignored 本地目录；交付中的关键摘要、hash 和复现命令不依赖这些旧路径才能重新运行。

## 下一最小 slice（未执行）

先独立审阅当前产品边界，再按新需求选择一个小范围：更严格的 schema/版本迁移与证据导出；或在明确 provider/model/凭据来源/请求输出/费用上限后做 live smoke。不要默认扩大并发、开放写工具或伪实现 session restore。

B09 仍须先修复原 scores 的四种错误类型，冻结有效性 envelope、实验单位、数据切分、rubric 和预算，再决定 evaluator pilot。Raven selector、candidate 搜索、演化准入、Graphiti、远端部署、训练均不在本轮。

本轮仅本地提交，未 push/merge/deploy。完成交付检查后停止。
