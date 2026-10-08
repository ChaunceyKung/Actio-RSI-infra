# Phase 1B.1 实现与验收

2026-10-08；产品基线 `668754fc`，交接 `4e0a473`。预算 0；Windows x64 / Python 3.12.10 / DSH SDK+runtime-bin 0.1.5rc1 / 固定 Concordia source；provider/GM 均 fixture。所有新源码、测试和证据在本分支，Phase 1A/1B 历史证据保持原样。

## 四项边界

| 发现 | 结果 | 实现与实际验收 |
|---|---|---|
| B1R1 | PASS | 版本化 scenario_terminal 绑定 manifest、owner、ordered operations、domain/world hash。seal 和 finish 都核对 native receipt/flush/final source、领域回执和场景规则。真实 B turn 完成后 A 构造失败、真实 Engine 第一步 callback 异常、domain receipt 删除/不一致均保持 partial；world/已执行事实不回滚。正常助手、两人成功、合法拒绝仍成立 |
| B1R2 | PASS | `begin` 的短事务内先查规范 request，赢家才冻结 memory/spec/pins。返回 fresh=False 的入口立即返回；执行权限由当前 Store/控制进程持有，不能从可读 run ID/epoch 恢复。两个真实控制进程在两个入口同步竞争：assistant 仅一个 runtime/工具/effect，social 仅一个 owner 的两个 turn。输家不能 finish；完成/unknown 重试无新派发 |
| B1R3 | PASS | CLI 先解析目标，recover 检查目标 run/epoch、owner birth、命名 Job，回收前后再核对 lease/run/worker 集合。未知/历史目标不调用另一 Job 的回收；活 owner 拒绝；受控 lease 改变拒绝旧清理结果。原真实 owner-death 和 crash 回归通过；reconcile 无模型/工具重发 |
| B1R4 | PASS | API sentinel 和 CLI default 区分“未给参数”与显式 False/None/revision；replay 的任何显式起点 override 均在创建 run/worker 前拒绝。必要字段、snapshot hash、spec/runtime pins、原 manifest hash 必须一致。原样 replay 新 run/creation/stream，world 语义相同，原 memory 不变 |

`operation execution_complete` 仅说明该 operation 的原生事实与领域效果完成。完整 episode 另外要求场景凭据。助手为一条 operation；社会成功为按 B→A 顺序的两个正确实体、两个 GM resolved 与 domain receipts；非法 B action 可在 world 更新前合法结束为 `complete/task_failure`。基础设施异常不会根据现存 operation 推导缺失步骤完成。主要失败原因持久保存，清理错误另存 audit/note；清理不能确认时保留 lease。

原同 host 两 turn 回归保持原生 receipt、barrier、memory 两次效果断言，并修正最后一项期望：两条底层 turn 不冒充“一步助手场景”，因此 operation complete、scenario incomplete。这是本轮明确的合同收紧，没有回填旧测试结果。

## Schema 与历史

新增 `request_identity`、`scenario_terminal`、`migration` 三张表和 `PRAGMA user_version=2`。只识别随包保存的已知 Phase 1B schema=0 与当前完整结构；未知未来/残缺库拒绝。Store 默认打开已有库，只有显式 create/init 新建。查询 agent/run 和导出可只读打开旧库，不刷新旧 pins。

`migrate --output NEW_COPY` 对源库只读；SQLite backup 捕获 WAL 一致快照，先保留恢复副本/hash，再在 staging 单事务写三表/迁移记录/版本。最终 rename 到新输出。测试逐表比较旧行、旧事实和 pins，重复迁移稳定；异常和真实控制进程 `os._exit(85)` 都保留可恢复备份，DDL/版本没有半提交。未知路径查询不创建库。旧完整声明缺新凭据时维持 legacy_unverified；不兼容旧 spec 可读可导出，执行明确拒绝。

## 包与独立核验

导出器只读一个 SQLite 快照并取单 run 引用闭包。原生 raw 行、投影、intent/accepted/flush、domain/world、终态、冻结 spec/input/memory、最小前序 source/effect 与清理都入包。无原任务根依赖，32 MiB/20,000 行和 64 memory revision 上限；失败不发布半包。详细格式见 [包合同](04_bundle_format.md)。

7 组 evidence 验收包括：真实完整/合法拒绝/第二实体失败/unknown 分类；缺文件/hash/未知版本；重新计算清单 hash 后的 duplicate/gap/barrier/domain/world/projection/conflict/缺 memory source；标准库 `-I -S` 独立进程（禁止原目录/runtime/network）核验；稳定重复导出、无新 run/worker/effect 和无额外 identity；超限保留失败 staging；历史 complete 与 current partial 并存；单次读快照期间另一 WAL writer 删除 receipt，当前包仍一致，随后新包诚实 partial。

5 个小型 [合成样例](samples/README.md) 约 201 KiB 原始 evidence，精确 native 字节未改写。完整 raw SQLite/journal/log/缓存留本地 ignored，manifest 登记原包/归档 hash。memory 证明只覆盖实际引用 source，不递归认证前序全部 episode，不证明检索未选数据集合完整；没有 evaluator 或综合能力分数。

## 实测与保留失败

| suite | 聚合行为组 | 证据强度 |
|---|---:|---|
| contract | 6 | SQLite、memory CAS/去重/权限、cursor/conflict/limits |
| runtime | 2 | 官方 DSH + 实际 MCP/native journal + 真实 Concordia；跨控制进程、隐私与 replay |
| failures | 6 | 静态最终 guard、stage deadline、资源限制、window C、stop 与 Job 清理 |
| processes | 4 | 真实 owner/SDK host 死亡、windows A/B/D、两控制进程 lease 竞争 |
| reliability | 7 | 新场景终态、真实 Engine 定点失败；目标恢复/lease 变化、清理双异常、严格 replay |
| entry_concurrency | 1 | 两入口分别用两个真实控制进程、同步闸门、真实 runtime 路径 |
| schema | 5 | 已知旧库/WAL 一致迁移、重复/异常/真实进程中断、未知结构、不兼容 spec |
| evidence | 7 | 真实 fixture 轨迹导出 + 离线/矛盾/可迁移/快照核验 |

合计 **38 组 PASS**；每组含多个断言，不是统计样本数。实际命令、退出码、平台、完整 product 与对应 test/fixture hash、raw archive、Job 清理见 [manifest](evidence_manifest.json)。首次 evidence suite 将“flush 已完成、canonical 未导入”的 unknown 前缀误报为矛盾，保留 FAIL 记录；修正后分别报告 missing prefix 与 infrastructure_failure，重跑创建新记录，未覆写旧 FAIL。

新隔离 `.local/phase1b1-delivery-venv` 按锁文件安装，41 个缓存 wheel 逐 hash 核对、固定 Concordia 本地 Git archive 全文件核对、DSH exe 核对、pip check 通过。未使用网络重新下载，参考仓库只读。`scripts/phase1b1_smoke.py` 实际以公开 CLI 新进程运行助手/social/replay/拒绝、查询/reconcile、override 拒绝、旧库 query/migrate（含重复）、export 和两种 verify 入口。源码逐文件与 installed package 一致。前期新 suite 的通用 runner 顶层 mode 过宽，以 manifest 和 per-test 的明确强度说明为准，历史记录不改写。

未执行 live、研究评估、candidate 搜索、演化、训练或远端部署。没有替换 agent loop、升级 DSH/Concordia pins 或改上游。Git 发布遵循本项目 AGENTS.md：验证后 commit、普通 push 当前分支、核对远端 SHA；不合并 main。
