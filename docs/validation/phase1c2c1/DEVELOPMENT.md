# C2C1 开发记录

冻结前保留两份失败验证记录：第一份纯测试的 text-only fixture 错含 reasoning_content:null，因此旧 v1 正确拒绝；修正 fixture 后通过。第二份 runtime 接线遗漏 A 的 subordinate_scaffold，导致完整性核验拒绝；修正 scenarios 的版本化 payload 分派和 campaign mode 白名单，原运行与未完成导出全部保留，无自动 retry。

prefreeze-draft-v0 保留首次生成但未发布/未执行主矩阵的草案。后续审阅补充：即使通道拒绝，也保留 SSE 直接观察的 finish_reason；prepared 比较只归一化独立 UUID4 message IDs（不进入 full wire）。最终合同与受影响的纯/真实 runtime 测试重新验证后才发布，草案不作为主矩阵证据。所有开发本机发送与 unknown 单列于 census。

源码未改 headers/idle/total/result/worker 的期限传递，C2C0 的 31 秒延迟证据沿用。当前源码的 8 项 C2C1 测试覆盖本轮变更；20 项既有纯回归在同轮前一个源码快照通过，之后只补了 C2C1 失败报告的 finish 观察，不影响旧分派。固定历史 reader 回归与旧文件不变检查单列。
