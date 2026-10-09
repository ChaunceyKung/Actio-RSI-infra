# C2C0 任务集与独立评估合同

本轮为 engineering pilot。版本：`pilot-config.v7`、`actio-task.v3`、`finite-independent-measurement.v1`、`engineering-preregistration.v2`、`suite-evidence.v1`。旧 v6/task v2、旧超时与历史 reader 不改变允许值。领域事实仍由 SQLite Store、账务由 Ledger、行动由官方 DSH SDK/runtime → TS loop → Concordia Sequential 产生；只读评估器重算指标。

## 任务与来源

12 张 Actio 合成卡，每 family 6 张，卡片许可 CC0-1.0。议价选项与收益机制窄适配 Concordia `b71d202750e23444ce1bf28d9f114bcd88aa41db` 的 haggling_multi_item；保留 Apache-2.0 归属和 [许可证](CONCORDIA_LICENSE)。具体源码 hash、二开映射和 SOTOPIA/Raven 的仅参考边界见 [provenance](provenance.json)。未引入完整研究模拟、Redis、真人数据或 live judge。

Scheduling 使用 morning/afternoon/evening、公共 open 集合、自身 availability 和整数偏好。A 只能提议；B 对公开开放且自己可用的时间接受，否则 decline。偏好不是否决条件。完整且合法接受并满足双方 hard rule 才实现各自时段效用。所有语法选项仅从公共 catalog 与冻结 presentation 构造，保留格式合法但违反规则的选择。

Bargaining 的 A 固定 buyer/proposer，B 固定 seller/responder；apple/banana，整数 1..5。精确语法为 `apple for 3 coins` 等列举选项；大小写、尾随解释、未知物品和域外价格均拒绝。buyer 必须满足公共 allowed、预算和估值；seller 按公共 allowed 且 price ≥ cost 接受，零利润接受。实现交易时效用分别为 value−price 和 price−cost，单位为 toy coins，不能解释为 API 币种或金钱。

GM 对语法合法行动保留实际公开行动；若接受违反公共/任一 actor hard 条件，阻止交易并明确记录 hard flags，完整 pair 的实际效用为 0。完整合法拒绝也是 0。缺失、格式非法、文本不可信和不完整 pair 的效用为 null。语法非法不写入 world，但保留拒绝 receipt 和行为证据；A 非法时 B 不运行。不能将错误行动修成正确行动。

## 信息与独立评估

模型只看公共规则与动作域、自身 role/private 状态、固定关系描述、实际公开历史、空 memory。任务 case、group、对方隐藏值、oracle、全任务/hash/spec/op 均在外部绑定层。SDK message ID 在序列化时移除；HTTP `X-Actio-Attempt` 为独立 uuid4。检查实际 prepared、system/user wire、options、空 tools 和实际 headers；反事实固定随机审计 ID、自己的状态与公共历史后改变对方 private 与分组，投影后的完整 prepared/wire 字节不变。自身状态或实际 A 行动改变则输入改变。

`suite_oracle.py` 使用独立集合/整数计算，不调用生产 result、GM task_result 或上游 evaluator。有限域穷举交叉检查生产世界结果，另有手算测试向量及 first_option/always_accept/always_reject/own_rule 离线策略。它们是 fixture 和代码独立性证据，**human_labels=0**，不是专家效度校准。

原始字节→SSE delta→官方 adapter→native answer 继续严格绑定。四个条件分列：文本可核验、语法合法、domain 可执行、目标实现。可信原生文本即使语法非法也进入 format 分母，并记 false；不可核验文本缺失，usage 单独记账。joint、效用和全知上界不是 actor 可知答案；regret/Pareto 单列描述，不转换成自身约束错误。

## 完整分母

每个 planned episode 预先绑定 family/case/role/route/feasibility；未启动也保留。每项都有 value、state 和 reason：

