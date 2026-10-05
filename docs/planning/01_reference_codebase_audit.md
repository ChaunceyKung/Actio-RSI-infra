# 01 · 参考代码库审计

本审计按角色查入口→实现→存储/外部依赖→结果→失败/恢复→tests，非全仓库安全/覆盖率审计。路径、行号、完整SHA、canonical repo、license统一在[15](15_evidence_registry.md)；覆盖与运行状态分开见[16](16_capability_and_maturity_checklist.md)。已读旧报告/v2/详解作为导航，冲突按当前源码修订。没有“有tests目录所以成熟”的总分。

## DSH / Cordis：主执行路径，有真实SDK但生命周期尚缺

`DeepSeekHarness.start_session→Session.run→HarnessClient` 启动/通信 → `HarnessSdkJsonRpcServer.handleRequest` → `getOrCreateSession/createSession` → `ctx.agents.create` → `ReactLoopAgent` 模型/工具循环 → session events/JSONL。server实际只有 `initialize`、`session/prompt`、`shutdown` 三种request；新session是prompt路径创建，不是已有完整的open/resume API。initialize提供worker级model/provider；异构roster需要显式composition，不能默认一个worker承载所有spec。

client有stderr tail、pending waiter、通知订阅、close/shutdown/terminate/kill路径；SDK超时并不证明服务端取消，queue.Queue默认无界。SessionStore内部fork可在合法seq上取inclusive prefix，buildForkSeed补seed/turn closure；它不是世界、工具、plugin状态快照。JSONL handle串行写/200ms live batch、scanner合法前缀、尾部修复、拒绝部分committed corruption、migration验证、kernel lock是值得保留的实现；通知与flush/断电持久性仍须真实runtime探针。

Cordis effect/disposer逆序清理可复用，不提供外部事务。DSH MCP transport/tools/connection用官方client2.0.0，signal/timeout/reconnect存在，HTTP互动OAuth未被工厂接入，resources另一个plugin。local sandbox平台差异显式，Windows partial enforcement不能承担任意代码候选安全隔离。runtime wheel文档列Windows x64和配对发行，但本机未安装/执行该wheel；源码pyproject的`0.0.0.dev0`不是可直接当发行pin的版本。

测试：上游client29项在UTF-8隔离副本通过，初次3项为GBK fixture编码失败；不是模型/MCP/wheel全链。公开A SDK+B RuntimePort为主，C01补生命周期；5日探针超界转Strands（E001–E006，R01/R02）。MIT根/Cordis，THIRD_PARTY_NOTICES与wheel闭包另审。

## Raven：比较四种粒度

Host Agent的registry dispatch、ModelRouter（classifier/cache）、DAG runner、AdjudicationDesk/Outbox与workspace backend形成完整产品编排路径。DAG finalize补terminal status、写manifest；registry坏文件会警告后按空表处理，memory记录失败可不使node失败。其失败语义适合产品协作，不等于科学实验完整事实存储。Curator在README中仍为experimental/repository-only，不能列为稳定安装包能力。

外置evolver拆开scoring/EvalFn、gate、baseline、tree/node、archive、bench和git执行。paired_lift实际把mean改进作为promoted，2σ只独立credited；PairedTwoSigmaGate并未把名字变成强制显著性门槛。infra尝试保留分母、缺task按0；n1/零方差inf对Actio准入不合适。37项gate/scoring测试通过正好确认这些语义，并非证明其统计判断适用于社会场景。

archive的WHERE×WHY、cell elites、重组冲突过滤有模块价值；超固定vanilla即可bank，未必胜当前champion；save吞OSError、load错误清空、部分lineage仅promoted记录，不能原样做权威档案。README明确计划退役evolver树。对比：①root fork F：多owner且升级包袱；②独立evolver adapter B不选：仍拉bench/git/loop与不合适判定；③局部C02/C03主选：保留诊断/selector切断闭包；④纯D备选：若抽取代价过高退到标准统计诊断/SQL parent query。Apache2与NOTICES必须保留（E007–E009）。

## Letta：当前local/cloud与历史archive必须分开

旧letta main导航已指向letta-code；archive是退休V1服务，BlockManager→DB/session/actor权限，不能按MemGPT论文名字推断独立memory库。当前letta-code `Backend`有LocalBackend/APIBackend路径，local extends HeadlessBackend；LocalStore保存agent/conversation/transcript，MemFS以git revision参与system prompt compilation。cloud专用能力如environment routing通过caps区分，不代表整个项目必须云服务。

