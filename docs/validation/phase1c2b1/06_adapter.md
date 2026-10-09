# 固定官方 adapter 复用

固定源码 `dsh-v0.1.5-rc.1` → `183f08e9c6dde7e36cd2318eaee70b0da08fb35e`。本轮读取 llm-pi-ai README、package、index/config/catalog/provider/stream/context/auth 和 sdk-minimal composition，URL/时间/字节 hash 见 [upstream.json](upstream.json)，MIT 许可见 [DSH_LICENSE.txt](DSH_LICENSE.txt)。尝试 src/types.ts 得到真实 404；该包类型实际位于 config.ts/catalog.ts，没有猜测缺失文件内容。

README 明确 supports hand-declared OpenAI-compatible gateway，apiKeyEnv 是显式环境引用，默认 retry 可能为五次。sdk-minimal 默认挂载 llm-deepseek；本轮先禁用旧 adapter/扩展/inventory 并挂载官方 `@deepseek-ai/dsh-llm-pi-ai`，以假 key 和 literal loopback 验证，而不是以“源码存在”推断可用。

[实际加载记录](evidence/probe-20261009T034911Z-3e492336.json) 使用固定 SDK/binary，真实收到 1 次 `/v1/chat/completions`。选中 route=actio-tokenkey、model=gpt-5.6，wire 为官方 system/user、stream/include_usage/max_tokens，无 DeepSeek thinking 或 inventory 扩展；原生 result=propose:morning，usage/cache 映射一致。probe 为本机诊断，不计真实模型请求。

固定 binary 已包含可用包，因此没有安装外部 Node 依赖、没有升级 runtime、没有重写协议或第二 solver loop。生产路径复用同一官方 adapter，通过既有 RuntimePort/Concordia/发送 gate；来源到 binary 的完整构建映射仍 unproven。

官方 stream.ts 的 mapUsage 将 pi-ai input/output/total 写为 native usage，非零 cacheRead/cacheWrite 才出现；reasoning 已折入 output。网关原始 SSE usage 与这些观察交叉检查，cost 独立保留。llm/stream hook 只作观测，原 Response/序列化/翻译仍归官方实现；有界审计 tee 在 finish 交给 consumer 前读完，避免 disposal 竞态。
