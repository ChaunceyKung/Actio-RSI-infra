# interfaces：解析、装配与进程边界

`interfaces` 是系统的边界层。它把 CLI argv、IPC stdin、Worker 配置和内部 wiring 转成 application 调用，并负责稳定的 stdout/exit code；业务规则仍归 contracts/domain/application/evidence。

## 三类入口

- 用户 CLI：`actio` / `python -m actio`，由 `cli/main.py` 按命令显式延迟导入；命令包括 `run`、`verify`、`evaluate`、`candidate`、`preflight`、`diagnostics` 和 `campaign verify`。
- 内部 IPC：`python -m actio.interfaces.ipc.budget <ledger>`，保持 TS→Python 的 JSON stdin/stdout、退出码和一次 reservation 语义。
- 子进程 Worker：`interfaces.workers.host`、`mcp_server`、`eval_worker`，保持 argv/stdin 协议、生命周期和隔离 guard。

## 设计思想

顶层 help/只读命令不加载 DSH、Concordia、MCP 或 SQLite；handler 接收显式 `argv`，不反复改写全局 `sys.argv`。接口层只负责解析、受信 profile 选择和装配，避免把所有实现塞进 dispatcher。旧根 API 已按 0.2.0 迁移删除。

## 使用方式

```powershell
actio --help
actio diagnostics transport plan
python -m actio.interfaces.ipc.budget ledger.sqlite < request.json
```

程序调用 handler 时传 `main(argv)`；子进程调用必须使用安装 wheel 的新 module path。测试 CLI 的成功、拒绝、未知命令、外部能力未加载和 child IPC stdout，不要只测 `--help`。

## 扩展方向

新增命令先定义参数映射、退出码、离线/运行依赖和迁移文档，再在 `cli/main.py` 增加一个显式分支。新增 IPC/Worker 必须声明协议、限制、timeout、cleanup 和 deny list；不要恢复旧根 shim、sys.modules alias、import hook 或构建期隐藏入口。

入口：[cli/main.py](cli/main.py)、[ipc/budget.py](ipc/budget.py)、[workers](workers/)、[wiring.py](wiring.py)；测试：[test_modularity.py](../../../tests/test_modularity.py)、[test_budget.py](../../../tests/test_budget.py)、[test_processes.py](../../../tests/test_processes.py)。

[九模块导航](../README.md) · [迁移指南](../../../docs/architecture/MIGRATION_0_2.md)
