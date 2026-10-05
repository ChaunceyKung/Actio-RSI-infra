# 16 · 能力与成熟度检查表

状态只使用：**已实现 / 部分实现 / 缺失 / 无法判断**。已实现表示所命名行为有源码，不保证完整生产适用。执行状态独立：未运行/通过/失败/阻塞；目标Actio集成全部未运行。无coverage数据，不编造百分比。README/论文声明、实现、找到tests、本机tests通过、目标集成通过是五级不同证据。

下表按项目逐能力审计；某组非该项目选用角色时标无法判断，不能为了填满矩阵误称缺失。Engineering关注release/CI/tests/平台；未跑CI就不宣称CI通过。License和完整revision在[15](15_evidence_registry.md)，P0决策在[02](02_reuse_decision_matrix.md)。

## DSH/Cordis

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 部分实现 | 初始化/模型工具循环/结束、内部cancel存在；SDK缺完整cancel/status/resume，timeout非停止证明 | client29通过；真实worker未跑 | E001–E006 |
| Plugin/Hook | 已实现 | 注册/effects/disposer与依赖生命周期；任意热替换状态兼容无法判断 | 未运行 | E001–E006 |
| Session/State | 部分实现 | JSONL/fork/lease/migration/半写修复有实现；SDK恢复缺口，外部快照缺失 | 未运行persistence suite | E001–E006 |
| Tool/MCP | 部分实现 | stdio/HTTP tools/signal/timeout/reconnect；互动OAuth未接，resources另plugin | 未运行互操作 | E001–E006 |
| Memory | 缺失 | Actio observer/M0–M6/branch合同；runtime context不等于社会memory | 未运行 | E001–E006 |
| Environment | 缺失 | Actio世界裁决/时钟合同；由adapter承担 | 未运行 | E001–E006 |
| Observability | 部分实现 | native events/journal存在；域事件/可靠cursor映射/背压需补 | client假进程协议通过 | E001–E006 |
| Evaluation/Evolution | 缺失 | 独立四态admission与社会评估不由此SDK提供 | 未运行 | E001–E006 |
| Engineering | 部分实现 | alpha tag、SDK/wheel文档/测试；Windows x64未实装，native sandbox部分限制 | 初次编码失败后UTF-8通过 | E001–E006 |
| Reuse isolation | 部分实现 | 官方SDK/profiles/public transport可复用；worker级配置与sidecar闭包待准入 | 目标未运行 | E001–E006 |

## Raven

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 已实现 | Host/registry/routing/DAG执行与取消路径存在；不是Actio Root合适性证明 | root未运行 | E007–E009 |
| Plugin/Hook | 部分实现 | 外部harness/subagent dispatch；Curator experimental repository-only | 未运行 | E007–E009 |
| Session/State | 部分实现 | workspace manifest/registry；读损坏空表与archive吞写异常不适合canonical | 未运行恢复 | E007–E009 |
| Memory | 部分实现 | node memory/经验档案，不覆盖社会心智/branch隔离 | 未运行 | E007–E009 |
| Observability | 部分实现 | node status/output/manifest与trajectory；部分memory记录失败不使node失败 | 未运行root suite | E007–E009 |
| Evaluation/Evolution | 部分实现 | TaskEval/split/paired/gates/archive存在；mean-only promotion/小样本/infra语义需改 | gates/scoring37通过；archive未跑 | E007–E009 |
| Engineering | 部分实现 | v0.2.4/root pre-alpha，evolver树计划退役；无覆盖率测量 | 局部测试通过 | E007–E009 |
| Reuse isolation | 部分实现 | paired/selector可切断闭包；整个loop携bench/git/backend | 抽取未实现 | E007–E009 |
| Tool/MCP、Environment | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E007–E009 |

