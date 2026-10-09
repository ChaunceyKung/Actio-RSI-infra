# C2C0 CLI

在仓库根目录执行，环境为本轮新建、离线锁定安装并运行 pip check 的 `.local/phase1c2c0-runtime-venv`。公开 CLI 的实际 argv、输出、退出码与源码字节一致性记录在 `evidence/cli-*.json`。

```powershell
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.suite plan
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.suite preflight
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.suite verify docs/validation/phase1c2c0/samples/pilot.json
```

plan/preflight/verify 不读取 key/env，不访问网络、启动 Worker/上游 evaluator 或写文件；独立进程还用拒绝这些副作用的 audit hook 复核。verify 中 sent/usage 是导出的历史事实，`model_requests_during_measurement=0`。

首次 live 前，必须将实现和 preregistration 提交、普通推送到任务分支与 main，并保持 clean checkout。以下入口由本轮用户指令授权；同一预注册一经执行，不能用于重跑或补样。专用执行前置层验证远端 publication 后才读取 key；一次性 claim 跨输出目录有效。

```powershell
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.suite execute --project . --preregistration docs/validation/phase1c2c0/preregistration.json --root D:/actio-c2c0-live/registered-pilot --authorized-phase1c2c0
```

阶段正常完成或按合同停止均交付实际计数，不能仅用 CLI 退出码推断全部计划已执行。已冻结实现的 publication 记录和 first intent 保存在 samples/freeze.json 与 samples/intent.json。

本机增量验证与历史纠正：

```powershell
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py suite phase1c2c0
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py suite_runtime phase1c2c0
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2c0_history.py
```

首次 runtime suite 的一个反事实序列化断言失败已保留；修正后只重跑矩阵方法，其他通过的方法未重复执行。额外 evidence 反例检查只读引用矩阵导出；详细实际命令以证据记录为准。重跑本地验收会创建新短目录/Job/loopback，不会生成外部请求，但不能与正式 live 或构建并行。

凭据仅来自忽略的 `.local/credentials/token_key.txt`，仅内存传入且目标限 `https://api.tokenkey.dev/v1/chat/completions`；无自动重试、目录扫描或额外模型诊断。清理及原始运行归档使用 `scripts/phase1c2c0_collect.py`，已记录的目录和 Job 不按泛化进程名清理。
