# Phase 1C2B2 结果

预注册冻结提交：`80d13896a790cb341ecf923f41330b967591b210`；preregistration SHA256：`a36c3088bd6ccbe589b957b488bf745f360cc22be99f37b58ad9ec66b188e41a`。
远端核验 2026-10-09T06:29:22.119Z，首次 intent 2026-10-09T06:29:22.404Z；顺序由导出中的每个请求 UTC 复核。

完整计划 32 episodes / 64 seats。本次状态 `stopped`：observed episodes=27、未启动 episodes=5。

|执行维度|计数|
|---|---|
|assigned|64|
|attempted|54|
|sent|54|
|response|53|
|terminal|53|
|admitted|53|
|not_run|10|
|protocol_error|1|
|usage_responses|53|
|unknown|1|

reported input/output tokens：16116 / 270；raw cost 字段 13 条。estimated_cost=null，billed_cost=null，raw cost 币种/单位仍未核实。没有自动 retry、新 API 目录扫描或直接模型诊断。

|TokenKey route|格式 true/N|A own true/N|B local true/N|feasible joint true/N|infeasible joint true/N|
|---|---|---|---|---|---|
|claude-sonnet-4-6|27/27|14/14|13/13|7/7|0/6|
|gpt-5.6|26/26|13/13|13/13|7/7|0/6|

共同结果是协议结果，冲突中合法 decline 不记为 B 能力错误。逐单位/seat action、not_run reason、operation/occurrence/receipt、reported cache/reasoning、请求/响应标签、HTTP ID/date、headers/首 text/请求/episode 时延见 [完整报告](samples/report.json)。时延为本机/供应商报告事实，不代表独立网络计时证明；unknown 不按零费用处理。

只有一个任务 family、四个参数实例、两类对称结构；两模型为配对路由 cohort，repeats 与镜像相关。joint presentation 同时反转两 seat 选项，不识别单 seat 位置效应。independent_research_units=0；不作能力排名、显著性检验、推广 CI 或 cost-normalized ranking。

当前产品 hash 下 31 个选定测试通过。完整真实 DSH/Concordia 本地矩阵 16 episodes/32 sends；另有负例、UTF-8 字节分片、并发 claim、旧路径与零副作用回归。开发过程 4 次验证运行未通过，原证据全部保留。早期断言曾未实际改到分片文本、将 SDK 外部消息 ID 纳入跨运行 equality、随机取到 B 导致 proposal 替换为空操作；随后用实际内容变更和固定外部 ID 校正。旧 preflight 回归还发现局部导入遮蔽旧 validator，已用独立别名修复并复跑。未更改历史真实原件。

最终固定实现重新完成矩阵；此前本地源版本归档在 baseline evidence。固定旧 reader：C0=1e85d8c2、C1=af0a88cf、C2A.1=b086cba、C2B0=f65045a、C2B1=1e00535。原 8 条 C2B1 live raw/adapter/native 文本追加检查全通过，原有 22 次生成尝试（20 次有 usage、2 次 usage 未核实）和 1 次目录 GET 不进入 pilot 分母；历史未核实 usage/费用不回填为 0。

清理清点：193 个具名 Job 均 inactive/reaped，77 个本地服务已 join，剩余监听端口=0，活动 reservation/sending=0。生成文件已检查真实/假凭据；失败和 raw 数据在明确目录归档，ZIP/hash/逐文件清单见 manifest 指向的 census。依赖 node_modules/bytecode 不重复扫描，固定 runtime/锁定安装另行核对。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [预注册](preregistration.json) · [历史追加复核](historical-text-review.json) · [route/cost registry](route-cost-registry.json) · [证据 manifest](evidence_manifest.json)

停止于 C2B2。C2C 应增加有区分度且有来源的任务、独立校准和评估准入，再考虑单 seat 候选与谱系；本轮不自动执行后续阶段。

本次停止详情：`ep-26` / claude-sonnet-4-6 / B，官方 pi-ai 原生事件报告 `stream idle timeout after 30000ms`。未取得 HTTP headers/body，不能据此推断供应商是否接收或收费。26 个 episode 完整结束，第 27 个保留 A 的已完成前缀与 B 的 unknown；余下 5 个 episode 未启动。受影响 Worker 已 reaped，未重试、补样或追加模型诊断。详见 [只读故障复核](failure-review.json)。
