# 预算状态与未实施边界

**当前只交付配置 schema，没有请求预算账本或执行门控。** `stub-config.json` 的合成 calls/input_tokens/output_tokens/cost_minor 是字段示例；不能限制或授权现有 fixture 入口，也没有用于四次诊断探针。诊断按实际服务接收另行计数，共 2 次。合成费用不是真实报价，真实费用为 0。

P0 通过后才应实施以下最小状态机；本轮未新增表、迁移旧 DB 或完成这些行为测试。

| 预定状态/转换 | 必要证据与约束（尚未实现） |
|---|---|
| 新 attempt → reserved | Python 冻结 campaign/run/operation/attempt/config hash、请求 hash、calls/token 上界、输出上限、价格版本；TS 每次真实 attempt 前检查并持久 reserve。并发最后额度只能一个赢家 |
| reserved → sending | 提交发送事件；调用一次官方 serializer/transport。attempt ID 重用不能重发；关联元数据不进入模型上下文 |
| sending → settled | 完整可信终态、request 归属和 usage 对账成立；服务接收与控制面事实分别保存 |
| sending → unknown | 超时、断流、进程崩溃、终态/usage 缺失；保留预留，不按零费用、不自动释放或重试 |
| reserved → released | 仅能证明未发送时释放，记录依据和原因；崩溃后无法证明则保持保守状态 |

成功记录、失败、unknown 都进入分母。只读核验需对总额、attempt 唯一性、request 归属、接收、终态和结算反例负责；不能只信服务计数或 Python 自报 0。请求硬上限需在真实发送 seam 验证，不能由任务开始前检查替代。

token/费用将来必须分别记录 provider usage、stub 合成 usage、保守估算与 unknown。`synthetic-byte-upper.v1` 只是本轮静态测试报价标识，不是对真实 tokenizer 或收费上限的证明。在没有可证明上界时，不声称真实费用硬封顶；live 继续 BLOCKED。
