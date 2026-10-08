# 官方源码复用与发行物差异

固定参考：[deepseek-ai/deepseek-harness @ 5badb15009ae1756c3afe0ae0cef1faafc290ccc](https://github.com/deepseek-ai/deepseek-harness/tree/5badb15009ae1756c3afe0ae0cef1faafc290ccc)。本地参考 checkout 只读，未 pull/改写/执行上游 live e2e。11 个窄范围文件与 GitHub 同 SHA raw 内容按 LF 归一比较相同，逐项 URL/hash 见 [reuse.json](evidence/reuse.json)。许可为 MIT，Copyright (c) 2026 DeepSeek，原文保留 [DSH_LICENSE.txt](DSH_LICENSE.txt)。

| 项目 | 固定参考源码 | 固定实测发行物 |
|---|---|---|
| 版本 | llm-deepseek package `0.2.1-alpha.1` | Python SDK/runtime `0.1.5rc1`；实际插件 inventory `@deepseek-ai/dsh-llm-deepseek` `0.1.5-rc.1` |
| sdk-minimal provider | API-key wrapper `@deepseek-ai/dsh-llm-deepseek-api-key` | 默认旧 `@deepseek-ai/dsh-llm-deepseek` |
| 官方 route | `deepseek-official` | 同名，但同名不保证相同协议 |
| wire | `POST /v1/messages`、`x-api-key`、Messages SSE | 捕获 `POST /chat/completions`、`Authorization: Bearer` 假 key；未获得成功 stream |
| 显式 Messages 插件 | 源码中存在 | 实际 loader `ERR_MODULE_NOT_FOUND` |
| retry | 默认策略包含重试；不能当零重试 | 配置禁用 llm-retry 且 maxRetries=0；本机 429 仅一次接收是窄证据 |

固定 runtime exe SHA256：`7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`。没有升级/替换 exe；源码到二进制构建映射仍未证明。本轮恰好显示两者有实质协议差异。

复用范围：通过现有 Python SDK → 官方 TS Worker → 默认官方 provider 发真实 loopback 请求；保留官方 serializer/error parser。探针 `scripts/phase1c2a_probe.py` 的 Messages 合成事件形状参考 MIT mock-server，但没有被该旧 adapter 成功消费，因此只是拟用 fixture，不是已证复用链。`scripts/phase1c2a_probe.mjs` 在 `llm/stream` 观察请求/原样传递 chunk，最终增加独立 fetch 出口限制；没有另写 serializer/provider 或 Python solver。最后显式插件加载失败发生在初始化，尚无 provider request。

源码中的 `llm/stream` waterfall、`deepseekLlmApiExtensions` 请求准备 seam 已定位；没有把其中任何一个宣布为已验证的逐 attempt 持久预算门控。未复用 Files API、全测试平台、模型 e2e、自动恢复/重试，也未引入源码依赖到产品包。

探针 record 的 `runtime_pins.provider=actio-fixture` 是继承 RuntimePort 的**基础 profile 身份**，不能当作实际 provider。诊断 ProbePort 在 `prepare()` 明确改写配置，真实 provider 以保存的 `host-config.json`、`profile.patch.yml`、`llm-request` 和 wire 为准。这些诊断 run 没有被 seal/export 为新 transport campaign。正式新模式必须先定义独立 pins/spec，当前未做。

四次原始探针、最终源码、早期源码快照以及局部失败均由 [manifest](evidence_manifest.json) 关联；早期快照是留存检查点，不承诺逐次失败都有完全独立源码归档。完整 wire body 在公开探针 JSON，原始 native/plugin inventory 在本地 hash 归档；最终 `probe_findings.json` 摘录必要证据供无本地目录的读者检查。
