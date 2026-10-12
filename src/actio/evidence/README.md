# evidence：只读可信度与失败解释

`evidence` 读取封存包、raw receipt、Ledger snapshot、固定信任表和历史 lineage，输出认证结果、完整分母、缺失原因和诊断报告。它不执行 artifact 指定代码、不启动 runtime、不写 Store/Ledger。

## 五组职责

- `audit`：stream/channel/transport/accounting 的绑定和账务认证。
- `bundles`：task/evaluation/terminal package 的结构、hash 和一致性核验。
- `campaigns`：pilot、suite、candidate、evaluation、robustness 的汇总与计数。
- `lineage`：候选、evaluation、历史 reader 和 decision 谱系。
- `diagnostics`：failure observation、task/transport diagnostic 与固定 fixture。

## 设计思想

证据是事实的受限投影，不是第二数据库。reader 重新计算关键字段，区分结构无效、行为错误、技术失败、unknown 和不适用；原始 request/response、usage 和 not_run 必须保持可追溯。历史材料由固定 commit 的可信 reader 选择，不能由 artifact 自选导入器。

## 使用方式

```python
from actio.evidence.bundles.verify import verify_bundle
report = verify_bundle(bundle_path)
```

只读核验返回报告和退出码；campaign measurement 接收已认证的 entries；application 如需写 decision，必须显式调用写用例。失败诊断 reader 可对关闭后的 entry 做独立重算，不重新发送。

## 扩展方向

新证据类型先定义来源、hash、分母、缺失/unknown 语义和固定 reader，再实现 verifier 与篡改向量。禁止把 runtime 调用塞进 reader；需要新执行能力时放到 application/adapters，并让 evidence 只消费其 receipt。

入口：[bundles/verify.py](bundles/verify.py)、[audit/accounting.py](audit/accounting.py)、[diagnostics/failure_observation.py](diagnostics/failure_observation.py)、[lineage/evaluation_lineage.py](lineage/evaluation_lineage.py)；测试：[test_evidence.py](../../../tests/test_evidence.py)、[test_failure_observation.py](../../../tests/test_failure_observation.py)。

[九模块导航](../README.md)