## Meta-Harness

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 部分实现 | experimental Harbor child执行/timeout；不含Actio共享runtime | 未运行 | E010 |
| Session/State | 部分实现 | candidate/source hash和历史文件；域crash恢复未证实 | 未运行 | E010 |
| Observability | 部分实现 | eval输出与候选source；infra/任务损失需重新分类 | 未运行 | E010 |
| Evaluation/Evolution | 部分实现 | proposer历史/onboarding/test隔离，AST validate/evaluate_source真实；AST非sandbox | 测试收集阻塞：缺harbor | E010 |
| Engineering | 部分实现 | MIT研究/experimental路径；正式域接口/平台兼容未验证 | exit2 | E010 |
| Reuse isolation | 部分实现 | 文档方法可D；controller带BaseAgent/Harbor/bench闭包 | D，不提取 | E010 |
| Plugin/Hook、Tool/MCP、Memory、Environment | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E010 |

## DGM

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 部分实现 | Docker coding benchmark self_improve_step；不是通用agent runtime | 未运行 | E011 |
| Session/State | 部分实现 | metadata.jsonl/archive resume，POSIX cp路径 | 未运行 | E011 |
| Observability | 部分实现 | resolved/empty_patch等benchmark日志，非统一域事件 | 未运行 | E011 |
| Evaluation/Evolution | 部分实现 | parent/mutation/eval/archive实现；best升序选择需复核 | 未运行 | E011 |
| Engineering | 部分实现 | Apache2研究仓库，Docker/数据/模型/Windows依赖未验证 | 无GPU/模型调用 | E011 |
| Reuse isolation | 部分实现 | archive思想独立，完整执行闭包不适合抽取 | D | E011 |
| Plugin/Hook、Tool/MCP、Memory、Environment | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E011 |

## Letta current / old / archive

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 已实现 | current LocalBackend/APIBackend/HeadlessBackend；cloud特性capability区分 | raw静态，未运行 | E012–E014 |
| Plugin/Hook | 已实现 | mods工具/provider/permission注册和disposer；hooks timeout；skill sources | tests树确认，未跑 | E012–E014 |
| Session/State | 部分实现 | LocalStore agent/conversation/transcript持久；完整跨服务恢复未证实 | 未运行 | E012–E014 |
| Memory | 部分实现 | git MemFS/context compilation/lease/consolidation；主agent编辑并非全锁 | 未运行 | E012–E014 |
| Observability | 部分实现 | transcript/mod事件/版本来源；不满足Actio全域事实合同 | 未运行 | E012–E014 |
| Evaluation/Evolution | 缺失 | Actio独立四态准入/封存实验；dream/reflect不等同此能力 | 未运行 | E012–E014 |
| Engineering | 部分实现 | current SHA/tag已取、Apache2；clone checkout中断改raw；Windows自动dream受限 | 未装依赖 | E012–E014 |
| Reuse isolation | 部分实现 | 可独立用Letta应用；memory与backend/agent/current settings深耦合 | 整体第二owner排除 | E012–E014 |
| Tool/MCP、Environment | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E012–E014 |

## Strands Python / TS

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 已实现 | Python模型/工具循环、cancel/concurrency控制；TS有自己的执行栈 | 未运行 | E015/E016 |
| Plugin/Hook | 已实现 | before/after hooks、interrupt/writable字段；interventions/Cedar路径 | 未运行 | E015/E016 |
| Session/State | 部分实现 | Py repository/messages与TS snapshot/history；单文件atomic，非全域事务 | 相关tests存在，未跑 | E015/E016 |
| Tool/MCP | 部分实现 | model/tool/MCP接入为SDK能力，逐transport/auth与DSH替代兼容未验证 | 未运行 | E015/E016 |
| Observability | 部分实现 | hooks/messages/snapshot可观察；Actio域事件仍要adapter | 未运行 | E015/E016 |
| Engineering | 部分实现 | Apache2/NOTICE；远端bidi更新已查；Py/TS与Windows完整组合未测 | 未运行 | E015/E016 |
| Reuse isolation | 已实现 | Python/TS包seam存在；首选Python备选而非自写loop | 替换合同未验证 | E015/E016 |
| Memory、Environment、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E015/E016 |

