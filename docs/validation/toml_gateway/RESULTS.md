# TOML 路径配置与 gateway 入口（2026-10-30）

按用户最新指令，本轮先将实际运行路径移入 TOML，并预留 LLM 配置；不再相信或自动探测旧机器的绝对凭据/历史数据库路径。真实供应商调用仍为 **0**。

## 改动

- 根 `actio.toml` 集中声明 database、runs、authority、credential_file、uv Python/venv/cache/temp；相对路径按配置文件目录解析，支持 `--settings`。默认运行根为 `../t`，位于 `D:\Work\5\actio` 树下并满足 DSH 的短路径约束。
- LLM 段提供 provider、base_url、model、max_output_tokens、明确 uncapped 策略及有限 Episode 计划。当前只执行已有 TokenKey v5 合同支持的配置；其他值在读凭据前明确拒绝，未虚构通用 provider 支持。
- 删除凭据 resolver 的 `D:/调研/...` 回退和自动复制，只在 live 分支读取显式配置的文件。项目内凭据继续要求 Git ignored/untracked，不允许把密钥正文写入 TOML。
- uv 安装脚本从 TOML 读取环境与缓存目录，真实执行已通过；测试运行根、临时目录和两个可选历史输入也从 TOML 读取。未配置历史输入明确 skip，不能算通过。
- `actio config show` 查看解析结果；`actio gateway run --settings FILE --rehearsal` 运行真实 DSH + Concordia 本机链路；去掉 rehearsal 才读取该文件指向的真实凭据。运行记录含设置 hash/快照、有限发送、usage/unknown、证据包和清理结果。保留旧冻结 JSON execute 入口。

## 实际验证

公开命令本轮独立执行了本机 TokenKey adapter 链路：一张 compatible 卡，2 个 Agent，2 次发送、2 次 settled、0 unknown，Run execution_complete / task success，campaign 重新核验 valid，两个 Worker 均 reaped / active=0，凭据扫描未发现泄漏。它使用官方 adapter 和原生 DSH/Concordia，响应来自本机 fixture；不是实际 TokenKey 模型生成。详见 [e2e.json](e2e.json)。

配置、pure、state、environment、runtime 共检查 96 个不同测试方法：94 通过、2 个可选历史输入未配置而 skip、0 failure/error。state runner 保留非 PASS 状态，不把缺失历史数据改报成功。逐组结果见 [tests.json](tests.json)。架构检查 PASS，173 modules / 672 edges，见 [architecture.json](architecture.json)。

本轮也复查此前传输超时：无并发负载下，原来的 v3 transport_stub 已成功完成两步，2 次 settled；受控计时的 TokenKey adapter 本机链路成功，reserve/sending Python IPC 各约 0.47–0.50 秒。计时收据见 [diagnostic.json](diagnostic.json)。这些结果说明此前 1500ms 超时具有负载敏感性，不能把它描述为每次必现的断路；尚未证明单一完整根因。没有放宽旧 v3 门槛，也没有绕过 ledger、改写官方 serializer/parser。新入口使用原有 v5 的 30 秒 idle 等固定期限。

实际复现方式及 LLM 配置边界见 [配置指南](../../architecture/CONFIGURATION.md)。真实服务、账号鉴权、上游模型可用性和实际账单仍未验证；后续在用户配置的凭据文件就绪后使用同一入口验证。历史研究阶段的来源冻结和 once-claim 安全规则未迁移、未启动，旧阶段授权边界不变。

本轮只发布源码、TOML 示例和小型收据；本机环境、缓存、密钥、数据库与原始日志不入 Git。完成验证后普通推送 `main`，核对远端与本地 SHA，不 force push。
