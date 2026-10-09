# Phase 1C2B2 审阅与 Phase 1C2C0 行动方案

审阅日期：2026-10-09（Asia/Shanghai）。基线：`e89d8b370c6cc53de21f651b49e7b2626eb1a559`；本轮开始时本地 main、origin/main、C2B2 任务分支一致。冻结实现为 `80d13896a790cb341ecf923f41330b967591b210`。

**建议进入 C2C0：任务集与独立确定性评估准入。** C2B2 按预注册正确停止，原始输入/行动证据与总分母可以复核；但分层 joint 汇总漏掉了部分未启动单位。先修正新版本统计、明确超时层次，再引入两个有限任务 family，完成离线真值及区分度验收后运行独立预注册的新 pilot。不要重跑 C2B2 unknown、补齐旧 not_run 或直接进入候选晋升。

[完整执行 Prompt](../prompts/phase1c2c0_task_suite_and_evaluation_admission.md) · [本轮审阅证据](phase1c2b2_review_evidence.json)。本轮仅审阅与规划，未改产品代码，新增真实模型请求为 0。

## 1. 复核结论与范围

| 检查 | 本轮实际结果 | 边界 |
|---|---|---|
| 文件来源 | 44 个 artifact、47 个产品文件、4 个入口、73 个工具/测试文件匹配 | 工作区与 Git 字节核对；AGENTS.md 仅既有 CRLF/LF 差异 |
| 原始归档 | 23 个 ZIP、5,725 个成员、127,810,089 bytes 匹配 | 检查归档及成员 hash，未重新封存原件 |
| 安装一致性 | release 环境 47 个产品文件匹配 | 未重装或升级运行栈 |
| 已发表测试 | 31 项当前测试与来源绑定一致，4 次失败验收记录保留 | 本轮没有重跑这 31 项 |
| 离线解释 | 固定 C2B2 reader 重算报告与已发表报告完全一致 | 禁止网络、子进程、key/env、文件写入和 runtime import；一致不代表没有统计设计缺陷 |
| 账本 | 210 个数据库文件 hash 匹配；104 个 Ledger 只读重算 | 前后字节未变，历史 rehearsal 与 live 分开统计 |
| 冻结 | preregistration hash 一致，产品文件自冻结未变 | 本地记录支持发布先于 intent；不是独立签名的时间戳证明 |
| 清理 | 193 个具名 Job 无活动进程；77 个登记端口无监听 | 77 个服务 join 是历史记录核对，未冒称重新观察已消失的线程 |
| 上游复用 | 实际执行 Concordia 两个议价模块的 27 项原测试，全部通过 | 只验证 payoff/parser/选项/累计逻辑，未运行完整上游模拟或模型 |

计划为 32 episodes / 64 seats；实际启动 27、完整结束 26、未启动 5。attempted/sent=54，response/terminal/admitted/usage=53，not_run=10，unknown=1；13 个模型配对 block 完整，3 个不完整或未启动。总分母能回到冻结计划。

原合同的已准入分母中，两条 route 的格式、自身约束及 B 本地回应指标均通过；各自可行 pair 的 joint 为 7/7，不可行 pair 为 0/6，合法拒绝不属于 actor 错误。这个 singleton 排期矩阵已经达到指标上限，继续重复主要增加相同结构的观测。新任务应先证明指标能区分离线控制策略；同时将可信但格式错误的原文纳入格式分母，不能只在成功准入行动中统计格式正确率。

本轮历史 pilot reported input/output tokens 为 16,116/270，13 条含 raw cost。币种、单位、估算适用性与实际账单仍未知。累计真实生成尝试保持 **76**（14 次前置诊断 + 8 次 C2B1 + 54 次 C2B2）；目录 GET 1 次另计。本次审阅不增加这些计数。

## 2. C0R1：分层 joint 指标遗漏未启动单位

位置：[pilot_measurement.py](../../src/actio/pilot_measurement.py)，`analyze_pilot` 的 `available` 过滤及 `joint_by_feasibility` 聚合，基线第 85–92 行附近。

