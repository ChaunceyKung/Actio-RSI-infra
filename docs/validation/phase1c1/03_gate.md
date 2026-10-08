# Phase 1C1 Gate 与边界

| Gate | 状态 | 依据与范围 |
|---|---|---|
| 离线工程 | CONDITIONAL_GO | TaskSpec 冻结、真实 DSH/Concordia 闭环、共享语义、离线评估、campaign 完备性、标注绑定及阻断路径验收通过；见最终 manifest |
| 人工校准 | BLOCKED | 当前 3 个待标 case、0 真实标签。synthetic_label_fixture 只证明导入与分歧处理 |
| Live provider | BLOCKED | 模型预算 0；未实现 transport；preflight 即使完整正预算也退出 2 |
| 研究效度 / 演化晋升 | BLOCKED | 单个 authored synthetic family、无独立研究单位、无 holdout；未创建 candidate、训练或激活版本 |

任务结果按实际行动与冻结约束重算；runtime complete、task success、valid measurement 分开。合法 accept 在冲突卡仍为 not_agreed。非法动作不产生该动作的 world 效果；缺第二行动的 partial 没有第二个评分。controlled response 的数字是 preset 结构 fixture，不是模型判断或人类 gold。

支持仅两个明确定义的卡、两 seat、固定两步、morning/afternoon。TaskSpec 校验精确接受这两个 authored 卡和新身份绑定；不提供任意社会任务 DSL。Actor 收到 own private + public history；审计证据包含双方冻结私有信息，judge 仅收到有授权的指标 view。标注时只分发 annotation.md、cases.jsonl 与空模板；internal.json 不分发。

哈希证明内部一致性，不证明作者、真实人类标签来源、执行可信证明或二进制到上游源码的构建映射。group 固定在 development，calibration_pending 仅为协议允许值，本轮无密封留出。没有统计效度、相关系数、置信区间、显著性或能力提升结论。

保留 Windows 短路径限制，campaign 的临时发布应使用新的短目录。已有 Python 3.12 / DSH 0.1.5rc1 / 固定 Concordia 及依赖锁均保持；无 DB migration、原生 resume/fork、中途恢复或 semantic cancel。

用户本轮授权 main 发布：通过验收后普通推送任务分支和 main，核对远端 SHA；这不授权费用或部署。停止在 Phase 1C1。
