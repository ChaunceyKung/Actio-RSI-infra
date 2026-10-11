# Codex Prompt：Actio-RSI 模块化重构与行为保持验收

你是本仓库的重构负责人。请完成顶层设计落地、代码重构、简明设计文档、完整的适用回归和本机运行验收，随后提交并推送任务分支及 main。不要只提交方案或移动文件，也不要推进 C6 实验。

## 任务与事实基线

仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`

远端：`https://github.com/ChaunceyKung/Actio-RSI-infra`

C5 产品基线：`c5aeec2e4f99b99da4fda5cb6cc59476ce0be890`。本 Prompt 所在提交是后续文档规划，不代表产品已重构。先 fetch，检查最新 main 与此基线的关系；若有新代码，阅读并保留，不 reset 或强推。

当前 69 个产品 Python 文件中67个平铺根目录，9,182行；静态 import 图含33节点强连通分量。核心问题包括多版本 campaign 反向进入 budget/transport、纯合同与 I/O 混合、产品本机入口导入 tests、整包路径 hash 与历史来源耦合。盘点不是可直接执行的信任根。

C5：9场景12次loopback sends，5 settled/可信usage/admitted，7 unknown，6 not_run；12 Worker、9服务已清理。首次诊断 FAIL 保留，最终 PASS 是对原冻结 `196e8a6f3327b9d17ee0c0ba3bc45c93c38334e0` 运行的离线重算，**不是最终源码再次运行**。新重构必须取得自己的最终安装实测证据。

既有边界：C4=INCOMPLETE，C1=infrastructure_failure，activation=false，研究有效性UNESTABLISHED；历史真实生成172次，目录GET1。账单/费用币种单位及上游身份未核实；binary_source_mapping=unproven，full_controller_recovery=unsupported。

## 先读这些材料，再开始实施

1. `AGENTS.md`、根 README、MILESTONES；用户最新“验证后推送 main”优先于旧阶段“不合 main”。
2. `docs/architecture/README.md`、`MODULES.md`、`REFACTOR_PLAN.md`、`inventory.json`。三篇是目标设计，实施结束要改成实际设计。
3. `pyproject.toml`、锁文件、`src/actio`、tests、bootstrap/validate 工具；核对所有 CLI/IPC、package resources 和真实调用方。
4. C5 的 RESULTS/CONTRACT/GATES/CLI/DEVELOPMENT、freeze/manifest；C2/C3/C4 原结果、固定 reader、evaluation_history、task_diagnostic_trust、pins/c5_runtime 及 history/recompute 工具。
5. 早期 planning 架构仅作背景，不把其未来 viewer/多机/训练栈作为本任务功能。

## 授权和执行范围

- 这是完整的工程重构任务。自行完成必要的设计细化、分步实现、失败修复、测试与发布，不每一步向用户要确认。
- 本轮仅进行离线和本机 fixture 验证；新 provider、目录 GET、外部 MCP 请求为0，不读取实际 API key来运行，不执行 C5未来计划，不补 C4后缀。
- 用户无金额上限授权仍保留，本任务的零真实调用来自“暂停实验、进行重构”的范围，不是撤销或重问费用授权。
- 保留已有 live 接口语义，但不调用它；用 loopback/固定向量验证。无训练、部署、judge、人工校准、新候选、原生 resume/fork、完整恢复或 SDK 升级。
- 凭据仅可在交付扫描需要时由既有受控 scanner 内存读取，不能打印内容/前缀/长度/hash，不写 Git。开发测试使用新内存假凭据。
- 普通 GitHub 推送属于本任务授权；不要因为禁止模型外网而禁止正常 fetch/push。无需安装新架构框架或下载另一套 agent 栈。

## 目标：一个职责明确的模块化单体

落地 `contracts / domain / tasks / profiles / application / adapters / measurement / evidence / interfaces`，保留 `_vendor` 的最小摘取和许可。adapters 按 persistence/runtime/environment/transport/filesystem 分组；不必创建空层级。目录名称可以据调用关系小幅调整，但记录理由并满足架构依赖测试。

