# 实现与验收

日期 2026-10-08。模型预算 0；没有调用真实模型、研究 evaluator 或第三方写效果工具。Phase 1A `56865ac` 之后的所有实现和失败记录在本目录独立保存。

## 实现边界

| 所有者 | 实现 | 关键约束 |
|---|---|---|
| SQLite 台账 | `store.py` / `schema.sql` | 不可变 AgentSpec；request key+输入 hash；唯一 lease、递增 epoch、owner PID+创建时间；新 run/stream/creation；派发前 intent |
| 受管执行 | `runtime.py` / `supervisor.py` / `host.py` | 自有 Popen SDK host 先进入命名 Windows Job，再放行 stdin；SDK 仅公开 API；关闭/超限清理整棵树 |
| 静态许可 | `plugins/guard.mjs` | 最终 schema/完整 registry/工具文件 hash/参数/run/session/creation/epoch/expiry/预算；未知默认拒绝；callId 不预登记 |
| 模型与工具 | `fixtures/provider.mjs` / `mcp_server.py` | provider 只替代模型输出；DSH 实际 loop/工具 dispatch；官方 MCP SDK 固定只读合成键，无用户文件路径 |
| 原生事实 | `facts.py` | 逐行受限读取，只读 native v3 journal；逻辑 stream+seq 去重；UTF-8 原始行去 CR/LF 后 hash；冲突保留双方，连续 cursor 不越 gap |
| 最小记忆 | `memory.py` | episodic 一种；namespace、来源、CAS、revision、effect receipt 同事务；consumer pin 显式迁移；受控 correction；冻结检索快照 |
| 两场景 | `scenarios.py` | 助手与真实 Concordia external Entity 使用同一 RuntimePort；ActionSpec 先验证；GM intent 与 resolved world 表分别保存 |

产品不导入 probes。测试故障注入仅存在于 `tests/`；测试 close-host helper 临时进入测试 venv，不打进产品 wheel。未改变 DSH/Concordia 参考仓库，没有上游 patch。

## 完成和失败

`dispatch_intent → accepted/messageId → native observed → flush marker → canonical contiguous prefix → domain receipt → execution_complete` 各有记录。发行物的成功原生 turn 终态为 **completed**，provider 的 finish **stop** 不是同一个状态名。

plugin 通过本次受管进程的 append-only spool 交接 flush，host 经自己的 spool 返回，绑定 run、native creation、session、epoch、operation、nonce、receipt、terminal seq 和 through。控制进程验证 nonce、绑定和 journal 中的实际 receipt/终态。只有单活动 turn；前一 turn 的 domain effect 未确认时不得继续。真实同 host 两轮测试证明 receipt/operation 不混淆、seq 递增、旧 marker 被拒绝。

原生事件 projection 的 `audit` slot 不产生 memory。只有显式授权 `assistant.final` slot 的一次 memory 写入产生 episodic effect。mapper v1→v2 重投影与重复 receipt 不产生新经验；增加未授权 slot 被拒绝。Memory correction 留新 revision，旧 snapshot 仍读取旧内容。

任务结果与轨迹独立：非法 action 是 task_failure，可有完整拒绝轨迹；runtime/receipt/flush 缺证维持 incomplete、unknown/needs_reconcile；未派发的初始化失败为 infrastructure_failure。`stop_requested` 与执行终态独立。停止/期限均不表示工具效果已回滚。reconcile 只读取已登记 stream 的受管 journal，不创建新 worker、不重发 prompt，缺领域回执不升级成成功。

## R1–R5

| 发现 | 处理和验收 |
|---|---|
| R1 | 独立最终 guard；完整 registry 的实际 hash 比较；工具文件 hash 比较；合法任意 callId 通过；scope/绑定/expiry/schema/late registry/rewrite/budget 拒绝零 MCP received；同 creation 重复或冲突 ID 无第二次派发，不同 creation 同 ID 各自正常；Python/TS 含非 BMP 键的受限 JSON hash 一致 |
| R2 | 独立受控 spool 和 operation 绑定；真实 flush、journal receipt/terminal、连续 cursor 与 domain receipt 共同确认；旧 marker、gap、冲突、partial tail 拒绝完整性声明 |
| R3 | SDK host + Windows Job；启动闸门、非继承句柄、kill-on-close；init/run/drain/close/MCP 卡住/Worker exit/supervisor death/assignment rejection/慢消费/条数/单条限额均有证据；异常前缀保留，Job active=0 |
| R4 | namespace 最少 project/agent/environment/branch/visibility；agent 不可省略；A→social 显式授权；CAS+memory+source+effect 一事务；ack 丢失和 mapper 迁移不加经验；来源和跨 namespace 拒绝有断言 |
| R5 | 产品 evaluator capability=false；未搬原函数。旧 scores 为 null/list/number/bool 时未捕获异常，继续作为 B09 启动前的结构验证和四项回归前置，不宣称修好了旧 probe |