memory-filesystem/operation引用backend、settings/currentAgent、初始化prompt、git hooks；file lease串行化harness writer，但primary agent编辑不都走同锁。mods注册tools/providers/permissions并持disposers；hooks spawn且设timeout；skill source枚举bundled/global/agent/project，说明扩展真实存在。Windows自动dreaming默认关闭/受限，不应夸成完全无memory能力。

本次浅clone取到tree后checkout中断，改用相同SHA raw文件与hash；未安装/运行。当前memory不是可零成本脱离Letta的library。选择D git-memory/lease/consolidation模式，F完整Letta作为DSH旁第二owner；理由是状态和依赖耦合，不是“必须商业云”。Apache2根，运行依赖/模型独立审核（E012–E014）。

## Meta-Harness / DGM：研究执行外环不直接变产品root

Meta-Harness ONBOARDING明确domain spec、fixed model、完整候选历史、搜索/测试隔离；reference example展示领域搜索，experimental Harbor controller `validate_source→evaluate_source→run_child` 做AST检查、临时source、Harbor子进程及结果聚合。AST不是sandbox；timeout/reward路径可能混淆infra与task。上游controller tests导入缺Harbor阻塞，未启动Docker/付费评测。MIT代码只D，吸收evaluation envelope/冻结方法，不为薄格式引Harbor闭包（E010）。

DGM `DGM_outer.initialize_run/choose_selfimproves→self_improve_step→Docker/SWE evaluation`，metadata archive与parent selection存在，但指标依赖coding accuracy/resolved/empty patches，恢复用POSIX cp。best分支升序accuracy取前K值得复核；不能未经测试复制为最优选择。Apache2，D lineage/探索方法，F直接coding root；没有运行模型/benchmark（E011）。

## Strands：可信备选方向，不假定Python/TS完全对等

Python harness `resolve_interventions`提供off/ask/smart/Cedar/natural-language规则，SDK Agent持model/tool loop、cancel、invocation concurrency，hooks支持before/after模型/工具/调用、可写字段与interrupt。FileSessionManager用随机tmp+os.replace，损坏JSON抛SessionException；每文件原子不等于全agent/world事务。

TS session manager有snapshot_latest/history及invocation/message/trigger保存，FileStorage固定`.tmp`+rename；interventions含异步Cedar WASM依赖，和Python闭包不同。当前远端bidi变更未推翻本次snapshot seam，但仍pin本地审计SHA。测试文件存在，未执行完整依赖/服务suite。Apache2+NOTICE；B备选优先Python worker，保留Python control，不自写loop；切换需相同contract suite（E015/E016）。

## 三个结构不同的环境

Concordia当前是Engine/Entity/GM。`make_observation→next_acting→Entity.act(ActionSpec)→resolve→GM.observe/act`；resolve无Outcome返回，run_loop掌管scheduler。泛型checkpoint保存有prefab config的EntityWithComponents/GM，external Entity可能跳过，restore不恢复engine cursor。B主adapter可用观察/行动seam，完整恢复/branch需组合manifest；第一阶段从episode起点重执行（E017/E018）。

AgentSociety当前v2.9.3：`Society.step→Ray step_agent_batch→gather→EnvRouter.step→advance time→to_workspace`。ServiceProxy/EnvRouter提供环境seam；gather失败时agent文件可能已经写入，tick非全局原子。workspace resume与trace timeline不证明可确定重执行；B/P2要求pending/barrier/proxy重建，而非沿用论文v1MQTT/Postgres结构（E019）。

OASIS `OasisEnv.reset/step/close→platform task/channel/DB`；推荐系统更新后并发manual/LLM actions，clock由平台逻辑推进。ManualAction适合Actio intent，但interview可触发模型；LLMAction应禁用以避免第二loop。step返回None，DB/队列结果需映射；close发送EXIT并等待。B/P2兼容，不声称DB dump包含全部in-flight/RNG（E020）。三者根Apache2，场景/外部数据另审；方法映射见06。

## Graphiti / SOTOPIA / ACE