## Concordia

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 部分实现 | GM/Entity执行循环有实现；Actio solver必须桥接避免第二loop | 未运行 | E017/E018 |
| Plugin/Hook | 部分实现 | Entity/components与run_loop callback可扩展；语义拦截需wrapper | 未运行 | E017/E018 |
| Session/State | 部分实现 | component checkpoint/restore，跳过无prefab实体，不恢复engine cursor | checkpoint_test存在未跑 | E017/E018 |
| Environment | 已实现 | per-entity observation、ActionSpec、GM resolve、调度；resolve返回None | engine/sequential tests未跑 | E017/E018 |
| Observability | 部分实现 | raw_log/callback，structured Actio outcome需映射 | 未运行 | E017/E018 |
| Evaluation/Evolution | 缺失 | Actio admission/lineage由外环负责 | 未运行 | E017/E018 |
| Engineering | 部分实现 | Apache2，当前Engine API已核；依赖/模型/平台未实装 | 未运行 | E017/E018 |
| Reuse isolation | 部分实现 | Entity/Engine seam适合B；完整快照不能假定 | adapter未实现 | E017/E018 |
| Tool/MCP、Memory | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E017/E018 |

## AgentSociety v2.9.3

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 部分实现 | Ray batch agents执行；不选其solver代替Actio runtime | 未运行 | E019 |
| Session/State | 部分实现 | workspace to/from/resume；failed tick可能部分写入 | 未运行 | E019 |
| Environment | 已实现 | Society.step/EnvRouter/ServiceProxy、clock/barrier | Ray未运行 | E019 |
| Observability | 部分实现 | sharded traces/timeline可观测；确定重执行未证实 | 未运行 | E019 |
| Engineering | 部分实现 | 有v2.9.3 tag，不套论文v1；Ray部署/Windows未验证 | 未运行 | E019 |
| Reuse isolation | 部分实现 | proxy/router有seam，batch/pending重建增加成本 | P2设计验证 | E019 |
| Plugin/Hook、Tool/MCP、Memory、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E019 |

## OASIS

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Runtime | 已实现 | platform task、manual/LLM actions、并发；LLMAction不用作第二loop | 未运行 | E020 |
| Session/State | 部分实现 | DB/close EXIT task存在；queue/RNG全快照未知 | 未运行 | E020 |
| Environment | 已实现 | recommendation/platform/agent graph/clock与step | 未运行 | E020 |
| Observability | 部分实现 | DB/trace结果需映射，step返回None | 未运行 | E020 |
| Engineering | 部分实现 | Apache2；平台/模型依赖未验证 | 未运行 | E020 |
| Reuse isolation | 部分实现 | ManualAction可B，interview可能额外LLM需禁用/计费 | P2 | E020 |
| Plugin/Hook、Tool/MCP、Memory、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E020 |

## Graphiti

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Memory | 部分实现 | write/search/temporal edge/episodes/driver实现；group可省，UUID scope需强制 | 未运行 | E021 |
| Session/State | 部分实现 | 图driver持久化；branch snapshot/迁移端到端未知 | 未运行 | E021 |
| Observability | 部分实现 | episode source可追踪；非canonical域事实存储 | 未运行 | E021 |
| Engineering | 部分实现 | Apache2，graphiti-core0.30.2；服务/模型/embedding成本未测 | 未运行 | E021 |
| Reuse isolation | 部分实现 | 可注入driver/client，适合B投影；不能自动namespace隔离 | P2 | E021 |
| Runtime、Plugin/Hook、Tool/MCP、Environment、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E021 |

## SOTOPIA

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | async structured evaluator实现；sync未实现，空结果/identity顺序缺口 | test_evaluators未跑 | E022 |
| Environment | 无法判断 | 本角色只审评委，不据其社会环境声称Actio world兼容 | 未运行 | E022 |
| Observability | 部分实现 | 评分解释与日志；异常[]必须wrapper变invalid | 未运行 | E022 |
| Engineering | 部分实现 | MIT代码，数据/Redis import/model closure另验 | 未运行 | E022 |
| Reuse isolation | 部分实现 | 单评委wrapper可行但非零依赖library | B/P | E022 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E022 |

