# Phase 1C0 实施合同

基线：产品 bc0c034，交接 449691e；实施分支 phase1c0-offline-measurement。Windows/Python 3.12，live budget=0。旧证据、参考源码、runtime DB/spec 只读；评估结果另存不可变文件。

执行顺序：C0R1 输入绑定 → spec/准入/view → SOTOPIA parser/schema → 确定性与 controlled-response 两路径 → campaign/回归/干净安装 → commit/push/远端 SHA。

输入规则固定为 fixture-input.v2，由在线 seal 与离线 verifier 共用。历史无版本 manifest 的两字段 ActionSpec 按已固定 Concordia/scenario v1 展开 choice/tag=null；新 manifest 显式冻结四字段。Engine 每步向两实体送观察，B 在第 0 步看到一条，A 在第 1 步看到两条；检查 actual dispatch/native 输入，不宣称有独立观察交付日志。

bundle format 保持 v1；verifier 合同/实现独立版本。旧 verification.json 是受清单 hash 保护的历史报告，当前结论始终重算，不以字典相等认定损坏。真实文件清单损坏仍拒绝。

EvalSpec 只开放两种本地模式，无任意代码/文件引用插件：deterministic 的助手工具合同及社会 action/GM 约束；controlled_response 的 goal 0..10、relationship -5..5 整数 schema。原 social 无冻结 goals/关系基线，不准入社会评分；独立 synthetic 输入用于结构流测试。

admission/task/measurement 三轴分报。缺证不评分；task_failure 保留可用约束事实；非法响应不补零；异常/timeout 单列，失败也发布记录，不自动重试。alias 按冻结 seat 排序映射真实 agent，与行动顺序无关。view 只选必要事实，拒绝超限，无静默截断。

SOTOPIA 固定 a0aaafb440e570e5e61b7c44a44e5e417c545383 (MIT, 0.1.5)。顶层导入含 Redis/litellm/aact 等闭包，采用可追踪 AST 定义原样提取：LLMBaseModel/LLMEvalBaseModel、score models、PydanticOutputParser、EvaluationForAgents。仅导入胶水使用 pydantic.Field 代替存储 Field；定义本身原样，记录源/提取 hash 与 LICENSE。Episode evaluator 仅测试侧原定义执行，固定 generation/transport seam，兼容失败如实保留，不进入产品。

记录绑定源 content、必要 manifest、spec/campaign/view/alias/pins、raw response hash、三轴结果及实际调用计数。原子无覆盖发布；请求 hash 相同读取原记录。重复包和 export metadata 不增加测量，replay run 保留但标同起点 cluster。所有 split 为 synthetic engineering fixtures，无独立研究样本或 holdout 宣称。

Gate 仅为离线测量工程 CONDITIONAL_GO；真实效度/统计晋升/模型费用/演化不在本轮。必要行为、原 evidence/runtime/reliability 回归、隔离运行与干净安装均留证，失败不删除。