Graphiti `Graphiti.add_episode/add_triplet/search→LLM/embedder→graph_driver`，EntityEdge有episodes及valid/invalid/expired/reference时间，默认Neo4j/OpenAI但可注入。group_ids可省与UUID lookup意味着必须额外强制scope；namespace模块不是branch实验隔离。Apache2，B可选关系投影；没有图服务/模型测试，初期SQL足够（E021）。

SOTOPIA `EpisodeLLMEvaluator.__acall__→agenerate→structured response→agent_N dimensions`，同步入口未实现；过滤did-nothing、按values枚举身份、异常返回[]是明确wrapper责任。MIT代码，社会scenario数据许可独立；B单评委，不引其整环境/agent loop，先使用自有合成任务（E022）。

ACE `Curator.curate/propose_operations→LLM JSON→apply_curator_operations`。delta提案有价值，但当前merge工具主要ADD，UPDATE/MERGE/DELETE/CREATE_META仍TODO；失败可能返回原playbook。Apache2、D，不将其当带权限/来源/迁移的社会memory后端（E023）。

## Viewer 与协议

Phoenix有trace/OTLP、dataset、experiment evaluation路由，SQLAlchemy持久化/queue/background处理；result或error验证存在。ELv2限制实质性功能的第三方托管，不能当无限制MIT；B内部备选，未部署（E024）。Langfuse有项目鉴权、gzip/size/content/ID验证、OTLP→S3 batch→queue→worker、dataset/score API；畸形batch可能整体拒绝，API ACK不是canonical完成。compose包含Postgres/ClickHouse/Redis/MinIO/web/worker；社区MIT排除EE路径。B主viewer provisional，资源/许可闭包gate，不以其数据库做Actio权威存储（E025）。

MCP当前规范2026-07-28与DSH所用官方client2.0.0都查到；modern discovery/per-request metadata与legacy initialize并存，SDK stdio auto协商可临时启动probe sibling，工具server startup应避免副作用。DSH transport只接headers而非互动OAuth；tools/resources/cancel/error逐项映射见10。实际LICENSE是MIT/Apache过渡，不只读npm metadata（E026）。A2A proto与ACP v1 schema均查官方仓库，后者canonical组织迁移，未选用SDK/未做互操作；D/P2不引内部协议（E027/E028）。OTel官方spec/proto和SDK1.45.0 wheel静态确认span单parent+links、有界queue/drop/timeout限制，A/B仅projection（E029/E042）。

## 缺口驱动的补充审计

| 项目 | 实际入口/观察 | 结论/缺口/许可边界 |
|---|---|---|
| ADAS | `_arc/search.py`生成并exec候选 | D search，F直接不可信执行；Apache2，未跑（E030） |
| AgentSquare | `module_evolution/prompt_memory.py`生成Chroma memory代码并清旧路径 | D seat设计；不当branch-safe memory；根LICENSE本次未定位，禁止A/B/C（E031） |
| AFlow | `scripts/optimizer.py::Optimizer._optimize_graph`选择round/experience/workflow | D planning search，MIT；不当共享runtime（E032） |
| Sotopia-RL | `prompter/direct_attribution_function.py` LLM反馈 | D社会策略诊断，不是因果估计；训练/数据另核（E033） |
| ALSO | `EXP3Bandit`概率权重/gamma更新 | D L0 adaptation，非L1准入；未跑实验（E034） |
| RSIHub | frozen interfaces+driver，远端DSH配方变动 | D外环替代线索；采用须重审当前recipe/许可闭包（E035） |
| autoharness | CampaignEvaluatorPolicy/promotion policy | D冻结评估机制，MIT；不添root（E036） |
| OpenEvolve | Program.parent_id、archive/islands、动态加载evaluator | D/P2 search，Apache2；非世界状态系统（E037） |
| R-Zero/verl/VerlTool | README/训练artifact边界 | D L3外部接口，未下载权重/跑GPU；细节成熟度无法判断（E038–E040） |
| GSME/HarnessBank | 官方abs仍写code upon acceptance | D论文；未验证可导入源码，不能否定所有公开渠道（E041） |
| Self-Evolving Harness | 官方abs未找到repo链接 | D论文，当前实现可用性无法判断（E041） |
| Claude Code Mods | 本地blog/links导航，官方页403 | D文档；访问失败不是无源码（E041） |

核心完善的判定始终是能力级：实现边界、已有tests、执行结果、目标集成四列分别看。商业许可、官方来源、依赖与数据授权不明的代码不得进入确定A/B/C交付。
