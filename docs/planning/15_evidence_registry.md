# 15 · 证据登记与旧结论修订

核验日期：2026-10-05（Asia/Shanghai）。E-ID 是全套规划的唯一证据键；repo 表给出共同的 revision/路径/工作树/许可，证据项继承这些字段。固定 SHA 链接用本机实际存在文件与行号生成；行号只对该 SHA 有效。A/B/C 的根及已涉及子目录许可已核，**不等于依赖 SBOM、数据、模型或商业部署全部准入**。状态定义见 [16](16_capability_and_maturity_checklist.md)，实际执行见 [18](18_validation_log.md)。所有目标集成均未实现、未运行。

## 现场与资产

目标 checkout：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\Actio-RSI-infra`。初始远端为空，unborn `main`、无已有 docs/README/AGENTS/用户改动；读取祖先范围未发现适用 AGENTS。参考 checkout 只读；新文件与测试副本位于工作区 `_external/_audit`。未切参考分支、未在参考原目录安装或测试。Letta 新克隆仅取到 Git tree，checkout 卡住中断；以下以固定 SHA raw 文件核验，不将该不完整 checkout 的 staged deletions 当用户改动。

下列为决定主路径的资产。短 tag 字段等于 SHA 前缀时只是 `git describe --always` 输出，不是发布 tag；HEAD 相同也不保证发布 artifact 已测。

| Key / canonical repo | 本地绝对 root | branch / SHA / tag | 工作树 / remote | 许可范围 |
|---|---|---|---|---|
| 01_deepseek-harness · [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\01_deepseek-harness\repo` | master / `5badb15009ae1756c3afe0ae0cef1faafc290ccc` / dsh-v0.2.1-alpha.1 | clean；同 SHA | MIT；vendor/cordis MIT；THIRD_PARTY_NOTICES 与 wheel 闭包须保留、逐依赖审核 |
| 02_Raven · [EverMind-AI/Raven](https://github.com/EverMind-AI/Raven) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\02_Raven\repo` | main / `3632e6040c7038a60ec418ce39ccae185c72c19f` / v0.2.4 | clean；同 SHA | Apache-2.0；NOTICES 中 nanobot/hermes/ink 等 MIT 及 agentscope Apache 衍生说明 |
| 10_meta-harness · [stanford-iris-lab/meta-harness](https://github.com/stanford-iris-lab/meta-harness) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\10_meta-harness\repo` | main / `8123ccabe2b19fa1123090b2e5f1bacc20963ce8` / 8123cca | clean；同 SHA | MIT；Harbor/benchmark/模型数据另核 |
| 11_DGM · [jennyzzt/dgm](https://github.com/jennyzzt/dgm) | `D:\调研\RSI_AI训AI\codebase\11_DGM\repo` | main / `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2` / a565fd2 | clean；同 SHA | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 05_letta · [letta-ai/letta](https://github.com/letta-ai/letta) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\05_letta\repo` | main / `5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a` / 5bcdd17 | clean；同 SHA | Apache-2.0；archive 依赖/数据另核 |
| letta-code · [letta-ai/letta-code](https://github.com/letta-ai/letta-code) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\_external\_audit\letta-code-sources` | main / `f898fda60932b34ddbcfd389ea414515b0a5d272` / v0.34.4 | 固定 SHA 原始文件；浅克隆 checkout 中断，不能视为完整工作树；同 SHA | Apache-2.0；package 依赖闭包尚未再分发审核 |
| 04_strands-harness · [strands-agents/harness-sdk](https://github.com/strands-agents/harness-sdk) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\04_strands-harness\repo` | main / `8ba04f70af542e41aadbc2eb8093b1a07df5ec96` / 8ba04f7 | clean；远端 `59f126f82a6b8118e35fd2f5a38c892ab4725a91` | Apache-2.0；LICENSE.APACHE + NOTICE；harness-py/ts 子包 NOTICE |
| 15_concordia · [google-deepmind/concordia](https://github.com/google-deepmind/concordia) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\15_concordia\repo` | main / `b71d202750e23444ce1bf28d9f114bcd88aa41db` / b71d202 | clean；同 SHA | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 16_agentsociety · [tsinghua-fib-lab/AgentSociety](https://github.com/tsinghua-fib-lab/AgentSociety) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\16_agentsociety\repo` | main / `8cc5bb9a9c27d039ec5519375db9d73ccf508cba` / agentsociety2-v2.9.3 | clean；同 SHA | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 17_OASIS · [camel-ai/oasis](https://github.com/camel-ai/oasis) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\17_OASIS\repo` | main / `affe52e8dcbc70bba0a4162bfea1057aa5df9316` / affe52e | clean；同 SHA | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 21_graphiti · [getzep/graphiti](https://github.com/getzep/graphiti) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\21_graphiti\repo` | main / `3c427640abf909f12f71f963fce15eb514a3c493` / 3c42764 | clean；远端 `b7fc30f2a1e288266760640164a37bdb7d1d0f28` | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 18_sotopia · [sotopia-lab/sotopia](https://github.com/sotopia-lab/sotopia) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\18_sotopia\repo` | main / `a0aaafb440e570e5e61b7c44a44e5e417c545383` / a0aaafb | clean；同 SHA | MIT 代码；数据与模型不随根许可自动授权 |
| 13_ACE · [ace-agent/ace](https://github.com/ace-agent/ace) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\13_ACE\repo` | main / `82709de050e1db6e6ef2f07bcb0393560b94992a` / 82709de | clean；同 SHA | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 25_phoenix · [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\25_phoenix\repo` | main / `9212a42a512d08de7e2a8e81b15821f4483812ce` / 9212a42 | clean；同 SHA | Elastic License 2.0；托管限制、notice 与修改标记 |
| 26_langfuse · [langfuse/langfuse](https://github.com/langfuse/langfuse) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\26_langfuse\repo` | main / `f75c661dbe8c6b85523c81486b39e8403ac2c141` / f75c661 | clean；远端 `74512fcf585e662035b9f7fac99330b23b5cadd6` | MIT，排除 ee/、web/src/ee/、worker/src/ee/；EE 商业许可 |
| 22_MCP · [modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\22_MCP\repo` | main / `75db1e987cbbba6d170315dc99d0dfc440754aef` / 75db1e9 | clean；同 SHA | 实际 LICENSE 为 MIT/Apache-2.0 过渡；非规范文档 CC-BY-4.0 |
| 23_A2A · [a2aproject/A2A](https://github.com/a2aproject/A2A) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\23_A2A\repo` | main / `fe182ee3c053d2e6a3ad2576c959fa5f7d8b5d07` / fe182ee | clean；同 SHA | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 24_ACP · [agentclientprotocol/agent-client-protocol](https://github.com/agentclientprotocol/agent-client-protocol) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\24_ACP\repo` | main / `2bc773bc77d245c72971fbb3263b51484faa9ee3` / 2bc773b | clean；远端 `cae7aca7f07cefd59da2a3cb374933cb623a2959` | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| otel · [open-telemetry/opentelemetry-specification](https://github.com/open-telemetry/opentelemetry-specification) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\_external\_audit\opentelemetry-specification` | 远端 HEAD 文件快照 / `d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b` / 未核发布版本 | 原始文件快照；raw 固定 SHA；无完整 checkout | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 06_ADAS · [ShengranHu/ADAS](https://github.com/ShengranHu/ADAS) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\06_ADAS\repo` | main / `2702bee8fefda42255efc5be9f60e3bd3db96ae4` / 2702bee | clean；同 SHA | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 07_AgentSquare · [tsinghua-fib-lab/AgentSquare](https://github.com/tsinghua-fib-lab/AgentSquare) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\07_AgentSquare\repo` | main / `8f5b3fe5d8a32f9b59d20370823bef2a2c86928c` / 8f5b3fe | clean；同 SHA | 代码许可不作为 A/B/C admission，D only；数据/LFS 未审核 |
| 08_AFlow · [FoundationAgents/AFlow](https://github.com/FoundationAgents/AFlow) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\08_AFlow\repo` | main / `3f457218fc716093fe53f6df8a5d5e6379d66346` / 3f45721 | clean；同 SHA | MIT（仅 D） |
| 19_sotopia-rl · [sotopia-lab/sotopia-rl](https://github.com/sotopia-lab/sotopia-rl) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\19_sotopia-rl\repo` | main / `2ebb14ea4802c4b8cb3def40e9a0f9a0398265c5` / 2ebb14e | clean；同 SHA | 仅 D；根许可/数据/训练产物需进入采用阶段再审核 |
| 20_ALSO · [Babylonehy/ALSO](https://github.com/Babylonehy/ALSO) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\20_ALSO\repo` | main / `20cefbee0918840707569b22dc7f4ad6d98b33ba` / 20cefbe | clean；同 SHA | 仅 D；根许可/数据/训练产物需进入采用阶段再审核 |
| 10_RSIHub · [simple-agent-lab/RSIHub](https://github.com/simple-agent-lab/RSIHub) | `D:\调研\RSI_AI训AI\codebase\10_RSIHub\repo` | main / `bb8f4ddde8f6c301bbf0a976af01747d11b8dab1` / bb8f4dd | clean；远端 `64491da6b7fcea2acf758333ca39df4ca2221182` | 仅 D；根许可/数据/训练产物需进入采用阶段再审核 |
| 22_autoharness · [kayba-ai/autoharness](https://github.com/kayba-ai/autoharness) | `D:\调研\RSI_AI训AI\codebase\22_autoharness\repo` | main / `7cfd52e12fe1d72a3e321da91a56433edfcb37c5` / 7cfd52e | clean；同 SHA | MIT |
| 20_OpenEvolve · [algorithmicsuperintelligence/openevolve](https://github.com/algorithmicsuperintelligence/openevolve) | `D:\调研\RSI_AI训AI\codebase\20_OpenEvolve\repo` | main / `411fb59c886c18704caaffb611e17cf9e7d824d2` / v0.3.2 | clean；远端 `4f4b0c4f40906f434d64fe5089aff24e927f7e24` | Apache-2.0；保留适用 LICENSE/NOTICE；第三方、数据与模型独立审核 |
| 05_R-Zero · [Chengsong-Huang/R-Zero](https://github.com/Chengsong-Huang/R-Zero) | `D:\调研\RSI_AI训AI\codebase\05_R-Zero\repo` | main / `5699329d018d79535b7910abdedf5a6eebf355fd` / 5699329 | clean；同 SHA | 仅 D；根许可/数据/训练产物需进入采用阶段再审核 |
| 13_verl · [verl-project/verl](https://github.com/verl-project/verl) | `D:\调研\RSI_AI训AI\codebase\13_verl\repo` | main / `1252cc71aa5bd82e5604322064d69bfe6454c660` / 1252cc7 | clean；远端 `8718ca30a3f002f93b7c4fd99b9b2506718681bc` | 仅 D；根许可/数据/训练产物需进入采用阶段再审核 |
| 14_VerlTool · [TIGER-AI-Lab/verl-tool](https://github.com/TIGER-AI-Lab/verl-tool) | `D:\调研\RSI_AI训AI\codebase\14_VerlTool\repo` | main / `383d4b1539ba387f94c3a117d3edc06b467c09d1` / 383d4b1 | clean；同 SHA | 仅 D；根许可/数据/训练产物需进入采用阶段再审核 |
| archive_wt · [letta-ai/letta](https://github.com/letta-ai/letta) | `D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\05_letta\archive_wt` | detached HEAD / `56ba9c25552605eec89de8ed3dc6394b625c1993` / 56ba9c2 | clean；远端 `5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a` | Apache-2.0；retired V1；数据库/数据依赖独立审核 |

旧 Letta archive：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\05_letta\archive_wt`，HEAD `56ba9c25552605eec89de8ed3dc6394b625c1993`，服务入口 `letta/services/block_manager.py`；[固定源码](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/block_manager.py)。退休 V1，不替代当前 Letta Code，也不代表原始 MemGPT paper snapshot。

## 主结论证据

### E001 · 01_deepseek-harness / REQ-RUNTIME

实际观察：Python SDK 启动 stdio JSON-RPC 子进程；高层 session/run 汇集事件。server 仅分派三个 request：initialize、session/prompt、shutdown（session 在 prompt 路径创建）；session 创建新 agent。没有完整公共 resume/cancel/fork/catch-up；initialize 的 provider/model 是 worker 级配置。超时只结束本地等待，队列无界。不能把私有 _launch_args 当稳定部署入口。

- [python/sdk/src/deepseek_harness/client.py:39](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/python/sdk/src/deepseek_harness/client.py#L39) · `class HarnessClient`。
- [python/sdk/src/deepseek_harness/api.py:14](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/python/sdk/src/deepseek_harness/api.py#L14) · `class DeepSeekHarness`。
- [packages/sdk/server/src/server.ts:248](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/sdk/server/src/server.ts#L248) · `async handleRequest`。

上游测试/示例：python/sdk/tests/test_client.py。运行：**29 通过（UTF-8）；初次 26 通过、3 编码失败；V02**；目标集成未运行。影响：R01；A 官方 SDK + B RuntimePort；C01 小补丁，P0 超界则换 Strands。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E002 · 01_deepseek-harness / REQ-REPLAY

实际观察：SessionStore 按 event seq fork，复制 inclusive prefix 并补 end-seed/open-turn closers。内部 agent loop 有排队和 AbortSignal。事件分支不是环境/工具/plugin 内存快照，公共 Python SDK 不暴露这些完整生命周期。

- [packages/core/session/src/index.ts:1251](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/core/session/src/index.ts#L1251) · `  fork(`。
- [packages/core/session/src/fork.ts:21](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/core/session/src/fork.ts#L21) · `function buildForkSeed`。
- [packages/core/agent-loop/src/agent.ts:98](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/core/agent-loop/src/agent.ts#L98) · `class ReactLoopAgent`。

上游测试/示例：packages/core/session/tests。运行：**未运行**；目标集成未运行。影响：R01/R08；区分内部 API 与 SDK；branch 需全域 manifest。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E003 · 01_deepseek-harness / REQ-EVENT

实际观察：单 handle 串行 mutation chain、live write-behind，200ms 批等待；scanner 保留连续合法前缀，尾部半行可恢复、已提交 turn/end 后损坏拒绝。跨进程 kernel lock：POSIX flock/Windows semaphore，活进程不凭 TTL 抢锁。generation/migration 有验证路径，不能宣称任意版本均可迁移或每条通知已 fsync。

- [packages/session/session-persistence-jsonl/src/storage.ts:85](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/session/session-persistence-jsonl/src/storage.ts#L85) · `class JsonlSessionHandle`。
- [packages/session/session-persistence-jsonl/src/format.ts:386](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/session/session-persistence-jsonl/src/format.ts#L386) · `class SessionLogScanner`。
- [packages/session/session-persistence-jsonl/src/lease.ts:58](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/session/session-persistence-jsonl/src/lease.ts#L58) · `class SessionWriteLease`。
- [packages/session/session-persistence-jsonl/src/generation.ts:112](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/session/session-persistence-jsonl/src/generation.ts#L112) · `JsonlGenerationSourceChangedError`。

上游测试/示例：packages/session/session-persistence-jsonl/tests/jsonl.spec.ts; packages/session/session-persistence-jsonl/tests/lease.spec.ts; packages/session/session-persistence-jsonl/tests/v3-restart-migration.spec.ts。运行：**未运行**；目标集成未运行。影响：R01/R03；保留原生日志，canonical ingestion 单独持久化。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E004 · 01_deepseek-harness / REQ-RUNTIME

实际观察：Cordis lifecycle effect 收集 disposer、逆序清理，支持依赖生命周期；不代表网络调用回滚、不证明任意 plugin 热替换状态兼容。模型/tool runtime 继续由 DSH 承担，Actio 仅注入域上下文及语义事件。

- [vendor/cordis/src/fiber.ts:77](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/vendor/cordis/src/fiber.ts#L77) · `effect(`。

上游测试/示例：vendor/cordis（本轮未单独执行其测试）。运行：**未运行**；目标集成未运行。影响：R02；A/B plugin；运行中禁改 pin，L2 候选新 worker。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E005 · 01_deepseek-harness / REQ-RUNTIME

实际观察：local sandbox 文档与实现声明平台差异：Linux bwrap/Landlock、macOS Seatbelt、Windows restricted token/ACL；Windows 读限制不完整及 hardlink 边界。runtime wheel 文档列 Windows x64，内含 node/sidecar/Office closure；本机未安装或运行正式 wheel。

- [packages/sandbox/sandbox-local/src/index.ts:3](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/sandbox/sandbox-local/src/index.ts#L3) · `Windows`。
- [python/sdk-runtime/README.md:11](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/python/sdk-runtime/README.md#L11) · `Windows`。

上游测试/示例：packages/sandbox/sandbox-local（未运行 native 测试）。运行：**未运行**；目标集成未运行。影响：R01/R12；平台验证门槛，禁止把普通 subprocess 或 Windows partial enforcement 当 L2 隔离。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E006 · 01_deepseek-harness / REQ-PROTOCOL

实际观察：DSH 使用 @modelcontextprotocol/client 2.0.0。stdio 清理环境，HTTP 接收 headers；未接互动 OAuth authProvider。listTools 注册后 callTool 传 signal/timeout；连接重试不等于安全重试有副作用工具。resources 另一个 plugin；多种内容块并不都完整转成模型可用内容。

- [packages/mcp/mcp-client/src/transport.ts:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/mcp/mcp-client/src/transport.ts#L1) · `模块`。
- [packages/mcp/mcp-client/src/tools.ts:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/mcp/mcp-client/src/tools.ts#L1) · `模块`。
- [packages/mcp/mcp-client/src/connection.ts:1](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/packages/mcp/mcp-client/src/connection.ts#L1) · `模块`。

上游测试/示例：由 packages/mcp 下 tests 核查；见协议映射。运行：**未运行**；目标集成未运行。影响：R02；B 工具权限/效果账本；MVP stdio 只读工具，HTTP OAuth 后置。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E007 · 02_Raven / REQ-RUNTIME

实际观察：Host registry 是进程内 dispatch；router 依赖 embedding classifier/benchmark cache。DAG runner 写 manifest 并补 terminal status，store 依赖 workspace backend；坏 registry 会警告后空表，部分 memory 记录失败不使节点失败。AdjudicationDesk/Outbox 有取消与报告重试。真实产品编排能力存在，但不是 Actio 的持久社会实验控制面。

- [raven/agent/subagent/registry.py:1](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/raven/agent/subagent/registry.py#L1) · `模块`。
- [raven/routing/router.py:20](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/raven/routing/router.py#L20) · `class ModelRouter`。
- [raven/agent/subagent/dag_runner.py:1955](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/raven/agent/subagent/dag_runner.py#L1955) · `async def _finalize`。
- [raven/agent/subagent/dag_store.py:126](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/raven/agent/subagent/dag_store.py#L126) · `async def read_registry`。
- [raven/agent/subagent/dag_adjudication.py:100](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/raven/agent/subagent/dag_adjudication.py#L100) · `class AdjudicationDesk`。

上游测试/示例：tests 中 DAG/registry/routing 测试存在，未跑 root suite。运行：**未运行**；目标集成未运行。影响：R10；F root fork；D DAG/host 设计，不把它引入另一个 identity owner。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E008 · 02_Raven / REQ-EVOLUTION

实际观察：paired_lift promoted = candidate_mean > control_mean；credited_2sigma 独立。n=1 或零方差可给 inf；缺 task 按 0。策略加 full mean 非回归，不将 2σ 强制准入；infra attempts 留在 gate 分母。evolver README 计划退役该树，存在后续维护风险。

- [evolver/orchestrator/gates/paired.py:61](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/orchestrator/gates/paired.py#L61) · `def paired_lift`。
- [evolver/orchestrator/gates/strategies.py:46](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/orchestrator/gates/strategies.py#L46) · `class PairedTwoSigmaGate`。
- [evolver/orchestrator/gates/pipeline.py:1](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/orchestrator/gates/pipeline.py#L1) · `模块`。
- [evolver/orchestrator/scoring.py:35](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/orchestrator/scoring.py#L35) · `class TaskEval`。
- [evolver/README.md:3](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/README.md#L3) · `retir`。

上游测试/示例：tests/test_evolver_gates.py; tests/test_evolver_scoring.py。运行：**37 通过；V03**；目标集成未运行。影响：R06/C02；保留配对诊断结构，改四态 outcome/缺失处理/小样本/独立准入。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E009 · 02_Raven / REQ-EVOLUTION

实际观察：WHERE×WHY elite 与重组候选过滤真实实现。consider 可将超过固定 vanilla 的候选入 bank，即使未升当前 baseline；仅 promoted 更新部分 parent metadata。save 吞 OSError，坏 JSON load 清空。不能作为完整失败 lineage 或可靠 canonical archive。

- [evolver/orchestrator/archive.py:218](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/orchestrator/archive.py#L218) · `class GsmeArchive`。
- [evolver/tree/node.py:520](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/tree/node.py#L520) · `class HarnessNode`。
- [evolver/orchestrator/gates/policy.py:49](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/evolver/orchestrator/gates/policy.py#L49) · `class CandidateOutcome`。

上游测试/示例：本次在 tests/evolver 检索未找到直接覆盖 GsmeArchive/eligible_elites 的专门测试；gates/scoring fixture 可作后续输入参考，不能视为 archive 测试通过。运行：**未运行**；目标集成未运行。影响：R07/C03；拆 selector/descriptor，持久化和完整 lineage 由 canonical store 持有。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E010 · 10_meta-harness / REQ-EVAL

实际观察：onboarding 明确固定 base model、隔离 final test、完整历史。实验 controller AST 检查后写候选源码并调用 Harbor 子进程，超时/失败 reward 路径混入结果；AST 过滤不是隔离。研究示例不等于安装即用通用 evolution service。

- [ONBOARDING.md:15](https://github.com/stanford-iris-lab/meta-harness/blob/8123ccabe2b19fa1123090b2e5f1bacc20963ce8/ONBOARDING.md#L15) · `Keep final test`。
- [experimental/harbor_meta_harness/controller.py:144](https://github.com/stanford-iris-lab/meta-harness/blob/8123ccabe2b19fa1123090b2e5f1bacc20963ce8/experimental/harbor_meta_harness/controller.py#L144) · `def validate_source`。
- [experimental/harbor_meta_harness/controller.py:264](https://github.com/stanford-iris-lab/meta-harness/blob/8123ccabe2b19fa1123090b2e5f1bacc20963ce8/experimental/harbor_meta_harness/controller.py#L264) · `def evaluate_source`。
- [reference_examples/text_classification/meta_harness.py:1](https://github.com/stanford-iris-lab/meta-harness/blob/8123ccabe2b19fa1123090b2e5f1bacc20963ce8/reference_examples/text_classification/meta_harness.py#L1) · `模块`。

上游测试/示例：experimental/harbor_meta_harness/tests/test_controller.py。运行：**阻塞：harbor 缺失，收集退出 2；V04**；目标集成未运行。影响：R11；D onboarding/evaluation envelope；不为薄结果格式引入 Harbor 执行闭包。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E011 · 11_DGM / REQ-EVOLUTION

实际观察：outer loop metadata.jsonl/archive parent selection → self_improve_step → Docker/SWE/code benchmark evaluation。恢复 POSIX cp -r，指标依赖 resolved/empty_patch；best 分支按 accuracy 升序取前 K，需专项复核不能复制为最佳选择。Docker 使用不构成经过验证的安全边界。

- [DGM_outer.py:50](https://github.com/jennyzzt/dgm/blob/a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2/DGM_outer.py#L50) · `def choose_selfimproves`。
- [DGM_outer.py:15](https://github.com/jennyzzt/dgm/blob/a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2/DGM_outer.py#L15) · `def initialize_run`。
- [self_improve_step.py:1](https://github.com/jennyzzt/dgm/blob/a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2/self_improve_step.py#L1) · `模块`。

上游测试/示例：研究运行需模型、Docker、benchmark；未找到可独立满足 Actio 的现成测试链。运行：**未运行**；目标集成未运行。影响：R11；D archive/parent selection；F 整体 coding root。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E012 · 05_letta / REQ-MEMORY

实际观察：旧 Letta main 重定向当前 letta-code；archive 是 retired V1 服务，不能称其等于原始 MemGPT 论文实现。旧 BlockManager 依赖 DB/session/actor 权限体系，非可直接拷贝无状态 memory library。

- [README.md:5](https://github.com/letta-ai/letta/blob/5bcdd177d70fa2b31a754cfcd801e77b2e1ab16a/README.md#L5) · `letta-code`。

上游测试/示例：旧 BlockManager 是历史服务源码而非测试；独立 archive_wt 路径与符号见本项补充；未运行。运行：**未运行**；目标集成未运行。影响：R04；F 用旧 Letta server 作第二 memory owner；D 历史模式。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

历史源码补充：[block_manager.py:53](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/block_manager.py#L53) · BlockManager；版本/本地路径继承 archive_wt 资产行（detached HEAD、clean）。

### E013 · letta-code / REQ-MEMORY

实际观察：当前 LocalBackend extends HeadlessBackend，LocalStore 管 agent/conversation/messages，存在 cloud/API 与本地模式。git MemFS 路径、system prompt compilation、settings/current agent 深度耦合。claimMemoryOperation 序列化 harness memory writer，主 agent 编辑不都受同锁保护。Windows 自动 dreaming 默认受限；不能因此称无本地后端。

- [src/backend/local/local-backend.ts:178](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/backend/local/local-backend.ts#L178) · `class LocalBackend`。
  raw SHA-256：`a100906dd1e1dae11800819f427eeba21b7cbe224a07a843c8151c7afd4fc32a`。
- [src/backend/local/local-store.ts:331](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/backend/local/local-store.ts#L331) · `class LocalStore`。
  raw SHA-256：`65481a23bb29413722631d66ad7f7d626821bcd39b13a8243593014ed8695bb5`。
- [src/agent/memory-runtime.ts:13](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/agent/memory-runtime.ts#L13) · `isActiveMemfsEnabled`。
  raw SHA-256：`54ff0262bd947aa865f9e47cedba8c98b34bdc3d2b56aeae19749f8e9be9159b`。
- [src/agent/memory-operation.ts:35](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/agent/memory-operation.ts#L35) · `claimMemoryOperation`。
  raw SHA-256：`ad2ed4fe2a5db068748ca653b7e9e94a337685f1d114ef3b6bbfef6d18ba514c`。
- [src/agent/memory-filesystem.ts:1](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/agent/memory-filesystem.ts#L1) · `模块`。
  raw SHA-256：`a2884fd2e467af615a7a56584ccf9df520e470c6eef39930a98ec7dc10bfe628`。

上游测试/示例：从树找到 src/agent memory/skills 测试；raw 文件未安装执行。运行：**未运行**；目标集成未运行。影响：R04；D git-memory/lease/consolidation；F 完整 Letta 作为 DSH 旁第二权威运行时。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E014 · letta-code / REQ-RUNTIME

实际观察：mods 维护 provider/tool/permission 注册与 disposer；hooks spawn command 且有 timeout。skill-sources 枚举 bundled/global/agent/project，memory/skill 加载依赖当前 backend 语境；这些 seam 存在但不是已证明可脱离 Letta 的插件基础库。

- [src/mods/mod-engine.ts:218](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/mods/mod-engine.ts#L218) · `registerCapabilitiesGlobally`。
  raw SHA-256：`dcdd982ec33740e3d1f9346009332526d881997693647a4e17a0998d67ae23ef`。
- [src/mods/event-emitter.ts:27](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/mods/event-emitter.ts#L27) · `emitModEvent`。
  raw SHA-256：`b1ca8a17af668fca540594bf4277b50afaed6919eae3fcdb59adfb49b3a61cc1`。
- [src/hooks/executor.ts:130](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/hooks/executor.ts#L130) · `executeCommandHook`。
  raw SHA-256：`93545f6074c544b65b4e57154d9891c2bbf57e06acc69fff76ef645391bdd5c0`。
- [src/agent/skill-sources.ts:1](https://github.com/letta-ai/letta-code/blob/f898fda60932b34ddbcfd389ea414515b0a5d272/src/agent/skill-sources.ts#L1) · `模块`。
  raw SHA-256：`09ee929b4ef62b0311b7accd6141d5643c4cbae60c73a79d0c7b209a4e5c2734`。

上游测试/示例：src/hooks/executor.test.ts; src/mods/mod-engine.test.ts（Git tree 确认，未取回/未跑）。运行：**未运行**；目标集成未运行。影响：R04；D hooks/memory lifecycle；不另造全 Letta adapter。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E015 · 04_strands-harness / REQ-RUNTIME

实际观察：Python Agent 有模型/工具循环、取消与 invocation concurrency 策略；harness interventions 支持 off/ask/smart/Cedar。file manager 单文件随机临时名+os.replace、symlink 检查、损坏 JSON 抛 SessionException；非跨全部状态事务。hook 事件支持字段改写/interrupt，不等于任意社会域事件已有。

- [harness-py/src/strands_harness/interventions.py:83](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/harness-py/src/strands_harness/interventions.py#L83) · `resolve_interventions`。
- [strands-py/src/strands/agent/agent.py:180](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/strands-py/src/strands/agent/agent.py#L180) · `class Agent`。
- [strands-py/src/strands/session/file_session_manager.py:132](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/strands-py/src/strands/session/file_session_manager.py#L132) · `def _write_file`。

上游测试/示例：strands-py/tests; harness-py/tests（未跑）。运行：**未运行**；目标集成未运行。影响：R01 备选 B；如切换保留 Python control，改 Python worker，不自写 loop。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E016 · 04_strands-harness / REQ-REPLAY

实际观察：TS snapshot_latest 与 immutable_history，默认 invocation 后保存，可选 message/trigger；tmp 路径固定且 rename，错误包装 SessionError。与 Python 的 repository/messages 模型和 tempfile 不同，不能声称 Python/TS 恢复或并发语义自动等价。

- [strands-ts/src/session/session-manager.ts:124](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/strands-ts/src/session/session-manager.ts#L124) · `class SessionManager`。
- [strands-ts/src/session/file-storage.ts:168](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/strands-ts/src/session/file-storage.ts#L168) · `private async _writeJSON`。
- [harness-ts/src/interventions.ts:1](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/harness-ts/src/interventions.ts#L1) · `模块`。

上游测试/示例：strands-ts/src/session 下对应 tests；未运行。运行：**未运行**；目标集成未运行。影响：R01；Python 备选更贴近实验侧，需 contract conformance 再替换。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E017 · 15_concordia / REQ-ENV

实际观察：Engine/Entity 当前 seam：make_observation→next_acting→Entity.act(ActionSpec)→GM resolve。resolve 返回 None，GM 通过 observation/log 产生事实，不能把它当 Outcome DTO。GM 决定行动资格与裁决，可另有模型成本。

- [concordia/environment/engine.py:30](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/concordia/environment/engine.py#L30) · `class Engine`。
- [concordia/typing/entity.py:204](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/concordia/typing/entity.py#L204) · `class Entity`。
- [concordia/environment/engines/sequential.py:148](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/concordia/environment/engines/sequential.py#L148) · `def resolve`。
- [concordia/environment/engines/sequential.py:223](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/concordia/environment/engines/sequential.py#L223) · `def run_loop`。

上游测试/示例：concordia/environment/engines/sequential_test.py; concordia/environment/engine_test.py。运行：**未运行**；目标集成未运行。影响：R05；B 第一真实环境；external Entity 桥接 DSH intent，clock/world 留环境。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E018 · 15_concordia / REQ-REPLAY

实际观察：checkpoint 仅保存有 prefab config 的 EntityWithComponents/GM、raw_log、counter；简单 external Entity 会跳过。restore deep copy，但明确不恢复 engine cursors，不保证任意组件/模型/外部服务确定性。

- [concordia/prefabs/simulation/generic.py:337](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/concordia/prefabs/simulation/generic.py#L337) · `def make_checkpoint_data`。
- [concordia/prefabs/simulation/generic.py:546](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/concordia/prefabs/simulation/generic.py#L546) · `def load_from_checkpoint`。

上游测试/示例：concordia/prefabs/simulation/checkpoint_test.py。运行：**未运行**；目标集成未运行。影响：R08；MVP 默认 epoch 边界重执行；snapshot/branch capability 必须诚实为 partial/false。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E019 · 16_agentsociety / REQ-ENV

实际观察：v2.9.3 Society.step 同步 t，Ray batch 任务 gather，聚合 agent failure 后 raise，成功再 EnvRouter.step/时钟前进/to_workspace。agent 文件可能在总步失败前写入；非原子 tick。ServiceProxy/EnvRouter 是环境调用 seam，workspace resume 不是完整并发队列回放。

- [packages/agentsociety2/agentsociety2/society/society.py:768](https://github.com/tsinghua-fib-lab/AgentSociety/blob/8cc5bb9a9c27d039ec5519375db9d73ccf508cba/packages/agentsociety2/agentsociety2/society/society.py#L768) · `async def step`。
- [packages/agentsociety2/agentsociety2/env/router_base.py:1](https://github.com/tsinghua-fib-lab/AgentSociety/blob/8cc5bb9a9c27d039ec5519375db9d73ccf508cba/packages/agentsociety2/agentsociety2/env/router_base.py#L1) · `模块`。
- [packages/agentsociety2/agentsociety2/agent/service_proxy.py:1](https://github.com/tsinghua-fib-lab/AgentSociety/blob/8cc5bb9a9c27d039ec5519375db9d73ccf508cba/packages/agentsociety2/agentsociety2/agent/service_proxy.py#L1) · `模块`。

上游测试/示例：packages/agentsociety2/tests（范围详见矩阵，未运行 Ray 服务）。运行：**未运行**；目标集成未运行。影响：R05；B P2 第二 adapter，要求 pending、batch barrier、logical clock、failed tick reconcile。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E020 · 17_OASIS / REQ-ENV

实际观察：reset 启动 platform task；step 更新推荐后 gather actions，LLMAction 有并发限流，ManualAction 可避免第二 solver loop，但 interview 分支会触发模型。step 返回 None；平台/channel/DB 自有生命周期，close 发送 EXIT 并 await。DB dump 不捕获全部队列/RNG。

- [oasis/environment/env.py:48](https://github.com/camel-ai/oasis/blob/affe52e8dcbc70bba0a4162bfea1057aa5df9316/oasis/environment/env.py#L48) · `class OasisEnv`。
- [oasis/social_platform/platform.py:53](https://github.com/camel-ai/oasis/blob/affe52e8dcbc70bba0a4162bfea1057aa5df9316/oasis/social_platform/platform.py#L53) · `class Platform`。

上游测试/示例：examples 下 scripts；未运行平台或模型。运行：**未运行**；目标集成未运行。影响：R05；B P2 compatibility；首期不引入 OASIS agent loop。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E021 · 21_graphiti / REQ-MEMORY

实际观察：EntityEdge 包含 fact/episodes/valid_at/invalid_at/expired_at/reference_time；Graphiti 可注入 graph_driver、LLM、embedder，默认 Neo4j/OpenAI。add_episode 检索/抽取需模型，group_ids 搜索参数可省，namespace API 分组不是实验分支隔离，UUID 查找还需 owner 校验。

- [graphiti_core/edges.py:263](https://github.com/getzep/graphiti/blob/3c427640abf909f12f71f963fce15eb514a3c493/graphiti_core/edges.py#L263) · `class EntityEdge`。
- [graphiti_core/graphiti.py:137](https://github.com/getzep/graphiti/blob/3c427640abf909f12f71f963fce15eb514a3c493/graphiti_core/graphiti.py#L137) · `class Graphiti`。

上游测试/示例：tests 中 grouping/search_security；未运行图服务/LLM。运行：**未运行**；目标集成未运行。影响：R04；B 可选关系投影，MVP SQLite 足够；所有读写强制 namespace。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E022 · 18_sotopia / REQ-EVAL

实际观察：异步结构化 LLM evaluator 实现；同步入口抛 NotImplementedError。过滤 did nothing，按 response.values 顺序枚举 agent_N；异常打印日志返回 []。必须固定身份映射和全维度完整性，空结果记 infra_failure，不能按零分或成功处理。

- [sotopia/envs/evaluators.py:162](https://github.com/sotopia-lab/sotopia/blob/a0aaafb440e570e5e61b7c44a44e5e417c545383/sotopia/envs/evaluators.py#L162) · `class EpisodeLLMEvaluator`。

上游测试/示例：tests/envs/test_evaluators.py。运行：**未运行**；目标集成未运行。影响：R09；B 社会评委，使用自有 synthetic scenario；judge 校准和 Redis import closure 待验。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E023 · 13_ACE / REQ-MEMORY

实际观察：curate 调 LLM 产生 JSON 操作并合并 playbook；propose_operations/aggregate_operations 是候选 seam；异常可能返回原文本。playbook delta 对 context policy 有价值，不等于带来源/权限/版本的社会记忆。 实际 apply_curator_operations 仅处理 ADD；UPDATE/MERGE/DELETE/CREATE_META 仍为 TODO，不声称完整 delta CRUD。

- [ace/core/curator.py:18](https://github.com/ace-agent/ace/blob/82709de050e1db6e6ef2f07bcb0393560b94992a/ace/core/curator.py#L18) · `class Curator`。
- [playbook_utils.py:96](https://github.com/ace-agent/ace/blob/82709de050e1db6e6ef2f07bcb0393560b94992a/playbook_utils.py#L96) · `def apply_curator_operations`。

上游测试/示例：仓库示例；本轮不宣称测试覆盖。运行：**未运行**；目标集成未运行。影响：R11；D delta 提案，暂不 C，避免把字符串解析器变成领域存储。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E024 · 25_phoenix / REQ-EVENT

实际观察：OTLP/trace 与 dataset/eval 路由有实现；SQLAlchemy DB、queue/background ingestion。ELv2 限制向第三方提供具有实质功能的托管服务，需保留 notice/修改标记；内部观测可考虑，不能标为无限制 MIT 开源。 post_traces 只接 x-protobuf，支持 gzip/deflate，满队列503；解析后交 background _add_spans/enqueue_span并先返200，不能当域durability ACK。

- [src/phoenix/server/api/routers/v1/traces.py:470](https://github.com/Arize-ai/phoenix/blob/9212a42a512d08de7e2a8e81b15821f4483812ce/src/phoenix/server/api/routers/v1/traces.py#L470) · `async def post_traces`。
- [src/phoenix/server/api/routers/v1/experiment_evaluations.py:77](https://github.com/Arize-ai/phoenix/blob/9212a42a512d08de7e2a8e81b15821f4483812ce/src/phoenix/server/api/routers/v1/experiment_evaluations.py#L77) · `async def upsert_experiment_evaluation`。
- [src/phoenix/server/api/routers/v1/datasets.py:1](https://github.com/Arize-ai/phoenix/blob/9212a42a512d08de7e2a8e81b15821f4483812ce/src/phoenix/server/api/routers/v1/datasets.py#L1) · `模块`。
- [LICENSE:1](https://github.com/Arize-ai/phoenix/blob/9212a42a512d08de7e2a8e81b15821f4483812ce/LICENSE#L1) · `模块`。

上游测试/示例：tests/unit/trace/test_otel.py；未部署。运行：**未运行**；目标集成未运行。影响：R13；B 内部 viewer 备选；F 未获许可的对外托管。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E025 · 26_langfuse / REQ-EVENT

实际观察：OTLP API 验证项目权限、大小/gzip/content-type/ID；畸形 batch 可能整体拒绝。dataset/scores 服务是真实投影能力。compose 包含 web/worker、ClickHouse、MinIO、Redis、Postgres；不是天然轻量。MIT 根排除 ee、web/src/ee、worker/src/ee，EE 另有商业许可。 processOtelIngestion 将完整 batch 交 publishToOtelIngestionQueue，经 S3/queue/worker 异步处理；接收 ACK 不是 canonical 事实完成。

- [web/src/pages/api/public/otel/v1/traces/index.ts:18](https://github.com/langfuse/langfuse/blob/f75c661dbe8c6b85523c81486b39e8403ac2c141/web/src/pages/api/public/otel/v1/traces/index.ts#L18) · `processOtelIngestion`。
- [web/src/server/otel/processOtelIngestion.ts:46](https://github.com/langfuse/langfuse/blob/f75c661dbe8c6b85523c81486b39e8403ac2c141/web/src/server/otel/processOtelIngestion.ts#L46) · `async function processOtelIngestion`。
- [web/src/pages/api/public/datasets/index.ts:2](https://github.com/langfuse/langfuse/blob/f75c661dbe8c6b85523c81486b39e8403ac2c141/web/src/pages/api/public/datasets/index.ts#L2) · `createAuthedProjectAPIRoute`。
- [docker-compose.yml:17](https://github.com/langfuse/langfuse/blob/f75c661dbe8c6b85523c81486b39e8403ac2c141/docker-compose.yml#L17) · `clickhouse`。
- [LICENSE:1](https://github.com/langfuse/langfuse/blob/f75c661dbe8c6b85523c81486b39e8403ac2c141/LICENSE#L1) · `模块`。

上游测试/示例：web/src/__tests__/server/datasets-api.servertest.ts; web/src/__tests__/server/scores-api-v3.servertest.ts。运行：**未运行**；目标集成未运行。影响：R13；B 社区 viewer 主选 provisional，部署与许可证闭包 gate，canonical 数据不依赖 UI。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E026 · 22_MCP / REQ-PROTOCOL

实际观察：当前规范 2026-07-28：stateless per-request capability/version + server/discover；stdio JSON-RPC 与 StreamableHTTP POST/SSE。实际 client2.0.0 artifact 兼有 modern discovery/legacy initialize；取消 best effort，HTTP 关闭流不是外部效果撤销。LICENSE 为 MIT→Apache2 过渡、非规范 docs CC-BY4，不能只读 npm license 字段。 实际 SDK auto stdio 协商有 disposable sibling probe，再按 era 选择 modern 或 legacy；工具 server startup 不能假定只执行一次。

- [schema/2026-07-28/schema.ts:1](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/schema/2026-07-28/schema.ts#L1) · `模块`。
- [docs/specification/2026-07-28/basic/transports/index.mdx:1](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/docs/specification/2026-07-28/basic/transports/index.mdx#L1) · `模块`。

上游测试/示例：npm client artifact 静态核验，未执行互操作测试。运行：**未运行**；目标集成未运行。影响：R02；版本/transport/auth/resources/cancel 逐项记录，见 10。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E027 · 23_A2A / REQ-PROTOCOL

实际观察：AgentCard、Task、CancelTask、流式订阅和多传输结构；任务协作与 Actio 身份/世界/实验契约不等价。取消可拒绝，不提供跨模型/工具事务。

- [specification/a2a.proto:19](https://github.com/a2aproject/A2A/blob/fe182ee3c053d2e6a3ad2576c959fa5f7d8b5d07/specification/a2a.proto#L19) · `service A2AService`。

上游测试/示例：规范源码；未选 A2A SDK、未运行。运行：**未运行**；目标集成未运行。影响：R14；D/P2，MVP 不增内部 A2A RPC。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E028 · 24_ACP / REQ-PROTOCOL

实际观察：canonical 组织已迁移 agentclientprotocol；Agent Client Protocol 面向编辑器/client-agent。wire protocol version 与 Rust/schema package 版本分开；不是 AGNTCY 同名 ACP，不承担 simulation domain API。

- [schema/v1/schema.json:2344](https://github.com/agentclientprotocol/agent-client-protocol/blob/2bc773bc77d245c72971fbb3263b51484faa9ee3/schema/v1/schema.json#L2344) · `protocolVersion`。
- [README.md:1](https://github.com/agentclientprotocol/agent-client-protocol/blob/2bc773bc77d245c72971fbb3263b51484faa9ee3/README.md#L1) · `模块`。

上游测试/示例：规范 schema；未选 ACP SDK、未运行。运行：**未运行**；目标集成未运行。影响：R14；D/P2 client facade，MVP 暂缓。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E029 · otel / REQ-EVENT

实际观察：span 只有零/一个 parent，links 可多源；不能直接当完整领域 DAG。另读官方 opentelemetry-sdk 1.45.0 wheel：BatchSpanProcessor 有界 queue/drop，export timeout 参数未传 exporter；只作可重建 projection，不能承担事实可靠入库。

- [specification/trace/api.md:405](https://github.com/open-telemetry/opentelemetry-specification/blob/d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b/specification/trace/api.md#L405) · `Links`。
  raw SHA-256：`1962fe69fcda0ac07bedc17abd338e0de052b17805ae73cebeb14a7e10ae7bd9`。
- [specification/trace/sdk.md:75](https://github.com/open-telemetry/opentelemetry-specification/blob/d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b/specification/trace/sdk.md#L75) · `Batching processor`。
  raw SHA-256：`fb59a77b27dfdbdeaf78bb6947f4a54881c43cefab6c563fce0c9c9a40ff3f56`。

上游测试/示例：未安装 SDK；spec+wheel 静态，exporter 尚需 pin/集成验证。运行：**未运行**；目标集成未运行。影响：R03/R13；A SDK provisional、B 映射，保留 canonical 多父边。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E030 · 06_ADAS / REQ-EVOLUTION

实际观察：meta-agent 搜索生成 agent code，评估路径直接 exec；不具备可直接用于不可信 L2 的隔离。

- [_arc/search.py:177](https://github.com/ShengranHu/ADAS/blob/2702bee8fefda42255efc5be9f60e3bd3db96ae4/_arc/search.py#L177) · `exec(`。

上游测试/示例：研究任务例子未跑。运行：**未运行**；目标集成未运行。影响：R11；D search 思路；F 直接执行候选。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E031 · 07_AgentSquare / REQ-MEMORY

实际观察：模块化搜索含 memory prompt 代码，生成片段初始化 Chroma 并清旧目录；不提供稳定 branch namespace 与持久记忆迁移保证。

- [module_evolution/prompt_memory.py:1](https://github.com/tsinghua-fib-lab/AgentSquare/blob/8f5b3fe5d8a32f9b59d20370823bef2a2c86928c/module_evolution/prompt_memory.py#L1) · `模块`。

上游测试/示例：研究例子未跑、未取 LFS。运行：**未运行**；目标集成未运行。影响：R11；D 模块 seat，不导入生成执行路径。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E032 · 08_AFlow / REQ-EVOLUTION

实际观察：optimizer 从已有 rounds/experience 选择并产生 workflow graph，依赖 domain graph/operator/evaluator 路径；非共享持久 agent 运行时。

- [scripts/optimizer.py:32](https://github.com/FoundationAgents/AFlow/blob/3f457218fc716093fe53f6df8a5d5e6379d66346/scripts/optimizer.py#L32) · `class Optimizer`。

上游测试/示例：未跑模型搜索。运行：**未运行**；目标集成未运行。影响：R11；D Planning seat，P2 再评。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E033 · 19_sotopia-rl / REQ-EVAL

实际观察：direct attribution 使用 LLM 评价/文本归因；没有仅凭该函数就成立的干预识别或因果估计。

- [prompter/direct_attribution_function.py:1](https://github.com/sotopia-lab/sotopia-rl/blob/2ebb14ea4802c4b8cb3def40e9a0f9a0398265c5/prompter/direct_attribution_function.py#L1) · `模块`。

上游测试/示例：未跑训练/LLM。运行：**未运行**；目标集成未运行。影响：R08/R11；D 社会策略反馈，不能作为因果证明。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E034 · 20_ALSO / REQ-EVOLUTION

实际观察：EXP3 策略概率和 gamma 更新是真实 L0 adaptation 机制；SOTOPIA prompt space 绑定实验驱动，与 L1 版本准入是不同层。

- [experiments/also/core/bandits/exp3_bandit.py:19](https://github.com/Babylonehy/ALSO/blob/20cefbee0918840707569b22dc7f4ad6d98b33ba/experiments/also/core/bandits/exp3_bandit.py#L19) · `class EXP3Bandit`。

上游测试/示例：未跑模型实验。运行：**未运行**；目标集成未运行。影响：R11；D 低成本策略探索，MVP 不引新依赖。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E035 · 10_RSIHub / REQ-EVOLUTION

实际观察：frozen evaluator/archive/operator 接口与 driver 真实存在；远端 DSH seed/runner/recipe 有较多更新，当前 snapshot 不能冒充最新 DSH 已集成验证。

- [src/evolve/frozen/interfaces.py:1](https://github.com/simple-agent-lab/RSIHub/blob/bb8f4ddde8f6c301bbf0a976af01747d11b8dab1/src/evolve/frozen/interfaces.py#L1) · `模块`。
- [src/evolve/driver.py:1](https://github.com/simple-agent-lab/RSIHub/blob/bb8f4ddde8f6c301bbf0a976af01747d11b8dab1/src/evolve/driver.py#L1) · `模块`。

上游测试/示例：未运行；compare diff 已获取。运行：**未运行**；目标集成未运行。影响：R11；D 外环替代参考，Raven 退役时再评受控 wrapper。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E036 · 22_autoharness / REQ-EVOLUTION

实际观察：campaign evaluator policy 固定 evaluator/judge/diagnostic identity；promotion policy 显式定义，适合冻结设计，非本次第二 control root。

- [src/autoharness/campaigns.py:9](https://github.com/kayba-ai/autoharness/blob/7cfd52e12fe1d72a3e321da91a56433edfcb37c5/src/autoharness/campaigns.py#L9) · `class CampaignEvaluatorPolicy`。

上游测试/示例：tests/test_campaigns.py（未跑）。运行：**未运行**；目标集成未运行。影响：R11；D 冻结 evaluator/准入策略。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E037 · 20_OpenEvolve / REQ-EVOLUTION

实际观察：Program.parent_id、islands/archive 有实现；evaluator 动态加载函数，运行安全取决于部署；主要解决代码优化搜索，非 agent/world 状态恢复。

- [openevolve/database.py:44](https://github.com/algorithmicsuperintelligence/openevolve/blob/411fb59c886c18704caaffb611e17cf9e7d824d2/openevolve/database.py#L44) · `class Program`。
- [openevolve/evaluator.py:67](https://github.com/algorithmicsuperintelligence/openevolve/blob/411fb59c886c18704caaffb611e17cf9e7d824d2/openevolve/evaluator.py#L67) · `def _load_evaluation_function`。

上游测试/示例：tests/test_database.py（未跑）。运行：**未运行**；目标集成未运行。影响：R11；D phase2 search，比直接 root 更可控。 覆盖：部分实现。许可继承资产表；核验日 2026-10-05。

### E038 · 05_R-Zero / REQ-TRAIN

实际观察：仅审训练边界：需要外部模型/数据/GPU/运行环境。把 dataset/evidence、job、model artifact 连到离线准入，不导入训练器作为 MVP infra；未验证训练收益或 Windows 可运行性。

- [README.md:1](https://github.com/Chengsong-Huang/R-Zero/blob/5699329d018d79535b7910abdedf5a6eebf355fd/README.md#L1) · `模块`。

上游测试/示例：未跑训练、未下载权重。运行：**未运行**；目标集成未运行。影响：R15；D L3 外部接口，细节部署后置。 覆盖：无法判断。许可继承资产表；核验日 2026-10-05。

### E039 · 13_verl / REQ-TRAIN

实际观察：仅审训练边界：需要外部模型/数据/GPU/运行环境。把 dataset/evidence、job、model artifact 连到离线准入，不导入训练器作为 MVP infra；未验证训练收益或 Windows 可运行性。

- [README.md:1](https://github.com/verl-project/verl/blob/1252cc71aa5bd82e5604322064d69bfe6454c660/README.md#L1) · `模块`。

上游测试/示例：未跑训练、未下载权重。运行：**未运行**；目标集成未运行。影响：R15；D L3 外部接口，细节部署后置。 覆盖：无法判断。许可继承资产表；核验日 2026-10-05。

### E040 · 14_VerlTool / REQ-TRAIN

实际观察：仅审训练边界：需要外部模型/数据/GPU/运行环境。把 dataset/evidence、job、model artifact 连到离线准入，不导入训练器作为 MVP infra；未验证训练收益或 Windows 可运行性。

- [README.md:1](https://github.com/TIGER-AI-Lab/verl-tool/blob/383d4b1539ba387f94c3a117d3edc06b467c09d1/README.md#L1) · `模块`。

上游测试/示例：未跑训练、未下载权重。运行：**未运行**；目标集成未运行。影响：R15；D L3 外部接口，细节部署后置。 覆盖：无法判断。许可继承资产表；核验日 2026-10-05。

### E041 · 文档/论文、未确认可导入代码

REQ-EVOLUTION。本地 `agentic_evolution_infrastructure/codebase/11_GSME`、`12_self-evolving-harness`、`03_claude-code-mods` 中详解/links/文档作为导航。在线实际访问 [HarnessBank v2](https://arxiv.org/abs/2607.13683v2) 与 [Self-Evolving Harness v1](https://arxiv.org/abs/2609.38372v1) 的 abs 页面；前者摘要仍写 code upon acceptance，后者本次 abs 页面未找到源码链接。官方 Claude blog 请求 HTTP 403；搜索连接器返回 error。这里的结论是“本次未验证可复用源码”，不是“代码一定未公开”。D only；论文/博客授权不推导软件许可；未运行任何实现。访问缓存 SHA-256 见下方 artifact 表。

### E042 · SQLite 与外部协议 artifact

REQ-EVENT/REQ-MEMORY/REQ-PROTOCOL。SQLite 官方 copyright 页面声明 public domain；Python 自带 sqlite3 不要求自建数据库引擎。MVP 复用 SQLite 事务与内容寻址文件，适配工作仍需 CAS、namespace、迁移与恢复设计。DB 驱动不保证跨工具/世界原子性。Python/其依赖的再分发另核 PSF/第三方许可。

以下 artifact **下载解包、未安装执行**；不把 package metadata license 字段当完整 LICENSE。OTel SDK 的 Python API/SDK 1.45.0 可作为规划 pin，OTLP exporter/semantic convention 版本组合仍须 B13 准入；A2A/ACP 未选 SDK，故不声称 SDK 兼容。

| Artifact | 固定版本/来源 | SHA-256 / 范围 |
|---|---|---|
| MCP client | `@modelcontextprotocol/client@2.0.0`；官方 npm registry、typescript-sdk repo | `cb470b0249b4a06e262145ab2281ea25344e77608f312a5a52ab4dcc26bfa732`；dist/index.mjs discovery/legacy、transport、LICENSE；本地 `_audit/mcp-client-2.0.0/package` |
| OTel SDK | `opentelemetry-sdk==1.45.0`；官方 PyPI wheel | `5dc634c946546f61b757c5b1781f9fd1a10e96ffaf7357c797e508fe9c57e75e`；`opentelemetry/sdk/trace/export/__init__.py` BatchSpanProcessor、`_shared_internal/__init__.py` BatchProcessor，Apache2 |
| OTel proto | `b3f75588eb23c5fca62264edd05d382de49beb1a` | [trace.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/b3f75588eb23c5fca62264edd05d382de49beb1a/opentelemetry/proto/trace/v1/trace.proto)；Apache2；未部署 collector |
| HarnessBank abs | 实际取得 2026-10-05 | `2672edf48bfc5a703fc463ce2d3e263437cc98c162bf93a7df34bff9900b9539` |
| Self-Evolving abs | 实际取得 2026-10-05 | `d7cd9fdb03c4d3a83c64145c4bfa62a6467e5e90df7a634b8860a373b7281009` |
| SQLite copyright | [官方说明](https://www.sqlite.org/copyright.html)，2026-10-05 | `44ca9f793055c8e32fc65f65a4f5bcf813a33f5bdaaa084067dd617a4ed3cc70` |

完整 artifact 本地 root：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\_external\_audit`。raw Letta 每次抓取脚本原 manifest 会覆盖，故本表与各 E013/E014 source 内容 hash 作为引用，不依赖覆盖后的单批清单。

## 远端差异与身份核验

GitHub repo metadata 和 `ls-remote HEAD` 分开核验。主要必查 repo metadata 显示非 fork、未 archive；这是本次访问状态，不是永久承诺。后续 GitHub API 403 是配额/访问限制，不能判缺仓库。比较文件下载有 hash/路径清单留 `_audit/remote-command.log`；没有覆盖本地 checkout。

| 项目 | local→remote 差异与决策影响 |
|---|---|
| Strands | 远端 `59f126f82a6b8118e35fd2f5a38c892ab4725a91`，主要 bidi/audio/restart docs/tests 与 TS package；本次引用 hook/session 文件未见列入 compare，仍 pin local |
| Graphiti | 远端 `b7fc30f2a1e288266760640164a37bdb7d1d0f28` 只改 CLA signature；能力结论不变 |
| ACP | 远端 `cae7aca7f07cefd59da2a3cb374933cb623a2959` 改 registry 文档；canonical 已从 zed-industries 迁移 |
| Langfuse | 远端 `74512fcf585e662035b9f7fac99330b23b5cadd6` 涉及 not-found/delete/datasets/EE billing；root license/compose/OTLP 主路径未列为变动。升级时补 dataset 回归 |
| RSIHub | 远端 `64491da6b7fcea2acf758333ca39df4ca2221182` 大量 DSH recipe/seed/runner/preflight 变化；D only，采用前重审，不能用旧 HEAD 证明远端配方 |

## Discrepancy table

“旧说法”包括两报告、v2 或本地项目详解的简化描述；下表按主张修订，不将导航笔记等同实现证据。

| 旧说法/易误读 | 当前实证 | 修订 / 影响 |
|---|---|---|
| 有官方 Python SDK = Actio 恢复已解决 | E001 只有初始化/建会话/prompt/shutdown | 保留桥接；C01 暴露生命周期，P0 gate |
| session fork 仅 turn 边界 | E002 支持任意合法 event seq 前缀与闭合 seed | 提升原生 fork 粒度；仍不等于 world branch |
| Cordis effect rollback = 外部事务 | E004 disposer 是资源清理 | 工具写操作需要独立账本/reconcile |
| statistical/2sigma gate 会强制显著性 | E008 promoted 与 credited 分离 | Actio 独立 admission，不能直用 promoted |
| GSME archive 只存正式晋升且是可靠 lineage | E009 超 vanilla 即 bank，异常清空/吞写失败 | selector 抽取、全候选 lineage 自管 |
| Raven evolver 可长期原样依赖 | E008 README 计划退役 | 固定快照/窄抽取，明确维护责任 |
| Letta 必须云端或 archive 就是原 MemGPT | E012–E014 当前 local backend 存在，archive retired V1 | 排除依据是双 owner/闭包，不是虚构商业依赖 |
| 当前 Concordia 沿用旧 Environment API | E017 当前 Engine/Entity，resolve 无 Outcome 返回 | 包装 intent/result，GM 单独世界权威 |
| Concordia checkpoint = 完整运行恢复 | E018 不存 engine cursor、可跳过 external Entity | snapshot capability 默认不完整 |
| AgentSociety 仍是论文 MQTT/Postgres 驻留模型 | E019 v2.9.3 Ray batch+workspace | contract 加 pending/barrier；不承诺原子 tick |
| OASIS step 直接给逐人 Outcome | E020 返回 None，DB/channel 另行观察 | ManualAction adapter 和裁决映射必须验证 |
| MCP 只有旧 initialize | E026/client2 同时 modern discovery 与 legacy | pin spec/SDK/artifact，实测协商 |
| Phoenix 可任意商业托管，Langfuse 一定轻量 | E024 ELv2；E025 多服务+EE 例外 | 社区 Langfuse 主选 provisional；内部 Phoenix 备选 |
| trace links 或 LLM attribution 就是因果 | E029/E033 只有观测/文本机制 | 多父 provenance 独立；因果需实验识别 |
| model seed 保障确定 replay | 外部推理/调度未冻结 | 只能承诺已记录 I/O 匹配或受控重执行 |

## 背景与未深入资产

已读两份 architecture/research 报告、v2、两个 codebase README，以及必查项目详解/links；仅作为需求和路径导航。补充根的其他项目只做资产登记，没有强行扩展为候选。下列清单不表示深审或可用：

- `D:\调研\RSI_AI训AI\codebase\00_NeoHorse\repo` · `3368d3010ce1dc44c7ecb9fa604bbf8a6047bb54` · https://github.com/TokenRhythm/NeoHorse · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\01_autoresearch\repo` · `228791fb499afffb54b46200aca536f79142f117` · https://github.com/karpathy/autoresearch · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\02_AutoTrainess\repo` · `561aca455c10f4542cc784d52abe887a7b2a8e5a` · https://github.com/simple-agent-lab/AutoTrainess · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\03_RD-Agent_FT-Agent\repo` · `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` · https://github.com/microsoft/RD-Agent · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\04_Agent0\repo` · `f775b5101e62fe92976831adf4a21a38fcc0a767` · https://github.com/aiming-lab/Agent0 · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\06_Absolute-Zero-Reasoner\repo` · `484afa480c8f6fd77faa3d35451f24f287f58ee1` · https://github.com/LeapLabTHU/Absolute-Zero-Reasoner · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\07_SEAL\repo` · `6d9c9f9ee392c6cc618e771f399d436d190f6ca4` · https://github.com/Continual-Intelligence/SEAL · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\08_genetic-autoresearch_GEAR\repo` · `79525686e263516988a68a62b96a70de28ab5bf3` · https://github.com/nm-le/genetic-autoresearch · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\09_Bilevel-Autoresearch\repo` · `2010e958028fa13e5aacfe2bf73d65314ecdde65` · https://github.com/EdwardOptimization/Bilevel-Autoresearch · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\12_HyperAgents\repo` · `59a68f672dfb92c74aeb7e61535d776fb36e172d` · https://github.com/facebookresearch/HyperAgents · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\15_AI4AI-Bench\repo` · `5ced1e2eb1882baf52e6d928f9257006aa71968c` · https://github.com/Einsia/AI4AI-Bench · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\16_PostTrainBench\repo` · `3ed1d32ff1ec1f41282be6f8ebbcec07b19fc3d1` · https://github.com/aisa-group/PostTrainBench · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\17_Automated-AI-Researcher\repo` · `4e3356190d323f0d698c47e480e0ab810fc7b432` · https://github.com/NoviScl/Automated-AI-Researcher · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\18_HarnessForge\repo` · `05b3ecadb3c9a7a938f75129ea22b8f2b36cf289` · https://github.com/mingju-c/HarnessForge · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\19_SkillRL\repo` · `8e66726ed866a4e0a7f053586a41022798192e6c` · https://github.com/aiming-lab/SkillRL · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\21_MLEvolve\repo` · `9c5c8a3b23f0361708b59a401452dddc00f97189` · https://github.com/InternScience/MLEvolve · 仅 inventory，未纳主路径。
- `D:\调研\RSI_AI训AI\codebase\23_awesome-RSI-survey\repo` · `8f6e897ff1faa685ae8c3c6bbe66bf1b5548c89b` · https://github.com/D2I-ai/awesome-recursive-self-improving-agents · 仅 inventory，未纳主路径。

## 发行核验补充（2026-10-05）

GitHub `releases/latest`只返回合适的稳定release；404不代表仓库或所有release不存在。DSH随后查`releases?per_page=5`确认最新列项[dsh-v0.2.1-alpha.1](https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.2.1-alpha.1)，2026-10-03发布、prerelease=true，该GitHub release无附带assets；不能据此否定PyPI/其他分发，也不代表wheel已验证。

- [EverMind-AI/Raven release v0.2.4](https://github.com/EverMind-AI/Raven/releases/tag/v0.2.4)：published_at=2026-10-03T16:36:22Z，prerelease=False；不自动等于本地HEAD对应发布包已运行。
- [letta-ai/letta-code release v0.34.4](https://github.com/letta-ai/letta-code/releases/tag/v0.34.4)：published_at=2026-10-04T23:49:18Z，prerelease=False；不自动等于本地HEAD对应发布包已运行。
- [strands-agents/harness-sdk release python/v1.57.2](https://github.com/strands-agents/harness-sdk/releases/tag/python/v1.57.2)：published_at=2026-10-01T18:54:51Z，prerelease=False；不自动等于本地HEAD对应发布包已运行。
- stanford-iris-lab/meta-harness：latest endpoint HTTP Error 404: Not Found；稳定release状态未确认，源码仍以固定SHA为准。
- jennyzzt/dgm：latest endpoint HTTP Error 404: Not Found；稳定release状态未确认，源码仍以固定SHA为准。

## A/B/C 许可原文定位

- 01_deepseek-harness：[LICENSE](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/LICENSE)；[THIRD_PARTY_NOTICES.md](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/THIRD_PARTY_NOTICES.md)；[vendor/cordis/LICENSE](https://github.com/deepseek-ai/deepseek-harness/blob/5badb15009ae1756c3afe0ae0cef1faafc290ccc/vendor/cordis/LICENSE)。
- 02_Raven：[LICENSE](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/LICENSE)；[NOTICES.md](https://github.com/EverMind-AI/Raven/blob/3632e6040c7038a60ec418ce39ccae185c72c19f/NOTICES.md)。
- 04_strands-harness：[LICENSE.APACHE](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/LICENSE.APACHE)；[NOTICE](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/NOTICE)；[harness-py/LICENSE](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/harness-py/LICENSE)；[harness-py/NOTICE](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/harness-py/NOTICE)；[harness-ts/LICENSE](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/harness-ts/LICENSE)；[harness-ts/NOTICE](https://github.com/strands-agents/harness-sdk/blob/8ba04f70af542e41aadbc2eb8093b1a07df5ec96/harness-ts/NOTICE)。
- 15_concordia：[LICENSE](https://github.com/google-deepmind/concordia/blob/b71d202750e23444ce1bf28d9f114bcd88aa41db/LICENSE)。
- 16_agentsociety：[LICENSE](https://github.com/tsinghua-fib-lab/AgentSociety/blob/8cc5bb9a9c27d039ec5519375db9d73ccf508cba/LICENSE)。
- 17_OASIS：[LICENSE](https://github.com/camel-ai/oasis/blob/affe52e8dcbc70bba0a4162bfea1057aa5df9316/LICENSE)。
- 21_graphiti：[LICENSE](https://github.com/getzep/graphiti/blob/3c427640abf909f12f71f963fce15eb514a3c493/LICENSE)。
- 18_sotopia：[LICENSE](https://github.com/sotopia-lab/sotopia/blob/a0aaafb440e570e5e61b7c44a44e5e417c545383/LICENSE)。
- 25_phoenix：[LICENSE](https://github.com/Arize-ai/phoenix/blob/9212a42a512d08de7e2a8e81b15821f4483812ce/LICENSE)。
- 26_langfuse：[LICENSE](https://github.com/langfuse/langfuse/blob/f75c661dbe8c6b85523c81486b39e8403ac2c141/LICENSE)；[ee/LICENSE](https://github.com/langfuse/langfuse/blob/f75c661dbe8c6b85523c81486b39e8403ac2c141/ee/LICENSE)。
- 22_MCP：[LICENSE](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/LICENSE)。
- otel：[LICENSE](https://github.com/open-telemetry/opentelemetry-specification/blob/d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b/LICENSE)。

许可定位只证明已采用范围的根/子目录条款；未安装的传递依赖、数据/模型、容器镜像与商业服务仍由B01准入。
