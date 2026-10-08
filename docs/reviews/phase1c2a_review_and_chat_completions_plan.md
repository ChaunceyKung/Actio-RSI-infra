# Phase 1C2A 审阅与 Phase 1C2A.1 行动方案

审阅日期：2026-10-08。产品基线 `7fb2f682b2726ce3bba9b38bc71ebbf893c5de22`，远端任务分支与本地一致；main 仍为 `af0a88cfff23c22c396fd7c9ef9916f0df8cd21f`。开始时工作树干净。

**认可本轮按停止条件交付 NO_GO；下一轮推荐保留 `0.1.5rc1`，改用发行物实际支持的官方 Chat Completions 路径，完成剩余传输和预算准入。** 阶段名为 Phase 1C2A.1，不提前进入 C2B live。当前预算仍为 0。

这次 NO_GO 的范围是所要求的 Messages adapter 不能加载，不是 DSH 既有 G0/fixture 主路径失效。上轮方案把 `0.2.1-alpha.1` 参考源码的协议能力限定为 `0.1.5rc1` 的必经目标，这一规划选择需要纠正；执行 session 如实停在不兼容处是正确的。

配套：[执行 Prompt](../prompts/phase1c2a1_chat_completions_and_budget.md)、[审阅证据](phase1c2a_review_evidence.json)。本轮仅新增文档，未修改产品、旧证据、依赖或数据库；未启动 DSH/HTTP 服务，也未实施下一阶段。

## 1. 本次核验

| 范围 | 结果与限制 |
|---|---|
| 文件与归档 | 1,500 项 hash 比较全部匹配，含 33 个产品文件、当前测试/脚本/锁文件、27 个阶段 artifact、20 个 raw archive 及内部成员、9 个当前 suite 的源码/测试绑定、已安装 delivery 包；包含重复比较，不是 1,500 个不同文件 |
| 历史验收 | 当前 9 suites 共 47 组 PASS，明确是配置和既有路径回归，没有被当作新传输通过 |
| 实际重跑 | preflight 5、input_binding 3、SOTOPIA 3、evaluation 8，共 19 组 PASS；未重跑真实 runtime/恢复/迁移 |
| 四次探针 | hash 与状态匹配；实际接收数 1/1/0/0，共 2；前两次均 `/chat/completions`；最终正确 disable+insert 的 loader 失败支持 NO_GO |
| 旧证据 | 校验固定源码副本后，在 `-I -S` 标准库子进程实际复核 C0 12 记录、C1 22 记录及完整 25 登记 campaign，全部通过；零 evaluator 调用 |
| 清理和安装 | 历史 delivery 的 41 个具名 Job active=0、4 个探针端口无监听、干净安装/CLI/pip check 证据成立；本轮未重新枚举这些 Job/端口或再次安装 |
| 本轮网络/费用 | 仅 GitHub 源码/ref 读取及文档推送；provider HTTP 接收 0、真实模型请求 0、真实费用 0 |

## 2. 可以关闭的事项与仍未完成的事项

C2R1 角色预算配置问题可以按原定义关闭：`pilot-config.v2` 允许确定性 GM 和 disabled 角色使用零远端预算，禁止不适用的 provider/credential/quote 字段；整数金额、重复 JSON key、类型和角色约束有真实检查。preflight 的配置成立不等于传输或 live 准入，这一分离应保留。

四次探针的证据层次清楚：默认 provider 的实际 wire 证明协议是 Chat Completions；429 单次接收只证明该局部错误路径；错误 patch 和 loose-file import 不证明 bundled 插件不存在；最终真实 loader 对显式 Messages 插件的 `ERR_MODULE_NOT_FOUND` 才支持停止。后加的 fetch 限制没有被追认到早期探针。

以下仍是欠缺能力，而非本轮完成项：无答案双 seat 的正式合同、成功 SSE/usage、完整错误矩阵、持久 reserve/settle/unknown、并发末额度、新 transport campaign 对账。旧 fixture 的 `answer` 和 `pins.provider=actio-fixture` 不能直接继承成正式 HTTP 运行身份。

