# 0.2.0 明确接口迁移

适用于 actio-rsi 0.2.0；这是开发期破坏性迁移。没有 alias、import hook、旧 console script 或隐藏 fallback。命令后原参数保持顺序与语义；基础全局 `--db` 等参数放在 `run` 后。

| 旧 module / console | 新命令前缀 |
|---|---|
| `actio.cli / actio 原基础命令` | `actio run` |
| `actio.verify` | `actio verify` |
| `actio.evaluation / actio-eval` | `actio evaluate` |
| `actio.candidate / actio-candidate` | `actio candidate` |
| `actio.candidate_evaluation / actio-candidate-evaluation` | `actio candidate-evaluation` |
| `actio.preflight` | `actio preflight` |
| `actio.readiness` | `actio readiness` |
| `actio.gateway` | `actio gateway` |
| `actio.pilot` | `actio pilot` |
| `actio.suite` | `actio suite` |
| `actio.robustness` | `actio robustness` |
| `actio.task_diagnostics` | `actio diagnostics task` |
| `actio.transport_diagnostics` | `actio diagnostics transport` |
| `actio.transport_campaign` | `actio campaign verify` |

可直接运行的离线例子：
```powershell
python -m pip install ./actio_rsi-0.2.0-py3-none-any.whl
python -m actio --version
actio run --db ./local.sqlite init
actio evaluate --help
actio candidate --help
actio candidate-evaluation --help
actio diagnostics task plan
actio diagnostics transport export ./diagnostics-new
actio diagnostics transport verify ./diagnostics-new/package.json
```

核验已有产物：`actio verify ./bundle`、`actio campaign verify ./campaign`。不会因此创建发送资格。内部入口保持原 argv/stdin/stdout/exit 协议：

| 旧入口 | 新入口 |
|---|---|
| actio.budget | `python -m actio.interfaces.ipc.budget <ledger>` |
| actio.host | `python -m actio.interfaces.workers.host <配置>` |
| actio.mcp_server | `python -m actio.interfaces.workers.mcp_server <配置>` |
| actio.eval_worker | `python -m actio.interfaces.workers.eval_worker`（stdin JSON） |

19 个根模块（上表含 cli/verify 与四个内部入口，另 common）全部删除；`actio.evidence.failure_observation` 也删除。Python 用户应按实际 owner 导入：`canonical/digest/seal/ContractError` 从 `actio.contracts.json`；文件/身份帮助函数从 `actio.adapters.filesystem.common`；`Ledger` 从 `actio.adapters.persistence.ledger`；策略从 `actio.profiles.registry`；`from_entry` 从 `actio.evidence.diagnostics.failure_observation`。命令 handler 从 `actio.interfaces.cli.<对应文件名>`，使用 `main(argv)`；不要依赖它的偶然再导出。原 interfaces 命令模块也移入 cli；新 IPC 与 workers 不经用户 dispatcher。

根 `readiness_quote.json` → `resources/pricing/readiness_quote.json`；根 `evaluation_history.json`、`task_diagnostic_trust.json` → `resources/trust/`；原 `pins/{concordia,c5_runtime}.json` → `resources/pins/`。五份字节不变，经 `actio.resources.data_path(group,name)` 定位。SQL/MJS/license 不搬家；当前 transport.mjs 只替换 budget 子进程地址。Clock、旧 quote、schema 与事务语义不因迁移改变。

旧材料须用对应固定 reader：C2 `3bef7e15b0eb21beeb10888eb508056592b977b0`、C3 `0a66334d61a0de302bbf8f5e15ee1db1b9d2e8fb`、C4 `3750954ea7cc8dff64115039e27bb671fa618d01`、C5 `196e8a6f3327b9d17ee0c0ba3bc45c93c38334e0`。维护工具 history/history_c5 在受控临时目录从这些 Git archive 提取 reader，以 -I -S 和只读 guard 认证，不执行 artifact 指定代码，不改旧 manifest。旧 0.1 命令仅由固定旧版本支持。

安装到新 venv，避免旧安装遗留模块。full 使用固定依赖并 pip check；minimal 使用 `pip install --no-deps`，只验证离线 reader，不代表依赖齐全。新回归/源码身份与历史分开，见[验收 CLI](../validation/refactor_entrypoints/CLI.md)。

源码的九模块 README 用于仓库导航；wheel 携带根 README 和完整 Python/SQL/JSON/MJS/license 运行闭包，仓库文档链接需在源码仓库阅读。
