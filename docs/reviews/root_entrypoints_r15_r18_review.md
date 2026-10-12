# R15–R18：收拢根入口与完成整体验收

日期：2026-10-12；审阅代码基线：`9e4db3211592d1656cbac6cae09862c6ffe2ce5a`。本次是文档审阅与下一轮计划，不执行产品迁移或实验。

## 结论和用户已经确定的取舍

当前代码已经有职责层和 evidence 五组划分，但 `src/actio` 根层仍放着大量旧入口，目录视觉与维护方式没有充分体现模块化。上一轮“继续保留全部兼容薄层”的方案无法达到用户期待，且整体验收尚未完成。

用户本轮明确选择：**统一改用新入口；旧命令仅由固定历史版本支持，允许明确的接口迁移。** 因此下一轮可以删除当前版本中的旧根模块、旧 CLI 别名和登记 reader 旧路径，不再为兼容而把文件留在根层；必须提供迁移表并同步所有当前调用者。旧历史版本及证据不受此变更影响。

本轮直接改善根 README 的开头，并添加 [src/actio 导航](../../src/actio/README.md)。实际代码搬迁由[完整执行 Prompt](../prompts/refactor_public_entrypoints_r15_r18.md)完成。

## 审阅发现

| 优先级 | 事实与影响 | 行动 |
|---|---|---|
| P1 | R11–R14 结果为 INCOMPLETE，根 README 却继续突出 R7–R10 的“当前重构完成” | 本次修正文案；下一轮完整验收前不能标完成 |
| P1 | 根层有24个跟踪文件：19个兼容.py、2个包入口.py、3个JSON，另有11个目录 | 删除19个旧入口，将3个JSON与pins收进resources；新增README只用于目录导航 |
| P1 | Python/TS 内仍以字符串启动 actio.budget/host/mcp_server/eval_worker；静态import图看不到这些耦合 | 新命令及内部IPC/child入口必须同时迁移并实测 |
| P1 | 新递归检查器仍有漏检，见下方临时反例 | 修正规则并加入回归，不能用SCC=0替代完整分层结论 |
| P1 | 34 suites的源码当前有165个test_方法，较R7–R10新增1个边界反例；suite-map不是最终执行证据 | 按实际方法清单保全与一一映射，最终完整执行，不硬编码只检查164 |
| P2 | minimal运行装配失败与离线reader要求混在pure组 | 分开标准库离线能力与完整依赖运行装配；修复测试分组或依赖注入，保留失败 |
| P2 | resources通过parents索引及硬编码路径加载；移动会影响身份闭包与wheel | 使用清楚的资源owner和可安装定位，维护新源码身份，固定历史不刷新 |

本次独立运行现有AST检查：169模块、595边、模块SCC=0、现有规则违规=0、未迁移根实现=0。这不意味着根层文件少，也不意味着所有边界都被检查。

### 两个复现的漏检

在临时目录运行当前 `inspect(root)`，没有改动产品：

1. `evidence/audit/__init__.py` 导入 `evidence.campaigns.leaf`，同时 `evidence/campaigns/__init__.py` 导入 `evidence.audit.leaf`。模块图可以无环，但分组图应有 audit ↔ campaigns；当前结果的分组边全部为空、PASS，因为组检测忽略三段的包节点。
2. `contracts/nested.py` 执行 `import_module('..application.impl', __package__)`。应识别 contracts → application 越界，当前只记录字符串并PASS。

另外，兼容清单虽然存在，checker仍依赖docstring前缀识别根shim，尚未把清单当可执行约束。旧结果保留，新规则需说明覆盖范围；不能倒写旧报告。

### minimal 失败的实际位置

本机 `D:/ar-directory-20261012/pure2/failure_observation.log` 显示：测试仅mock了run，但CLI仍执行 `diagnostic_ports()`，通过runtime导入 `mcp.server` 后失败。这里不能把“安装了MCP即可”说成离线模块已经独立。应分别测试：

- 离线reader及help在无DSH/Concordia/MCP环境下可用；
- 运行装配和受管执行在完整锁定环境下可用；
- CLI返回失败退出码的纯路由测试可以注入ports factory，另有真实装配测试防止mock掩盖问题。

`full-pure/receipt.json` 虽写PASS，仅覆盖报告所述七组，未包括failure_observation；不能当完整八组或34-suite通过。本次没有重跑运行测试。

## 目标目录与验收口径