本次没有发现要求撤销配置修正的阻断缺陷。也没有把一次诊断性 `globalThis.fetch` 计数器视为已验证的预算系统。

## 3. 新找到的、与发行版本名称对应的官方源码

GitHub `git ls-remote --tags` 实际返回：

```text
183f08e9c6dde7e36cd2318eaee70b0da08fb35e refs/tags/dsh-v0.1.5-rc.1
```

本轮从该不可变 SHA 读取了 16 个源码/文档/测试文件；`packages/llm/llm-deepseek/package.json` 的版本为 `0.1.5-rc.1`。新版布局的 `tests/stream.spec.ts` 在此标签不存在（404）；读取目录列表后使用实际的 `adapter.spec.ts`、`sse.spec.ts`、`translate.spec.ts`。没有修改原本地 `5badb150…` checkout，也没有运行上游 e2e。

| 官方文件（均为 `183f08e…`） | 实际观察及复用方向 |
|---|---|
| [README](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm-deepseek/README.md) / package.json | 明确是 DeepSeek Chat Completions adapter；`deepseek-official` 路由；默认 normal retry 五次，依赖 composition 是否启用 |
| [adapter.ts](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm-deepseek/src/adapter.ts) | 直接 fetch `${baseURL}/chat/completions`；保留官方 serializer/error parser，不重写 transport。图片/Files 还可能触发其他请求，下一轮只准纯文本 |
| [serialize.ts](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm-deepseek/src/serialize.ts) | `stream: true`、`stream_options.include_usage: true`、max_tokens；请求合同应以实际 wire 捕获为准 |
| [translate.ts](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm-deepseek/src/translate.ts) / sse.ts | 支持 finish 附带或尾部 usage-only；block-end/usage/finish 等到 `[DONE]`；无 DONE 报 STREAM_CLOSED；cache-read 与 inputTokens 分开，不能漏计或重复计费 |
| [mock-server.ts](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm-deepseek/tests/mock-server.ts) | 已有 choices/delta、finish_reason、usage、`[DONE]` 的完整文本样例和错误/断流行为，可窄拆测试结构 |
| [sdk-minimal profile](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/bundle/sdk-minimal/cordis.patch.yml) | 默认加载旧 `@deepseek-ai/dsh-llm-deepseek`，另有 session-title、llm-retry；必须按实际发行物核对与关闭不必要 producer |
| [llm service](https://github.com/deepseek-ai/deepseek-harness/blob/183f08e9c6dde7e36cd2318eaee70b0da08fb35e/packages/llm/llm/src/index.ts) | `llm/stream` waterfall 可观察/包装 next；是待实测的调用门控候选，不直接承诺一次 hook 等于一次 HTTP send |

文件 URL/hash 和目录查询记录见审阅证据。源码暂存在本地 `.local/phase1c2a-review-upstream/`，下个 session 可以从固定 GitHub SHA 重取。所有复用保留 MIT 许可；不要求上传整套源码。

**标签相符、package 版本相符、wire 相符仍不等于构建来源映射成立。** runtime pyproject 使用构建注入版本，当前 exe 保持 SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6`。下一轮声明“固定发行物实测 + 对应版本标签参考”，不要声明 reproducible build 已完成；完整构建映射不是此次离线准入的新增阻断条件。

## 4. 方案选择

| 选项 | 判断 |
|---|---|
| 保持 `0.1.5rc1`，采用官方 Chat Completions | **推荐并纳入下一执行 Prompt。** 有真实请求和同版本标签源码支持，保留已验 runtime/Engine/隔离路径；仍需成功链路和预算验收 |
| 升级到 Messages runtime/SDK | 当前需求并未指定必须 Messages，升级扩大回归与依赖范围；暂不采用，只有已验证旧路径无法满足必要合同才提交具体备选 |
| 自写 provider/协议转换、第二 solver、Strands 替换 | 当前证据不支持这样扩大范围；不作为修复 protocol 不匹配的默认动作 |

下一执行 Prompt 明确改变协议目标，取代前 Prompt 的 Messages-only 限制。执行者按本次选定范围推进，不需要再问是否可使用 Chat Completions；这不授权真实模型调用。

## 5. Phase 1C2A.1 实施顺序

| 顺序 | 最小完成项 | 验收后继续 |
|---|---|---|
| S0 成功协议探针 | 原 exe/官方 adapter → 本机 `/chat/completions` → 完整文本、finish、usage、DONE → SDK；分别测 attached 与 trailing usage | 成功后直接做 S1–S3，不仅交付一份探针报告 |
| S1 新正式运行合同 | `protocol=chat-completions` 的显式版本、正确 provider/spec/pins、无答案 actor 输入、两 seat 真实 DSH/Concordia 运行 | 目标卡不扩容；新模式与旧 fixture/旧 Messages 设计分开 |
| S2 每次发送预算 | Python 权威新实验账本，TS 最终发送前核对/持久 reserve、settle/unknown、一次性资格、有限错误/并发矩阵 | 请求计数是硬约束；合成 token/价格估算不冒充真实收费上界 |
| S3 证据与交付 | source/spec/view/wire/attempt/预算/世界效果全链绑定，只读 verifier、相关回归、旧版固定复核、干净安装与 CLI、清理 | 新 Gate 准入后停在离线工程；正常提交推送任务分支 |

新配置/协议语义必须显式版本化，旧 `pilot-config.v2` 的 Messages 示例不能被新代码悄悄解释为 Chat Completions。不改历史文件；使用新身份、新库和新证据目录。

预算门控应验证到实际发送边界。若采用 llm/stream hook，须证明固定纯文本 profile 内没有越过它的额外 adapter fetch；诊断性全局 fetch wrapper 只有在生命周期、作用域、重试、请求体/方法绑定和失败处理均实测后才可能成为受限实现，不凭“一个 counter”宣称强保证。没有可靠 seam 时保留 NO_GO，不重写整个 provider 或扩大为网络网关平台。

预留和发送之间崩溃无法证明未发送，应保留 unknown；缺 usage 不结为零费用，不释放额度后自动重试。合法任务结果、传输终态、账务状态分别记录。未知账务至少阻断后续尝试，已经发生的原生事实和世界效果不删除。

## 6. 完成标准与后续

C2A.1 的工程 CONDITIONAL_GO 需要成功流、无答案双 seat、请求级预算、错误与未知处理、只读对账全部通过；不能因 Chat Completions 发出了一个 HTTP 请求就提升 Gate。400/401/429/500、空/畸形 SSE、缺 DONE、缺 usage、超时和并发边界都应按实际重要路径测试，报告真实次数与未覆盖范围。

47 组历史回归、41 个历史 Job、2 次历史 HTTP 都保留原数。新阶段独立统计 provider attempt、真正发出的 HTTP、本机接收/拒绝、合成 usage、真实费用和进程清理，不能把本机测试请求说成真实模型调用，也不能把它们抹成 0。

之后的 C2B 仍需单独确认真实 provider/model、endpoint、合成数据范围、calls/tokens/费用上限、报价与凭据引用；当前不创建可自动跑 live 的配置。人工标签、研究效度、judge 与演化保持 BLOCKED。没有必要再为接口不通扩写合成评估分数。

## 7. 起点和发布

本轮文档分支：`docs/phase1c2a-review-chat-completions-plan`，基于 `7fb2f68…`。下一 session 从其已核对远端 HEAD 创建 `phase1c2a1-chat-completions-budget`，记录完整交接 SHA，不能从落后的 main 开始。

遵循 [AGENTS.md](../../AGENTS.md)：每轮验证后 commit → 普通 push 当前任务分支 → 核对远端 SHA。push 阻塞保留本地提交并报告；不 force push、不自动合并 main、不部署。
