# 模块化重构终验

**工程验收 PASS。** R7–R10 已落地，同一最终 wheel 完成 34 suite、164/164 个唯一测试方法（原163全部保留，新增Clock边界1项），无 skip。普通 Git 发布已完成，两远端产品 SHA 核对一致，见 completion/publication.json。

最终 wheel SHA256：`867d85c6dfa6f3f30b224bb2b9f77dbd86970e87d0b03466c4526a9919bda37b`。新身份 `actio-modularity-r7-r10-20261011`，源码/资源/wheel/安装逐字节核对见 [installation-and-history](completion/installation-and-history.json)。旧阶段与上轮冻结不改；此前工程结果保存在 completion/previous-*。

| 验证 | 结果 |
|---|---|
| 架构 | PASS：163 Python、594 edges，SCC=0、unmigrated root=0、violations=0；原检查器未修改 |
| 差分 | PASS：555 完整 JSON 向量逐项相等，不排除身份字段后伪称全等 |
| 状态 | PASS：state27、budget4、readiness6及全量并发/usage/unknown/receipt断言通过 |
| 打包 | PASS：repo 外安装、pip check、4 console + 4 module、SQL/JSON/MJS/license；minimal --no-deps reader 独立通过 |
| 历史 | PASS：1,048 文件、SQL/MJS资源字节、旧quote/pins；固定C2/C3/C4 reader、原C5认证与重算、19 claims |
| 正式本机 | PASS：同 wheel 九场景；12 sends、5 settled/usage/admitted、7 unknown、6 not_run；12 Worker/9服务/端口清理 |
| 全量回归 | PASS：34 suite，原163+Clock1=164/164；全部来自同一最终wheel；一次ready超时按原断言独立复核通过 |
| 发布 | PASS；产品提交已推送两分支并分别核对远端 SHA |

R7 的新 Clock 配置仅允许 priced_rehearsal 固定 UTC，system/live 保持真实 UTC 和过期拒绝。新 schema/profile 与旧固定 reader 区分；旧报价窗口没有刷新。Clock 进入配置 hash、Ledger meta、账务快照和 TS→Python child IPC。

R8 建立任务 core 和唯一 registry，消除版本 dispatcher 回边。R9 将 policy 从 Ledger/budget 抽入 profiles；纯 validators 不导入 Ledger/application/preflight。R10 将同连接 Store 用例、持久化资源、runtime/environment/transport、evidence 和接口装配拆开；没有第二 Ledger 或多个 repository 代替原事务。

较早 wheel 的诊断 field-bound FAIL 完整保留在 [superseded-formal-failure](completion/superseded-formal-failure.json)，它实际额外发送12次。修复后的新 reader 仅允许完整当前源码身份映射使用原 items 上限，任意其它字典仍保留128-field限制；新 portable 包明确为v2。最终源码只有一次正式矩阵，开发及旧安装结果不混入正式分母。

本轮真实 provider、目录 GET、外部 MCP 和真实凭据读取均为0。C4=INCOMPLETE、C1=infrastructure_failure、研究UNESTABLISHED、activation=false、binary_source_mapping=unproven、full_controller_recovery=unsupported保持。没有进入C6。

设计见[architecture](../../architecture/README.md)，命令见[CLI](CLI.md)，逐Gate见[GATES](GATES.md)。

## 运行中的失败与复核

最终 all-local 首次运行中，failures suite 的一个 artifact 子场景遇到 Worker ready deadline，后两个子场景因此被 active lease 拒绝。原失败、清理和受控日志 hash 保留在 [runtime-startup-failure](completion/runtime-startup-failure.json)。整组结束后，在同一 wheel、相同测试与 deadline 下独立复测 failures 6/6 通过；没有修改代码、重置 lease、删除断言或增加重试权限。全量主收据和这一次复核均列在 [regression](completion/regression.json)，候选 runtime 的一个测试还因隐式 AUTH 导出移除而失败，改为从 profiles.gateway_base 的真实 owner 导入同一个常量后，3/3 独立复核通过。授权值、资格拒绝断言与产品源码不变；两组复核均来自同一最终 wheel，没有混用旧安装结果。这不承诺任意并行本机负载下不会发生启动超时。

所有原方法与断言保留见 [assertion-preservation](completion/assertion-preservation.json)；最终 Clock 与跨 IPC 收据见 [clock](completion/clock.json)。开发与中断根的清理见 [development-cleanup](completion/development-cleanup.json)。当前证据索引为 completion/evidence_manifest.json，根 evidence_manifest.json 保留为上一轮历史收据。

开发接收文件清单记录429次loopback receives；另有两次被替代矩阵各12次、最终正式矩阵12次，共465次可枚举接收。该清单不是网络抓包，不含MJS进程内响应发射。开发/中断根722个Job、216个服务清理通过；最终正式矩阵12个Worker、9个服务单列，均无活动残留。
