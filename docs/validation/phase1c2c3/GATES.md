# C2C3 Gate

| Gate | 结果 | 证据范围 |
|---|---|---|
| historical_source_assurance | PASS_LOCAL_FIXED_READER | 原受控delivery经固定reader精确重算；portable verify不重复raw认证 |
| retrospective_diagnostic_reproducibility | PASS | 12卡两臂、原指标精确相等、条件集合和gap重算 |
| visible_information_boundary | PASS | 仅可见策略、64反事实、世界对内A完整payload一致；无wire/runtime主张 |
| diagnostic_dataset_integrity | PASS | 8/16/32及显式顺序变换，数据hash和固定生成器 |
| oracle_consistency | PASS | 416合法组合、128额外向量、10手算样例 |
| control_sensitivity | PASS_SYNTHETIC_ONLY | 两family A违规、B错接受/拒绝，同分及不相交见证 |
| offline_portability | PASS | 独立目录、最小环境、只读guard、重封坏包拒绝 |
| live_solver_discrimination | NOT_RUN | 本轮真实请求0 |
| research_validity | UNESTABLISHED | 开发启发合成集，独立研究单位0，真人标签0 |
| capability_admission | insufficient_evidence | 沿用C1旧决定；没有新增decision |
| production_activation | BLOCKED_FALSE | 未建立或切换active pointer |
| billing/upstream_identity | UNVERIFIED | 不由离线工程结论解决 |
| binary_source_mapping | unproven | 沿用历史限制 |
| full_controller_recovery | unsupported | 本轮无controller执行 |

机器可读包用`control_sensitivity=PASS`，其counts/kind明确为synthetic；此处补足语义范围。若不提供受信旧reader认证，历史来源Gate变为`PARTIAL_PUBLIC_PROJECTION_ONLY`，其他内部重算Gate不能覆盖这一限制。

过程限定：设计文本先冻结，但初次开发有限探针早于机器可读数据/源码封存；结果和精确开发命令另存，未调数据、未隐藏失败，不作为完全盲化预注册。正式验收在数据/政策封存及产品提交后进行。
