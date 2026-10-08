# Phase 1C1 可复制入口

在仓库根执行，Windows x64 / Python 3.12。每次生成证据使用新的短目录；不要覆盖已有 campaign 或 run 身份。CLI 跨进程输出含中文路径时显式 `-X utf8`。核心与可选评估锁均保持不变。

```powershell
python -X utf8 scripts/bootstrap.py --venv .local/phase1c1-new-venv --offline-wheels --concordia-source ../../codebase/15_concordia/repo
$pythonC1 = '.local/phase1c1-new-venv/Scripts/python.exe'
& $pythonC1 -m pip --isolated install --no-index --require-hashes --only-binary=:all: -r requirements-eval.lock --find-links .local/wheels --find-links .local/eval-wheels
& $pythonC1 -m pip --isolated check
$rootC1 = 'D:/actio-c1-' + [guid]::NewGuid().ToString('N').Substring(0,8)
New-Item -ItemType Directory -Path $rootC1
& $pythonC1 -X utf8 -m actio --db "$rootC1/ledger.sqlite" init
& $pythonC1 -X utf8 -m actio --db "$rootC1/ledger.sqlite" agent C1_A --create
& $pythonC1 -X utf8 -m actio --db "$rootC1/ledger.sqlite" agent C1_B --create
$cardC1 = & $pythonC1 -X utf8 -m actio --db "$rootC1/ledger.sqlite" task-card --variant compatible --a C1_A --b C1_B --output "$rootC1/tasks" | ConvertFrom-Json
$runC1 = & $pythonC1 -X utf8 -m actio --db "$rootC1/ledger.sqlite" --short-root $rootC1 schedule --key compatible --task $cardC1.task | ConvertFrom-Json
& $pythonC1 -X utf8 -m actio --db "$rootC1/ledger.sqlite" export $runC1.id --output "$rootC1/bundle"
& $pythonC1 -X utf8 -m actio.verify "$rootC1/bundle"
```

将 variant 换成 conflict、使用新 key，默认 propose:morning + accept 合法但无法满足共同约束。自定义脚本只接受独立 JSON 文件，例如 `{"A":"propose:morning","B":"decline"}`，传 `--script`；它是 fixture 输入，不是 judge 的期望答案。相同 key / 相同参数返回原 run，不启动第二执行；replay 只传 `--replay <run-id>` 和新 key，不允许显式 task/script 覆盖。代码 pins 变化后创建新身份、新任务卡、新数据库。

最终封存 campaign 的复核完全只读，不启动 evaluator：

```powershell
& $pythonC1 -X utf8 -I -B -m actio.campaign verify-campaign docs/validation/phase1c1/campaign
$indexC1 = Get-Content -Raw docs/validation/phase1c1/campaign/campaign.json | ConvertFrom-Json
$datasetC1 = 'docs/validation/phase1c1/campaign/' + $indexC1.body.dataset
# 以下显式新测量仅本地 deterministic / controlled response；仍无模型请求。
& $pythonC1 -X utf8 -I -B -m actio.campaign run $datasetC1 --output "$rootC1/campaign"
```

独立核验同时检查冻结 dataset、记录登记与去重、spec pins、source/alias/view、分组、inventory 与分母。只检查单个 record 不能替代它。historical 文件必须在 index 中显式列出，不进入当前计数；缺、额外或错属 current 文件均失败。

标注交接文件见 [标注指南](05_annotation.md)。完整格式 CLI：

```powershell
& $pythonC1 -X utf8 -I -B -m actio.calibration import-labels docs/validation/phase1c1/annotations/internal.json docs/validation/phase1c1/annotations/blank-labels.jsonl --raters rater_1 rater_2
# 空白模板预期退出 2，并列出缺标；不会补零。
& $pythonC1 -X utf8 -I -B -m actio.preflight docs/validation/phase1c1/pilot-config.json
# 当前始终 BLOCKED，退出 2。
```

逐组验收（将失败写入新的 evidence 文件，不覆盖历史）：

```powershell
foreach ($suiteC1 in @('task','input_binding','evaluation','runtime','reliability','evidence','schema')) {
  & $pythonC1 -X utf8 scripts/validate.py $suiteC1 phase1c1
}
python -X utf8 scripts/bootstrap_eval.py --venv .local/phase1c1-new-eval --offline --characterization
.local/phase1c1-new-eval/Scripts/python.exe -X utf8 scripts/validate.py sotopia phase1c1
.local/phase1c1-new-eval/Scripts/python.exe -X utf8 scripts/phase1c1_legacy.py
```

原 C0 12 个记录只能用明确固定 `1e85d8c2fb4a756de81acb333905190df9e97592` 的受控源码复核。legacy 脚本从这个固定 Git commit 取源码，隔离 `-I -S` 子进程，禁止网络/运行时；不导入 record 指定的任意代码。当前 verifier 对旧 pins 明确 unsupported。重跑本轮交付脚本需要新输出路径，不能覆盖本次已发布的 campaign/annotations。