## ACE

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Memory | 部分实现 | playbook/curator ADD操作；UPDATE/MERGE/DELETE仍TODO | 未运行 | E023 |
| Evaluation/Evolution | 部分实现 | LLM propose/aggregate与反馈；没有Actio四态admission | 未运行 | E023 |
| Observability | 部分实现 | logger/操作记录；失败可退原文本 | 未运行 | E023 |
| Engineering | 部分实现 | Apache2；本轮无覆盖率或集成结果 | 未运行 | E023 |
| Reuse isolation | 部分实现 | 字符串utils可取但语义不足，当前D更省维护 | 不复制 | E023 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Environment | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E023 |

## Phoenix

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Observability | 已实现 | trace/OTLP、dataset、eval路由与queue/DB | tests存在未跑 | E024 |
| Evaluation/Evolution | 部分实现 | eval记录/结果与error，不等于独立admission | 未运行 | E024 |
| Session/State | 部分实现 | viewer SQL持久化，非agent/world恢复 | 未运行 | E024 |
| Engineering | 部分实现 | ELv2实际条款已读，部署资源未测 | 未部署 | E024 |
| Reuse isolation | 部分实现 | B内部viewer；第三方托管受许可限制 | 对外托管blocked直到许可符合 | E024 |
| Runtime、Plugin/Hook、Tool/MCP、Memory、Environment | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E024 |

## Langfuse

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Observability | 已实现 | OTLP项目鉴权/校验、S3+queue+worker、dataset/score API | server tests存在未跑 | E025 |
| Evaluation/Evolution | 部分实现 | 评估投影/数据集，不是canonical gate | 未运行 | E025 |
| Session/State | 部分实现 | 多服务数据库/对象存储，不能担任Actio状态owner | 未运行 | E025 |
| Engineering | 部分实现 | MIT含EE例外，compose多服务，资源/可用性未测 | 未部署 | E025 |
| Reuse isolation | 部分实现 | HTTP/OTLP B边界清晰；实际部署许可闭包待B01/B13 | P | E025 |
| Runtime、Plugin/Hook、Tool/MCP、Memory、Environment | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E025 |

## MCP spec + client2

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Tool/MCP | 部分实现 | modern/legacy、stdio/HTTP、tools/resources/auth/cancel SDK存在；DSH wrapper覆盖不同 | artifact静态未运行 | E006/E026 |
| Session/State | 部分实现 | 协议session/negotiation不等于域session或外部效果事务 | 未运行 | E006/E026 |
| Engineering | 部分实现 | 规范2026-07-28、client2.0.0固定artifact；MIT/Apache过渡 | 未互操作 | E006/E026 |
| Reuse isolation | 已实现 | 官方client package可依赖，沿DSH内置客户端 | A/B P | E006/E026 |
| Runtime、Plugin/Hook、Memory、Environment、Observability、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E006/E026 |

## A2A / ACP

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Tool/MCP | 无法判断 | 它们是任务协作/client-agent协议，不是MCP实现 | 未运行 | E027/E028 |
| Runtime | 部分实现 | 规范Task/CancelTask或client交互，不证明某SDK运行兼容 | 未选SDK | E027/E028 |
| Engineering | 部分实现 | 官方proto/schema+Apache2，ACP canonical迁移已核 | 规范静态 | E027/E028 |
| Reuse isolation | 无法判断 | MVP未选择SDK，不能称A/B已准入 | D/P2 | E027/E028 |
| Plugin/Hook、Session/State、Memory、Environment、Observability、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E027/E028 |

## OTel spec/proto/SDK

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Observability | 部分实现 | 单parent+links，SDK batching/queue/drop/flush实现；exporter组合未pin | wheel仅解包静态 | E029/E042 |
| Session/State | 缺失 | canonical事实事务与实验多父DAG，不由SDK保证 | 未运行 | E029/E042 |
| Engineering | 部分实现 | Apache2，SDK1.45.0固定wheel/hash；未安装或部署 | 未运行 | E029/E042 |
| Reuse isolation | 已实现 | SDK可package复用，Actio仅projection/outbox | A/B P | E029/E042 |
| Runtime、Plugin/Hook、Tool/MCP、Memory、Environment、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E029/E042 |

## ADAS

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | exec候选搜索存在，隔离缺失 | 未运行 | E030 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E030 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E030 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E030 |

