# contracts

输入：原始 JSON、wire 与端口数据。

处理：受限解析、canonical、seal 与端口声明。

输出：受检值或 ContractError。

依赖边界：不依赖 I/O/运行实现。

入口：[json.py](json.py)；对应测试：[test_contract.py](../../../tests/test_contract.py)。

[九模块导航](../README.md) · [完整模块卡片](../../../docs/architecture/MODULES.md)