未启动 episode 的 `metrics=None`。汇总先删除这些行，再按 `joint_feasible` 分层；但 feasibility 可直接从冻结任务确定，与是否启动无关。因此总计划和逐行记录完整，**分层的 missing 少算**。

| TokenKey route | joint_feasible | 应分配 episodes | 已定义 joint | 应为 missing | 原报告 missing |
|---|---|---:|---:|---:|---:|
| gpt-5.6 | true | 8 | 7 | 1 | 0 |
| gpt-5.6 | false | 8 | 6 | 2 | 0 |
| claude-sonnet-4-6 | true | 8 | 7 | 1 | 0 |
| claude-sonnet-4-6 | false | 8 | 6 | 2 | 1 |

表中是 episode 级指标，不能与 seat 级 not_run=10 相加。Claude 已启动但 B unknown 的一行已被记为 missing；其余 5 个未启动 episode 未进入分层 missing。

这不改变已准入行动、53 份 usage 或 54 次发送，也不证明已有行为结论反转。下一版应从完整计划分层，输出每项 `assigned/eligible/defined/missing/not_applicable` 及原因，校验分母恒等式。给 C2B2 追加带新 reader/source hash 的纠正表，保留旧报告、旧 reader 与旧 Gate 原文；不能静默重算后覆盖历史。

本次审阅对“raw/input integrity”的已有证据予以支持；对“所有分层统计完整”不放行，修正后再准入新评估版本。历史 `measurement_integrity=PASS` 不能泛化成所有统计汇总已正确。

## 3. C0R2：超时按原规则停止，下一合同应明确有效期限与失败分类

`ep-26` 的 Claude B 记录了官方 pi-ai 原生 `TIMEOUT: stream idle timeout after 30000ms`；没有保留到 HTTP headers/body/status。A 的已完成前缀仍在，B 保持 unknown/needs_reconcile，剩余 5 个 episode 未启动。供应商是否收到或收费不可推断，不能补零或自动重试。

旧合同 headers=45s、idle=30s、total=90s。idle 计时也覆盖首 headers 前的等待，所以 45s headers 并不是有效的首次响应等待上限。fetch 层观测 29,276ms 与上游 30s 并不矛盾：两层起算点不同。

当前 broad `protocol_error=1` 和外层 `pilot text evidence rejected; batch frozen` 是准入后果，不能覆盖原生 timeout 根因。新版本应分开记录 failure stage、native code、deadline 起点/触发、response 是否观察到、文本准入与账务 unknown。没有原始证据的细分保持 unknown。

建议新合同先在本机验证 **headers=60s、idle=60s、total=90s**，保留有限的 result/Worker 外层期限并核对全部层次。60s 是新的工程取舍，不是“已证明修复 TokenKey”或由小样本推导的可靠性阈值。本地延迟 headers、停顿、心跳、total deadline 和清理验证通过后才冻结；不得修改旧运行期限或重发旧 B。

已准入请求的最大首 text 延迟：GPT 16,427ms、Claude 24,160ms；这排除了超时样本，不能作速度排名、尾延迟承诺或成功率推断。下一版展示成功分布时同时披露 censored/unknown。

## 4. 不从零开始：已查验的任务资产及必要改造