## AgentSquare

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | memory模块生成存在，branch安全缺失、license未定位 | 未运行 | E031 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E031 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E031 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E031 |

## AFlow

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | workflow搜索存在，持久域状态缺失 | 未运行 | E032 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E032 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E032 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E032 |

## Sotopia-RL

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | 文本归因反馈存在，因果识别缺失 | 未运行 | E033 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E033 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E033 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E033 |

## ALSO

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | EXP3 L0存在，L1准入缺失 | 未运行 | E034 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E034 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E034 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E034 |

## RSIHub

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | frozen外环接口存在，远端recipe更新未运行 | 未运行 | E035 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E035 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E035 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E035 |

## autoharness

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | campaign冻结规则存在，Actio环境未集成 | 未运行 | E036 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E036 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E036 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E036 |

## OpenEvolve

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 部分实现 | archive/islands/evaluator存在，域恢复缺失 | 未运行 | E037 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E037 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E037 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E037 |

## R-Zero

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 无法判断 | 训练边界文档，只审L3接口 | 未运行 | E038 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E038 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E038 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E038 |

## verl

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 无法判断 | 训练栈边界文档，只审L3接口 | 未运行 | E039 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E039 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E039 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E039 |

## VerlTool

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 无法判断 | 工具训练边界文档，只审L3接口 | 未运行 | E040 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E040 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E040 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E040 |

## GSME/HarnessBank

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 无法判断 | 官方abs仍写code upon acceptance，源码未核 | 未运行 | E041 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E041 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E041 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E041 |

## Self-Evolving Harness

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 无法判断 | 官方abs未找到源码链接，公开性无法判断 | 未运行 | E041 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E041 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E041 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E041 |

## Claude Code Mods

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Evaluation/Evolution | 无法判断 | 本地blog导航，官方访问403 | 未运行 | E041 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E041 |
| Reuse isolation | 无法判断 | 仅D，采用源码前重新核许可/闭包/运行 | 未集成 | E041 |
| Runtime、Plugin/Hook、Session/State、Tool/MCP、Memory、Environment、Observability | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E041 |

## SQLite

| 能力组 | 覆盖状态 | 具体行为/缺口 | 独立运行状态 | 证据 |
|---|---|---|---|---|
| Session/State | 部分实现 | 标准事务存储与public domain授权；目标schema/负载未实现 | 未运行 | E042 |
| Engineering | 无法判断 | 未做整栈CI/平台/覆盖率审计；不能从release或论文成绩推断 | 未运行 | E042 |
| Reuse isolation | 部分实现 | SQLite A后端；其余D，不纳确定代码依赖 | 未集成 | E042 |
| Runtime、Plugin/Hook、Tool/MCP、Memory、Environment、Observability、Evaluation/Evolution | 无法判断 | 不在本项目本次复用角色的深审范围，不作MVP实现来源 | 未运行 | E042 |

## P0 readiness gates

| Gate | 当前状态 | 阻断什么 / 下一验证 |
|---|---|---|
| 许可与artifact闭包 | 根/相关子目录已核，SBOM及模型数据未全准入 | 阻断正式再分发/部署；B01 |
| 单runtime生命周期 | SDK client测试通过，真实wheel/cancel/resume/catchup未验 | 阻断共享持久运行；B03/B05 |
| 状态/事件可靠性 | 源码seam存在，Actio合同未实现 | 阻断自动恢复/强branch；B04/B05/B12 |
| 单world与单memory owner | 规划已统一，行为未验 | 阻断双slice宣称；B06–B08 |
| evaluator与admission独立 | 上游diagnostic测试通过，领域gate未实现 | 阻断候选生产准入；B09–B11 |
| L2隔离 | Windows限制明确、未验证Linux隔离 | L2 blocked；不阻断structured L1 |
| viewer | 静态接口/许可核验，未部署 | 可延后，不阻断canonical链 |

没有把缺凭据、服务或测试依赖的项目写成失败实现；也没有把“未找到专门测试”写成零覆盖率。已有测试名/执行命令和输出摘要见18。
