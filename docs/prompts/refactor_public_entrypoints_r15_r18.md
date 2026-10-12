# Codex Prompt：R15–R18 根入口收拢、模块导航与完整验收

请在下一session实施本任务，持续完成到新最终wheel验证和GitHub发布。不是只写计划，不在搬完文件或pure通过后主动停止。

## 一、目标与用户确认

仓库：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。
GitHub：`https://github.com/ChaunceyKung/Actio-RSI-infra`。
审阅代码基线：`9e4db3211592d1656cbac6cae09862c6ffe2ce5a`；其后可能已有本Prompt的文档提交，以实际main为起点，不reset回旧SHA。

用户不满意src/actio根目录仍有太多文件，要求根README开宗明义说明模块及功能。用户已明确选择：

> 统一改用新入口；旧命令仅由固定历史版本支持，允许明确的接口迁移。

此选择覆盖旧Prompt中保留全部根shim、四个旧console scripts、旧reader地址的要求。执行明确API迁移，不为同一选择再次询问，不保留一层隐藏的旧入口。历史版本、历史证据和行为合同仍需保全。

先读AGENTS.md、`docs/reviews/root_entrypoints_r15_r18_review.md`、当前README和三页architecture、refactor_directory的RESULTS/manifest/compatibility/suite-map、R7–R10完整验收、原R11–R14 Prompt。冲突以本次用户新选择及本Prompt为准。检查status/worktree/branch/remote，保留并发与用户改动；建议任务分支`refactor-public-entrypoints`。

范围：工程入口、资源、README及完整验证。真实凭据读取=0，provider/catalog/外部MCP请求=0，不做C6、judge、训练、部署或激活。Git发布和锁定依赖准备可以正常联网；用户无金额上限偏好仍在，但本轮不需要真实模型调用。

## 二、当前事实，不夸大旧验收

R11–R14已完成evidence五组目录，扫描169 modules/595 edges、SCC=0；但新wheel完整34-suite、正式C5、全历史保全仍INCOMPLETE。根README中的旧“模块化重构完成”不能替代本轮状态。

当前src/actio根层24文件=19个旧shim+init/main+3JSON，另11目录。当前测试源码有34 suites、165个test_方法（R7–R10的164+R11新增边界1）。实施时重新清点实际方法；旧suite-map只是清单不是通过证据。

minimal的failure_observation测试失败点：mock run后仍执行diagnostic_ports()，最终导入mcp.server失败。full-pure收据的PASS仅覆盖七组选定套件，不代表全部pure或all-local。

## 三、硬目标与目录

完成后Git跟踪的src/actio根层只允许：
`__init__.py`、`__main__.py`、`README.md`。
根层其余均为以下职责目录，不保留*.json、pins、19个兼容.py或同名替代文件夹。

```text
src/actio/
  __init__.py
  __main__.py
  README.md
  contracts/ domain/ tasks/ profiles/
  application/ adapters/ evidence/ measurement/
  interfaces/
    cli/          main与用户命令handlers
    ipc/          budget内部协议入口
    workers/      host、mcp_server、eval_worker子进程入口
    ...           现有必要装配/桥接，按职责记录
  resources/
    __init__.py
    pricing/readiness_quote.json
    trust/evaluation_history.json
    trust/task_diagnostic_trust.json
    pins/concordia.json
    pins/c5_runtime.json
  _vendor/
```

这是模块化单体，不创建微服务/通用插件系统，不把实现整体塞进一个core、legacy或utils。adapters和evidence已清晰，保留已有五组。application仍含SQL/mixin，保持原单连接事务，不在此轮重做Repository/UoW。

禁止为达到根文件数而使用sys.modules alias、meta_path/import hook、sys.path注入、构建期生成旧actio.*入口或旧命令的隐藏fallback。源布局和安装wheel均检查，不能源代码根干净而wheel继续偷偷保留旧API。

## 四、R15：基线与检查器

1. 记录当前commit、跟踪树、旧命令/API/export、源码与资源闭包、34suite及165方法的身份映射；私有import、子进程字符串和console metadata都要扫描。
2. 先用临时fixture复现并修复两个当前漏检：
   - audit/__init__.py导入campaigns.leaf，campaigns/__init__.py导入audit.leaf。模块DAG可无环，但分组应判audit↔campaigns环；当前checker忽略三段包节点。
   - contracts/nested.py内import_module('..application.impl', __package__)应识别向application越界，不能只记录字符串后PASS。
3. 递归解析绝对/相对/包init/局部/字面量动态导入；非字面量无法解析的明确列出，不谎称完整覆盖。包组归属根据路径完整判断，未知组报清楚错误，不KeyError或静默漏掉。
4. 执行实际边界规则：纯层向下依赖；application不直连具体runtime/transport/environment/persistence/interfaces；只读evidence不反向引入writer/application/runtime。资源数据读取与validators、无I/O规则区分；不要为了resources包增加一个可以从纯层执行任意I/O的宽泛豁免。
5. 删除“docstring写Compatibility就豁免根实现”机制在新布局中的必要性，改根文件白名单与owner检查；记录版本变化，旧checker及旧报告仍可按固定SHA取回。
6. 新增包级与相对动态导入反例、root白名单反例、当前代码通过例；保存机器报告。测试checker应观察规则拒绝的具体原因，不仅检查任意异常或非零返回。

