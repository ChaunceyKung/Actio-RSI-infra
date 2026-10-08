# Phase 1B.1 Gate

**CONDITIONAL_GO**：四项边界修正、已知旧库兼容/可恢复迁移、可迁移证据与独立分层核验、相关原回归及 Job 清理均通过。38 组聚合行为测试、干净安装与公开 CLI 结果由 [独立 manifest](evidence_manifest.json) 绑定；过程中的失败保留为独立记录。逐项说明见 [结果](02_results.md)。

准入仅限 Windows x64、Python 3.12、锁定 DSH 0.1.5rc1/Concordia、单 store 单活动 run、静态最终 guard、只读工具、合成 fixture、预算 0。操作完成与场景终态分离；合法拒绝可以完整，部分 world 保留但不会被升级为完整社会 episode。历史 Phase 1B complete 是当时声明，未补造终态凭据。

旧资料可以只读查询、迁移到新副本和导出；旧 spec 源码 pins 不兼容新 runtime 时执行仍拒绝。本轮未实现 AgentVersion 激活、跨版本稳定身份演化或完整 memory migration。新测试和 smoke 使用明确的新合成身份。

证据包的 hash 和语义检查只证明包内一致性/冻结合同完整性，不证明上游二进制来源、作者签名、真实模型执行或社会评估有效性。前序 memory 闭包只证明所选事实/投影/effect，不递归认证整个历史。离线 verifier 不是 evaluator；退出码 0 的合法 partial 不能用于要求完整 episode 的测量。

继续不支持 native reopen/resume/fork/catchup、semantic cancel、完整 world restore、多活动 run、写效果工具、live provider、SOTOPIA live judge、Raven 演化、任意候选代码或训练。SDK 内部队列、二进制到源码映射、系统断电/disk-full、多平台和规模仍沿用原限制；本轮未为其补 PASS。

交付包括源码、测试、合同/结果/Gate/格式、独立 evidence manifest、五个小型合成包及 GitHub 实现分支。普通 push 和远端 SHA 校验是本轮最后动作；不自动 merge main。完成后停止，Phase 1C0 的 envelope/SOTOPIA parser 与测量合同另轮规划，原 scores 的四种错误类型前置仍未实现。
