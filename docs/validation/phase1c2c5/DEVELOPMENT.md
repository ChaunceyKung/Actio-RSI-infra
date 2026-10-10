# C2C5 开发记录

实现前先阅读用户Prompt、审阅、既有源码与参考stream.ts，并提交设计合同。正式故障矩阵前将另封存实际实现、fixture和断言。历史C4结果不变；没有本轮provider请求。开发探针和失败不得重标成正式验收。

1. 设计提交 b37463d；固定历史读者认证 history-fe0824eda3f4.json PASS，3个历史reader及19份C4 claims保留。只读结构检查有两次预期字段不匹配（查询不存在文件、把workers投影当含root的完整记录），没有启动runtime。
2. 新纯函数开发检查：7类合成观察及C4归档重算符合结构预期，未来旧16前缀8/0/0、新16前缀8/8/8；首次10组单测PASS，控制日志 `.local/phase1c2c5-pure-dev01.log`。这是开发检查，不冒充后续最终源码验收。
3. 全新 `.local/phase1c2c5-runtime-venv` 从锁定本地wheel和Concordia固定Git归档离线安装成功；安装期间补齐驱动后又执行一次 --no-index --no-deps --no-build-isolation 安装。日志分别为 `.local/phase1c2c5-bootstrap.log` 和 `phase1c2c5-install01.log`。
4. 第一CLI开发包装器因子进程stderr本地编码/父进程UTF8解码冲突失败，随后None.encode触发；已保留 development-cli01-failure.json 和部分输出目录。修正为子进程显式 -X utf8。没有loopback发送。
5. acceptance-18de8a178371.json FAIL：10组纯测试均PASS，但把需要argparse的run-local非法参数测试放进只读env guard，得exit1而非预期2。只读guard仅适用plan/analyze/verify，修正这3项运行方式；原FAIL不改标。
6. acceptance-37ff38783faf.json PASS：10组纯测试与10个CLI命令；plan/analyze/verify、移址合成包与固定历史entry均在guard下运行；非法live/credential_ref/external endpoint退出2；export新目录成功，重复目录拒绝。此时开发runtime sends=0，真实requests=0。
7. `freeze.json` 封存9场景、12发送上限、fixture、expected、全部产品与测试/工具hash。必须在正式运行前提交。矩阵结果和后续修复将追加，不覆盖本次冻结或既有记录。
