# 18 · 实际验证记录与未完成的技术验证

核验日2026-10-05。Windows x64 / PowerShell；Python3.12.10（MSC1943 AMD64），pytest9.1.1，pydantic2.13.4，Git2.55.0.windows.3，Node24.19.0。系统已装pytest/pydantic；未安装上游完整依赖。未启动付费模型/GPU/Ray/Harbor/graph/viewer，不生成Actio运行代码。

日志根：`D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\workingspace\_external\_audit`。原始JSON日志与副本保留本地，**不提交原始环境dump/上游源码/临时脚本**；此文提供可复核命令和经筛选摘要。所有目标集成状态为未运行。

## V01 现场、来源与Git核验

执行`git status --porcelain`、`git branch --show-current`、`git rev-parse HEAD`、`git remote -v`、`git describe --tags --always`、`git ls-remote --symref <origin> HEAD`，并用GitHub repo API核canonical/default_branch/fork/archived。输出`inventory.json`、`inventory-command.log`；参考原工作树初始clean，未切分支/改代码/原位测试。目标远端初始为空，checkout unborn main，无已有README/docs/AGENTS或用户修改。

GitHub compare diffs以固定local/remote SHA下载，输出`remote-command.log`，只读相关变化，不pull覆盖参考。Graphiti仅CLA、ACP文档、Strands bidi/版本、Langfuse delete/datasets/EE、RSIHub DSH recipe变动，结论边界见15。API后段403不作为不存在证据。

补查`releases/latest`及DSH`releases?per_page=5`：Raven v0.2.4、Letta Code v0.34.4、Strands python/v1.57.2稳定release已确认；DSH latest返回404后确认alpha.1 prerelease，无GitHub attached assets，不能推断其他渠道无wheel；Meta/DGM latest404仅代表该endpoint未给稳定release。记录`release-check.json`、`dsh-releases.json`，未下载/运行发行包。

Letta浅clone取到tree和HEAD后checkout停滞，取消；这是不完整新clone，非用户文件变更。改用 `https://raw.githubusercontent.com/letta-ai/letta-code/<SHA>/<path>` 有界获取，保留内容hash。误猜的`src/skills/index.ts`、`src/agent/skills-discovery.ts`返回404，随后用git ls-tree定位并读取`src/agent/skill-sources.ts`；不把404泛化为项目没有skills。其他源码搜索偶有路径错误，已由存在性校验纠正，错误命令不计为源码证据。

## V02 DSH 上游客户端测试

独立副本通过 `git -C <DSH repo> archive HEAD python/sdk` 导出至 `_audit/upstream-tests/dsh`。执行现成 `python/sdk/tests/test_client.py`，没有修改上游测试/功能。

初次命令：`python -m pytest -q -p no:cacheprovider python/sdk/tests/test_client.py`，PYTHONPATH为副本SDK src，exit1，26通过/3失败。失败均fake bundled runtime的Python source在Windows GBK默认编码下含中文temp路径，出现UTF-8 SyntaxError；并非真实TS runtime功能测试。初次沿用系统temp设置，fixture输出落在既有临时根；没有删除不属于本任务的临时文件。原始日志`upstream-tests/dsh-client-result.json`。

修正执行环境而非源码：`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`、`PYTHONDONTWRITEBYTECODE=1`、`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`，明确`--basetemp`到独立audit目录。

```text
cwd: _audit/upstream-tests/dsh
PYTHONPATH: <cwd>/python/sdk/src
python -m pytest -q -p no:cacheprovider --basetemp <audit>/upstream-tests/dsh-client-utf8-tmp python/sdk/tests/test_client.py
exit: 0
stdout: ............................. [100%]
result: 29 passed (29 test cases verified), wall time 4.16s
```

日志`upstream-tests/dsh-client-utf8-result.json`。覆盖fake subprocess协议、配置/显式DSH_HOME、通知与生命周期client行为。**不覆盖正式wheel、native持久化、TS model loop、MCP服务、跨系统恢复或Actio适配**。运行正式smoke需B03；SDK pyproject源码dev版本不能当发布pin。

## V03 Raven 上游gate/scoring

副本由 `git archive HEAD evolver tests/test_evolver_gates.py tests/test_evolver_scoring.py` 导出到 `_audit/upstream-tests/raven`，PYTHONPATH该副本；UTF-8与禁缓存设置同V02。

```text
python -m pytest -q -p no:cacheprovider --basetemp <audit>/upstream-tests/raven-gates-tmp tests/test_evolver_gates.py tests/test_evolver_scoring.py
exit: 0
37 passed in 0.68s
wall time: 1.17s
```

日志`upstream-tests/raven-gates-result.json`。证明上游paired/scoring当前语义，包括mean-only promoted与独立credited；不代表社会实验准入有效。没有运行root suite、真实bench或archive可靠性测试；本次未找到专门GsmeArchive/eligible_elites测试，不虚称覆盖。

## V04 Meta-Harness controller

副本由 `git archive HEAD experimental/harbor_meta_harness` 导出到 `_audit/upstream-tests/meta`，PYTHONPATH该副本。

