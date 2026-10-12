# domain

输入：状态、身份、账务与 ClockSpec。

处理：状态约束、namespace 与额度聚合。

输出：领域决策值。

依赖边界：仅依赖 contracts；不读取系统资源。

入口：[clock.py](clock.py)；对应测试：[test_readiness_config.py](../../../tests/test_readiness_config.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
