# 模块化重构验收

**整体 INCOMPLETE。** 本轮完成了部分职责提取、可独立安装的产品 fixture、兼容入口及新本机验收，但未完成用户要求的九层无环架构。下面的 PASS 均有范围，不能据此宣称完整重构成功。

## 身份与实际改动

- 起点 main：`6ba6573dc2057b12624477c3b3a90cbf246f8f63`；C5 产品基线：`c5aeec2e4f99b99da4fda5cb6cc59476ce0be890`。
- 最终运行产品：`d64264f67191d99b94598d79c67bdb7eb7b92a37`。该提交推送任务分支后才执行正式矩阵。后续仅追加文档与验收摘要，未改变安装运行闭包。freeze11.json记录新身份；原freeze.json属于10并原样保留。
- wheel SHA256：`475dbbd2beedb25ab31096be1b99e879d95a5f5273a048488458be725f8e0de2`。标准 wheel 在干净源码副本构建，final/minimal 均非 editable；105 个产品文件与 Git/checkout/wheel/安装逐字节一致，见 [final-source-check.json](final-source-check.json)。
- 提取 `contracts` 的规范编码/受限 JSON/封包、`domain` 的候选/namespace/计账、`tasks`、独立 `measurement`、文件适配器、原 Ledger 事务体、budget IPC 和本机 fixture。正式 run-local 删除 tests 路径注入和 monkeypatch，显式注入 response_policy；最后残存的 robustness rehearsal 测试依赖亦移除。
- 原 69 Python、67 根文件/最大 SCC33 → 当前 89 Python、57 个根 Python/最大 SCC23；全部 SCC 为 23/7/3/2/2。根数含入口与 common shim；精确待迁移实现清单见 [architecture.json](architecture.json)。产品→tests/scripts 已清零，但不能称全局 DAG。

## 验证与来源

| 验证 | 实际结果 |
|---|---|
| 最终 wheel 纯/状态 | 47 / 27 项 PASS；包含4项本次边界测试 |
| 最终 wheel 官方基础集成 | 2项 PASS：DSH、真实 Concordia assistant/social、MCP、隔离及显式共享 |
| 最终 minimal wheel | 无DSH/Concordia、repo外、`-I -B`；11项打包命令/guard PASS；四console scripts和完整final环境pip check PASS |
| 最终正式 entry 纯核验 | 9 entry在禁止key/env/network/process/write/runtime导入的guard内PASS；重封篡改拒绝，退出2；新增发送0 |
| 基线差分 | 555项完整JSON相等，无忽略字段；最终d64264f复核PASS，源码身份变化另记 |
| 完整维护suite | 34个suite共163个测试方法均已执行；33个suite（157方法）PASS，readiness的6方法suite仍FAIL。逐suite、每次失败/修复、源版本差异见[汇总](regression-summary.json)。不同安装不合并冒充全量最终wheel PASS |
| 全局架构 | INCOMPLETE；检查器返回1，保留所有循环，无忽略白名单 |
| 历史 | 固定C2/C4受控原delivery/DB、C3公开包及19claims PASS；原C5固定reader认证和离线重算PASS；1048文件/工具字节未变 |

开发全量 runtime 使用较早 wheel04，修复复测主要为 wheel09；最终 wheel11 复跑 pure/state/runtime 基础、打包/guard和正式矩阵。汇总逐项列出与最终安装不同的文件，不能将旧安装结果改名为最终源码实测。最终11相对10统一Python源码为仓库规定LF，逻辑不变；原因是发布前发现旧wheel/工作区CRLF与Git的LF字节不一致。已重建、独立freeze11、推送后重跑纯/状态/基础集成/正式矩阵/guard和向量，旧freeze.json、freeze09.json和运行记录原样保留。构建工具现在拒绝CRLF源码，发布核对同时比对Git字节；[字节差异记录](publication-byte-check.json)证明88个文件只改变行尾。

## 新本机运行与计数

最终 `formal11` 是独立新运行，不是原C5重算：9场景，assigned18，sent/received/responses12，settled/可信usage/admitted5，unknown7，not_run6，active0。12 Worker、9服务/端口已清理；本轮假凭据扫描20,251文件、34,685,626字节，无落盘凭据。原始DB/raw/日志仅留 `D:/ar-mod-20261011/formal11`，公开摘要见[formal-runtime.json](formal-runtime.json)。

前两次安装 `formal09`、`formal10` 各额外12次本机发送单列保留，不混入最终12次。开发回归113个记录根目录的去重fixture接收为261次，未发现计数读取错误；加前两次安装矩阵共24次与最终矩阵12次，本轮记录范围合计297次loopback接收。计数包含失败/重复测试，排除进程内MJS fixture输出。开发清理核查404个命名Job的active均为0，158份服务记录joined=true；一个旧端口被系统代理用于新出站连接，TCP状态为Bound/Established而非Listen，未终止其进程。首次独占绑定核查记录保留，最终状态见[development-cleanup.json](development-cleanup.json)。fixture收到请求与账务提前记录sending含义不同，不将接收文件统计说成网络抓包。

## 失败、修复和未完成范围

保留开发失败：CLI过早导入MCP（延迟导入修复）；setuptools旧build/lib残留已删除私有模块（全新源码副本构建修复）；源身份仍指向已删除模块（完整当前闭包修复）；v3 PROFILE局部遮蔽（基线复现后修复）；eval可选依赖缺失（按原锁本地安装）；测试复用历史脚本私有模块（提取tests/support修复）。日志不公开，receipt保留hash和结果。

**未完成的工程实现**：Store规则/用例/SQL与最小ports未完整拆分；application/profiles/evidence仍混在根模块；runtime/environment接线未全部归位；profile仍自行读取文件hash，尚未由外层注入身份；23节点等SCC未消除。这是尚未完成的实施范围，不是外部授权阻塞。

**未通过的回归**：readiness 6项suite包含15个失败子用例和1个错误；原quote于2026-10-10T16:00Z到期，真实系统时间下正确拒绝，固定C5基线同样复现。未改旧报价、系统时间、断言或skip。其成功路径仍需可审阅的跨IPC测试Clock与相应过期拒绝回归；不能把当前拒绝行为当作该suite已通过。

G1/G7未通过，G8不代表全工程成功；完整逐Gate说明见[GATES.md](GATES.md)。未因重构修改数据库schema、历史manifest/freeze/pins、原失败、六份candidate decisions、历史evaluation或C5未来计划。

## 发布与保持的边界

本轮普通推送任务分支 `refactor-modular-architecture` 和 `main`，fetch确认并发关系后安全快进，不强推。最终两远端SHA核对回执保留于本轮短路径根 `publication.json`，最终回复给出实际核对SHA；产品运行身份与后续文档发布身份分开。证据索引见[evidence_manifest.json](evidence_manifest.json)，执行命令见[CLI.md](CLI.md)，设计见[架构README](../../architecture/README.md)。

本轮真实provider / 目录GET / 外部MCP均为0；历史生成172/目录GET1不变。C4=INCOMPLETE、C1=infrastructure_failure、activation=false、研究UNESTABLISHED、binary_source_mapping=unproven、full_controller_recovery=unsupported；费用币种/单位、账单及上游身份仍未核实。没有推进C6。