- assigned = eligible + not_applicable；eligible = defined + missing。
- 布尔指标 defined = true + false。format 单位 seat，joint/utility 单位 episode，route-pair coverage 单位 block。
- format：全部分配 seat eligible；可信文本 defined，未运行/unknown/不可信 missing。
- A own：已知非法语法 not_applicable，同时 format=false；尚未观察到仍 missing。
- B local：已知 A 非法为 task_predecessor_invalid，或 B 非法，为 not_applicable；未知前驱仍 missing；另报 B not_run。
- joint/utility：全部计划 eligible；不完整/非法/未知缺失，合法拒绝为完整观察。每个 family × route × feasibility 汇总回到全计划。
- pair coverage：12 个冻结配对 block，不完整配对 missing，不删除也不补零。

[C2B2 纠正 sidecar](c2b2-correction.json) 绑定原始文件 hash、固定旧 reader 提交与新 reader hash；仅纠正 episode joint 的分层 missing，保留旧报告、unknown=1、not_run=10 及 claim。

## 有限期限与失败

生产期限（秒）：ready 30、RPC 5、headers 60、idle 60、total 90、result 115、drain 5、close 5、Worker 165。SDK initialize 20 包含于 ready。Worker 起于 supervisor launch；ready+result+drain+close=155，留 10 秒余量。RPC 是单条 RPC 确认，非生成总期限。result 起于提交后的 wait，包含生成与本地返回；outer Worker 仍可优先生效。

headers 起于最终 fetch；官方 idle 从 adapter stream 开始，包含 headers 前等待；官方 total 与 fetch total 是独立 90 秒计时，先到者生效，心跳不能延长总期限。deadline_boundary、hook/fetch/headers/finish UTC、触发源、native failure、status/body 是否观察到、accounting state 与 admission 分列。时间证明仅为本机记录，非独立签名时间戳。

生产参数用固定 runtime 的 >30 秒延迟 headers 进行本机实测；缩短期限只用于 loopback 测试，profile 原件随测试归档，不混入 live 合同。测试覆盖 headers 前、首文本后停顿、心跳总期限及终态附近取消，检查一次发送与 Job 回收。60 秒是有限工程选择，不保证供应商成功；semantic cancel/full recovery 仍不支持。

## 计划、发布与停止

2 families × 6 cards × 2 TokenKey routes × 1 repeat = 24 episodes / 最多 48 sends。固定 seed，family 轮换，每卡两条 route 配对并轮换模型先后；每卡冻结一种 option order，不声称位置因果效应。路由为 gpt-5.6、claude-sonnet-4-6，同 episode 同路由。independent_research_units=0，不创建 holdout，不输出综合排名、显著性、推广 CI 或 cost-normalized ranking。

实现与 preregistration 在首次 live 前普通推送任务分支和 main，核验 SHA 和 clean checkout 后才读取凭据/登记 intent。独立 `.local/phase1c2c0-claims` namespace 按 preregistration hash 原子领取一次，跨输出目录仍拒绝重领；每 episode 使用一个不可变子 Ledger。不得改旧 C2B2 claim。

每 seat 只发送一次，首个配对 block 后只检查完整性/清理。A 语法非法跳过 B、继续后续计划；任务失误/合法拒绝/低效用继续。首个基础设施 unknown、timeout、文本/身份/协议矛盾停止整个 pilot；保留 prefix 和全部 not_run，不自动重试、补样、换路由或第二个 live 批次。

显式 `uncapped_for_phase1c2c0` 与用户授权绑定；金额 null 仅在此策略下有效。历史 76 次生成尝试与 1 次目录 GET 排除于本轮；本地 fixture、被拒绝未发送、真实 sent 分开计数。raw usage/cost、报价、估算和账单分开；缺币种不折 USD，unknown 不补零。上游身份/账单 UNVERIFIED；binary_source_mapping=unproven，full_controller_recovery=unsupported。停止于 C2C0。
