# evidence

输入：封存材料、固定信任与账务快照。

处理：audit 认证；bundles 核验；campaigns 汇总；lineage 谱系；diagnostics 失败分类。

输出：可信度、完整分母、缺失与报告。

依赖边界：reader 不导入 writer/runtime/SDK，不执行 artifact；文件读取不是纯函数。

入口：[bundles/verify.py](bundles/verify.py)；对应测试：[test_evidence.py](../../../tests/test_evidence.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
