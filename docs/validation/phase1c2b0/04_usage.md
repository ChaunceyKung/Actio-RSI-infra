# CLI 复现

要求 Windows x64 / Python 3.12；从仓库根执行。锁文件不变，依赖准备不并发构建同一源码。本轮干净交付环境为 `.local/phase1c2b0-release-venv`。

```powershell
python -X utf8 scripts/bootstrap.py --venv .local/c2b0-repro --offline-wheels --concordia-source ../../codebase/15_concordia/repo
python -X utf8 scripts/bootstrap_eval.py --venv .local/c2b0-repro --offline --characterization
.local/c2b0-repro/Scripts/python.exe -X utf8 -m pip --isolated check
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness plan docs/validation/phase1c2b0/candidate.json
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness preflight docs/validation/phase1c2b0/candidate.json
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness execute docs/validation/phase1c2b0/candidate.json
```

plan 退出 0 表示已生成 proposal，但其状态为 BLOCKED；preflight/execute 退出 2。三者均不读 secret、不发网络请求、不创建 SDK client/Worker。`python -m actio.preflight candidate.json` 也明确分派 v4；v2/v3 仍按原语义静态检查。默认预算 0，批准为空，quote/token 未决项显示在输出。随源码/报价改变，旧合同及批准 hash 失效；不能手工改 hash 绕过未验证项。

本机预演（只用任务生成的随机假凭据，生成新短目录及新计数）：

```powershell
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B scripts/phase1c2b0_rehearsal.py
```

输出新 `D:/actio-c2b0-smoke/<ID>`、HTTP 接收、账务/场景和凭据扫描结果；root 中保留 result.json、budget.sqlite、bundle/、campaign/。默认两请求、两个 settled USD estimate、领域 success，真实费用 0，实际账单未核对。quote 复核窗口过期后会在发送前拒绝；复跑者须先更新有来源的候选合同，不以延长日期代替供应商复核。预演失败也保留新证据。

下面读取公开合成样例，不启动 Worker/evaluator/HTTP、不解析凭据：

```powershell
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness verify docs/validation/phase1c2b0/samples/success
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness verify docs/validation/phase1c2b0/samples/stall
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness verify docs/validation/phase1c2b0/samples/length
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness verify docs/validation/phase1c2b0/samples/last-money
```

valid 仅说明绑定/估算/分母自洽，不等于场景成功或账单核对。标准库 portable reader 的测试还禁止了 socket、subprocess、写入及 runtime 导入。

导出需要已关闭运行的 ledger、服务捕获和 bundle；目标目录必须不存在。只读源文件/数据库，向新的不可变 artifact 目录写出结果，不启动运行：

```powershell
.local/c2b0-repro/Scripts/python.exe -X utf8 -I -B -m actio.readiness export D:/actio-c2b0-smoke/<ID>/budget.sqlite D:/actio-c2b0-smoke/<ID>/receives.json D:/actio-c2b0-smoke/<ID>/exported D:/actio-c2b0-smoke/<ID>/bundle
```

将 `<ID>` 替换成该次实际输出；0 接收且没有 receives.json 时，用单独的合成空列表文件 `[]` 明确表示未接收，不伪造供应商日志。只读验证已导出的 campaign 不再依赖原 DB/authority 路径。

行为回归会增加本轮以外的新测试计数，运行证据追加不覆盖：

```powershell
foreach ($suite in @('readiness_config','readiness','transport','budget','preflight','transport_config','task','runtime','reliability','evidence','schema','input_binding','sotopia','evaluation')) {
  & .local/c2b0-repro/Scripts/python.exe -X utf8 scripts/validate.py $suite phase1c2b0
  if ($LASTEXITCODE -ne 0) { throw "failed: $suite" }
}
.local/c2b0-repro/Scripts/python.exe -X utf8 scripts/phase1c2b0_legacy.py
```

历史 C0/C1 reader 固定原 SHA；C2A.1 三样例固定使用 b086cbae97fcebd5c818dce611a0c2a331380cb1。artifact 不能选择执行源码。新协议或 v4 新实现不兼容时拒绝，不重封历史 pins。

`phase1c2b0_cli.py` 记录本批交付环境的 CLI/退出码；`phase1c2b0_release.py` 只读收集本批根路径、计数、安装/历史 hash、Job/端口清理和本地归档，再由 `--seal <delivery.json>` 一次性封存。它们绑定本批路径，不是外部调用入口，也不能覆盖已发布 manifest。
