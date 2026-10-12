# measurement

输入：任务卡、行动与缺失。

处理：独立 oracle 及诊断指标计算。

输出：指标值、适用性和原因。

依赖边界：不以生产裁决冒充独立 oracle；不运行 Worker 或写账本。

入口：[oracle.py](oracle.py)；对应测试：[test_suite.py](../../../tests/test_suite.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
