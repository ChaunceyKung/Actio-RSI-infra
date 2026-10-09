# C2B1 CLI 与复核

要求 Windows x64 / Python 3.12。所有命令从仓库根执行；依赖、DSH 与 Concordia 固定版本见 [合同](01_contract.md)。本轮使用两个独立安装目录，构建、安装、紧期限 runtime suite 均顺序运行。真实 argv、返回码和源码 hash 由 [manifest](evidence_manifest.json) 指向的各份 evidence 保存，不能把命令示例当作实测记录。

## 准备与纯离线操作

本机有锁定 wheel 缓存与固定 Concordia 仓库时，可建立新环境：

```powershell
python -X utf8 scripts/bootstrap.py --venv .local/phase1c2b1-release-venv --offline-wheels --concordia-source ../../codebase/15_concordia/repo
python -X utf8 scripts/bootstrap_eval.py --venv .local/phase1c2b1-release-venv --offline --characterization
.local/phase1c2b1-release-venv/Scripts/python.exe -m pip --isolated check
```

`bootstrap_eval.py` 的附加依赖只支持旧离线测量回归，不开放 live judge。没有缓存时按仓库原有 bootstrap 说明准备锁定依赖；不升级 runtime 或使用其他版本的 adapter。

以下命令只生成/核验执行说明，不解析凭据，不联网，不启动 Worker。两份公开 proposal 的 authority 为 null，不能直接用于 execute；实现 hash 变化后旧 proposal 明确拒绝，不能重封历史证据来执行。

```powershell
.local/phase1c2b1-release-venv/Scripts/python.exe -I -B -m actio.gateway plan --model gpt-5.6
.local/phase1c2b1-release-venv/Scripts/python.exe -I -B -m actio.gateway preflight --config docs/validation/phase1c2b1/claude-sonnet-4-6-proposal.json
.local/phase1c2b1-release-venv/Scripts/python.exe -I -B -m actio.gateway verify docs/validation/phase1c2b1/samples/gpt56
.local/phase1c2b1-release-venv/Scripts/python.exe -I -B -m actio.gateway verify docs/validation/phase1c2b1/samples/claude
```

`verify` 从导出的 dataset、ledger、source bundle 与 manifest 交叉核验，不访问原机绝对路径，不读 key/网络/Worker/evaluator。旧 C0/C1/C2A.1/C2B0 证据必须使用各阶段固定 reader；本轮的 `scripts/phase1c2b1_legacy.py` 验证这些历史来源，没有令 artifact 指定任意执行源码。

## 本机验收

公开 rehearsal 使用内存假凭据、literal loopback 和真实官方 DSH/Concordia，compatible 两步共 2 次本机 HTTP，生成独立短目录。它不是 TokenKey 真实模型调用。

```powershell
.local/phase1c2b1-release-venv/Scripts/python.exe -X utf8 -I -B scripts/phase1c2b1_rehearsal.py
.local/phase1c2b1-runtime-venv/Scripts/python.exe -X utf8 -I -B scripts/validate.py gateway phase1c2b1
.local/phase1c2b1-runtime-venv/Scripts/python.exe -X utf8 -I -B scripts/validate.py gateway_lifecycle phase1c2b1
```

`scripts/phase1c2b1_cli.py` 集中验证两环境 pip check、plan/preflight、未确认执行标志的拒绝、C2B0 execute 继续拒绝、本机 rehearsal 及只读导出。重复验收产生新 evidence，不能覆盖已封存的 manifest；新验收属于后续交付。

## 已授权真实批次

本轮用户授权已明确，`--authorized-phase1c2b1` 是显式操作标志，不是再次请求费用批准。脚本先写 live intent、分配新 authority/config/root，再调用同一 `actio.gateway execute`。它读取被 Git 忽略且未跟踪的指定凭据文件；禁止将密钥放在命令行或复制到公开 config。

```powershell
.local/phase1c2b1-release-venv/Scripts/python.exe -X utf8 -I -B scripts/phase1c2b1_live.py --model gpt-5.6
# 检查前一批完整结果及清理后，执行同一合同的跨模型候选：
.local/phase1c2b1-release-venv/Scripts/python.exe -X utf8 -I -B scripts/phase1c2b1_live.py --model claude-sonnet-4-6
```

每次命令最多执行一个模型的 compatible→conflict 有限计划，每 seat 单次请求，错误/unknown/不完整时停止。没有自动重试、模型发现或 SDK 备选调用。旧 root 不能 execute；同一 authority 不能换库发送。必要新诊断须使用 `--predecessor <旧run/result.json> --reason <新增证据与变化>` 关联旧批次，先确认 Worker 已回收；不能通过重复运行脚本抹掉旧 unknown。

本轮完成后停止于 C2B1。新正式研究需要另行预注册任务、路由与重复策略；本 CLI 不授予 judge、真人校准、训练/演化、部署或账户修改权限。
