# C2C5 CLI

Windows x64 / Python3.12，先用现有bootstrap的`--offline --concordia-source`从本地锁定wheel与固定Concordia Git归档安装。也可在只有标准库的Python3.12中使用同版本`src/`运行纯入口；它不需要DSH或Concordia导入。官方runtime矩阵需要完整固定安装。

```powershell
$C5Python = '.local/phase1c2c5-runtime-venv/Scripts/python.exe'
& $C5Python -X utf8 -I -B -m actio.transport_diagnostics plan
& $C5Python -X utf8 -I -B -m actio.transport_diagnostics verify docs/validation/phase1c2c5/package.json
& $C5Python -X utf8 -I -B -m actio.transport_diagnostics analyze docs/validation/phase1c2c5/package.json
```

plan生成本机验收合同及未来只读顺序，无预约/执行权。analyze/verify对同版本portable重算合成输入、expected、observed、源码与future顺序；包移址不改变结果。公开历史和runtime投影不等于raw认证。上述命令实跑只读guard，禁止key/env/network/process/runtime导入/文件写入。错误出口只显示固定拒绝消息。

受控 `transport-diagnostic-controlled-entry.v1` 可通过同样的analyze/verify入口逐个认证：历史仅接受代码固定的C4 ep-16 entry；本机需完整原dataset/Ledger/service/native来源。正式9场景控制文件位于 `D:/actio-c2c5-formal-v1/<case>/entry.json`，不会随Git下载。历史固定reader外层harness命令为 `python -B -X utf8 scripts/phase1c2c5_history.py`，它负责受信Git归档和子进程启动；内部reader才是无进程的guard范围。

写包命令只接受不存在的新目录：

```powershell
& $C5Python -X utf8 -I -B -m actio.transport_diagnostics export D:/c5-new-export
```

可附加受控historical entry文件作为第三参数，输出仅保留诊断摘要。不复制原request/raw/reasoning/message/DB。重复目录退出2，不覆盖。当前可审阅发布包已导出，无需重复运行模型。

本轮正式实测使用下面的显式本机入口；这不是后续真实试验命令：

```powershell
& $C5Python -B -X utf8 -m actio.transport_diagnostics run-local --root D:/actio-c2c5-formal-v1 --project . --freeze docs/validation/phase1c2c5/freeze.json
```

run-local只创建literal127.0.0.1临时服务和内存fake credential；没有endpoint、credential_ref、live参数。拒绝已有root，核验安装/项目源码、fixture和代码维护工具列表。固定9场景最多12 sends；技术失败只停止所在场景，不重试。先保存原账本/slots/原异常，结束服务与Workers，再诊断、导出、扫描。扫描不全保持INCOMPLETE，不触发模型重跑。重复执行9场景不是默认验证步骤。

上面的正式命令在196e8a6冻结安装中执行。其后仅修正纯诊断，最终安装故意不能使用旧freeze启动新运行。当前reader可用代码固定的9份entry摘要读取该原始矩阵；`scripts/phase1c2c5_recompute.py` 在外层归档固定196e8a6 reader、guard认证后，用当前诊断重算。它不重发模型请求。初版FAIL及最终离线PASS分别保留。

`scripts/phase1c2c5_validate.py --runtime-root D:/actio-c2c5-formal-v1` 只重算纯测试及CLI/已存在受控entries，不发模型请求。准确运行版本和失败记录见DEVELOPMENT及各acceptance收据。若产品源码发生变化，不能刷新旧freeze让旧证据看似同源；使用冻结Git源码/安装来认证。
