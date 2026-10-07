# Phase 1A experimental probes

这里是合同/集成验证，不是产品API。官方DSH TS executable拥有agent loop和journal；Python SDK是控制通道；provider plugin只生成固定模型输出。MCP用官方Python SDK，访问合成data.json。Concordia使用固定源码中的真实Sequential Engine。**无付费调用，live预算0，不需要任何key。**

复现要求：Windows x64、Python3.12（本次3.12.10）、可访问PyPI/GitHub；安装空间包含约72MB压缩runtime wheel及隔离venv。命令从仓库根运行。所有路径由已提交脚本推导，不需要作者session变量/私人缓存；脚本使用仓库所在盘根下新建的短临时目录，避免native模块MAX_PATH问题。没有系统/用户全局安装或配置修改。

```powershell
python probes/phase1a/bootstrap.py
probes/phase1a/.local/venv/Scripts/python.exe probes/phase1a/artifact_info.py
probes/phase1a/.local/venv/Scripts/python.exe probes/phase1a/run_runtime.py
probes/phase1a/.local/venv/Scripts/python.exe probes/phase1a/event_probe.py
probes/phase1a/.local/venv/Scripts/python.exe probes/phase1a/eval_probe.py
probes/phase1a/.local/venv/Scripts/python.exe -m pip check
probes/phase1a/.local/venv/Scripts/python.exe probes/phase1a/build_manifest.py
```

`bootstrap.py`用requirements.lock的40个确切版本+hash安装；从固定Concordia SHA归档导入必要package闭包，不装整个研究栈。若已有只读Concordia参考repo，可使用 `--concordia-source <path>` 从该repo执行固定SHA的git archive，绝不在原repo安装依赖。可选 `artifact_info.py --dsh-source <path>` 比较SDK三个文件与固定SHA；不传时仅报告installed hashes，不能把比较结果写成已测。Concordia pin与许可证hash见validation evidence；真实Engine代码保持原样。

网络慢时可以在bootstrap之前只获取本平台官方runtime文件（先打印metadata size，6个并发range、每块最多2次尝试、总调度deadline300s，最后核整个SHA256）：

```powershell
python probes/phase1a/fetch_artifact.py deepseek-harness-runtime-bin 0.1.5rc1 win_amd64
```

`requirements.in`仅说明直接依赖；**复跑不用它重新解算浮动传递依赖**。`lock_environment.py`是初次制作锁文件时使用的官方metadata/下载hash核对器；只有有意升级锁文件才再次使用，它会更新lock和artifact清单。

单独复测可传case，例如：

```powershell
probes/phase1a/.local/venv/Scripts/python.exe probes/phase1a/run_runtime.py lifecycle tools policy-isolation constraints
probes/phase1a/.local/venv/Scripts/python.exe probes/phase1a/run_runtime.py tool-interruption event-integration receipt-loss concordia
```

完整case清单：lifecycle、tools、policy-isolation、constraints、iserror、transport、timeout、init-timeout、run-timeout、eof、exit、tool-interruption、event-integration、receipt-loss、concordia。每个case有120s外层期限；SDK初始化默认20s、request3s、run12s，特定deadline测试更短。**run timeout不等于server cancel**：adapter停止worker并留下unknown；Windows Job最后清理子孙进程。环境从零allowlist构建，SDK不会收到用户provider secrets。

`event_probe.py`和`eval_probe.py`仅stdlib，可用系统Python单独运行，不需要下载runtime。前者验证7项occurrence/projection/transaction合同，后者13项受控evaluation分类；不能代替真实runtime测试。`event-integration`把实际journal接入相同Collector。

| 文件 | 边界 |
|---|---|
| runtime_adapter.py | assistant/Concordia共用的薄SDK调用；private `_proc`仅故障注入/诊断，不是可继承的产品生命周期API；未用 `_launch_args` |
| fixtures/provider_policy.mjs | 公开provider接口、冻结policy、最终guard、flush marker；没有实现agent loop |
| fixtures/mcp_server.py | 官方MCP SDK stdio，固定合成只读key；error/timeout/exit仅测试fault |
| runtime_cases.py / concordia_case.py | 真实runtime与Engine边界断言；fault仅针对这些任务进程 |
| event_probe.py / eval_probe.py | 小型合同实验，不建立生产store、memory、outbox或admission服务 |
| run_runtime.py / winjob.py | 显式清洁环境、Windows Job进程树、有界期限、raw归档与脱敏证据 |

输出：小型JSON写入 `docs/validation/phase1a/evidence/`；完整合成raw.zip、venv/wheels/缓存放 `.local/`（ignored），包含hash和当次脚本hash。原始任务短根位置记录在 `.local/runs/*/location.json`，只用于诊断，不是复现输入。各Job结果须active=0。没有网络listeners；本任务测试结束后不留后台进程。旧失败证据保留；新跑成功不会把native-cancel兼容失败或未测live改成PASS。

正式使用必须先读 [限制与下一slice](../../docs/validation/phase1a/06_go_no_go_and_next_slice.md)。完整SDK cancel/resume/fork/catchup、动态Python审批、其他MCP组合、远端worker/压力测试均不在本套件内。没有live可执行开关；若未来授权provider/model与正数预算，应另写有请求/输出/费用上限的smoke，不把此fixture换一个key后直接运行。
