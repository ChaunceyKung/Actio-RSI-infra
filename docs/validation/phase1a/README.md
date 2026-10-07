# Phase 1A · 实际集成验证

日期：2026-10-07。规划基线：`fad04fcf0d14ded6684d54dc0633f4ee213276f3`。本轮为 experimental probes，没有创建正式 `src/actio`、服务、演化外环或第二 agent loop。

**结论：CONDITIONAL_GO。** G0 在 Windows 11 x64 / Python 3.12.10 / 官方 DSH SDK 与 runtime-bin `0.1.5rc1`、短路径隔离根、静态只读 policy plugin 下通过。助手与真实 Concordia Sequential Engine 的两个 external Entity 共用 `runtime_adapter.Adapter`。固定模型输出和 GM 决策是 fixture；DSH executable/loop/journal/MCP 与 Concordia 调度路径是真实实现。G1 仍有限制；G2 live/研究效果 BLOCKED（授权预算 0）。继续 DSH 主选，未触发 Strands。

最终可复跑套件包含 **36 项真实运行路径断言、7 项 SQLite 合同检查、13 项受控评估检查**。另有 artifact 校验。历史启动与 fixture 失败、原生取消兼容性失败单列保留，未被算作通过。原生 cancel 的兼容性缺口以拒绝执行和有界进程终止规避，绝不称其为语义取消成功。

| 阅读入口 | 内容 |
|---|---|
| [01 审阅问题](01_review_resolution.md) | F01–F05 的 decision、changed files、verification、remaining risk |
| [02 Artifact/环境](02_artifact_and_environment.md) | 来源、锁文件、hash、license、源码/二进制差异 |
| [03 Runtime/工具](03_runtime_and_tool_results.md) | 真实路径、授权选择、工具清单、兼容性与 capability inventory |
| [04 事件/故障](04_event_and_failure_results.md) | occurrence/projection、flush、故障窗口、未证明事项 |
| [05 Concordia/评估](05_concordia_and_eval_results.md) | Engine/Entity seam、provider input 隔离、评估分类 |
| [06 Gate/下一 slice](06_go_no_go_and_next_slice.md) | 明确允许范围、禁止依赖能力、后续任务验收 |
| [Evidence manifest](evidence_manifest.json) | Phase1A 独立 E-ID、逐测试命令、状态、证据哈希 |
| [复现说明](../../../probes/phase1a/README.md) | 环境准备与执行命令 |

证据目录的 JSON 是已执行输出及经过路径替换的 transcript，模型输入均为合成数据。原始 journal/SDK 通知/SQLite/profile/进程日志打包在 ignored `.local/runs/*/raw.zip`，manifest 保存其 hash；复跑会生成新包，不要求读取作者个人缓存路径。provider 输入、关键 native 事件、guard 顺序、MCP 计数、退出记录已提交，完整大日志和二进制不入 Git。

2026-10-05 的 29 项 fake-client 与 37 项 Raven 测试原事实保留，未无理由重跑；不能用于本轮 G0。Windows 之外的平台、live provider、SOTOPIA 上游 evaluator、Graphiti/viewer/Ray/Harbor 均未运行。
