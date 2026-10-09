# C2B1 Gate

| Gate | 结果 | 证据 / 限制 |
|---|---|---|
| local_engineering | **CONDITIONAL_GO** | 当前 16 suites / 75 组通过；旧路径回归、干净安装、CLI、hash 一致性、凭据与清理检查 |
| dsh_concordia_tokenkey_live | **CONDITIONAL_GO** | 两种模型各完成 compatible→conflict；共 4 个完整 episode、8 次正式发送与 8 份可信 usage，无新 unknown |
| live_authorization | **AUTHORIZED_C2B1_SCOPE** | 2026-10-09 用户明确 TokenKey 与无金额上限；执行范围、请求期限、记录与停止条件仍有限 |
| billing_reconciliation | **UNVERIFIED** | cost 仅部分返回，币种/单位未证实；实际账单、供应商接收数为 null |
| upstream_model_identity | **UNVERIFIED** | 8 次响应标签与请求一致，但第三方 gateway 标签不能证明上游权重版本 |
| binary_source_mapping | **unproven** | 固定二进制 hash 和实际官方 adapter 加载已核实，完整构建映射未证明 |
| full_controller_recovery | **unsupported** | Worker/预算中断保守留痕与回收通过，不宣称完整控制器恢复 |
| judge / human_calibration | **BLOCKED** | 无 live judge、真人标注或校准授权与证据 |
| research_validity / evolution_promotion | **BLOCKED** | 每模型两个合成 episode，无独立研究单位、重复或统计效力 |

CONDITIONAL_GO 的条件是继续使用已验收的固定可信 profile、版本化合同、精确 TokenKey origin、有限登记计划、单 seat 单次请求、原子 Ledger 与现有可见性规则。不是任意插件网络沙箱、通用模型网关或任意模型的生产承诺。

两次 conflict 的 task_failure 是合法 decline 后“未达成共同时间”，与协议成功、完整轨迹和账务 settled 并存。没有为了提高任务成功率重试或修改原答案。HTTP200 本身不构成通过；本轮还验证 raw SSE/DONE、usage/native、response_model/id、action 与世界效果。

首轮本机验收的实现错误保留原失败、原配置与源码快照；正式调用在修正后的全套相关回归、干净 CLI 检查后执行。详见 [结果与计数](02_results.md)、[账务](05_accounting.md)、[模型选择](07_models.md) 和 [manifest](evidence_manifest.json)。

本轮停止于 C2B1，不继续扩展模型列表、live judge、研究/演化或部署。下一步应先确定正式测量合同及 TokenKey 计价/路由证据，再设计独立的研究准入。
