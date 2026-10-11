# 模块化重构：审阅、迁移与验收

**本轮仅完成审阅与设计；下一个重构 session 实施。** 基线为 C5 `c5aeec2e4f99b99da4fda5cb6cc59476ce0be890`，审阅时本地 main 与独立 `git ls-remote` 结果一致。当前目标是行为保持的结构重构，暂停 C6/真实实验、候选扩展和能力晋升。

## 1. 现状结论与证据

问题主要是职责依赖和版本组织，而不是某个超大文件。源码共 9,182 行 Python，最大文件 433 行；适合增量整理现有代码，无需换框架或重写系统。

| 发现 | 可核查位置 | 影响与改法 |
|---|---|---|
| 69 个产品 Python 文件，67 个在包根目录；另有 14 个 py/mjs/sql/json 范围内的非 Python 资源和 1 个上游许可文件 | [逐文件清单](inventory.json) | 按稳定能力分包，每个文件有去向和负责人职责，阶段标签退出核心命名 |
| 407 条静态包内依赖；含函数内 import 的图有 33、3、2、2 节点的强连通分量 | inventory 的 `strong_components` | 这是潜在调用耦合，不等于启动时报错；拆掉跨业务包反向依赖，并建立自动约束 |
| `budget.py` 识别多阶段配置并导入 campaign；`transport.py` 同时处理 profile、运行、账务和场景 | [budget](../../src/actio/budget.py)、[transport](../../src/actio/transport.py) | 把显式版本校验移到 profiles，纯转移移到 domain，SQL 留 persistence，执行留 application |
| Store/数据库 migration 相互依赖；Store 还直接使用进程身份、候选/评估专用函数 | [store](../../src/actio/store.py)、[database](../../src/actio/database.py) | 保留单一连接和事务，将用例与状态规则拆出；进程身份通过端口输入 |
| common 混合 canonical/hash 与环境、临时目录、文件写入；eval_contract 又导入完整 verifier/terminal | [common](../../src/actio/common.py)、[eval_contract](../../src/actio/eval_contract.py) | 提取小型纯 contracts；I/O 进入 adapters；禁止只读读包隐式导入 runtime |
| 产品 `diagnostic_runtime.run` 插入 tests 路径并导入、改写 gateway_stub | [diagnostic_runtime](../../src/actio/diagnostic_runtime.py) | 当前 checkout 可跑不等于 wheel 可独立跑；fixture server 成为产品显式本机适配器，测试依赖产品 |
| preregistration 把整个包的相对路径与内容 hash 纳入身份；部分 validate 要求与当前生成计划完全相等 | [pilot_contract](../../src/actio/pilot_contract.py)、[transport_diagnostics](../../src/actio/transport_diagnostics.py) | 移动文件会改变身份；旧 reader/pins 必须固定，新布局使用新的实现身份 |
| CLI、Python 子进程、TS 插件含模块名；SQL/JSON/MJS 用相邻路径加载 | [pyproject](../../pyproject.toml)、[MJS 发送插件](../../src/actio/plugins/transport.mjs) | 同步迁移资源和入口，必须通过 repo 外 wheel、child/IPC、实际 CLI 验证 |
| tests 有 42 个 Python 文件，scripts 有 88 个 Python 文件；测试辅助逻辑与阶段脚本混杂；当前没有 `.github/` | [tests](../../tests/)、[scripts](../../scripts/) | 当前测试分层、共享 helper 独立；历史工具保留受信原版本，不为目录美观改写旧验收 |

静态统计由 AST 遍历所有 Import/ImportFrom（包括函数内），动态导入单列；不自动执行产品。inventory 覆盖 84 个产品文件（69 Python + 14 资源 + 1 许可），列出旧路径、hash、建议去向；它是审阅证据，不是运行时的新的信任根。

本轮另做了有限验证：已安装 C5 与 checkout 的 83 个 `.py/.mjs/.sql/.json` 文件逐字节一致；现有 `test_failure_observation.py` 12 项通过；公开 C5 package 在原只读 GUARD 下 verify 通过，仅认证合成重算。未重跑官方运行矩阵，也未重新认证受控历史 raw。

审阅试验曾将“禁止读环境变量”的纯读包 guard 套到全部 12 项测试；其中模拟 `run-local` 的 argparse/gettext 读取环境，导致 11 通过/1 ERROR。该错误是本次验证范围设置不当，记录保留在 inventory 的 review_checks；随后按原本边界分别验证 12 项测试与纯 verify，没有改产品、放宽纯 verify guard 或声称修复了产品缺陷。

## 2. 重构保持什么

