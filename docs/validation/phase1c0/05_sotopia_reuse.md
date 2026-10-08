# SOTOPIA 最小复用与兼容性

固定上游 [a0aaafb440e570e5e61b7c44a44e5e417c545383](https://github.com/sotopia-lab/sotopia/tree/a0aaafb440e570e5e61b7c44a44e5e417c545383)，metadata 0.1.5，MIT / Copyright (c) 2023 Hao Zhu。本地 checkout clean 且 HEAD 精确一致，未 pull/修改参考源码。

直接导入闭包包含 redis-om、litellm、provider SDK、aact 等，远超两个字段所需。采用 MIT 许可下的窄源码提取，产品不导入 `sotopia` 顶层。提取的 class/function **定义文本原样保留，仅 CRLF→LF**；[provenance](../../../src/actio/_vendor/sotopia_provenance.json) 登记 SHA、原路径、起止行、整个原文件字节 hash、定义 LF hash、生成文件 hash；[LICENSE](../../../src/actio/_vendor/SOTOPIA_LICENSE) 随包分发。

| 原资产 | 产品用途 | 修改边界 |
|---|---|---|
| LLMBaseModel / LLMEvalBaseModel | extra-forbid 结构基类 | 只移除 Redis/storage import 闭包 |
| PositiveReasoningScore / BidirectionalReasoningScore 与 range validators | goal 整数 0..10、relationship 整数 -5..5 | 定义不改；import glue 将存储 Field 替换为 pydantic.Field；所选字段不使用索引参数 |
| OutputParser / PydanticOutputParser | 真正执行原始文本 parser | 定义不改；限定 json-repair 0.48.0 与 Pydantic 2.13.5 |
| EvaluationForAgents | 显式 alias → 两维 model | 定义不改；Actio 接管 exact alias/维度和原始类型检查 |
| Evaluator / EpisodeLLMEvaluator | 仅测试侧原定义执行 | gin/validate_call 真实；Message 数据 shim、generation 和 supports_response_schema 为固定测试 seam |

11 个原定义均可由 `scripts/extract_sotopia.py --check` 从固定 checkout 重建。产品的 Actio 两维组合通过 create_model 组合真实上游 score classes，未冒充上游全维度模型。Actio 外层 `scores` 映射到上游 `evaluations` 只是字段名 adapter；验证前不修复 alias、不排序猜身份、不删不行动事件。

## 实际刻画

| 路径 | 上游实际结果 | Actio 处理 |
|---|---|---|
| 合法原始 JSON，有/无 context | 原 parser/schema 成功 | 在严格原始校验后采用 |
| repair、`value` 展开，有 context | 可转成 model | 不用来使原非法响应变有效 |
| repair、`value` 展开，无 context | 回落到原文本 JSON 校验并失败 | 保留独立刻画 |
| `properties` 展开 | 两条路径都校验展开值，传入 context 被绕过 | 产品 envelope 不允许 properties 包装 |
| bool/数字字符串分数 | Pydantic 转成 int | Actio 先用 type(score) is int 拒绝 |
| 标准 nested reasoning/score 返回 Episode | `[1]/[0]` 访问失败，捕获后 `[]` | COMPATIBILITY_FAIL，未采用 |
| 反序 alias、tuple-shaped 维度返回 Episode | values 枚举后重新命名，agent_2 被归入 agent_1 | Actio 读取原 key 和冻结映射 |
| history-only，无 messages | num_agents=0，结果 `[]` | 不用上游人数推导 |
| did nothing | 从 prompt history 删除，但仍计参与人数 | Actio 保留 synthetic actions |
| 固定 generation 抛异常 | 上游打印并返回 `[]` | 产品内部错误单独 measurement_error，不吞成正常结果 |

测试中 nested 形状同时经过真实原始 parser 路径和 structured-model 返回路径；tuple 形状专门用于暴露 values 身份错配，未被当作选定产品 schema。没有 mock parser 后宣称复用成功。

上游完整 evaluator 实验失败不等于 parser 复用失败；本轮不修复完整上游、不发 issue/PR、不启动 Redis/模拟平台，也未执行 live judge。模型请求始终为 0。