依赖方向：纯 contracts 为底；domain/tasks 不依赖基础设施；profiles只提供显式版本配置和纯构造；measurement的独立oracle不调用生产裁决；evidence只核验；application依赖纯包和自己定义的最小ports；adapters实现ports，不能导入应用用例；interfaces负责CLI和具体装配。包初始化不批量导入隐藏副作用。

禁止 product→tests/scripts、业务包→旧shim、纯reader→runtime、任务→oracle 的反向依赖。目标业务包DAG无环，包含函数内 import 和已知动态选择。固定历史 checkout 的源码与当前产品隔离，不靠大段 ignore 让架构测试变绿。

必须处理四个实际耦合：

1. common/eval_contract：提取canonical、受限JSON、seal/digest、错误与基本require；文件、环境、临时目录留adapters。不得改变编码、错误拒绝、原摘要。
2. Store/Ledger：拆纯规则、用例和SQL，但保持现有状态权威、原子事务、WAL/readonly、fencing、一次资格和unknown语义。禁止引入第二权威数据库或自动修改原工作库。
3. transport/pilot/gateway/campaign：纯版本差异进入受信profiles，实际编排进入application，DSH/Concordia/Windows/TS接线进入adapters。不要抽象出能执行任意artifact代码的通用引擎。
4. diagnostic_runtime：把正式本机fixture服务从tests提取到可安装产品适配器，去掉sys.path注入和对测试模块的monkeypatch；公开run-local在独立wheel中可用。

接口以已有行为推导：DomainUnitOfWork、AttemptLedger、AgentRuntime、Environment、EvidenceSource/ArtifactSink以及确有用途的小Clock/ProcessIdentity；不做每函数一个类，不暴露万能SQL接口，不通过多个repository提交破坏事务。

## 历史、兼容性和源码身份

建立三份可审阅清单：

- migration-map：覆盖全部产品模块和资源，写明移动/拆分/保留/shim和对应测试；同步核对42个测试/辅助Python文件、88个历史工具Python文件。
- compatibility：四个console scripts、已用到的python -m命令、public reader、TS→Python budget IPC、host/MCP/eval worker、参数/输出/退出码。私有import不承诺永久保留，必要shim只做薄转发。
- identity-and-history：数据schema身份、当前源码/资源/执行工具闭包、历史固定reader身份分别定义；old/new对应关系和字段级差异白名单明确。

重构会改变整包相对路径/hash。不能通过更新旧manifest/freeze/plan/pins、删除实现身份检查、忽略大段report来实现兼容。旧证据用代码维护的固定commit/reader/trust registry复核，artifact不提供可执行模块或命令。需要启动旧reader的外层harness与无进程/无网络的内层reader分开。

新profile由外层传入受验证的当前源码身份。新的实现manifest完整覆盖运行相关Python/MJS/SQL/JSON、信任注册表和必要工具；不能只hash小facade或随意排除路径。历史源码保持旧算法，不悄悄降低认证强度。

历史原文件/DB/raw/失败/19claims/六份candidate decisions/各evaluation与C5未来计划不改。默认不变更数据库schema；确需变化先给最小理由和显式复制迁移，单独验证，绝不自动迁移用户库。

## 实施顺序

R0：检查工作树/远端；从最新main建立 `refactor-modular-architecture`（已存在则先检查并合理复用）。保存基线、清单和初始失败；short path独立测试根目录，不覆盖旧root。

R1：提取纯contracts/domain/tasks/measurement，建立高价值差分向量和依赖检查。

R2：拆persistence/文件/OS适配与最小ports，验证事务和失败边界。

R3：拆runtime/environment/transport，移出本机fixture，统一application用例与显式版本profiles。

R4：整理evidence/history与composition/CLI/shim，分层tests、提取tests/support、形成当前tools入口；旧阶段脚本保留原路径并标明历史用途。

R5：构建标准wheel，干净安装到隔离短路径环境；冻结当前运行源码/fixture/必要工具，提交并推送任务分支后进行最终本机集成。文档结果可随后追加；若产品/运行工具再改，重新核对影响范围并重跑必要验证，不能把旧安装运行叫作最终源码验证。

R6：更新三篇架构文档、README导航/使用/目录、MILESTONES工程条目；完成证据、扫描、提交任务分支及main、核对远端。持续到实现和适用验收完成，不以“仅移动文件”“只完成R1”作为成功交付。

