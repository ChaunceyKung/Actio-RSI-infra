# application

输入：冻结命令、Store 和注入 ports。

处理：claim、执行、认证、效果、导出和追加决策。

输出：run/事实/记忆/评估状态。

依赖边界：不导入具体 runtime/transport/persistence；SQL/mixin 保持原连接事务。

入口：[transport.py](transport.py)；对应测试：[test_reliability.py](../../../tests/test_reliability.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
