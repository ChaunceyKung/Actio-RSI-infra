# C2C5 开发记录

实现前先阅读用户Prompt、审阅、既有源码与参考stream.ts，并提交设计合同。正式故障矩阵前将另封存实际实现、fixture和断言。历史C4结果不变；没有本轮provider请求。开发探针和失败不得重标成正式验收。

1. 设计提交 b37463d；固定历史读者认证 history-fe0824eda3f4.json PASS，3个历史reader及19份C4 claims保留。只读结构检查有两次预期字段不匹配（查询不存在文件、把workers投影当含root的完整记录），没有启动runtime。
2. 新纯函数开发检查：7类合成观察及C4归档重算符合结构预期，未来旧16前缀8/0/0、新16前缀8/8/8；首次10组单测PASS，控制日志 `.local/phase1c2c5-pure-dev01.log`。这是开发检查，不冒充后续最终源码验收。
3. 全新 `.local/phase1c2c5-runtime-venv` 从锁定本地wheel和Concordia固定Git归档离线安装成功；安装期间补齐驱动后又执行一次 --no-index --no-deps --no-build-isolation 安装。日志分别为 `.local/phase1c2c5-bootstrap.log` 和 `phase1c2c5-install01.log`。
4. 第一CLI开发包装器因子进程stderr本地编码/父进程UTF8解码冲突失败，随后None.encode触发；已保留 development-cli01-failure.json 和部分输出目录。修正为子进程显式 -X utf8。没有loopback发送。
5. acceptance-18de8a178371.json FAIL：10组纯测试均PASS，但把需要argparse的run-local非法参数测试放进只读env guard，得exit1而非预期2。只读guard仅适用plan/analyze/verify，修正这3项运行方式；原FAIL不改标。
6. acceptance-37ff38783faf.json PASS：10组纯测试与10个CLI命令；plan/analyze/verify、移址合成包与固定历史entry均在guard下运行；非法live/credential_ref/external endpoint退出2；export新目录成功，重复目录拒绝。此时开发runtime sends=0，真实requests=0。
7. `freeze.json` 封存9场景、12发送上限、fixture、expected、全部产品与测试/工具hash。必须在正式运行前提交。矩阵结果和后续修复将追加，不覆盖本次冻结或既有记录。
8. 正式冻结提交 `196e8a6f3327b9d17ee0c0ba3bc45c93c38334e0` 后运行9场景，原root `D:/actio-c2c5-formal-v1`。12 sends、5 settled/admitted、7 unknown、6 not_run，12个具名Job退出，9个服务join。扫描20,251文件、34,211,878 bytes，包括生成日志/DB/native和依赖缓存，未跳过目录；首次扫描无hardlink复用。formal-original.json 保留原FAIL，原驱动错误地在输出FAIL时返回0的缺陷也明确记录。
9. 初版FAIL来自两个纯诊断错误：漏读官方native的text-chunks/reasoning-chunks压缩delta；误把UUID排序的attempt首行当成A，影响议价B历史检查。修正为有界无损展开、按scope.seat查A，并修正FAIL退出码。参考上游assistant-stream.ts；不改变旧成功审计/账本/运行时/TaskSpec/Concordia。没有修改原runtime材料，没有增加模型路径发送。
10. 固定196e8a6 Git reader在guard中重新认证9份完整dataset/Ledger/service及原budget DB（前后hash相同）。仅将这9份精确entry hash加入代码维护的窄C5来源信任表；artifact不能指定执行源码。最终诊断对原始native重新展开后，runtime-recomputed-f6c627a96092.json 的9场景均PASS。该结果是最终诊断源码的离线重算，不是“最终全部产品重新实跑”，也不覆盖原FAIL。
11. 最终验收 acceptance-cec45e1c4746.json：12组纯单测、20项CLI命令均PASS；包含9个真实官方本机entries的guard分析与篡改拒绝。新增压缩delta合法/畸形测试和FAIL退出码测试。复用范围仅为未改变的官方执行、账务、领域路径及原始12 sends；修改过的纯诊断/断言/CLI重新验证。正式freeze仍绑定原源码，不刷新成最终源码。
12. history-c0f4e5bf13e3.json：最终源码加入后，固定C2/C3/C4再次全部PASS、19份claims保持。domain-census.json独立只读检查9个原领域库：5条world/domain receipt，所有memory表0行；七错误场景无scenario_terminal，B-error保留A一条事实，所有库前后hash相同。
13. 标准库移址安装首试失败于嵌套sysconfig子进程的Windows本地路径编码，已保留development-portability01-failure.json和失败环境；修正子进程 -X utf8 后，portability-470bc5a4d9f7.json 的plan/analyze/verify在guard中全部PASS。环境没有DSH/Concordia、没有pip安装或网络请求。仅修复安装工具，产品与runtime观察不变，不重跑长矩阵。
