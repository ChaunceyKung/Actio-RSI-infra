# measurement：独立测量与 oracle

`measurement` 计算任务指标、诊断单元和 robustness 定义。它读取冻结卡片、行动和缺失原因，输出指标与适用性；不写生产裁决、不启动 Worker、不访问 Ledger。

## 设计思想

独立 oracle 必须与生产执行路径分离，能对边界、反事实、缺失和篡改向量给出可重复结果。指标保留完整分母，not_run/unknown 不被静默删除；适用性和数值结果分别报告。

## 使用方式

```python
from actio.measurement.oracle import evaluate
result = evaluate(card, {'A': action_a, 'B': action_b})
```

先由 tasks 生成合法 view，再将封存输入传给 oracle；evidence/campaigns 负责把结果放入报告，application 负责显式写入 decision。

## 扩展方向

新增指标要定义单位、缺失/非法输入语义、边界向量、独立性依据和完整分母字段。不要从 Store 读取“最终分数”作为 oracle，也不要把新指标回填到旧实验分母。

入口：[oracle.py](oracle.py)、[diagnostic.py](diagnostic.py)、[robustness_definitions.py](robustness_definitions.py)；测试：[test_suite.py](../../../tests/test_suite.py)、[test_task_diagnostics.py](../../../tests/test_task_diagnostics.py)。

[九模块导航](../README.md)
