# 固定标签复用

协议依据是官方 [dsh-v0.1.5-rc.1 / 183f08e9c6dde7e36cd2318eaee70b0da08fb35e](https://github.com/deepseek-ai/deepseek-harness/tree/183f08e9c6dde7e36cd2318eaee70b0da08fb35e)。审阅已从该固定 SHA 下载 16 个文件，本轮逐个重算本地 hash 与审阅的 GitHub URL/hash 相同，见 [reuse.json](reuse.json)。原较新 `5badb150…` checkout 只读且不作为当前协议依据。

| 复用点 | 实际采用 |
|---|---|
| llm-deepseek adapter/index | 官方发行物 provider，不复制或替换 serializer；默认插件、route、baseURL、retryPolicy 配置由实际 wire/profile 验证 |
| serialize.ts | 纯文本 system/user 转换，实际请求 `stream=true`、`stream_options.include_usage=true`、`max_tokens=64`、`thinking.type=disabled`，附带官方插件 inventory |
| sse.ts / translate.ts | 官方解析 choices/delta/finish_reason/usage/`[DONE]`，成功终态和 usage 等到 DONE；无 DONE 保留错误 |
| mock-server.ts | 窄适配 choices/delta、附带和尾部 usage、DONE 的测试事件形状到 Python stdlib 本机服务；计划由测试端持有 |
| llm service waterfall | `llm/stream` 观察 prepared call 和原样传递 chunk；与最终 fetch门控相互绑定 |
| sdk-minimal / llm-retry | 禁用 retry 和 session-title，关闭持久 shell/MCP/工具、压缩；服务次数与 ledger 次数独立核验 |

未执行上游 live e2e，未采用 Files/images、完整 provider 平台、另一 solver 或新版 Messages 插件。旧 tag 的测试文件是 adapter.spec.ts、sse.spec.ts、translate.spec.ts；不存在新版 stream.spec.ts 不是能力缺失。

许可为 MIT，Copyright (c) 2026 DeepSeek，原文 [DSH_LICENSE.txt](DSH_LICENSE.txt)。本轮测试 helper 与诊断脚本保留归属说明。源码 tag/package version 与实际 wire 相符；**binary_source_mapping 仍为 unproven**，没有声称可复现构建已证实。

S0 三个诊断探针先于预算库，独立限一次 fetch 和一次计划响应，明确 diagnostic。两种成功流均得到合法非空 `propose:morning` 与 SDK/native completed；finish 后缺 DONE 的流没有被认证完成。它们沿用诊断基础 pins，不作为正式 transport campaign/spec。正式路径另用版本化 transport pins 和逐请求账本。

门控作用范围是固定纯文本 provider：此 tag 的 adapter 直接调用全局 fetch；request/prepared 观察、sending 提交和服务接收逐一对应。测试还主动发起未绑定外部/localhost/Files 和重复 fetch，全部在 wrapper 内拒绝。底层 official fetch、响应和 translator 保留；响应 clone 仅用于有界审计。进程结束销毁 wrapper，正常 dispose 恢复原 fetch。未知插件、任意其他 Node 网络 API 不在本证明范围。
