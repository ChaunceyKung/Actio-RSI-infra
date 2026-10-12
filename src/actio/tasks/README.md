# tasks

输入：任务版本、卡片、actor 与行动。

处理：registry 选择叶 family、可见性和行动裁决。

输出：可见观察与任务结果。

依赖边界：叶模块不导入 registry 或其它 dispatcher。

入口：[registry.py](registry.py)；对应测试：[test_task.py](../../../tests/test_task.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
