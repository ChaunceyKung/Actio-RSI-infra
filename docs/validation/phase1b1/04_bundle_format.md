# 证据包 v1 与独立核验

公开入口：`actio --db DB export RUN --output NEW_DIRECTORY`、`actio verify DIRECTORY`、`python -m actio.verify DIRECTORY`。最后一种入口仅导入标准库及 `actio.common/terminal/verify`；不要求原 DB、DSH home、Concordia、发行物缓存或作者目录可用。格式草案见 [example](format_example.json)，实际可验包见 [samples](samples/README.md)。

## 文件合同

| 文件 | 内容与权威 |
|---|---|
| manifest.json | `format=actio-evidence`、整数 `version=1`、source store/run/schema/active_lease；所有附带文件的固定名称、精确 UTF-8 字节大小和 SHA256 |
| evidence.json | 单 run 的原始历史状态与冻结 input/hash；所引用 AgentSpec/Persona/pins；request_identity；worker 清理报告；stream/native creation/header；operation；native raw occurrence/hash、projection/cursor/conflict；audit、world/domain receipt、scenario_terminal；实际 memory snapshot 与有界来源证明 |
| verification.json | 导出时重新计算的分层核验结果；不是权威的 PASS 标签。存在时必须与此次重新计算一致，可以省略后独立重算 |
| export.json | 时间与读取/审计范围说明；不影响内容 hash。存在时需为可解析 JSON；不是来源认证 |

仅接受目录与固定文件名，无 ZIP/TAR 解包或文件引用执行。拒绝重复 JSON key、未知格式版本、链接/reparse 路径、额外文件、超限和未知 schema。单包读取总量至多 32 MiB、顶层记录至多 20,000。导出遍历同时限制 20,000 SQL 行与 16 MiB 原始行序列化预算，最终内容留出 1 MiB 给 metadata，memory 闭包至多 64 个 revision。超限不静默截断成 complete。

`manifest.json` 必须引用 `evidence.json`，所有附带的 verification/export 文件也必须登记 hash/大小；清单和实际文件集合一致。manifest 自身的 hash 由交付 evidence_manifest/外部保管者登记，不能自签真实性。对 JSON 对象的语义 hash 使用项目既有受限 canonical JSON；native `raw_hash` 则是原始 UTF-8 行去除 CR/LF 后的 SHA256，不重新序列化 native 内容。header 使用原台账保存的解析内容。schema/mapper/pin 变化需要显式版本，不能用新 parser 假装补齐旧事实。

## 一致性与最小闭包

导出以只读连接开启一个 SQLite read transaction，第一次查询固定快照；所有后续 run、事实、memory、lease 查询都来自同一快照。不会 collect 新原生文件、执行场景、启动 worker、检索产生新 retrieval 或修改 spec。原始事件副本来自已登记 SQLite occurrence，足够脱离作者目录核验；没有声称导出时重新审计未导入的原生文件。

本 run 的每条 occurrence/projection、intent、accepted、flush 和 domain/world 引用都能在包内解析。验证连续 seq、实际 cursor、原生 header/creation、receipt 到 completed 的区间、marker/run/epoch/nonce、实际原生 prompt 与 dispatch intent、最后 assistant source 和领域回执。不能只凭 operation.state 或 trajectory 字段成立。

对 memory：冻结 namespace/as_of/实际顺序/limit/byte_limit/truncated/context_hash；逐项附对应 memory revision、source occurrence、source stream/header、projection、最小 origin scope、episodic effect 与必要 correction 审计。不递归复制前序 run 的其他 identity、memory 或全轨迹。该证明核验所选 memory 的来源与映射，**不认证整个前序 episode 完成，也不证明未选数据的完整性**。所引用 closure 缺失必须报告 missing；不能以作者的绝对路径代替内容。

包包含本次合成审计所需的 private observation/GM/memory。它不是 agent 上下文包，不修改 namespace ACL，不回灌 solver。公开 samples 无凭据和真实人员数据；保留 native 行的精确 hash，不通过修改原始行来做“脱敏后仍声称原证据”。完整 raw archive/SQLite/日志只留 ignored 本地目录。

## 结果维度

| 字段 | 意义 |
|---|---|
| bundle_integrity | valid/invalid：固定清单、内容 hash/大小、格式与可解析结构 |
| facts_consistency | consistent/partial/invalid：可用内部事实是否一致；缺前缀/回执为 partial；相互矛盾为 invalid |
| recorded_prefix | consistent/partial/invalid/unverified：与整集 scenario 完成分开 |
| scenario_completeness | complete/partial/legacy_unverified/unknown：场景终态和冻结规则是否成立；活动 lease 一律不能 complete |
| task_outcome | success/task_failure/infrastructure_failure/unknown；合法非法行动拒绝为明确 task_failure |
| execution_mode | fixture 属性；任何结论都须结合完整性维度和固定 provider/GM pins 阅读 |
| historical_claim | 原 run.state/task/trajectory，和当前核验并存，不回填旧证据 |
| source_trust_limits | hash 不认证作者/签名/上游 binary-source，也不证明 live 模型或能力提升 |

退出码 0 表示封装有效且未发现内部矛盾；合法 partial 仍可为 0。退出码 2 表示封装失败或事实矛盾。后续测量必须明确要求各维度满足自己的准入合同，不能把退出码或一个 bool 当作可评估的充分条件。本轮不输出分数。

当源数据库后来发现缺 receipt/conflict 时，新包保留新的核验记录与原历史声明；旧包仍代表过去读取快照。并发 WAL 写入测试证明导出不会拼接两个时点的数据。重复固定快照导出时 evidence、verification 的字节 hash 及 manifest 的内容条目稳定；export 时间及其清单 hash 可以变化。

发布顺序：同父目录独占 staging → 写内容并 fsync → 离线 verify → 写结果和 metadata → 再 verify → rename 到不存在的目标。失败仅留下 staging/failure.json，目标不会出现半包。这里证明的是本地进程级提交边界，不是物理断电/设备缓存认证。

## 复现

先按根 README 安装当前源码，然后运行 `scripts/validate.py evidence`。该 suite 从真实 DSH fixture/Concordia 生成完整、拒绝、partial、unknown，再验证篡改、重算 hash 后的内部矛盾、迁移与原目录不可访问。portable 用单独 Python `-I -S` 进程和最小模块副本，audit hook 拒绝原目录读取、runtime 导入、subprocess/socket；不破坏原目录。
