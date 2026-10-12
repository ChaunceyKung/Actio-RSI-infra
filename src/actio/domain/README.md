# domain：可审计的状态规则

`domain` 保存身份、episode、memory、账务和 ClockSpec 等规则。它把“什么状态是合法的”与文件、SQLite、SDK 等效果隔开，使重放、并发和失败路径可以用确定性输入复核。

## 设计思想

领域规则优先于流程编排：lease 不能因超时自动授权接管，unknown 不会被折算成成功或零 usage，Clock 的 mode/instant 必须进入配置身份。对象尽量接受普通 dict/值并返回新状态或明确的 `ContractError`，不在这里读取环境变量或启动进程。

## 使用方式

- `clock.py`：live/system 使用真实 UTC；priced rehearsal 只能使用合同窗口内的 fixed instant。
- `accounting.py`：计算 reservation、usage、settled/unknown/released 的守恒关系。
- `episode.py`、`roles.py`、`memory.py`：维护 run、角色和记忆 namespace 的状态约束。

application 在事务边界内调用这些规则，并把返回值写入唯一 Store/Ledger；adapter 不应绕过 domain 直接修改状态。

## 扩展方向

新增状态规则先写边界表和纯函数测试，再接入 application。涉及时间、额度或身份的字段必须进入 hash、snapshot 和 evidence。恢复、重试、自动接管属于新的合同能力，需要显式 capability 和历史兼容策略，不能通过放宽现有规则实现。

入口：[clock.py](clock.py)、[accounting.py](accounting.py)、[episode.py](episode.py)、[memory.py](memory.py)；测试：[test_readiness_config.py](../../../tests/test_readiness_config.py)、[test_budget.py](../../../tests/test_budget.py)。

[九模块导航](../README.md)