```text
src/actio/
├── __init__.py                 轻量包元数据
├── __main__.py                 唯一 python -m actio 入口
├── README.md                   九个核心模块及导航
├── contracts/                  格式与端口
├── domain/                     状态和领域规则
├── tasks/                      任务与可见性
├── profiles/                   配置与准入规则
├── application/                用例编排、原事务与状态变更
├── adapters/                   持久化/运行时/环境/传输/文件
├── evidence/                   audit/bundles/campaigns/lineage/diagnostics
├── measurement/                独立oracle与指标
├── interfaces/
│   ├── cli/                    用户命令的轻量路由与handlers
│   ├── ipc/                    budget等内部协议入口
│   ├── workers/                host/mcp/eval子进程入口
│   └── 现有装配与服务桥接模块
├── resources/
│   ├── __init__.py             轻量资源锚点
│   ├── pricing/                readiness_quote.json
│   ├── trust/                  evaluation_history.json、task_diagnostic_trust.json
│   └── pins/                   concordia.json、c5_runtime.json
└── _vendor/                    窄复用及许可
```

硬验收：包根层只允许 `__init__.py`、`__main__.py`、`README.md` 三个跟踪文件，另为上述模块目录。不能以“19个文件都只有几行”替代此结果；也不能将19个文件改成19个同名文件夹。检查以Git跟踪文件和安装wheel为准，缓存不纳入。

不增加覆盖全项目的core/utils大杂烩，不复制旧实现，不用sys.modules、import hook、动态alias或构建期生成的旧入口来制造表面兼容。原application事务抽象的深化不属于本轮。

## 入口与资源迁移

- 统一用户入口为 `actio` / `python -m actio`，采用显式命令树；旧四个console scripts收敛为一个，旧 `actio-eval` 等命令写出替代形式。
- 内部入口为 `actio.interfaces.ipc.budget` 与 `actio.interfaces.workers.{host,mcp_server,eval_worker}`。保持stdin/stdout、异步调用、argv、错误码、期限、Job及清理合同，只改变寻址。
- 将旧公开reader迁到实际owner，包括 `actio.evidence.diagnostics.failure_observation.from_entry`。用户新选择覆盖上一轮要求“继续保留旧reader路径”的限制。
- SQL、TS插件、fixtures与第三方许可继续随adapters/_vendor owner；根层JSON与pins整体收拢。资源内容原字节保持；源码路径清单、当前身份和TS启动地址会因必要变更产生新hash，不伪称原字节不变。
- 这属于明确的开发期破坏性API迁移，计划包版本 `0.2.0`（以实施时尚未使用的下一minor为准），不无故更改实验schema。旧命令和旧材料使用各自固定commit及对应wheel环境，不向新入口回填旧hash。

## README 的开头应让读者知道什么

前面先说明模块化单体与核心模块，不以阶段日志开场：项目目的 → 九模块职责表及源目录链接 → 输入/输出关系 → 当前状态 → 使用导航。模块名与代码目录一一对应，adapters和evidence各自的五个子模块有简短说明；resources与_vendor标为支持内容。

[系统一页图](../architecture/README.md)、[模块卡片](../architecture/MODULES.md)、[流程](../architecture/FLOWS.md)继续承担深入说明。所有例子区分当前命令、拟议命令、固定历史复现。README里的“功能已经实现”与“本轮最终验证完成”必须分开。

## 实施顺序与终点

| 步骤 | 工作 | 必须交付 |
|---|---|---|
| R15 | 建基线、复现两个checker缺口、清点命令/165方法/资源、分清minimal与full | 可执行新入口映射、规则反例、基线证据；无需先重跑一轮旧正式C5 |
| R16 | 唯一用户CLI、独立IPC/worker入口、删除根shims、迁移当前调用者 | 当前用户、Python API、TS/子进程和测试调用全部同步，旧入口明确失效 |
| R17 | 根资源收拢、资源/源码身份/打包同步、README开头与模块导航 | 根3文件、完整wheel资源、当前与历史版本分工明确 |
| R18 | 完成上一轮欠缺的D2–D6及本次入口破坏性变更验收 | 同一最终wheel全34 suites/至少165原方法+新测试、555差分、完整历史保全、九场景C5、清理、普通发布 |

新增tests物理分层不是本轮硬要求；现有suite/method映射与运行顺序必须正确。可顺手归类实际装配测试，但不能为搬所有测试文件延后主要目标与完整验收。

本轮需保持：外部实验请求0、真实凭据读取0、不进入C6，原C4=INCOMPLETE、C1=infrastructure_failure、研究UNESTABLISHED、activation=false。最终应给出完成结果或真实阻塞；不能到pure测试通过就主动停止，把可完成的验收一再留给后续轮次。
