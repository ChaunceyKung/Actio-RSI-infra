# 失败观察字段与来源

| 字段 | 原始来源 / 核验 | 含义与限制 |
|---|---|---|
| identity/source/bindings | Ledger scope、wire hash、operation/stream、dataset及原entry摘要 | 本机要求service capture与request/response逐字相等，包括unknown；历史要求固定ep-16摘要，不接受只填reader标签的伪归档 |
| transport.sending_recorded/http_status/capture_exception_present | 原sending事件、HTTP状态、response.error | HTTP200且error=null不能证明成功；不认证供应商实际收到或账单 |
| protocol | base64与UTF8全文一致、严格JSON、逐帧event/data/comment及终止位置 | 有界负面观察；不改变原成功profile；网络分段仅有合成测试，不冒充runtime可观测事实 |
| provider_declared_errors | data.error或HTTP error body；受限type/code白名单 | 只证明响应声明；未知标识输出unclassified；message仅报告是否存在，不保留内容、不按关键词推断 |
| adapter_native | 实际response.chunks_json与原生assistant/message或assistant/attempt stream、turn/end | 显示usage、finish.kind、failure.code和一致性；官方code可能来自message映射，并非独立根因 |
| admission | 原channel_audit v2重算、operation、domain_receipts | 错误观察不授予准入，content前缀不能成为行动；旧verdict与领域事实各自保留 |
| accounting | 原Ledger state/usage；raw tokens到adapter规范化；native usage比对 | 无raw usage不把adapter 0当可信0；错误usage可独立比较，但不授予settlement；账单始终UNVERIFIED |

classification优先保留矛盾，其后为未支持/缺失证据、HTTP、deadline、供应商声明错误、成功对照或不完整。signals并存，不以主分类抹去其他事实。SHA为本地内容一致性证据，不是外部签名或时标。

受控历史entry先由代码选择的C4 Git闭包认证完整delivery、v4原库和原report；sidecar再次校验固定ep-16 canonical hash。C2/C3分别保留原固定reader。公开portable只重算合成fixtures和调度，对历史/实测projection只提供内部hash完整性，不重新认证原始来源。

参考DSH checkout：`5badb15009ae1756c3afe0ae0cef1faafc290ccc`，`packages/llm/llm-pi-ai/src/stream.ts` SHA256 `e3563cc091cc2e6b0c2bdbd4c1614339d7cbb01f747a956931b43f3256e0c640`；MIT LICENSE SHA256 `ebb4f09972aee8608be255debaf78451a68e95c290f55c240dec2ecfa16ea6be`。只读核对error→usage/finish映射；没有复制或替换官方parser。binary_source_mapping仍unproven。

官方native保存有损失为零的压缩delta记录：text-chunks/reasoning-chunks含index、texts、time0和dt。新版读取严格验证字段、数量与时间形状后展开，再逐项比较adapter原chunks；不丢弃无法理解的记录。参考同checkout的`packages/llm/llm/src/assistant-stream.ts`，实测以固定发行物为准。原初版遗漏delta的FAIL保留；C5正式runtime来源由196e8a6固定reader认证，最终观察通过9份精确entry hash绑定，不能把旧runtime说成最终源码重跑。
