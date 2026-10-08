# Phase 1C2A 可复制入口

Windows x64 / Python 3.12，从仓库根运行。当前新产品只开放静态配置验证；官方 Messages 准入 NO_GO，未实现 transport/live 运行命令。所有数据为合成，所有 provider key 为任务创建的假值。

## 安装与公开 CLI

使用新的 venv 目录。以下安装按顺序运行，避免多个本地 wheel build 同时改同一 `build/lib`。离线模式需要已有 hash 锁定的 `.local/wheels` / `.local/eval-wheels`；Concordia 参考目录只读。锁文件未变。

```powershell
py -3.12 -X utf8 scripts/bootstrap.py --venv .local/phase1c2a-delivery-venv --offline-wheels --concordia-source ../../codebase/15_concordia/repo
py -3.12 -X utf8 scripts/bootstrap_eval.py --venv .local/phase1c2a-delivery-venv --offline --characterization
.local/phase1c2a-delivery-venv/Scripts/python.exe -m pip --isolated check
.local/phase1c2a-delivery-venv/Scripts/python.exe -X utf8 -I -B -m actio capabilities
.local/phase1c2a-delivery-venv/Scripts/python.exe -X utf8 -I -B -m actio.preflight docs/validation/phase1c2a/stub-config.json
.local/phase1c2a-delivery-venv/Scripts/python.exe -X utf8 -I -B -m actio.preflight docs/validation/phase1c2a/future-live-config.json
```

`capabilities` 退出 0，`live_provider=false`。两个 preflight 都退出 **2**：stub 示例 `configuration_valid=true`，其他准入维度 false；未填写的 future-live 示例 `configuration_valid=false`。示例端口 23456 仅字符串，不启动或指向本轮服务。可把 `authorization_ref` 写成任意批准字符串也不会改变 live=false。重复 key CLI 负例由发布脚本在独立短目录生成并保存 stdout/退出码。

实际本轮先建 `.local/phase1c2a-runtime-venv` 和 `.local/phase1c2a-eval-venv` 做回归，最终另建上述 delivery venv 再核对源码/安装文件集合与内容。最终安装和 CLI 结果见 [manifest](evidence_manifest.json) 引用的 delivery JSON。

## 已执行的回归与只读旧版复核

```powershell
foreach ($suite in @('preflight','task','runtime','reliability','evidence','schema')) {
  .local/phase1c2a-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py $suite phase1c2a
  if ($LASTEXITCODE -ne 0) { throw "Suite failed: $suite" }
}
foreach ($suite in @('input_binding','sotopia','evaluation')) {
  .local/phase1c2a-eval-venv/Scripts/python.exe -X utf8 scripts/validate.py $suite phase1c2a
  if ($LASTEXITCODE -ne 0) { throw "Suite failed: $suite" }
}
.local/phase1c2a-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2a_legacy.py
```

runner 拒绝 installed source 与仓库内容不一致，每次写新 evidence UUID，失败不覆盖。fixtures 使用真实 SDK/Concordia + 固定响应，**没有 provider HTTP**。固定旧版脚本只信代码中硬编码的 C0/C1 commit，不执行 artifact 指定路径；新代码对旧 pins 的拒绝也被验证。

## 协议阻断复现与证据封装

必要定位已结束，无需反复跑失败探针。若复核阻断，当前脚本支持以下有界命令：

```powershell
.local/phase1c2a-runtime-venv/Scripts/python.exe -X utf8 scripts/phase1c2a_probe.py --case explicit-adapter
```

预期 **退出 1**，本机服务接收 0，真实 loader 报 `@deepseek-ai/dsh-llm-deepseek-api-key` 不存在。该脚本只做诊断，不建立正式 transport 身份/预算/campaign。`--case success` 是预期 Messages 成功的设计用例名，历史实际失败；`--case 429` 的局部通过也不提高 Gate。每次再跑都会新增记录和 Jobs，现有 manifest 不自动覆盖，不能混用旧计数。

`scripts/phase1c2a_reuse.py` 的固定 `evidence/reuse.json` 是一次性 append-only 文件；重复查验时需用新的证据目的地，不覆盖本轮记录。现有 manifest 与独立 delivery 验证由：

```powershell
.local/phase1c2a-delivery-venv/Scripts/python.exe -X utf8 scripts/phase1c2a_release.py
```

生成。脚本在 manifest 已存在时拒绝覆盖；首次生成需本轮原始短根可用，执行 hash/只读 SQL/Job 状态/CLI/依赖检查，不运行新的 DSH 或 HTTP 探针。`status=PASS` 表示 **NO_GO 交付材料检查通过**，`transport_gate=NO_GO` 单列。重新做 C2A 应新建证据批次，而非刷新本 manifest。

本轮普通提交/推送目标固定为 `phase1c2a-solver-transport-and-budget`。最终 Git commit 在 Git 中承载 manifest；manifest 不包含自己的 hash 或待生成 commit SHA，避免循环。推送后另核对本地 HEAD 与远端 ref 完整 SHA，相等后才能报告推送完成。
