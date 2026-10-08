# CLI 与复核

Windows x64 / Python 3.12，从仓库根执行。锁文件、固定 DSH exe 和 Concordia 源码不变。以下准备逐个执行，不并发构建同一源码。缓存准备方式见仓库 README；本轮实测干净环境为 `.local/phase1c2a1-release2-venv`。

```powershell
python -X utf8 scripts/bootstrap.py --venv .local/c2a1-repro-venv --offline-wheels --concordia-source ../../codebase/15_concordia/repo
python -X utf8 scripts/bootstrap_eval.py --venv .local/c2a1-repro-venv --offline --characterization
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -m pip --isolated check
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -I -B scripts/phase1c2a1_smoke.py
```

smoke 创建自己的 `D:/actio-c2a1-smoke/<随机ID>`、临时 loopback 服务、假 key、新身份/任务库/预算库，运行两个 seat 并清理 Job/服务；输出新 root、实际 HTTP 数、场景终态及账务状态。`result.json`、`bundle/`、`campaign/` 位于新 root。服务端固定计划不会回显请求中的答案。预期默认 smoke 为 2 次本机 HTTP、两笔 settled、complete/success；真实模型请求/费用=0。命令主动执行本机合成实验，重复执行会产生新证据及新增本机 HTTP。

已封存的三个合成 campaign 可以直接复核，不产生新请求：

```powershell
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -I -B -m actio.transport_campaign docs/validation/phase1c2a1/samples/success
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -I -B -m actio.transport_campaign docs/validation/phase1c2a1/samples/missing-done
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -I -B -m actio.transport_campaign docs/validation/phase1c2a1/samples/last-call
```

`valid=true` 表示记录对账自洽，不表示任务成功或全部费用已结算。missing-done 保留第一步世界效果及第二笔 unknown；last-call 有两条 run、四个预登记 seat，只有一个实际接收，失败与 not_run 均计入分母。campaign 使用现有不可变对象/源 bundle 快照机制；标准库读者无需 SDK、Concordia 或评估依赖。transport 测试的 portable 子进程以审计钩子禁止写入、socket、subprocess 和 runtime 导入后仍能通过。

配置只读预检：

```powershell
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -I -B -m actio capabilities
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -I -B -m actio.preflight docs/validation/phase1c2a1/stub-config.json
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 -I -B -m actio.preflight docs/validation/phase1c2a/stub-config.json
```

两个配置各按 v3 Chat / v2 Messages 静态语义校验，均 BLOCKED/退出 2；重复 JSON key 也退出 2，并明确 configuration_valid=false。新 transport 不接受旧 v2。`stub-config.json` 的 18080 仅是可读示例，smoke 自行分配临时端口；它不假设已有服务，不读取用户 credential 或环境 proxy。

完整行为矩阵（会启动本机测试 Worker/服务并追加证据）：

```powershell
foreach ($suite in @('transport','budget','transport_config','preflight','task','runtime','reliability','evidence','schema','input_binding','sotopia','evaluation')) {
  & .local/c2a1-repro-venv/Scripts/python.exe -X utf8 scripts/validate.py $suite phase1c2a1
  if ($LASTEXITCODE -ne 0) { throw "failed: $suite" }
}
.local/c2a1-repro-venv/Scripts/python.exe -X utf8 scripts/phase1c2a1_legacy.py
```

旧版复核固定受信 Git commit：C0 `1e85d8c2fb4a756de81acb333905190df9e97592`、C1 `af0a88cfff23c22c396fd7c9ef9916f0df8cd21f`，不执行 artifact 指定的源码，不刷新旧 spec。复核不启动 Worker、evaluator 或 HTTP。

`phase1c2a1_cli.py` 记录本机交付环境的命令/退出码，包括失败；`phase1c2a1_release.py` 只读汇集最新测试、历史不变性、服务接收、预算账本、Job/端口状态及本地归档。它是绑定本批根路径/环境的交付工具，`--seal <delivery.json>` 在文档就绪后写一次 manifest，不覆盖已存在 manifest。复制环境复跑产生的新记录不属于当前封存批次，不应重写原 manifest 以冒充原验收。
