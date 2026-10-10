# C2C5 结果

已交付版本化失败观察、官方链路本机故障证据、可移址合成包和未来分块顺序。最终诊断工程验收 **PASS**；首次正式矩阵的诊断 **FAIL** 保留，修正后只做离线重算，没有重发。新增真实provider、目录GET、外部MCP均 **0**；历史累计真实生成 **172**、目录GET **1**。

C4固定reader认证了完整受控delivery、v4原库、原report和19份claims，读取前后hash不变。ep-16 A为第33次发送：HTTP200，普通chunk后两个结构化error（api_error；upstream_error / upstream_stream_truncated），无DONE、无raw usage。官方adapter usage为0/0/0、finish.kind=error、failure.code=PI_AI_ERROR。新版sidecar为 `provider_error_observed`，旧text audit仍拒绝，旧Ledger仍unknown且usage=null。只去掉event行仍缺DONE；供应商声明不证明实际上游、责任、可重试性、免费或已修复。

历史计数严格保留：64/128计划、33 sent/response、32 usage/admitted、unknown1、not_run95、16完整episodes、候选对8/32、hidden与presentation各0/32。C4仍INCOMPLETE，C1原decision仍infrastructure_failure，activation=false。

## 正式本机矩阵与分母

固定官方DSH SDK/runtime 0.1.5rc1、pi-ai、Windows x64/Python3.12和真实Concordia b71d202运行。9场景计划18席位，上限12 loopback发送，实际12；开发runtime发送0，修复后新增发送0。固定seed合成fixtures不是候选评估。

| 场景 | sent / 计划席位 | usage / admitted | unknown / not_run | 最终离线检查 |
|---|---:|---:|---:|---|
| 排期text对照 | 2/2 | 2/2 | 0/0 | PASS |
| 议价text+reasoning对照 | 2/2 | 2/2 | 0/0 | PASS |
| C4结构替身 | 1/2 | 0/0 | 1/1 | PASS |
| data.error无event | 1/2 | 0/0 | 1/1 | PASS |
| content前缀后error | 1/2 | 0/0 | 1/1 | PASS |
| A正常、B error | 2/2 | 1/1 | 1/0 | PASS |
| HTTP429 | 1/2 | 0/0 | 1/1 | PASS |
| HTTP503 | 1/2 | 0/0 | 1/1 | PASS |
| 无结构化error截断 | 1/2 | 0/0 | 1/1 | PASS |
| 合计 | **12/18** | **5/5** | **7/6** | **9/9** |

attempt/sent/received/response均12，settled及可信usage5、domain receipts/world rows5、active authorized/reserved/sending0。两完整技术对照的B均继承实际A，reasoning不进入B或领域记录。议价对照技术完整但交易未达成，原领域task_failure保留，不冒充经济结果成功。所有场景memory表均0行：本合同使用空初始记忆，没有新增长期记忆写入；不声称测到了持久记忆学习。

前缀错误没有action/domain/world/memory效果；B失败保留A的一条已发生world/domain receipt，未生成最终scenario_terminal，没有把A回滚成未发生。七个技术失败均保留原异常、unknown与完整slot后缀，无重试、换route或补样。识别错误不成为behavior violation，不授予行动或结算；有raw usage的合成负面向量单独核验usage一致性。

## 验证来源与修复范围

设计先提交b37463d；正式实现/fixture/expected冻结提交196e8a6。原正式报告为FAIL：提取器遗漏官方压缩delta，并错误假设attempt按A/B排序；另外驱动输出FAIL时返回0。所有原材料、原报告和失败来源保留于[首次报告](formal-original.json)。

修复只涉及诊断读取、B查找与CLI退出码。固定196e8a6 reader在只读guard下重新认证9份完整原dataset/Ledger/service及预算DB；代码维护9份精确entry hash，以免当前产品hash变化诱发历史pins刷新。最终新版诊断离线重算9场景PASS，[来源与结果](runtime-recomputed-f6c627a96092.json)。这不是最终全部产品重新运行；未改变的运行、账务和领域行为复用原12次实测。

最终12组纯测试、20项CLI验收PASS，包括strict JSON、bytes/base64/UTF8/上限、身份/摘要/终态/usage矛盾、native压缩delta、错误不准入、历史真实entry、九份本机entry和篡改拒绝。另有3项公开plan/analyze/verify在没有DSH/Concordia的新标准库环境移址PASS；只读guard禁止key/env/network/runtime/process/write。export新目录与覆盖拒绝实跑。所有开发包装器失败见[DEVELOPMENT](DEVELOPMENT.md)，未改标为最终PASS。

12个本轮具名Job均reaped且OS查询active0，9服务均有join收据，相关端口无监听。停止库存先落盘，再诊断和扫描；扫描20,251文件、34,211,878 bytes，覆盖生成日志/DB/native及依赖缓存，无跳过目录。首次扫描没有相同hardlink复用；完整库存保留在受控root。发布前另做精确秘密排除扫描，包含后处理与失败材料；真实key仅为本机排除而读入内存，不输出其属性。C4旧失败预演缺一份join的事实不变。

## 可移植性与未来计划

[公开package](package.json)重算合成fixtures、expected、观察和完整0..64覆盖曲线；历史/raw runtime认证仍需要独立受控来源。Hash不等于供应商签名。plan不执行任务、不创建claim/evaluation；新顺序16/32/48/64完成切点三类对照各8/16/24/32，旧16前缀8/0/0、首次hidden17/presentation21保留，不保证任意短前缀更好。分块也引入结构组的时间聚集，不能等同因果识别或可靠性提高。

provider_availability=NOT_RETESTED，研究UNESTABLISHED，独立研究单位0，费用币种/单位/账单与上游身份UNVERIFIED，binary_source_mapping=unproven，full_controller_recovery=unsupported。没有新candidate/evaluation、训练、judge、部署或active pointer。停止于C5；后续只有[NEXT_EXPERIMENT](NEXT_EXPERIMENT.md)中的审阅决策草案。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [字段来源](FIELD_SOURCES.md) · [manifest](evidence_manifest.json)。
