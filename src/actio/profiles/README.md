# profiles：受信运行配置

`profiles` 将 schema、模式、端点、reservation/caps、wire binding、trusted usage、terminal keys 和 Clock 选择集中登记。它回答“本次运行允许什么”，不执行运行本身。

## 设计思想

registry 负责分类和版本选择，`validation.py` 保持纯净，只依赖 contracts/domain/tasks；构造器才负责组装身份和资源。批准、endpoint 或环境变量都不是授权本身，授权必须来自 profile 合同和 Ledger 一次资格。

## 使用方式

```python
from actio.profiles.readiness_contract import rehearsal, validate
config = rehearsal('http://127.0.0.1:19999', root, request_key)
validate(config)
```

CLI/interface 选择受信 profile 后交给 application；Ledger 使用同一 profile policy 进行 reservation/usage 校验。priced rehearsal 写入 fixed Clock，system/live 永远使用真实 UTC。

## 扩展方向

新 profile 应创建明确 revision，列出 schema、默认 caps、wire binding、clock policy 和 trusted usage 来源，并加入 valid_from/valid_until、未知字段、旧配置拒绝测试。不要在 validator 中导入 Ledger、preflight、application 或具体 adapter，也不要修改历史 quote。

入口：[registry.py](registry.py)、[validation.py](validation.py)、[readiness_contract.py](readiness_contract.py)、[transport.py](transport.py)；测试：[test_readiness_config.py](../../../tests/test_readiness_config.py)、[test_preflight.py](../../../tests/test_preflight.py)。

[九模块导航](../README.md)