```text
python -m pytest -q -p no:cacheprovider --basetemp <audit>/upstream-tests/meta-controller-tmp experimental/harbor_meta_harness/tests/test_controller.py
exit: 2 (collection error)
agents.meta_harness -> harbor.agents.base
ModuleNotFoundError: No module named 'harbor'
1 error in 0.52s
```

日志`upstream-tests/meta-controller-result.json`。状态**阻塞**；没有为了通过测试安装整个Harbor/Docker/benchmark，也没改上游导入。下一阶段仅在决定采用此执行栈时建隔离完整依赖环境；当前D方向不以此阻塞MVP。

## V05 官方规范与artifact静态验证

实际获取官方MCP spec固定SHA、npm `@modelcontextprotocol/client@2.0.0` tarball并解包；读取dist协商/transport、LICENSE。读取A2A proto、ACP schema及迁移canonical；未选/未测试A2A/ACP SDK。OTel spec/proto固定SHA raw文件及官方PyPI `opentelemetry-sdk==1.45.0` wheel已解包，读取BatchSpanProcessor/BatchProcessor与LICENSE，未安装。hash与固定链接在15 E026–E029/E042。

`additional-network.json`记录：HarnessBank与Self-Evolving Harness官方arXiv abs成功；Claude官方blog403；SQLite官方copyright成功。网页搜索连接器返回error，不能据此断言项目没有源码。Letta raw files多批manifest会覆盖，所以证据登记额外持每份采用文件hash；原始下载manifest不作为全量清单。

## V06 本轮未运行与最小后续验证

| 范围 | 未运行原因 | 下一验证 |
|---|---|---|
| 正式DSH wheel/model/MCP | 未建立完整runtime artifact组合/凭据 | B03/B08：真实启停、两个profile、cancel/receipt/catchup |
| DSH native persistence/sandbox、Strands | 原目录只读；完整依赖/native平台组合未建立 | B05/B14：隔离副本官方tests+故障注入 |
| Concordia/AgentSociety/OASIS | 模型/环境/Ray依赖未部署，本轮禁实现adapter | B07起点场景；B15批步进/失败tick |
| Graphiti/SOTOPIA | graph/LLM/Redis相关闭包未部署 | B09评委完整性；B16检索scope/ROI |
| Phoenix/Langfuse/OTLP exporter | viewer多服务未部署，license/artifact组合待准入 | B13 exact deploy小压测/可重建投影 |
| DGM/训练/搜索项目 | Docker/benchmark/GPU/数据/付费模型未就绪 | D不阻断；B17有需求再单独验证 |
| Mermaid渲染 | 未发现mmdc，Node require.resolve('mermaid')失败 | 静态检查fence/节点/流程结构；不声称渲染成功 |

## V07 文档与提交范围验收

实际静态验证：21份Markdown（README+00–19），41个内部文件链接全部存在，74张表格列数一致，8个Mermaid块的fence/括号/subgraph或alt结构闭合。97处主证据文件/符号定位无缺失，另有历史archive BlockManager补充。E001–E042、ADR01–13、B01–B17引用范围检查通过。未发现文档占位稿。

46个原参考checkout（含旧Letta archive）的HEAD与工作树状态和初始inventory一致；新Letta不完整clone单列，不混作原参考。目标文件集合仅`docs/planning/*.md`，没有产品实现、vendor、凭据、模型或原始日志。内部链接、owner/接口/ADR/backlog对照已复核：world归环境、native journal归DSH、mind/memory/canonical/admission归Python；无第二runtime loop或memory权威。

验证中发现并修正：风险表多一列分隔符；SDK实际是三个request方法而不是独立session创建方法；ADAS根许可为Apache2；Raven archive专门测试未找到，不能从gates通过推断。source-path/symbol与schema迁移路径也已校正。全部结果写`planning-validation.json`，参考final状态写`reference-final-status.json`。

Mermaid仅静态结构检查，未做renderer/parser正式渲染验证；74表格不是视觉排版认证。真实技术验证尚未完成的项目仍保持provisional/blocked，不因规划完稿改变。

上游执行日志SHA-256（原始文件不提交）：

- `dsh-client-result.json`：`56332ff7dcecdcadc681247322af3bb5de9860d1d474aacae5c1b2564064f925`。
- `dsh-client-utf8-result.json`：`0cd81b056aa4299c1a8fc8894a8709e71d4ab97520668410097931f74c77bf53`。
- `raven-gates-result.json`：`4d73081064726872c545c00cb5c847998b3627cac11c9b72e89c1e982e41618a`。
- `meta-controller-result.json`：`7fa9017273a42c96dc65ad36695f96bf813d2bc9d6ca7e6b0fb8bb8f913068ed`。

Git交付采用明确的21个planning文件列表暂存、正常首提交并推送main；提交/push的最终成功状态与SHA以仓库记录和交付回复为准，不在自身commit内容中伪造自引用SHA。若远端认证/保护阻塞则保留本地commit并如实报告。
