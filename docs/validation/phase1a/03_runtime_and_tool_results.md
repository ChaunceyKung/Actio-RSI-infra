# Runtime、工具与授权结果

证据类型为 `REAL_RUNTIME_FIXTURE_PROVIDER`：真实官方 TS executable、SDK stdio、DSH session/loop/persistence与MCP client；只有模型输出由确定性provider plugin替代。所有工具来自官方MCP Python SDK server，读取唯一合成 `data.json`，不接受路径。Python Control 只冻结策略并记录结果，不另行执行工具。

| 范围 | 实际结果 | 证据 |
|---|---|---|
| 冷启动/initialize/turn/close | PASS；正常关闭 returncode0，所有Job最终active=0 | lifecycle.json / runtime_close |
| 同session多轮/不同session | PASS；同session保留 A_SECRET，other session不含；native seq继续推进 | lifecycle.json 的完整provider-input |
| 双home/persona/中文空格路径 | PASS；同时活跃的A/B不同PID、人格/私有标记不串 | lifecycle.json |
| 同op/session的policy隔离 | PASS；A允许一次，B拒绝零次；无MCP profile枚举零工具 | policy-isolation.json |
| 重启旧session ID | PASS（行为确认）；`session "same" already exists`，原journal hash不变；不是恢复/覆盖 | lifecycle.json |
| 初始化/运行deadline、EOF、意外退出 | PASS；全部有界，unknown/needs_reconcile，无自动重发 | init-timeout/run-timeout/eof/exit.json |
| 工具allow/deny | PASS；allow1次，deny0次 | tools.json 的final guard与MCP received |
| rewrite后校验 | PASS；初始参数被实际替换为changed，final hash失配拒绝，MCP0次 | tools.json：pre-execute→rewritten→final-guard |
| 许可绑定 | PASS；expiry/policy/lease/scope/run/toolVersion缺失或失配拒绝；最终schema/key scope/budget拒绝 | tools.json / constraints.json |
| 工具成功 | PASS；原生isError=false，返回SYNTHETIC FILE VALUE | tools.json |
| 工具isError/transport error | PASS；一个是server返回isError，另一个server主动退出，分别保存原因 | iserror.json / transport.json |
| 工具timeout | PASS；700ms MCP请求期限返回 -32001；fixture观察到CancelledError | timeout.json；取消是此fixture所观察的结果，不是任意工具回滚承诺 |
| pre-dispatch cancellation | PASS（映射为deny）；0次调用，不冒充SDK semantic cancel | tools.json / P2-cancel |
| 新source的原生cancel决策 | FAIL（compatibility）；已有许可的合成读取仍dispatch，G1不支持该能力 | native-cancel-limitation.json；最终plugin禁用该决策形态 |

实际最终工具清单只有 `mcp__fixture__read_fixture`，无MCP profile为空。`sdk-minimal` 原本含shell；本patch显式禁用 `persistent-bash/persistent-pwsh/terminal-bash/terminal-pwsh/pty` 及live provider，tools固定native模式。实际provider-input同时记录 registry schemas与模型可见tools；还请求了未注册`pwsh`并确认MCP0次。不加载filesystem、network、subagent工具；保留sandbox/subprocess基础服务供runtime/MCP工作不等于向模型暴露对应工具。不是靠prompt禁止shell，也不宣称任意插件代码具有OS sandbox隔离。

授权方案选择 F03-1：Python在启动前生成policy artifact；TS读入、深冻结，记录policy hash。每次执行以实际native callId/session关联，静态grant绑定 final request hash、固定MCP实现hash（tool version）、policy binding hash、run/scope、lease、expires。原生 `tools/pre-execute`完成rewrite后，由`tools.guard`完成校验和次数预算占用，再由同一个Worker dispatch。缺permit直接deny；拒绝不消耗MCP调用。per-op ID不是用户任意复用的业务identity；此probe在冻结清单内使用，产品必须由可信控制端分配。

本轮没有每次Worker→Python审批RPC。`dynamic`请求明确拒绝；`approval-timeout/approval-disconnect`是受控不可用策略状态输入，测试“不可用即拒绝”的分支，**不是动态通道超时/断线往返测试**。新增动态审批必须单独实现协议并验证，不从通用SDK incoming request方法推定支持。测试不会因为仅收到notification而当作allow。

| Capability | 本轮声明 |
|---|---|
| SDK initialize/session-prompt/shutdown | 已验证；public API保持原样 |
| 同进程同session多轮 | 已验证 |
| 有界deadline/强制终止/进程树清理 | 已验证Windows supervisor；不是语义cancel |
| 稳定source事件读取 | seq0起连续，session.v3.jsonl；只读collector已验证 |
| 原生flush | 公共plugin service `sessionPersistence.flush()`实际成功，marker非SDK RPC |
| 精细cancel/status/open-existing/resume/fork/catchup | unsupported/G1；内部源码seam不自动成为SDK能力 |
| Dynamic Python approval | unsupported，未实现业务协议 |
| arbitrary profile hot mutation / remote worker | NOT_RUN，不允许依赖 |
| MCP modern/HTTP/OAuth/resources/其他legacy组合 | NOT_RUN。只测 Python SDK1.26.0 stdio，实际请求/支持协议2025-11-25，clientInfo版本0.0.1非 npm release pin |
| live provider | BLOCKED；未配置凭据，预算0 |

probe内部读取 `_proc` 仅用于PID/退出诊断和定点故障注入，不修改SDK或使用私有launch参数；这是要丢弃/替换的实验监测代码，产品supervisor要拥有显式进程句柄。源码/发行物消息形态差异曾使fixture重复请求：final guard仍只允许一次MCP调用并拒绝重复，外层期限结束运行。修正以`source.kind/callId`识别tool-result，并增加每op最多6次fixture请求限制；保留 initial-tool-fixture-failure.json。最终回归结果不包含该旧失败的“成功”计数。