1. 持续复用 DSH/Concordia/SQLite，保持 Windows x64、Python 3.12、现有锁定版本。重构不顺带升级 SDK、改变 prompt/任务/模型参数、调超时或实现自动 retry。
2. Store 是领域权威，Ledger 是发送权威，DSH 是原生权威。不得因拆 repository 把一次多表事务变成多个提交，或将跨库一致性说成已经解决。
3. 保留 canonical bytes、schema 语义、输入可见性、实际 A 历史、准入、双通道/压缩 native 核验、unknown/null、完整计划分母、追加谱系和现有停止合同。
4. 数据库 schema 原则上不变。确有必要时必须单独说明原因、先备份/复制、定义只读旧库与显式迁移；不自动迁移用户工作库，不用 schema bump 掩盖布局变动。
5. 历史 `docs/validation/phase*`、受控 DB/raw、旧六份 candidate decisions、各 evaluation/claims、失败记录及 C5 future schedule 只读保全。后者保持 proposal，不执行。
6. 真调用计数仍 172，目录 GET 1。重构新 provider、目录、外部 MCP 请求均为 0；无 judge/人工标注/训练/部署/恢复开发。

## 3. 兼容性与身份设计

**公共接口需要登记，私有 import 不应成为永久包袱。** 从 pyproject、所有 `__main__`、README/CLI 文档、`subprocess -m` 和 TS 插件提取调用清单；至少覆盖四个 console scripts、现有 `python -m actio...`、host/eval_worker/mcp_server/budget IPC、公开纯 reader。清单记录保留路径、参数、stdout JSON、退出码、新实现和验证项。

保留必要旧路径的薄 shim，只转发到新接口；新实现不得反过来 import shim。内部测试转向新稳定 API；不为每个私有旧文件复制一份实现。根目录保留文件必须在兼容清单中解释，不能把 67 个旧文件原封不动包一层。

遇到同名文件变为包（例如 `evidence.py` → `evidence/`），不能同时依赖同名文件和包的导入优先级；需要兼容的符号放在受控包入口，模块执行使用包的 `__main__.py`，并单独验证。兼容层不得重新带入核心循环。

**拆开三种身份**：

- 数据协议身份：schema、canonical、任务规则和指标含义。目录变更不等于协议升级。
- 当前执行实现身份：新源码/资源/注册表/执行相关工具的完整闭包；确定排序、hash 规则和 wheel 对照，传给纯 profile 构造器。不能只 hash facade，也不能遗漏 TS/SQL/JSON 或被间接加载的文件。
- 历史认证身份：受信 Git commit、reader、source pins 和 artifact 原摘要。使用固定旧安装/checkout 核验，不把旧包来源改成新布局。

历史 reader 分派来自代码维护的注册表；拒绝 artifact 中的任意模块名、命令或可执行路径。外层 history runner 与内层纯 reader 分离。新实现需要独立 refactor plan/evidence identity；不要改旧 `implementation()`、旧 freeze、旧 manifest 的记录来凑 PASS。规范允许的 UUID、时间、临时路径和新实现身份差异必须逐字段登记，不能做大范围 JSON 删除再比较。

## 4. 迁移步骤与完成门槛

| 步骤 | 实施内容 | 离开该步骤前的证明 |
|---|---|---|
| R0 基线 | 从最新 main 建任务分支；读取 docs/AGENTS；重新盘点依赖、入口、资源、测试；保存源码和历史摘要；建立短路径隔离目录 | baseline/source/entrypoint/test 清单、基线测试及失败分类；未修改历史 |
| R1 纯核心 | 从 common/各 contract 提取 contracts；拆出 domain 规则、任务可见性与独立 measurement；先解除 eval_contract/terminal/verify 等反向依赖 | canonical/任务/指标/拒绝向量差分一致，纯包导入无 I/O；独立 oracle 不调用生产裁决 |
| R2 持久化与端口 | 引入最小业务端口，拆 Store/Ledger 的 SQL、迁移、快照；搬资源而不改其内容；拆 OS/文件 I/O | 事务、去重、revision、lease、并发资格、unknown 和 lineage 不变量通过 |
| R3 执行与 profiles | 拆 DSH/Windows/MCP/Concordia/transport；版本差异进入受信 profiles；application 统一编排；产品 fixture 摆脱 tests | 本机契约测试、完整输入绑定、停止/清理路径通过；新核心无阶段反向 import |
| R4 证据与入口 | evidence 纯读包、固定历史 runner、composition/CLI/child IPC/shim；迁移当前工具与测试组织 | CLI 矩阵、纯 guard、历史核验、新 wheel 资源及 repo 外导入/子进程通过 |
| R5 最终重新验收 | 冻结新源码/fixture/工具身份，实际运行下表的最终本机验收，保留开发失败；更新三篇架构文档 | 新源码实测与历史重算分开，原有能力不减少，清理与交付验收通过 |
| R6 发布 | 完成成果说明、迁移指南、README/里程碑、证据 manifest；提交任务分支与 main，普通推送并查远端 | 两远端 SHA 分别等于本地；工作树干净；未将不完整结果说成完成 |

