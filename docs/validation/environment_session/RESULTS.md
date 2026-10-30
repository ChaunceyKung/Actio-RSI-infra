# Environment Session 第一阶段验收（2026-10-30）

结论：通用同步 Session、PettingZoo TicTacToe 的 Experiment/Run 端到端链路和 Concordia 兼容接入已实现并实际运行。**完整旧系统回归 INCOMPLETE，不能宣称全部通过或外部模型链路成功。** 所有运行都使用本机合成 provider 或规则 Agent；真实模型调用 0，未读取真实凭据。

实现与重现命令见 [架构与安装](../../architecture/ENVIRONMENTS.md)。源码起点为 `6a98889`，Python 3.12.13 由 uv 安装到仓库 `.local/python`；依赖、隔离环境、下载缓存、临时目录和演示产物位于 `.local`，旧 DSH 测试短根为 `D:\Work\5\actio\t`。不提交 venv、缓存、SQLite、原始 journal 或大日志。

## 实际交付

- 最小 `EnvironmentSession` 与 factory，分离观察、合法动作/约束、提交接收、实际结算、终止和清理；显式声明同步/异步、多主体、同时动作、快照和时钟能力。
- `actio run experiment` 复用 Store 的 begin/fence/lease/audit/scenario_terminal/finish、现有导出和离线核验。每个 Episode 为一个 Run；重复请求键不重复执行。规则路径不虚构 DSH 原生来源或发送账本。
- PettingZoo 原生 `tictactoe_v3.env()`、first-legal 规则 Agent，3 局 × 7 步，两个玩家轮流行动，全部 execution_complete；每局原生 reward 为 player_1=1、player_2=-1。证据包导出和离线核验有效，详见 [e2e.json](e2e.json)。
- Concordia 仍由固定未修改源码的 `Sequential.run_loop` 执行；Session 用线程/队列暂停 Entity.act，主线程保留 DSH Runtime/Transport、Facts、Store 和 Ledger。原有两步执行限额、Actor 顺序、私有观察、ActionSpec 与结果合同保留。
- 安装包 entry point 注册环境，配置仅指定已安装名称；测试通过独立 distribution metadata 注册额外环境名并运行，应用层无需添加环境分支。

## 最终代码验证

| 检查 | 结果 | 收据 |
|---|---|---|
| 新增环境一致性 / 编排 / CLI / 扩展注册 | 7/7 方法通过，使用真实 PettingZoo 和 Concordia | [conformance.json](conformance.json) |
| 现有 pure 组 | 53/53 方法通过 | [pure.json](pure.json) |
| 现有 state 组 | 27 方法，25 通过，2 个缺历史数据库错误 | [state.json](state.json) |
| 最终环境相关回归子集 | 37 方法：环境7、modularity9、runtime2、reliability8、task7均通过；transport4方法失败 | [regression.json](regression.json) |
| 依赖方向/架构 | PASS，170 modules、655 edges | [architecture.json](architecture.json) |
| wheel / 依赖 | uv build 成功；wheel 的所有 py/mjs/sql/json 与源码逐字节相等；uv pip check 通过 | [e2e.json](e2e.json) 的 wheel SHA |

上述最终 pure/state/相关回归去掉重复的 modularity 9 项，合计 **108 个不同方法，102 通过、6 未通过**。transport 的 4 个方法包含 19 个失败子案例；不能把子案例数当成方法数。另一次独立 conformance 7/7 是同一组方法，不重复加总。

新增测试覆盖非法动作不修改世界、stale revision、错误行动者、重复提交与冲突、cursor 和真实 settlement、正常终止、终止后拒绝、等待行动时关闭、原生 Engine 错误、策略/工厂失败、动作上限、幂等运行、清理失败保留 lease、证据篡改和额外环境注册。测试专门验证 Engine 在第一次 EVENT 后抛错时，第一次真实世界结算仍先交给控制面并落库；修复前旧可靠性用例暴露了此前缀丢失问题，修复后 8/8 可靠性方法通过。

