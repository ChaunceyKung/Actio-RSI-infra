# adapters：外部能力的受控实现

`adapters` 将最小 ports 接到 SQLite/文件、DSH Worker、Concordia、TS transport 和本机 fixture。它是唯一允许接触具体 SDK、进程、socket、SQL connection 或安装资源的业务层。

## 五组职责

- `persistence`：Store/Ledger、schema、WAL、readonly 与迁移；保持原连接和事务边界。
- `runtime`：Supervisor、Job、host、MCP、eval worker、native facts 与 cleanup；原生 journal 归官方 runtime。
- `environment`：Concordia 顺序推进和 world effect；环境裁决不等于模型评价。
- `transport`：TS plugin、协议响应、fixture gateway 和发送/usage 适配；unknown 不冒充成功。
- `filesystem`：身份闭包、文件 hash、受控导出、凭据扫描和出版保护。

## 设计思想

adapter 只实现 port，不改变 domain 合同；所有外部效果都必须有 scope、deadline、cleanup、raw receipt 和错误状态。loopback fixture 与真实 provider 使用相同受限协议，但本轮只允许前者。runtime/environment/transport 不应被纯层或只读 evidence 直接导入。

## 使用方式

application/interface 通过 wiring 注入 `Store`、`RuntimePort`、`TransportPort` 或 `DiagnosticPorts`；测试可注入 fixture，但必须另有一次完整装配测试。直接调用 adapter 时先构造 profile/config，保留 authority anchor 和生命周期 finally。

## 扩展方向

增加外部能力先写 port、capability、resource limits、cleanup 和 raw evidence 合同，再添加 adapter。新 SDK/引擎需要 pin、source identity、license 和离线 fixture；不能在现有 adapter 中加入环境变量 fallback、自动重试或第二状态权威。

入口：[persistence](persistence/)、[runtime/runtime.py](runtime/runtime.py)、[environment/concordia.py](environment/concordia.py)、[transport/transport.py](transport/transport.py)、[filesystem/common.py](filesystem/common.py)；测试：[test_runtime.py](../../../tests/test_runtime.py)、[test_transport.py](../../../tests/test_transport.py)。

[九模块导航](../README.md)