## 资源合同

默认 initialize 25s、turn result 15s、drain 4s、close 3s；同一个 host 的所有受管等待共同受 75s wall-clock 执行预算约束。run 自创建起 180s 后不接受新派发，最多两个 turn、两个 worker（逐个执行）。SQLite TTL 绝不自动释放活动 lease；idle host 使用者必须关闭 RuntimePort/context manager，不能把 TTL 当后台回收服务。

每条 spool/journal 行上限 64 KiB，每个通道总量 8 MiB、4096 条；超限不消费半行、不丢弃后宣称完整。SDK 自身内部队列仍无界，未宣称修复；Job 每进程 768 MiB、总 1536 MiB、最多 12 个进程，配合阶段和全 host 时间预算限制损害。任务目录每次 poll 检查 128 MiB/2048 个文件预算；这是有界监测和终止，**不是文件系统硬配额**，poll 间可能短暂超出阈值。无 disk-full/物理断电结论。

memory 单条内容至多 16 KiB；检索最多 32 项，默认 8 项，并在 16 KiB 内容预算处停止，保存实际 ID/revision/顺序/truncated/context hash。没有 embedding 或第二模型循环。

## 故障窗口与证据强度

| 窗口 | 实际动作与结果 | 强度 |
|---|---|---|
| A | 官方 SDK 返回 accepted 后、应用 receipt 提交前控制进程 `os._exit`；Job 自动清理；重开为 needs_reconcile；相同请求返回原 run，worker 数不增 | 真实进程死亡；不是 wire 字节丢失 |
| B | MCP fsync received marker 到达后，终止已登记 SDK host；工具结果为空，收到次数=1，状态 unknown/incomplete，后代全部清理 | 真实受管进程 kill；只读合成工具 |
| C | host 已返回真实 flush、canonical 尚未开始时抛注入异常；只读 reconcile 补齐并去重，MCP 总次数仍=1；缺 domain receipt 保留 unknown | 精确边界异常；不是该瞬间 OS kill 或断电 |
| D | memory/source/effect 已事务提交，调用方收到 ack 之前 `os._exit`；重开重复消费只返回原 ID/revision，memory/effect 均=1 | 真实进程死亡；不是系统断电 |

Job 分配失败路径使用测试侧构造器拒绝注入，验证未放行等待子进程即被终止；不伪称实际 OS 拒绝原因。两个控制进程竞争同一 SQLite，仅一个取得 lease；owner PID 创建时间及命名 Job 核对防止凭 TTL 接管或 PID 复用误认。

## 安装、许可证和保留的失败

41 个锁定 wheel = 原 40 个最小闭包 + 构建用 `setuptools==80.9.0`（MIT，wheel SHA256 `062d34222ad13e0cc312a4c02d73f059e86a4acbfbdea8f8f76b28c99f306922`）。没有全局安装；Concordia Apache-2.0。实际 license metadata、LICENSE/NOTICE 文件 hash 和运行 pin 由 artifacts evidence 登记；DSH runtime 的依赖再分发/SBOM 与 binary→source provenance 仍未完成。

保留失败：首次 pip 在线下载 72 MB runtime 在约 42.5 MB 处超时；首次 runtime 文件筛选把附带 rg.exe/console exe 一并计入导致 pin 拒绝；初始终态把 provider stop 当成 native completed，完成谓词拒绝；首次 GitHub Concordia 归档因 Windows git archive 的 CRLF 版本 pin 被拒绝。没有把失败改成 PASS。

Concordia 修复没有忽略 hash：固定 commit 的 241 个 Python 文件及 LICENSE，在 command-local `core.autocrlf=false/core.eol=lf` 下与 GitHub ZIP 逐字节一致；最终 pin 为精确 LF 文件 hash，GitHub ZIP 另有整包 hash。参考仓库配置不改。详见 [归档比对](evidence/concordia-archive-comparison.json)。安装器的 pip/git/venv 子进程同样使用 allowlist 环境；初次隔离构建的深 TEMP 报 WinError 3，改用带 owner 标记的短 TEMP 后成功，失败日志保留。

最终 suite 和实际退出码以 [manifest](evidence_manifest.json) 为准。证据 JSON 提交 Git，完整合成 raw journal/SQLite/log 留在对应本地任务根，并为当前验收生成 ignored raw.zip 与 hash。依赖缓存缺失时按 README 的锁文件、固定归档重新准备；不能用作者路径充当运行依赖。