本地资产根：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase`。

| 资产 | 固定来源 | 推荐复用 | 必须隔离的上游假设 |
|---|---|---|---|
| Concordia 单/多物品议价 | `15_concordia/repo`，`b71d202750e23444ce1bf28d9f114bcd88aa41db` | 有限报价、买卖双方收益定义、原测试向量、公开报价传给响应者的顺序 | 宽松解析、按文本推断角色、缺参与者填 0、未知物品默认 0 |
| Concordia pub coordination | 同上 | 偏好、公共关闭条件与共同选择的测试思路，辅助扩展已有 scheduling | 本轮不另建第三套环境或完整研究运行栈 |
| SOTOPIA profile/schema | `18_sotopia/repo`，`a0aaafb440e570e5e61b7c44a44e5e417c545383` | 场景来源、私有目标、关系与可见性元数据参考 | 不重启失败的完整 evaluator/Redis 路线，不假定数据许可已覆盖 |
| Raven paired diagnostics | `02_Raven/repo`，`3632e6040c7038a60ec418ce39ccae185c72c19f` | 为后续候选/基线配对与谱系预留字段 | 不复制缺失填 0、零标准误推成无限 z 或均值稍高即 promoted |

实际核对了 11 个固定源码/许可文件；3 个 Concordia GitHub raw 文件返回 200 且与本地固定 Git blob 一致。Concordia Apache-2.0 许可与修改归属应随提取保留。

关键入口：[多物品收益与选项](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/examples/games/haggling_multi_item/simulation.py)、[测试向量](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/examples/games/haggling_multi_item/haggling_multi_item_logic_test.py)。这两类议价测试本轮实际运行共 27 项通过。

上游 parser 用 `re.match`，payoff 从行动子串动态判断买卖方；缺参与者或解析失败可返回零收益，未知物品用零估值/成本。Actio 必须绑定固定 seat/role、精确有限行动语法、显式物品域、完整 pair 前提及 null/invalid 语义。采用整数实验效用/coin，不与真实 API 金额混用。可以提取少量带许可函数及测试或写窄适配；不能把同一 payoff 函数换个 import 当成独立 oracle。

## 5. 下一阶段有限目标

沿用官方 DSH `0.1.5rc1` → 真实 Concordia Sequential、SQLite、两 seat / 两次行动。新增能力集中在任务定义与测量，暂不同时扩张多轮协商、工具环境、记忆演化或恢复控制器。

1. **修正统计与运行合同**：C0R1 完整分层与历史 sidecar；C0R2 根因分类、有限新 timeout 合同及本地测试。
2. **任务资产准入**：扩展 scheduling 的公共限制、多个选择及软偏好；提取有限多物品 bargaining。每 family 6 张覆盖卡，记录源模板/结构/对称组，不把参数卡称为独立研究样本。
3. **独立真值和区分度**：穷举小行动域，与人工编写但非“真人标注”的算术/集合真值表交叉校验。离线弱策略和确定性负例要让指标区分非法、合法但较差、合法且满足约束、正确拒绝及不可行；不要求真实模型一定出错。
4. **冻结新工程 pilot**：12 张卡 × 2 条现有 route × 1 次 =24 episodes，最多 48 次新 solver 发送。保持初始 memory/spec 固定、模型交错、每 seat 一次；先发布实现与预注册到 main，再执行。
5. **按完整计划交付**：任务失误保留为结果；首个基础设施/完整性异常按规则停止。新报告区分 task/format/transport/usage/缺失；无补样、无按结果挑卡。发布任务包、oracle、报告、manifest、CLI、Gate 后停止。

以上 48 次是工程设计范围，不是金额上限。用户的 TokenKey 无金额上限授权继续适用，无需重复费用批准。费用/路由身份待证只限制相关结论；不应再阻塞全部工程推进。

## 6. 准入与后续边界

下一阶段成功意味着：第二个任务 family 已经接入真实运行栈；离线 oracle、actor 信息边界、指标可区分性和完整分母有证据；有限新 pilot 可审计地完成或停止。合法拒绝/格式错误/基础设施未知不会混为一个 success 分数，完整性失败也不会从分母消失。

`task_suite_admission`、`measurement_admission`、`transport_readiness`、`pilot_execution` 分别报告。pilot stopped 不自动否定此前离线任务准入，离线准入也不等于 provider 稳定性已证实。仅说明两个 TokenKey route 在该时段/卡片上的工程观察；不作模型排名、推广统计或社会能力效度主张。

人工校准、live judge、研究效度、演化晋升仍待各自证据；binary_source_mapping=unproven、full_controller_recovery=unsupported。新任务满足准入后，C2C1 才考虑单 seat 候选、基线冻结与谱系的离线 dry-run，不在本轮自动实现。

## 7. 本次交付

本轮只增加本报告、审阅 JSON 和下一 session Prompt，保留所有历史证据及产品文件。文档/引用/JSON/计数及凭据检查后提交并普通推送 main，核对远端 SHA。复核事实与统计纠正表已写入审阅证据；下一 session 的新 reader sidecar 属于实施交付，不能将本报告冒称其已实现。
