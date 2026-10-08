# Phase 1B 审阅与 Phase 1B.1 行动方案

日期：2026-10-08。产品审阅基线：`668754fc51915a56818c25d1c0d6b3715f7f5396`。

**保留 Phase 1B 已验证路径的 CONDITIONAL_GO；下一轮先做 Phase 1B.1：运行完整性修正与可迁移证据导出。** 本次发现的完成判定、并发幂等和恢复目标问题，应先解决再把轨迹交给评估器。无需重新选择 runtime，也无需扩大成全套基础设施。

下一 session 执行：[Phase 1B.1 Codex Prompt](../prompts/phase1b1_reliability_and_evidence_export.md)。本轮只审阅、生成文档与发布这些交付，不修改产品实现。用户要求的“每轮验证后提交并推送 GitHub”已写入根目录 [AGENTS.md](../../AGENTS.md) 和后续 Prompt；不默认合并 main。

## 1. 核实结果

| 核对项 | 结果与证据强度 |
|---|---|
| Git 基线 | 本地 HEAD 与远端 `phase1b-persistent-vertical-slice` 均为 `668754fc…`；审阅开始时工作树干净 |
| main | 远端 main 仍为 `fad04fc…`，后续分支不能从这个旧 main 丢失已完成实现 |
| 行为验收 | 6 contract + 2 runtime + 6 failures + 4 processes，共 18 组 PASS；每组可以包含多个断言，不是统计样本数 |
| 产品证据 | 17 个产品源文件 hash、4 个当前 suite JSON 与 4 个 raw archive hash 全部匹配 |
| 历史与交付 | 24 个被引用的历史/artifact/交付文件 hash 匹配；bootstrap 日志 hash 匹配；41 个 Job 的交付清理记录均为 active=0 |
| 测试源码关联 | 当前各 suite 对应的测试文件和产品文件匹配。早期 runtime/failures 记录里的其他 suite/准备脚本 hash 有历史差异；后续专属测试和 bootstrap 有匹配记录，不将这些差异误报为产品未验证 |
| 本次新增实验 | 仅一个临时 SQLite 合同 fixture，确认一条已完成 operation 会被当作整个双步骤 run 完整；未启动 DSH、MCP、GM 或付费模型 |

本次没有重跑 18 组集成、重新安装依赖或重新查询所有历史 Job。上表中的行为通过、安装和清理属于已交付证据核对；新增实验的范围单独标注。摘要见 [审阅证据](phase1b_review_evidence.json)。

入口：[Phase 1B Gate](../validation/phase1b/03_gate.md)、[原 manifest](../validation/phase1b/evidence_manifest.json)、[运行 README](../../README.md)。原 Gate 中“未 push”是完成时的历史状态；用户后续已推送，本次也通过远端 refs 核实，无需改写旧证据。

## 2. 已落实且应保留的设计

- 产品包独立于 Phase 1A probes，官方 SDK/TS loop/native journal 与真实 Concordia Engine 持续复用。
- 最终 guard 与 provider/fault fixture 分离，核对实际 registry/schema 和工具文件 hash，合法 call ID 无需预登记。
- 自有 SDK host 进入 Windows Job 后才放行，公开 SDK 方法替代第三方 `_proc`，资源和阶段期限有明确上限。
- flush bridge 绑定 run、session creation、epoch、operation、receipt、nonce 与终态 seq；不以 idle 等同于持久完成。
- occurrence/projection 分层；memory CAS、来源与 effect receipt 同事务，消费 mapper 显式迁移。
- 私有 observation/memory 在实际 provider 输入处核验；助手与社会场景共用 RuntimePort，重执行使用新原生创建身份。

这些成果支持继续 DSH 主线。预算仍为 0，fixed provider/GM 不是能力评测，二进制构建来源仍未证明；Windows/短根/单活动 run/只读工具等限制继续有效。

## 3. 必须修正的发现

### B1R1 / P1：run 完成判定没有覆盖场景终态

位置：[Store.finish](../../src/actio/store.py)、[social/run_engine](../../src/actio/scenarios.py)。基线定位：`store.py:138`，`scenarios.py:89–94,120,185`。

`finish()` 只检查已有 operation 非空且全为 `execution_complete`。社会场景先完成 B，再启动 A；若 A 在创建 operation 前初始化失败，异常分支仍调用 `finish(task='infrastructure_failure')`，此时只有 B 的完成记录。

本次受控台账 fixture 固定 `order=['B','A'] / max_steps=2`，仅构造第一步完成、worker reaped，然后以第二步启动失败收尾，实际返回：

```json
{"state":"execution_complete","task":"infrastructure_failure","trajectory":"complete"}
```

