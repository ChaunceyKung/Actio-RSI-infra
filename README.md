# Actio-RSI · Phase 1B

单机、持久化、合成 fixture 双场景基础设施。Python 管身份/spec、run/lease/receipt、SQLite facts/memory；官方 DSH SDK + TS executable 管 agent loop、MCP 和原生 journal；真实 Concordia Sequential 管社会场景调度及 GM 裁决。预算 **0**，模型和 GM 输出为固定 fixture，未开放 live provider。

入口：[本轮合同](docs/validation/phase1b/01_plan_and_contract.md) · [实现与验收](docs/validation/phase1b/02_results.md) · [Gate](docs/validation/phase1b/03_gate.md) · [独立证据](docs/validation/phase1b/evidence_manifest.json)。Phase 1A 的 probes/证据保留原样。

## 准备

要求 Windows x64、Python **3.12**（实测 3.12.10），仓库外可写短目录，例如 `D:\actio-p1b`。不改系统长路径设置，不安装全局依赖。发行物及闭包使用 [requirements.lock](requirements.lock)，Concordia 使用固定源码及逐文件 [hash](src/actio/pins/concordia.json)，只安装必要导入闭包。

从仓库根执行。联网准备入口如下；无缓存全量网络下载在本机曾超时，最终验收使用相同 hash 的缓存 wheel，不把网络超时计作产品通过。

```powershell
python -X utf8 scripts/bootstrap.py
```

可先按锁文件准备 ` .local/wheels ` 缓存（所有 wheel 仍由 pip 校验 hash）：

```powershell
python -m pip download --require-hashes --only-binary=:all: -r requirements.lock -d .local/wheels
```

本机已验证的完全离线方式（参考源码仓库只读；相对路径对应本工作区布局）：

```powershell
python -X utf8 scripts/bootstrap.py --offline-wheels --concordia-source ../../codebase/15_concordia/repo
```

`--venv <新目录>` 可建立另一干净环境；`--wheel-cache <目录>` 只用于安装加速。省略 `--concordia-source` 会获取固定 commit 的 GitHub 归档并检查每个 Python 文件及 LICENSE。`--offline-wheels` 仅关闭 pip index，不关闭这一步源码下载。安装后的产品从自己的环境导入包，不引用参考仓库或 Phase 1A `.local`。

## 运行与查询

以下均为公开 CLI；每条命令都是新的控制进程。所有身份/内容均为合成数据。

```powershell
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite init
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite agent A --create
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite agent B --create
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite assistant --agent A --key assistant-one
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite memory --agent A --environment assistant --target social --revision 1
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite social --a A --b B --key social-one --memory-revision 1
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite query social-one
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite reconcile assistant-one
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite social --a A --b B --key replay-one --replay social-one
.local/venv/Scripts/python.exe -m actio capabilities
```

可以把全局 `--short-root D:\actio-p1b` 放在子命令之前。相同 request key/请求返回原记录，包括 unknown；不同请求复用 key 被拒绝。新代码/pins 不会改写已有 AgentSpec，需创建明确的新身份/spec；本 slice 不提供 spec 自动迁移。`social --illegal` 是固定非法行动演示，真实 ActionSpec 验证会在 world 更新前拒绝，记录 task_failure。

重启后遗留的活动 owner 必须先被证明已死亡，才可回收 lease：

```powershell
.local/venv/Scripts/python.exe -m actio --db .local/demo.sqlite reconcile assistant-one --recover-owner
```

命令只核对受管 journal 和本地事实，**不会再次调用模型或工具**。owner 活着时拒绝接管，TTL 不授权接管。缺 receipt、flush 或领域效果时维持 incomplete/needs_reconcile。status 是本地台账状态。

## 验证

```powershell
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py contract
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py runtime
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py failures
.local/venv/Scripts/python.exe -X utf8 scripts/validate.py processes
.local/venv/Scripts/python.exe -m pip check
```

必须先安装当前源码；runner 会逐文件拒绝源码与 installed package 不一致的测试。每次运行创建新的 evidence JSON，失败也保留。测试创建的 `D:\actio-p1b-tests\<唯一目录>` 保存合成 raw journal/SQLite/日志，不自动删除；venv、wheel、binary 不入 Git。故障注入只在 `tests/`，不进入产品包。每组 suite 为聚合行为验收，不能把聚合数量当作研究样本量。

## 范围

支持持久身份/spec/query、新 native session、当前 host 内串行 turn、只读 MCP、显式停止、只读 reconcile 和冻结起点重执行。RuntimePort 位于 [runtime.py](src/actio/runtime.py)，Memory 控制入口位于 [memory.py](src/actio/memory.py)。运行 freeze memory 内容、实际选中 ID/revision、顺序、截断和 namespace；A→social 的共享在 spec 中显式授权，B 无权检索 A 的 private namespace。

强制结束 Job 不是 semantic cancel 或效果回滚。native reopen/resume/fork、在线 catchup、完整 world restore、动态逐调用审批、任意写工具、evaluator/live provider 明确 unsupported。没有 Web/UI/HTTP 服务，没有完整心智/演化/训练栈。外部 `.mjs` 是受信固定闭包，不承诺恶意插件沙箱安全。二进制到源码构建映射仍未证明。
