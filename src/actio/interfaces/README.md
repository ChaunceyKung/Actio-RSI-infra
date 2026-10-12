# interfaces

输入：CLI argv、IPC stdin、worker 配置。

处理：cli 解析与延迟路由；ipc 保持协议；workers 承载子进程；wiring/store 装配。

输出：stdout、退出码和用例结果。

依赖边界：仅装配和桥接，行为由实际 owner 提供；不保留旧根 alias。

入口：[cli/main.py](cli/main.py)；对应测试：[test_modularity.py](../../../tests/test_modularity.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
