# contracts：系统的可验证语言

`contracts` 定义模块之间交换的最小语言：JSON 如何解析和规范化、对象如何 seal、wire 如何绑定一次行动、端点和传输配置允许哪些字段。它只描述“数据是什么以及是否有效”，不决定业务流程，也不执行网络、数据库或 Worker。

## 设计思想

- **先规范化再哈希。** `contracts.json` 的 canonical 编码保证字段顺序、数字和 UTF-8 表示稳定，`digest`/`seal` 才能成为跨进程身份锚点。
- **失败关闭。** 未知字段、重复键、非有限数字、类型漂移和额外尾部数据直接产生 `ContractError`，调用方不能把错误对象当作空结果继续执行。
- **合同与效果分离。** `ports.py`、`wire.py` 只声明端口和行动绑定；真正的发送、环境推进和持久化分别由 adapters/application 负责。
- **版本显式。** `versions.py` 和各合同中的 schema/version 让固定历史 reader 能识别旧材料，不靠当前代码猜测旧格式。

## 使用方式

```python
from actio.contracts.json import canonical, digest, parse, seal

value = parse(raw_bytes)                 # 严格解析，失败抛 ContractError
identity = digest(value)                 # 稳定身份
package = seal(value)                    # 带 schema/hash 的封存对象
wire_bytes = canonical(package)
```

业务模块应在入口处解析和校验一次，把已验证的数据传给 domain/application；不要在每个 adapter 内重新实现 JSON 规则。需要跨进程时传递 canonical bytes 和 identity，而不是 Python 对象。

## 扩展方向

新增合同应先定义 schema、未知字段策略、canonical/hash 规则和兼容窗口，再添加 reader/writer 测试。若格式真的改变，新增明确版本并保留旧 reader；不要修改历史 quote、manifest 或已发布 evidence 的解释。新的端口应放在 `ports.py` 的最小协议中，避免把 SDK 或数据库类型泄漏到 contracts。

主要入口：[json.py](json.py)、[wire.py](wire.py)、[ports.py](ports.py)、[transport.py](transport.py)；测试：[test_contract.py](../../../tests/test_contract.py)、[test_schema.py](../../../tests/test_schema.py)。

[九模块导航](../README.md) · [架构边界](../../../docs/architecture/README.md)