## 测试必须证明什么

以REFACTOR_PLAN中的G1–G8为准，提供一个维护中的明确runner及suite清单。默认不发外部请求。可分pure/state/packaging/history/runtime-local/all-local；命令名称由实现确定，必须实际运行并写入CLI.md。

1. 架构：检查所有静态import（包括函数内）、动态registry和import-time效果；禁止产品依赖测试/阶段脚本/旧shim；包级无环，不用手工白名单隐藏新依赖。
2. 差分：基线与新实现的canonical字节、schema、两family观察/行动/结果、指标/分母、candidate/evaluation、C5错误观察和篡改拒绝相同。UUID/时间/路径/新实现身份等差异逐字段解释。独立oracle保留独立算法并验证未调用生产裁决。
3. 持久化：真实SQLite的冲突/去重、memory权限/revision/effect、readonly旧库、迁移到新副本、一致快照、lease/fence、并发抢占、ledger状态和unknown；不写旧受控库。
4. 打包：安装wheel，repo外cwd，移除PYTHONPATH/源码和tests/scripts兜底；四个console scripts、module CLI、child IPC、所有SQL/JSON/MJS/许可资源可用；pip check通过。纯核验在无DSH/Concordia的最小环境可用，不能靠editable install证明。
5. 纯入口guard：plan/analyze/verify不读key/env、不联网/启动进程/写文件、不导入runtime。execute/run-local测试独立分组，允许其明确的本机副作用；不要把argparse环境读取误判成纯核验失败。
6. 历史：按固定reader验证C2/C3/C4及C5原运行/最终重算；分开报告公开合成投影与受控raw认证。缺少受控材料写BLOCKED，不能从summary重建原始证据。
7. 实际集成：在最终新wheel下跑必要的官方DSH、真实Concordia assistant/social、MCP、隔离和记忆共享回归；再独立执行新C5九场景矩阵，使用新freeze/new run id/new root。正式矩阵应为12本机sends、5准入/可信usage/settled、7unknown、6not_run，12Worker/9服务及端口清理。开发及其他基础测试发送单独计数。
8. 全面性：给每个原测试文件标明当前回归/固定历史/辅助迁移位置。所有仍维护的现有suite必须适配并跑；不能只选12个C5纯测试，也不随意执行会写旧phase结果的脚本。失败先找原因，不删断言、不把应通过测试改skip。

只增加验证本次边界、事务、兼容性和打包风险所需的测试，不写重复实现细节的测试。一次验证通过后，除非后续修改或失败有理由，不重复消耗本机完整矩阵。

## 交付物与停止条件

新增 `docs/validation/refactor_modularity/`，包含 RESULTS.md、CLI.md、迁移/兼容清单、Gate与证据manifest；可将清单合并成结构化文件避免文档泛滥。记录基线/最终源码和wheel身份、各层实际测试、开发失败与修复、新本机运行和历史重算、完整计数、清理及未解决限制。

三篇architecture文档控制篇幅，必须包含实际全局图、模块依赖、每模块I/O/状态owner/流程、三条主要端到端流程、扩展点与当前不支持项。更新inventory的当前状态或追加重构后对照，不抹去这次基线审阅。

所有历史结果和费用/来源限制不变，新的真请求0。没有所有必需Gate证据时标INCOMPLETE/BLOCKED，保留可交付成果和精确阻塞；不要因重构而宣称实验通过或新能力激活。正常情况下完成全部工程范围再结束。

扫描本轮staged/生成材料，避免key、历史敏感raw/reasoning/error.message/请求内容进入Git；不要添加venv/cache或大量原日志。只提交本轮相关内容。

必须正常推送任务分支和main：先fetch核对并发变更，优先安全快进；需要整合时保留他人提交并重新做受影响检查，禁止force push。分别用`git ls-remote origin refs/heads/<任务分支>`与`refs/heads/main`核对本地最终SHA。网络失败保留本地提交和精确待推送状态，不能声称发布成功。

最终回复用中文说明：重构前后模块与依赖变化、保留的兼容入口、实际测试/本机计数与清理、历史保全、剩余限制、任务分支/main的提交与远端核对、简明设计及验收链接。完成后停在本次模块化重构，不自动进入下一实验。