## 原始复现与未打通部分

原版在独立 uv 环境从 Git archive 安装，产品源码没有改动；测试仅重定位运行目录。已完成 26 个模块、138 个方法，14 个模块通过、12 个模块有失败/错误，详见 [baseline.json](baseline.json)。跨进程 DSH Runtime + Concordia 的原始双场景、回放、隐私和非法动作测试实际通过；这是**本机合成链路**，provider 为 fixture，不代表真实模型调用成功。

原版与新版均存在以下阻塞，保留失败而不扩大本轮改造：

1. **传输未打通。** 对同一个最小两步本机 HTTP fixture，原版和最终版分别运行后均得到 native `DeepSeek stream idle timeout after 1500ms`，控制面随后报告 `receipt/terminal evidence missing`，run 为 needs_reconcile/infrastructure_failure，1 次 attempt 保留 unknown。对照详见 [transport_comparison.json](transport_comparison.json)。这证明该失败可在原版复现；尚未定位底层超时的全部原因，不能据此排除所有其他传输回归，也没有延长/关闭预算或超时门槛来换取 PASS。
2. **历史数据缺失。** `test_evaluation_candidate` 需要 `D:/actio-c2c1-main-v1/candidates.sqlite`；`test_robustness` 的历史复制用例需要 `D:/actio-c2c2-live-v1/candidates.sqlite`。本机均不存在；没有造一个空库代替历史研究数据。
3. **旧回归的其他失败。** 故障注入存在 ready deadline、后继 active lease 和缺 `.limit`；旧 evidence legacy fixture 被现有 schema inspector 拒绝；初次评估测试缺 json-repair。原版日志 hash 和具体失败 ID 已保留。后来按现有 eval lock 补齐依赖，最终任务7/7通过；不把早先失败重写成 PASS。
4. **完整矩阵未完成。** 原版 readiness 6 方法运行约 1119 秒后仍有 2 项失败。在 transport、budget、readiness 的重复失败及最小原版/新版对照后，停止后续依赖该传输路径的矩阵。`gateway`、`gateway_lifecycle`、`pilot_runtime`、`suite_runtime`、`suite_evidence`、`candidate_runtime`、`evaluation_candidate_runtime`、`robustness_runtime` 未获得完整结果，明确列为 not_run。完整系统回归仍 INCOMPLETE。

首次基线后半段曾与产品重装交叉，已弃用那份混合版本结果，重新建立上述独立原版环境。修复前的重复新版大矩阵也被最终代码子集替代。短根初次放在仓库 `.local/t` 会使长场景名超过原生 80 字符限制，已改到共同父目录 `t`；首次 state 复核因默认沙盒不能写该兄弟目录报错，随后在用户已指定路径的授权执行环境重跑，剩余 2 项均为历史数据缺失。原始失败文件保留在 `.local`，没有混入通过计数。

可复查完整本机原始收据：`.local/environment-baseline-clean/receipt.json`、`.local/environment-final-regression/receipt.json`、`.local/environment-final-pure/receipt.json`、`.local/environment-final-state-authorized/receipt.json`。已提交收据含其 SHA、逐模块计数、失败 ID 和日志 hash；报告由 `scripts/environment_report.py` 生成，未提交大原始日志。

## 下一阶段

先独立诊断原生 1500ms streaming 超时和终态回执处理，再补齐历史数据与上述未验证矩阵。OpenRA 需增加真实服务端/进程控制、可见状态与命令 adapter、tick/revision 对齐、pending outcome 轮询、同 tick 多玩家提交、未知接收状态处理及受管清理；当前同步 runner 要扩展后才能启用实时异步能力。原生存档的覆盖范围未验证前不声明 snapshot/restore。细节和架构取舍见 [ENVIRONMENTS.md](../../architecture/ENVIRONMENTS.md)。

本轮按持续授权提交并普通推送 `main`，发布后核对远端 SHA；Git 发布不代表部署、研究激活或新增模型费用。