这是完成谓词的合同实验，不是实际 Engine 故障注入。源码中的真实场景调用顺序说明它是可到达的错误路径；下一轮需补真实 Engine 的定点故障回归。

**修正**：区分 operation 完成、场景终态和轨迹完整性，增加由场景 owner 确认的持久终态凭据。社会成功须有正确身份/顺序的两个 GM resolved 记录与回执；合法的提前拒绝可以是 task_failure，但须有明确终态理由。不要简单要求所有 run 都有两个 operation，助手和非法 action 的合法终态不同。基础设施故障可以保存完整的已执行前缀，不能伪装为完整 episode。

**验收**：第二实体启动失败、第一步后 Engine 异常、GM/domain receipt 不完整都不能成为完整社会轨迹；正常助手、正常两人场景及明确非法 action 拒绝仍正确分类。

### B1R2 / P1：场景入口忽略原子 begin 的执行所有权结果

位置：[scenarios.py](../../src/actio/scenarios.py)，基线第 42、89 行；[Store.begin](../../src/actio/store.py) 第 56–64 行。

`existing()` 是事务外预查询，`Store.begin()` 才在事务内判定同 key 是否已有 run，并返回 `fresh=False`。两个场景入口均用 `run,_` 丢弃该结果，随后仍进入执行。

两个调用者同时通过前置查询后，其中一方可能拿到另一方创建的 run/epoch，却继续分配 runtime 或走错误收尾。并非每种交错都会重复 dispatch，活动 worker/lease 检查可能挡住部分路径，但场景入口的“非创建者不能执行”规则没有成立。现有“同 key 顺序重试”及“不同 key 争抢 lease”测试不能覆盖该竞态。本次为静态审阅发现，未运行并发 dispatch 重现。

**修正**：原子 begin/claim 是唯一执行资格来源；未取得资格的调用者只返回已有状态，不能启动 worker、结束 run 或释放 lease。避免把后来才生成的 memory snapshot 与调用方请求幂等键混为一层；同 key 同规范请求应取得第一次冻结输入，同 key 不同请求必须冲突。

**验收**：同步闸门控制的两进程同 key 同请求，仅一个执行 owner，一次模型/工具路径与一次 effect；另一方返回同 run。不同请求同 key 冲突；同 key 已完成/未知状态重试不派发，也不写坏原状态。

### B1R3 / P1：指定 run 的恢复命令可能操作另一条活动 run

位置：[CLI reconcile](../../src/actio/cli.py) 基线第 49–50 行、[Store.recover](../../src/actio/store.py) 第 145 行。

`reconcile <run> --recover-owner` 先执行无目标参数的 `store.recover()`，它读取全局活动 lease 并核对/回收对应 Job，随后才解析 `<run>`。因此历史 run 或不存在的 run 参数也可能先触发另一条活动 run 的恢复，再返回指定 run 的结果或报 unknown run。

本次静态确认调用顺序和目标缺失，没有终止任何进程来验证这一点。

**修正**：先解析并验证目标，恢复操作必须绑定同一 run 与观测 epoch；不匹配时不修改任何其他 run/lease/worker。若需要全局 orphan recovery，以独立、明确的命令表达，不隐含在指定 run 的 reconcile 中。继续保留 owner birth、Job 清理和无自动重发约束。

**验收**：未知/历史 run 的恢复请求不影响另一条 lease；owner 仍活着拒绝；目标 owner 确认死亡后只回收目标；恢复过程中 lease 变化需重新核对，不能凭先前读取结果继续写。

### B1R4 / P2：replay 接受但忽略改变起点的参数

位置：[social replay](../../src/actio/scenarios.py)，基线第 72–89 行，以及 [CLI 参数](../../src/actio/cli.py)。

replay 分支复制旧 manifest，却仍把本次 `illegal/as_of` 记录在 request。`--replay X --illegal` 或额外 `--memory-revision` 不改变实际 manifest，也没有显式拒绝，导致请求记录和有效执行输入不一致。

**修正**：冻结起点 replay 拒绝冲突 override，或把它们定义为另一种显式新实验。此阶段选择前者即可。为输出保存 requested input 与 effective manifest 的明确关系，不悄悄忽略输入。

**验收**：原样 replay 产生新 run/stream 且语义结果一致；矛盾参数在创建 run/worker 前拒绝；省略参数按旧 manifest 执行。

## 4. 下一轮范围：Phase 1B.1

推荐按下列顺序在同一个实现 session 内完成，只有依赖 Gate 失败才停在可审阅边界。

