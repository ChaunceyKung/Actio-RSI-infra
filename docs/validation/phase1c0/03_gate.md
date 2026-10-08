# Phase 1C0 Gate

**CONDITIONAL_GO — offline engineering only**。

输入绑定缺口关闭；准入三轴、严格原始 envelope、alias 映射、可迁移记录、幂等无覆盖和全量 fixture 登记成立。真实 SOTOPIA parser/schema 执行通过；完整 EpisodeLLMEvaluator 兼容性实验失败，明确未采用。两条本地路径、相关原回归、干净隔离环境与零模型请求由 [manifest](evidence_manifest.json) 绑定，详见 [结果](02_results.md) 和 [复现](04_usage.md)。

本 Gate 不准入真实模型、测量效度、统计晋升、封闭 holdout、Raven 演化、训练或版本激活。预置 goal/relationship 分数只有 schema/数据流意义；旧社会包没有 goals/初始关系，不可倒填。episode/replay cluster 不当独立样本。hash 证明内部一致性，不证明签名、二进制来源或真实能力。

下一轮 Phase 1C1 才讨论真实任务数据、完整冻结目标/关系基线、独立单位与 split、人工对照/校准、provider 和独立 judge、预注册 pilot、调用预算与失败率。当前不执行这些工作。保留单机 Windows/Python 3.12、原 runtime 边界，不增加 DB migration。

发布：commit → 普通 push `phase1c0-offline-measurement` → 核对远端 SHA。停止于本轮，不合并 main、不部署。
