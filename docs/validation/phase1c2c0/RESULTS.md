# C2C0 结果

冻结提交 `2e5f77b69b98f85c61df87e18d7e3ffad28e8cba`；preregistration SHA256 `6c0ac05265bac98ef03f1676c51984cfd7a107b5644cab9664b5e6a40ec6ff5e`。
发布核验 2026-10-09T07:59:38.421Z → intent 2026-10-09T07:59:38.732Z；本机时间记录，非独立签名时间证明。

正式 pilot 状态 **stopped**。计划 24 episodes / 48 seats，实际启动 8，可评估完整 pair 7，未启动 16。

| 执行维度 | 数量 |
|---|---|
| assigned | 48 |
| attempted | 15 |
| sent | 15 |
| response | 15 |
| terminal | 15 |
| admitted | 14 |
| not_run | 33 |
| protocol_error | 1 |
| usage_responses | 15 |
| unknown | 0 |

reported input/output tokens=6171/121；raw cost 字段 3 条，币种/单位未核实；estimated_cost=null，billed_cost=null。unknown 不等于免费或未接收。
历史 76 次生成尝试及 1 次目录 GET 排除于本轮；累计真实生成尝试 91。loopback 在 census 中独立统计，不混作 provider 调用。

| family | route | format true/defined/missing | A hard true/defined | B local true/defined | joint true/defined/missing |
|---|---|---|---|---|---|
| scheduling | gpt-5.6 | 4/4/8 | 2/2 | 2/2 | 1/2/4 |
| scheduling | claude-sonnet-4-6 | 4/4/8 | 2/2 | 2/2 | 1/2/4 |
| bargaining | gpt-5.6 | 2/2/10 | 1/1 | 1/1 | 0/1/5 |
| bargaining | claude-sonnet-4-6 | 4/4/8 | 2/2 | 2/2 | 1/2/4 |

逐 seat/episode/pair 的 assigned/eligible/defined/missing/not_applicable、分层 feasibility、真实行动、效用/全知 regret/Pareto、时延与删失标记见 [完整报告](samples/report.json)。可信格式错误也计入 format；不完整、非法与不可信的效用为 null。合法拒绝和不可行任务不冒称 actor 能力错误。

本机准入：当前产品下 27 项选定测试通过；24 episodes/48 sends 两 family × 两 route 标签真实 DSH/Concordia 矩阵通过。穷举真值、手算边界和 4 个离线控制策略证明指标区分度；human_labels=0。实际完整 wire 反事实、严格 raw/adapter/native、计划删改拒绝、unknown/一次 claim、零副作用与离线 reader 通过。
新 headers/idle/total=60/60/90 秒；固定 runtime 的 31 秒延迟 headers 通过，缩短期限的 headers 前/首文本后/心跳 total/终态附近取消均按有限合同结束。不能据此保证 TokenKey 成功。
开发验收失败记录保留 1 次；首次 wire 反事实断言曾用紧凑 JSON 替代 host 的标准 JSON 空白，已按实际序列化修正，产品输入语义未改变。交付脚本另有一次相对路径规范化错误，记录保留在 evidence/delivery-path-failure.json；修正仅涉及交付脚本。

C2B2 原 reader 精确重现旧报告；新 [纠正表](c2b2-correction.json) 从完整计划分层，两 route 均为 feasible assigned/defined/missing=8/7/1，infeasible=8/6/2。原 unknown、not_run、claim、manifest 未改。

清理：78 个具名 Job inactive/reaped，35 个服务 join，监听端口=0，活动 authorized/reserved/sending=0。原始运行归档与逐文件清单在 evidence_manifest 指向的 census。

本次停止于 ep-07 / H5 / gpt-5.6 / A：HTTP 200 的 SSE 返回 reasoning_content，官方 adapter 也生成 reasoning block，超出冻结 pure-text 审计支持范围。不是超时，也不据此声称 raw/native 矛盾。usage 已核对并 settled，但文本未准入，未产生该 episode 的 world/receipt；B 及后续单位不再执行。详见 [failure-review](failure-review.json)。未放宽合同、重试、补样或增加模型诊断。

两 family、12 张自编卡及配对 route 不等于独立研究样本；independent_research_units=0。固定呈现不识别位置因果效应，TokenKey 标签不证明上游权重；不作综合排名、显著性、推广 CI 或 cost-normalized ranking。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [来源/二开](provenance.json) · [路由/费用](route-cost-registry.json) · [任务卡](task-cards.json) · [预注册](preregistration.json) · [manifest](evidence_manifest.json)

停止于 C2C0。C2C1 仅建议单 seat 候选/基线/谱系的离线准入演练；本轮没有候选生成、真人校准、judge、训练、正式研究、晋升或部署。
