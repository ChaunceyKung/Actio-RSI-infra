# C2B2 CLI

在仓库根目录执行，Python 为 `.local/phase1c2b2-release-venv/Scripts/python.exe`。源码或安装不一致时先重新安装；历史固定 reader 不使用此环境代替历史源码。

```powershell
& .local/phase1c2b2-release-venv/Scripts/python.exe -I -B -m actio.pilot plan
& .local/phase1c2b2-release-venv/Scripts/python.exe -I -B -m actio.pilot preflight
& .local/phase1c2b2-release-venv/Scripts/python.exe -I -B -m actio.pilot verify docs/validation/phase1c2b2/samples/pilot.json
```

plan/preflight/verify 不读取 key/env、不访问网络、不启动 Worker/evaluator、不写文件。verify 的 model_requests_during_measurement 为 0，报告的 sent 是被核验的历史事实。

首次真实执行由当前授权覆盖；必须先将实现和 `preregistration.json` 提交并普通推送任务分支与 main。下面命令是一次性入口，已执行过同一预注册时会拒绝，不能用于复跑补样。

```powershell
& .local/phase1c2b2-release-venv/Scripts/python.exe -I -B -m actio.pilot execute --project . --preregistration docs/validation/phase1c2b2/preregistration.json --root D:/actio-c2b2-live/registered-pilot --authorized-phase1c2b2
```

专用 key 仅在执行分支读取忽略的 `.local/credentials/token_key.txt`，仅发往 `https://api.tokenkey.dev/v1/chat/completions`。控制器、host、Worker 与账务 helper 各自使用最小环境，helper 不带 key；无 SDK 环境 fallback、重试或目录探测。

本地验收：`scripts/validate.py pilot phase1c2b2`、`scripts/validate.py pilot_runtime phase1c2b2`。后者使用公开 fake credential、loopback HTTP、真实 DSH/Concordia；与 live 不并行。历史解释：`scripts/phase1c2b2_legacy.py`；冻结：`scripts/phase1c2b2_prepare.py`。
