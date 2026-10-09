# C2C2 CLI

Windows x64 / Python 3.12，仓库根目录执行。命令实测的退出码、来源 hash 与 stdout hash 见 evidence 中 cli 文件。

```powershell
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --venv .local/phase1c2c2-runtime-venv --offline --concordia-source 'D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\15_concordia\repo'
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py evaluation_candidate phase1c2c2
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py evaluation_candidate_runtime phase1c2c2
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -I -B -m actio.candidate_evaluation plan
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -I -B -m actio.candidate_evaluation preflight
& .local/phase1c2c2-runtime-venv/Scripts/actio-candidate-evaluation.exe preflight
```

新模式 rehearsal 通过上述 runtime suite 使用 literal loopback 与内存 fake credential；完整 24 episode 合成验收另列 fixture case，不作候选真实性能证据。plan/preflight 都是纯函数，不执行发布网络检查。公开 execute 仅用于本轮唯一 live，要求已发布到两个分支、干净 checkout、当前安装/准入和冻结旧谱系来源。已经执行过的 claim 不允许重跑以下命令：

```powershell
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -X utf8 -m actio.candidate_evaluation execute --project . --root D:/actio-c2c2-live-v1 --source-database D:/actio-c2c1-main-v1/candidates.sqlite --authorized-phase1c2c2
```

controlled delivery 包含原始协议证据，可能含真实 reasoning 正文，保存在本地归档而不复制进公开 Git。完整离线复核不会调用 provider：

```powershell
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -I -B -m actio.candidate_evaluation verify D:/actio-c2c2-live-v1/delivery.json
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -I -B -m actio.candidate_evaluation lineage D:/actio-c2c2-live-v1/candidates.sqlite
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2c2_cli.py --root D:/actio-c2c2-live-v1
```

最后一条实测公开入口，并对子进程加拒绝 key/env/network/process/runtime import/write 的 guard，再独立重算完整 delivery；还重新 seal 篡改样本，验证缺 arm、错误 parent/历史 binding/decision 被拒绝。source 与实际运行 argv、原始归档/数据库 hashes 在 manifest/census；JSON 投影不是可恢复的权威 Store。

历史使用 scripts/phase1c2c2_history.py 的固定完整 SHA 注册表，不能由 artifact 指定源码/插件。已发布来源未改时可以复核；后续产品变化必须使用本阶段固定 reader，而不能重封存原计划。