## 五、R16：统一新入口，迁移完整调用链

唯一用户入口：`actio`与`python -m actio`。下表是拟议的新命令族，尚未实现；实现时保证全量旧功能可从新命令找到，逐条保留其参数/结果语义或给出明确机械映射。

| 原入口 | 新入口方案 |
|---|---|
| actio.cli / 原actio基础命令 | actio run <原基础子命令及参数> |
| actio.verify | actio verify <原参数> |
| actio.evaluation / actio-eval | actio evaluate <原参数> |
| actio.candidate / actio-candidate | actio candidate <原参数> |
| actio.candidate_evaluation / actio-candidate-evaluation | actio candidate-evaluation <原参数> |
| actio.preflight/readiness/gateway/pilot/suite/robustness | actio <同名命令族> <原参数> |
| actio.task_diagnostics | actio diagnostics task <原参数> |
| actio.transport_diagnostics | actio diagnostics transport <原参数> |
| actio.transport_campaign | actio campaign verify <目录> |
| actio.budget | python -m actio.interfaces.ipc.budget <ledger> |
| actio.host | python -m actio.interfaces.workers.host <配置> |
| actio.mcp_server | python -m actio.interfaces.workers.mcp_server <配置> |
| actio.eval_worker | python -m actio.interfaces.workers.eval_worker，保持原stdin协议 |
| actio.common | 按symbol改到contracts.json或adapters.filesystem.common，不造新common聚合层 |
| 旧reader imports | 改到evidence实际owner；例如failure_observation.from_entry迁到evidence.diagnostics.failure_observation.from_entry |

接口实现：
- 将interfaces/cli.py改成interfaces/cli包，旧main逻辑归run.py；按命令handlers拆分，轻量main只路由。旧interfaces里的命令main可迁到cli/，应用服务桥接留给实际owner，避免复制同一实现。
- 不把所有模块eager import；顶层--help和只读verify/diagnostics不得加载DSH/Concordia/MCP、创建DB或Worker。为原无argv参数的main增加显式argv，避免靠全局sys.argv反复改写路由。
- 如果从evidence/campaigns/transport_campaign迁出argparse/main，保留纯verify_campaign行为；新handler委托它，不重复实现核验。
- pyproject只保留actio console script，目标为新main；__main__.py只委托它。采用清楚的开发期破坏性版本（计划0.2.0；若已被使用则下一未用minor），包metadata与__version__一致。
- CLI用户命令、Python API、内部IPC是三类接口：CLI统一不代表内部协议都挤进一个用户dispatcher。IPC stdout只能是原协议，不插入banner或弃用提示。
- 同步TS插件spawnSync中的budget模块、supervisor默认host、runtime MCP args、evaluator -m，以及测试、当前维护工具里的import和命令字符串。
- 当前sandbox/eval_worker deny列表和只读guard也需包含新路径，保留必要的旧拒绝项。只改入口不能造成新模块绕过隔离。
- 删除19个根兼容.py；删除evidence/failure_observation.py旧公开facade，更新所有当前调用者到diagnostics owner。旧import不再可用是用户授权变更，必须在迁移文档标明。
- 旧命令验证为明确不可用，不能意外导入另一个环境的旧安装；新版wheel卸载/安装干净，避免遗留文件制造假兼容。
- 参数映射允许实施中基于实际签名微调，必须在MIGRATION文档提供可直接复制的新命令，不只写“换新路径”。

不要继续要求“当前TS插件字节不变”：本次迁移预算模块必然修改当前TS启动字符串。允许这项窄变更并验证原协议/guard/期限/无重试语义；旧TS资源仍在固定历史commit中逐字节验证。

## 六、R17：资源归位与README

- 将根3JSON及pins中的2JSON移到目标resources目录；数据字节不变。使用importlib.resources或适合安装包的集中只读定位，不能散落新的parents[N]魔数或按CWD查找。
- SQL、TS/MJS、fixture、许可保留实际owner，无需全部归一个resources仓库。
- 同步pyproject package-data、build/freeze/packaging、源码身份闭包和portable reader。新路径完整参与当前身份，不删项、放宽hash检查、扩大未受约束reader或假装旧材料来自新代码。
- 旧报价内容不改；rehearsal保留显式Clock，live/system真实UTC。artifact schema若语义没变无需强制升级；若不可避免发生格式变化，显式新版本并保留固定旧reader。
- 对history/vectors/completion等工具区分执行在“当前安装”还是“旧固定reader”里的代码字符串。只迁当前调用，不机械替换所有历史字符串；新验收路径可加窄适配，旧历史CLI按旧SHA重放。