按这些步骤形成可检查的小提交。它们是同一个重构任务的检查点，不是让 session 每做一步就停下请求确认。若发现依赖图要求改名/调整子目录，自行选择最小调整并记录理由；若资源确实缺失则完整说明阻塞，不能伪造测试通过。

## 5. 验收矩阵

新增结果统一写入 `docs/validation/refactor_modularity/` 或其受控 `.local` 路径，绝不沿用会写旧 phase 证据目录的发布脚本。以下命令/runner 是实现要求，不是假称当前已有命令。

| Gate | 必需验证 | 通过条件 |
|---|---|---|
| G1 架构 | AST 含函数内 import、显式动态 registry、package 初始化与实际 import guard；禁止 product→tests/scripts/旧 shim | 目标业务包 DAG 无环；纯包无 sqlite/SDK/process/env/network 副作用；无未登记兼容根文件 |
| G2 行为保持 | C5 基线与新实现：规范编码、schema、两 family 可见输入/规则、指标、candidate/evaluation、错误拒绝差分 | 确定性领域内容逐字节或逐字段相同；非确定性差异有精确白名单，不绕过来源检查 |
| G3 状态 | 事实去重/冲突、memory 可见性/revision、同事务 effect、只读旧库、快照、lease/fence、竞争进入、attempt 单次资格与 unknown | 测试真实 SQLite 和关键并发/中断；原 schema/事务语义保持，不证明完整恢复 |
| G4 打包与接口 | 标准 wheel 干净安装，当前 CLI 全矩阵，SQL/JSON/MJS/许可 resources、四个 console scripts、Python/TS child IPC | repo 外 cwd、无 src/PYTHONPATH/tests/scripts 兜底仍能工作；必要兼容入口/失败退出码一致；pip check |
| G5 历史 | 固定 C2/C3/C4 reader 与 C5 固定运行源码/最终诊断，旧 manifest 和受控材料 | 原结果、19 claims、各谱系和 unknown 不变；公开投影/受控 raw 的核验范围分列 |
| G6 本机真实集成 | 官方 DSH/真实 Concordia 的 assistant/social、MCP、隔离与记忆共享路径；再用**最终新安装**执行 C5 九场景 | 新矩阵正式 12 sends、5 settled/usage/admitted、7 unknown、6 not_run；12 Worker/9 服务清理、相关端口无监听；无外部请求 |
| G7 当前测试面 | 将42个现有 Python 测试/辅助文件逐一分类；所有仍受支持的当前测试进入分层 runner，阶段冻结测试通过固定 runner | 不得只跑12项纯测试替代项目回归；不得用 skip/删断言规避失败；按能力列明实际执行、历史核验或阻塞 |
| G8 交付 | 历史前后摘要、最终安装/源码身份、失败日志、清理、凭据/公开材料扫描、文档链接和发布核对 | 真实调用0；计数独立；没有 key/raw reasoning/error.message/敏感请求进入 Git；任务分支/main SHA 已核对 |

G6 的基础集成测试如需更多本机发送须有独立清单和计数；不能都混成“12 次”。新九场景保持原刺激和期望，但使用新的 run id、root、freeze 和证据包。开发失败也留档；修复后新的有限本机验收不是对 C4 真调用的重试或补样。

G5 受控文件不在 Git 内；本机若缺失则明确 BLOCKED，保留可完成工作。不能从报告重新合成 raw。发布可交付的失败/阻塞结论仍遵循用户推送要求，但结果不得标成“重构全部通过”。

wheel 做两类安装验证：完整锁定依赖环境要求 `pip check` 通过；纯 reader 另用无 DSH/Concordia 的最小环境（可显式 `--no-deps` 安装同一 wheel）验证能力隔离，后者不冒充完整依赖安装或 `pip check` 通过。

只读 guard 约束纯 plan/analyze/verify；execute/run-local 的 CLI 不要求禁止一切环境/进程访问，而要限制到明确的本机操作。两者的测试应分组，避免重复本次审阅时把 execute 参数解析误判为纯函数违规。

## 6. 最终项目要让开发者怎样使用

实现一个维护中的测试/核验入口，提供 pure、state、packaging、history、runtime-local 和 all-local 等明确选择；具体 CLI 在实施时确定并实跑记录。默认入口不能调用外部 provider。历史工具通过受信固定版本使用，不让普通开发者猜测应运行哪一个 phase 脚本。

三篇架构文档以实际实现为准更新：README 一页全局图，MODULES 写每个模块的输入/输出/不变量/流程，本文记录迁移步骤、兼容表与验收链接。README 链接这三篇，MILESTONES 保留历史并追加工程重构条目；不把 C5 改写为从新包生成的历史。

完成判据不是“目录变漂亮”，而是开发者能独立理解和测试模块，纯 verifier 能独立安装，产品不依赖测试目录，历史可复核，最终新源码有新的本机运行证据，既有实验结论没有被改写。
