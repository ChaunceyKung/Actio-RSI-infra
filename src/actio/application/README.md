# application：用例与事务编排

`application` 把冻结输入、ports、Store 和领域规则编排成 episode、campaign、evaluation、diagnostic、export 等用例。它拥有流程顺序和事务调用点，但不拥有具体 DSH、Concordia、TS 或文件实现。

## 设计思想

用例通过最小 ports 注入能力，保持同一 Store connection 的多表事务和 Ledger 的原子状态迁移。失败是结果的一部分：主异常、unknown、not_run、清理失败和 evidence 都要保留，不能用重试掩盖技术失败。

## 使用方式

CLI/interface 负责解析和装配；application 接收已验证的配置与 factory，然后执行 claim → freeze → run → certify → persist → export。`diagnostic_runtime.run` 只接受安装产品的受控 fixture，`export` 生成只读 bundle，`candidate/evaluation` 用例追加历史 decision 而不改旧记录。

## 扩展方向

新增用例先定义输入/输出、失败矩阵、事务边界和最小 port，再接入接口。跨 Store/Ledger 的协调应记录两个权威的独立状态，不创建第二 repository 或跨库伪原子事务。需要恢复、重放或新 provider 时，新增 capability 和 evidence schema，而不是在现有用例中加入隐式 fallback。

入口：[pilot.py](pilot.py)、[transport.py](transport.py)、[diagnostic_runtime.py](diagnostic_runtime.py)、[export.py](export.py)；测试：[test_reliability.py](../../../tests/test_reliability.py)、[test_evidence.py](../../../tests/test_evidence.py)。

[九模块导航](../README.md)
