# C2C1 CLI

在仓库根目录执行，Python 为 Windows x64 3.12。干净环境采用已缓存 wheels 与固定本地 Concordia 源码，安装阶段不访问 provider。

```powershell
& .local/phase1c2c0-runtime-venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --venv .local/phase1c2c1-runtime-venv --offline --concordia-source 'D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\15_concordia\repo'
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py candidate phase1c2c1
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py candidate_runtime phase1c2c1
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -m actio.candidate plan
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -m actio.candidate preflight
```

发布冻结合同后的一次性主矩阵入口：

```powershell
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2c1_run.py --root D:/actio-c2c1-main-v1
```

该入口检查本地 HEAD 与远端任务分支/main 一致、clean checkout、已提交计划完全匹配，随后只启动 literal loopback 与内存 fake credential。复用现有测试 fixture 服务及 pilot controller；整个计划只有一次 claim，不能换目录自动重发。候选库出现 evaluating 时不自动恢复。没有 live 分支或 key resolver。

可迁移导出与只读核验：

```powershell
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -I -B -m actio.candidate verify docs/validation/phase1c2c1/samples/delivery.json
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -I -B -m actio.candidate lineage D:/actio-c2c1-main-v1/candidates.sqlite
& .local/phase1c2c1-runtime-venv/Scripts/actio-candidate.exe preflight
& .local/phase1c2c1-runtime-venv/Scripts/python.exe -m pip --isolated check
```

verify 对计划、完整运行证据、任务指标、差值、谱系与决策独立重算；不使用产物指定源码/插件。lineage 单独检查结构与事实，完整证据绑定应使用 delivery。实际 CLI stdout 摘要、退出码、source/installed hashes 和 audit-hook 禁止 network/key/env/process/Worker/write 的证据写入 evidence。

历史核验使用 scripts/phase1c2c1_history.py 的固定完整 SHA 注册表，不用当前 implementation hash 重封存旧合同。精确真实密钥只在发布前本地扫描时读取，不进入日志、配置、trace 或 Git。
