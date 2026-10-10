# C2C4 CLI

Windows x64、Python3.12，仓库根目录。固定官方SDK/runtime 0.1.5rc1，Concordia固定源码闭包；不升级上游。当前模块入口为 `python -m actio.robustness`，没有依赖未注册的console命令。

干净环境安装和纯/必要runtime验收：

```powershell
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --venv .local/phase1c2c4-runtime-venv --offline --concordia-source 'D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\15_concordia\repo'
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py robustness phase1c2c4
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py robustness_runtime phase1c2c4
```

只读公开命令，不读key/env、不联网、不启动DSH/Concordia，不写输出文件。调用者可重定向stdout；那是调用者写入。

```powershell
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.robustness plan
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.robustness preflight
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.robustness analyze D:/actio-c2c4-live-v1/matrix/pilot.json
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.robustness verify D:/actio-c2c4-live-v1/delivery.json
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.robustness lineage D:/actio-c2c4-live-v1/candidates.sqlite
```

preflight返回完整冻结合同，不进行远端发布网络检查，也不表示本机/发布Gate自动通过。analyze重算完整campaign；verify可核验完整delivery、campaign或谱系（单谱系只认证结构/历史绑定）。公开report本身不包含raw，不能冒充完整delivery。原历史包需固定旧reader，当前共享源码的改变不会刷新旧hash。

完整正常主矩阵通过公开execute的明确rehearsal模式运行；只使用内存假凭据与literal loopback，写入指定新root。包装脚本另实跑五种只读CLI、五种guard内CLI和篡改拒绝，保存argv/exit/stdout hash/产品source。不是只读命令。

```powershell
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2c4_cli.py --root D:/actio-c2c4-rehearsal-v2 --rehearsal
```

该脚本实际调用：

```powershell
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.robustness execute --rehearsal --project . --root D:/actio-c2c4-rehearsal-v2 --source-database D:/actio-c2c2-live-v1/candidates.sqlite
```

已存在的root、evaluation claim、项目live-once及plan claim不可覆盖或删除。以下是真实执行入口的审计说明，只有本轮已完成本机验收并发布冻结后才能运行，不能复制命令开启第二批：

```powershell
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 -I -B -m actio.robustness execute --project . --root D:/actio-c2c4-live-v1 --source-database D:/actio-c2c2-live-v1/candidates.sqlite --authorized-phase1c2c4
```

execute先核验已提交计划、两个远端SHA、clean checkout、installed source与local admission，再建立v4快照和一次claim，最后解析ignored凭据。遇技术失败停止，保存原始库存和完整后缀；不延长期限、不重试、不补样。完整受控材料包含raw reasoning和数据库，不进入Git。验证实际执行范围以 [DEVELOPMENT](DEVELOPMENT.md)、验收收据和最终 [RESULTS](RESULTS.md) 为准。

一次执行结束后仅做离线重算与导出，不再次调用 execute：

```powershell
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2c4_cli.py --root D:/actio-c2c4-live-v1
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2c4_collect.py --rehearsal-root D:/actio-c2c4-rehearsal-v2 --live-root D:/actio-c2c4-live-v1
& .local/phase1c2c4-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2c4_finalize.py --root D:/actio-c2c4-live-v1
```

第一个包装器记录五条 literal、五条只读 guard 命令及六项篡改拒绝；后两个分别写本轮清理/账本清单和公开投影。它们会写指定证据目录，不声称包装器自身纯只读。最终发布检查 `scripts/phase1c2c4_publish_check.py --live-root D:/actio-c2c4-live-v1` 仅在内存读取 ignored 凭据作精确排除扫描，另检查 reasoning 未公开；无网络和 solver 调用。`--verify-only` 只检查最终文件、不新增扫描收据；`phase1c2c4_manifest.py` 更新公开文件清单，不读取受控 raw。

历史核验分别使用 C2C2 reader `3bef7e15b0eb21beeb10888eb508056592b977b0` 和 C2C3 reader `0a66334d61a0de302bbf8f5e15ee1db1b9d2e8fb`，实际 argv、源码清单、只读 guard 和原库 hash 见 [history.json](history.json)。当前代码不得通过刷新旧 pins 来冒充这些 reader。

首次 v1 预演在128次本机发送全部完成后，因验收包装器7200秒整体时限终止于目录扫描，整包验收失败。旧目录/claim/报告和失败收据保留；上述v2为修正包装器后使用的新目录。仅移除包装器整体截止时间，产品逐请求和Worker期限不变；不宣称旧服务有join收据。见 [DEVELOPMENT](DEVELOPMENT.md)。

本轮真实execute已消耗唯一批次资格：33发送后于ep-16技术停止，unknown1、not_run95。不得再次执行live命令或清除claim。冻结后最终验收仅运行离线包装器，10条命令及6项篡改拒绝通过，见 [实际CLI收据](evidence/cli-bfc248772b61.json)；[停止原因](stop.json)和[RESULTS](RESULTS.md)保留完整分母。