README前部必须在阶段日志之前展示：
1. 一句话项目目的与模块化单体形态；
2. 九模块表：contracts、domain、tasks、profiles、application、adapters、evidence、measurement、interfaces，逐项功能、输入/输出、源码链接；
3. adapters五组与evidence五组功能说明，resources/_vendor为支持内容；
4. 一条清楚的数据流：输入冻结→执行/准入→环境效果→持久化→只读核验/独立测量→追加决策；
5. 当前实验状态、当前重构Gate，分开历史已通过与本轮未完成/已完成。

root README不用塞完整阶段报告；详细历史留MILESTONES和validation。同步src/actio/README及architecture三页；每个核心模块提供简短包说明/README（可链接模块卡片，避免复制大段文档），覆盖职责、输入、输出、主要内部步骤、依赖边界、真实入口和对应测试。根树必须与最终实际一致，方案与现状明确区分。

新增`docs/architecture/MIGRATION_0_2.md`（按最终版本调整命名）：旧命令/API→新命令/API、移除列表、资源搬迁、适用版本、旧材料如何固定版本复现、当前安装方法。不要保留复制旧shim的“临时后门”。

## 七、R18：完成欠缺验收，不再只交目录

旧R11–R14结果保持INCOMPLETE这一历史事实；本轮结果明确哪些旧欠项在新的最终wheel被验证。无需先重跑一套旧正式C5再迁移；开发期定向，最终源稳定后构建唯一正式wheel完成全量验证。

- 清点并执行原34 suites/165方法（含新增边界1）+本轮必要新测试；保持原断言语义。物理测试分层可按副作用调整，不是本轮首要目标。若拆分方法，保留原→新一一或显式一对多覆盖关系，不能少跑、重复计数或只核名字。
- 明确minimal与full环境。minimal用--no-deps是离线功能测试环境，不等于满足项目完整依赖；full按锁定依赖安装并pip check。运行装配测试放full或用纯路由依赖注入+独立真实装配测试，不能删失败断言或把整个组skip。
- 原555向量完整JSON差分，在固定旧环境与新wheel独立进程比较。处理新路径/版本身份的机械差异时只允许事先列出的身份字段映射，不把业务结果归一化掩盖变化；输出完整差异与预期身份变化。
- 安装wheel与源码身份一致；从repo外-I运行新console/module CLI、纯imports、只读guard；检查资源字节/许可及没有19个旧根模块。做真正成功/拒绝路径，不能只验证help。
- TS→新budget IPC成功reserve/sending及拒绝/unknown路径，host/MCP/eval子进程新入口、async生命周期、stdout协议、超时、Job与端口清理。
- 根文件白名单、递归模块SCC=0、evidence包DAG、读写边界、入口字符串不再引用旧路径（仅历史/迁移说明或安全deny列表可登记出现）。
- 全量历史保全：原1048文件集合、固定reader、C2/C3/C4/C5、19claims、旧evaluation/decisions、unknown及not_run原样。历史证据按对应commit验证，不用新路径重写旧manifest。当前改动的TS/API/资源位置有明确新旧映射，不能笼统宣称所有产品资源字节未变。
- 同一最终wheel正式C5九场景：12 sends、5 settled、7 unknown、6 not_run；冻结、正式运行、独立复算与清理收据完整。只loopback，统计开发、失败、重测、正式发送各自与总量。保留原失败。
- 若测试发现产品缺陷，修复后重新构建最终wheel及相应验收，不能拼接不同wheel的成绩。最终通过且源码不变后不重复昂贵检查。
- 保存新`docs/validation/refactor_entrypoints/`：RESULTS、CLI、manifest、入口/方法/资源映射、架构/反例、差分、wheel安装、全量回归、C5、历史保全、清理与发布引用。摘要证据可发布，真实raw/密钥/DB/venv/wheel/大日志不提交。

完成定义：
G1 根3文件与职责目录；G2 命令/API/IPC全链迁移；G3 checker反例与真实结构；G4 原34suite/165方法+新增全过；G5 差分/历史；G6 安装与正式C5/清理；G7 README/模块文档/迁移说明真实且链接有效；G8 Git发布核对。
G1–G7未完成就不能宣称完成。遇可解决的测试/导入/打包错误继续修复，不把工作困难或执行时间长本身当作停止条件；真正缺失依赖/历史材料/网络阻塞则给精确证据与剩余项。

## 八、交付与发布

用户持续授权每轮提交并普通推送main，任务分支也发布，无需再问。检查差异和受控raw/凭据模式，不读真实key。fetch检查并发，安全快进或保留他人改动后整合，不force push，不reset覆盖。

分别普通推送任务分支和main，并分别ls-remote核对SHA。网络失败做有限诊断重试，保留本地提交并如实报告；发布成功不是验收通过。产品wheel/commit与后续仅文档发布commit分别记录。

最后中文报告：根文件前后数量和最终树、九模块与新命令入口、删除旧API及迁移文档、完整测试与原失败、正式C5/清理/历史、Gate、两个远端SHA和工作树状态。

真实生成累计仍172、历史目录GET1；C4=INCOMPLETE、C1=infrastructure_failure、research=UNESTABLISHED、activation=false、binary_source_mapping=unproven、full_controller_recovery=unsupported。关闭这轮入口与目录任务，不进入C6。
