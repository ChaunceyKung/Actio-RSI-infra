# C2C1 结果

冻结提交 `dc15292bc6827593e8321e31acbcf599dd25d772`，计划 SHA256 `47f728d661a192c2623dc25a1f8deb6c19d6259b70cca8984e04e5160c842d29`。
远端核验 2026-10-09T13:01:24.440Z → 首次 intent 2026-10-09T13:01:24.867Z；本机时间不是独立签名时间戳。

**工程闭环 PASS**：B0 → 人工通用 checklist C1 → 静态校验 → 真实 DSH/Concordia 本机配对执行 → 独立决策 → SQLite 持久谱系。B0/C1 的能力决策均为 **insufficient_evidence**；四个 synthetic 静态负例均 reject，六个提案全部保留且不可激活。

| 主矩阵维度 | 数量 |
|---|---|
| planned_episodes | 24 |
| observed_episodes | 24 |
| complete_episodes | 24 |
| assigned | 48 |
| sent | 48 |
| response | 48 |
| terminal | 48 |
| admitted | 48 |
| usage_responses | 48 |
| not_run | 0 |
| unknown | 0 |
| protocol_error | 0 |

12/12 arm pairs 完整。48 个 HTTP 请求是 seat 级消息，24 是 A/B episodes，12 才是 arm pairs；不是 48 个独立研究样本。两臂采用相同冻结 own_rule fixture，逐卡格式、A hard、B local、joint、两方 toy utility 的差值全部为 0。

| family | arm | format true/defined | A hard true/defined | B local true/defined | joint true/defined |
|---|---|---|---|---|---|
| scheduling | baseline | 12/12 | 6/6 | 6/6 | 3/6 |
| scheduling | candidate | 12/12 | 6/6 | 6/6 | 3/6 |
| bargaining | baseline | 12/12 | 6/6 | 6/6 | 2/6 |
| bargaining | candidate | 12/12 | 6/6 | 6/6 | 2/6 |

逐卡 utility 原值/差值/missing 与真实 wire hashes 见 [bindings](bindings.json)，所有完整分母和逐 seat 诊断见 [report](samples/report.json)。没有跨 family 综合排名、显著性、推广 CI 或无限 z。fixture 不解释清单含义，12 张卡均已用于开发，independent_research_units=0、human_labels=0。

新 v2 按 index/type 支持同时打开 reasoning/text，核验 raw UTF-8/SSE → 官方 adapter/end → native content/reasoning。只有 content 进入实际 A 行动、B 公开观察、世界与 memory。实际 prepared 仅归一化独立 UUID4 message IDs；full wire 的直接干预仅为 A checklist，固定 A 输出时 B wire 相同。

旧 C2C0 停止是冻结纯文本 v1 不支持 reasoning_content，不是已观察到的行动文本矛盾。只读新 sidecar 验证 raw/adapter/native 两通道一致；旧 admitted=14、sent/usage=15、not_run=33、unknown=0 及停止点不改。完整 HTTP/终态耗时保持 observed，行动未准入仍缺失；reasoning 正文未复制。

本轮主矩阵本机发送 48；开发验收本机发送 20、usage=16、unknown=4（包含故意 missing-DONE 和保留的失败验收），单独计数、不拼入主矩阵。新增真实模型/provider/catalog 请求均为 0；历史生成尝试仍 91、目录 GET 1。费用/账单/upstream identity 仍 UNVERIFIED。

验收：最终源码 8 项 C2C1 测试通过，另有 20 项受影响旧分派纯回归；历史 C0/C1/C2A.1/C2B0/C2B1 固定 reader 通过，C2B2/C2C0 原报告精确重现。两份失败测试和未发布草案保留，见 [开发记录](DEVELOPMENT.md)。事务内 proposal/event/edge/decision 写失败均回滚，重复登记幂等，evaluating 不重领，重开 DB 等值、坏库拒绝、v2→v3 copy/backup 与旧库不变已检查。

真实公开 CLI、pip check、源码/安装一致、完整 delivery 在 network/key/env/process/runtime/write 禁止的 audit hook 下核验，以及重新计算 outer hash 的篡改拒绝见 evidence/cli 文件。JSON 是 SQLite 的投影，原始数据库/Worker 日志保存在本地 hash 清单归档；公共 delivery 只承载可迁移的合成运行证据。

清理：68 个具名 Job 均 inactive/reaped；13 个服务已 join；13 个记录端口无残留监听；authorized/reserved/sending=0。原始归档、只读 DB hash 与 census 在 [manifest](evidence_manifest.json)。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [计划](preregistration.json) · [提案](proposals.json) · [决策](decisions.json) · [谱系](samples/lineage.json) · [完整导出](samples/delivery.json) · [来源](provenance.json)

停止于 C2C1。C2C2 仅建议：先独立冻结 live candidate/control 合同、更多独立任务及可审计的能力证据，再讨论 inactive 候选的准入与激活 CAS；本轮不执行、不生成新候选、不自动调用 provider。binary_source_mapping=unproven，full_controller_recovery=unsupported。
