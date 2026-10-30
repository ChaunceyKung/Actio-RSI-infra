# 项目 TOML 配置与 LLM 入口

当前执行配置统一放在仓库根 [actio.toml](../../actio.toml)。读取配置不再使用某台机器的旧盘符、私有调研目录或环境变量密钥作为回退；配置文件不存在时明确报错。相对路径始终以 **TOML 文件所在目录** 为基准，支持绝对路径和 `--settings` 指定另一份配置。

## 配置内容

- `[paths]`：默认数据库、运行根、gateway authority、凭据文件、uv Python 安装目录、虚拟环境、uv 缓存和临时目录。`runs` 默认 `../t`，便于满足 DSH 原有短路径约束；可按本机实际位置修改。该目录仍位于仓库所属的 `D:\Work\5\actio` 树下。
- `[llm]`：provider、base_url、model、max_output_tokens、spending_policy、episodes。密钥内容不得写入 TOML。当前执行适配器支持 TokenKey 的 `gpt-5.6` / `claude-sonnet-4-6`，输出上限固定为现有版本合同的 512，有限计划为一张 compatible 卡，或 compatible + conflict。其他 provider/model/上限字段已预留配置位置，但当前不支持的值会在读凭据之前明确拒绝，不偷偷换模型。
- `[history]`：可选的 candidate_database、evaluation_database。空字符串表示未配置；历史数据测试明确 skip，不虚构数据库、不尝试历史硬编码路径。显式配置但文件不存在或不匹配原合同仍报错。完整回归 runner 把 skip 保留为非 PASS，避免把未验证输入计入通过。

所有新目录默认留在共同项目目录下。配置是可信的本机运行输入，移动路径后可用 `config show` 核对实际解析位置。旧阶段封存文档、版本合同中的逻辑引用以及研究阶段的全局 once-claim 规则保留为历史/安全边界，不自动搬迁或用于寻找密钥；本轮未启动那些研究阶段。

## 安装、检查与实际本机链路

PowerShell 从仓库根执行。使用点调用，让脚本按 TOML 设置的 uv/cache/temp 环境在后续命令继续有效；`$python` 也是从 TOML 的 venv 解析得到：

```powershell
. ./scripts/environment_setup.ps1 -Config ./actio.toml
uv run --no-project --python $python python -m actio config show --settings ./actio.toml
uv run --no-project --python $python python -m actio gateway run --settings ./actio.toml --rehearsal
```

最后一条启动真实 DSH 受管 Worker、官方 TokenKey `llm-pi-ai` adapter、Concordia Sequential 和本机 HTTP fixture。默认完成两个 Agent 的两次调用，Ledger 的 attempts=2、settled=2、unknown=0；外部真实模型调用为 0。stdout 是小型 summary JSON，具体配置快照、原生材料、账本、证据包和结果保存在其 `root` 指向的新目录。每次分配新目录；`--root` 可显式覆盖，已存在目录会拒绝，不能靠重跑请求键清空 unknown。

重现环境实验也可保留原来的显式参数，或让 `actio run --settings FILE init` 使用 TOML 的默认 database，让 social/schedule 使用 TOML 的默认 runs。命令行显式 `--db` / `--short-root` 优先。

## 真实 LLM

先在 `[paths].credential_file` 指定的实际文件中放入单行密钥；项目内的凭据文件必须被 Git 忽略且不能被跟踪。只读取这个文件，不复制旧目录的文件、不使用环境变量密钥回退。配置可位于其他目录；解析器按实际凭据所在 Git 仓库检查忽略策略。项目外显式选定的文件直接在内存读取，不复制到项目。

去掉 `--rehearsal` 即执行该 TOML 对应的真实 TokenKey 小实验：

```powershell
uv run --no-project --python $python python -m actio gateway run --settings ./actio.toml
```

缺配置或缺密钥时在创建 Run/lease/authority 前停止。密钥经现有受管 Worker 的内存门禁传入，发送仅允许已授权的 `https://api.tokenkey.dev/v1/chat/completions`，禁止跟随重定向；不会把这个 key 发给另一个 origin。无金额上限仍是显式 `uncapped` 策略，保留每次调用、长度/期限、usage/unknown 和未核对的账单状态。旧 `gateway execute` 冻结 JSON 入口保留，新增 `--settings` 选择凭据路径；该 JSON 内历史 `credential_ref` 是旧版本的逻辑标签，实际文件选择由 TOML 完成。

失败后诊断可用 `--predecessor <旧 root/result.json>` 显式关联前次结果；原账本和 unknown 不清除。当前 TOML 预留好 LLM 配置，不表示本轮已调用真实供应商。

## 1500ms 超时诊断

单独运行原始 transport_stub 时本轮已成功 2/2 次结算；官方 TokenKey adapter 的本机两步链路也成功。受控诊断测得发送前 reserve/sending 两次 Python IPC 各约 0.47–0.50 秒，它们在 native fetch 的流计时期间发生；上一轮并发负载下的 1500ms 失败至少具有负载敏感性。尚不把此观察当作唯一根因证明。

本轮没有延长旧 v3 的 1500ms 门槛，没有替换官方 serializer/parser，也没有绕过账务。新 TOML 入口选择已有 TokenKey v5 合同，其现有 idle=30s、first_response=45s、request=90s 等限制保持原值。真实供应商运行仍须在实际配置与密钥就绪后验证。
