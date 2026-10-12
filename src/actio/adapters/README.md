# adapters

输入：端口调用、配置、路径。

处理：persistence 事务；runtime DSH/Job/MCP；environment Concordia；transport TS/fixture；filesystem 身份/文件。

输出：外部效果、原生回执、资源。

依赖边界：能力归实际 owner；本轮只本机 fixture，凭据读取0。

入口：[runtime/runtime.py](runtime/runtime.py)；对应测试：[test_runtime.py](../../../tests/test_runtime.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