| Slice | 工作 | 最小结束条件 |
|---|---|---|
| H1 行为修正 | B1R1–B1R4；场景终态与唯一执行 owner；目标化恢复 | 新定点回归通过，原成功/拒绝/unknown 行为无回退 |
| H2 小型存储兼容合同 | schema version、旧库显式迁移/兼容读取、未知版本拒绝；不改历史 spec/run pins | 旧 Phase 1B 库可查询/导出；迁移有 backup/hash，失败可恢复，不自动 reset |
| H3 可移植轨迹证据包 | 从一致 SQLite snapshot 导出 native/canonical/receipts/world/memory 输入及 pins 的最小闭包；本地离线 verifier | 原任务目录不可用仍可验证；缺项/改动/gap/conflict 不能被判完整；partial 可以诚实导出 |
| H4 回归与发布 | 当前源码/安装包一致，相关合同和真实 Engine/DSH 测试，新 manifest、说明与 Git 发布 | 正常本地提交、push 当前分支并核对远端 SHA；不自动 merge main |

这里的证据包服务于后续测量，默认仍为合成 fixture，不生成分数、candidate 或晋升结论。命令名按实现确定，最终 README 必须给出实测可运行的导出/验证命令。

### H2 的边界

当前 Store 在打开时执行 `CREATE TABLE IF NOT EXISTS`，没有显式 schema version。H1 新增场景凭据后，必须防止旧库被静默当成新合同。可以用简单整数版本和一条已知旧库迁移，不引入通用迁移平台。

缺场景终态的历史 run 不能凭旧 `trajectory=complete` 自动补签新证据。保存历史声明，另行记录当前核验状态；若可从既有权威记录建立有限证明，要记录推导版本、输入 hash 与范围，否则导出为 legacy/unverified。

已有 AgentSpec 的 pins 包含全部产品源码，新版本运行会拒绝旧 spec，这是当前公开限制。此轮保证旧资料可查询/导出并诚实拒绝不兼容执行，不要求顺带建设 AgentVersion 激活/迁移，也不允许原位改旧 spec hash。正式跨版本持续身份仍是进入 live/演化前的后续任务。

### H3 的边界

证据包至少含：格式/mapper/schema 版本、源 run 和有效 manifest、spec 与 memory snapshot 引用、operation/receipt/barrier、逐 stream occurrence/冲突与连续 cursor、必要 projection、domain/world 终态、运行/工具/plugin/provider pins、内容清单/hash，以及完整性和 fixture 标记。

只导出与该 run 有关的最小闭包，不能默认复制整份 DB 或整个 home。标明审计读取者可见数据与 agent 可见数据的区别；合成 private marker 可保留在明确审计范围内，但不能通过导出操作改变未来 agent 的输入权限。

离线 verifier 不启动 runtime、不联网、不运行 package 中任何脚本；不把“hash 一致”当成签名或真实性证明。分别报告封装完整性、事实内部一致性、场景完成性及来源信任限制。对历史已完成 run 新发现的缺口/损坏，保存新的核验结果，避免直接抹掉历史事实。

## 5. Phase 1C 的后续顺序

H1–H4 通过后再进入以下阶段，本轮只记录其准入条件：

1. **Phase 1C0 离线测量合同**：可靠 evidence package → task/infra/insufficient/invalid 分类 → 修复旧 envelope 对 null/list/number/bool 的处理 → 冻结身份、维度、范围、rubric/split/实验单位。
2. **SOTOPIA 复用验证**：本地源码为 `a0aaafb440e570e5e61b7c44a44e5e417c545383`，位置 `codebase/18_sotopia/repo`。`sotopia/envs/evaluators.py` 中 `EpisodeLLMEvaluator` 依赖生成接口并可能异常返回 `[]`；先验证真实 parser/schema 与离线 controlled response，明确边界，不能直接把上游输出当有效分数。
3. **Phase 1C1 live pilot**：另有 provider/model、凭据来源、请求/输出/费用上限才执行。当前预算 0 不授权此项；离线结构验证可先做。
4. **单 seat 演化**：稳定测量、冻结数据切分和独立准入就绪后再拆 Raven C02/C03。行为测试通过率不当能力提升；多次 replay 同一 fixture 不当独立研究样本。

binary→source provenance、完整 resume/fork、semantic cancel、写效果工具、多活动 run、远端/多平台与规模测试继续单列，不为本轮证据导出扩大依赖。

## 6. 发布与交接

本轮审阅/Prompt 单独放在 `docs/phase1b-review-phase1b1-plan` 分支，继承 `668754fc`。下一 session 优先从包含这些交接文件的该分支 HEAD 创建实现分支，不从旧 main 开始。

后续完成标准包含 **验证 → 本地提交 → 普通 push → 核对远端 SHA**。遇到鉴权/网络问题可保留本地成果并说明阻塞；正常情况不能停在“未推送”。main 合并是独立动作，本轮未要求。
