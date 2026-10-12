# tasks：冻结的任务与可见性规则

`tasks` 把任务卡、actor 视图、合法行动和版本 family 组织成可复现的任务规则。任务叶模块描述具体 family；`registry.py` 是唯一 dispatcher，负责按版本选择叶实现。

## 设计思想

可见性先于行动：每个 actor 只得到合同允许的字段，B 使用实际 A 的公开历史；生产 oracle 不参与任务裁决。`core.py` 提供 sealed 基础原语，family 模块保持叶依赖，避免阶段 dispatcher 互相导入形成循环。

## 使用方式

```python
from actio.tasks.registry import task_card, require
card = task_card('schedule-v1', bindings)
require(card['action'], allowed_actions)
```

application 通过 registry 取得 card、observation 和 action spec，再交给 environment/measurement。不要从另一个 family 私下导入实现，也不要把完整数据库或 provider response 塞进 task view。

## 扩展方向

新增 family：先在 `core.py` 明确 schema/visibility/sealed invariants，新增叶模块和 registry 映射，再添加完整可见性、非法行动、历史顺序和独立 oracle 向量。旧版本保持可读；新版本必须有独立版本号和 method map。

入口：[core.py](core.py)、[registry.py](registry.py)、[finite.py](finite.py)、[robustness.py](robustness.py)；测试：[test_task.py](../../../tests/test_task.py)、[test_suite.py](../../../tests/test_suite.py)。

[九模块导航](../README.md)
