# C2C3 开发与过程限制

起点为`217af1bcb106884fd4c164fc370f00cbaecffcc3`，fetch后与origin/main相等，工作树干净。设计文本先在`bc645c1`提交，含8组全部数值、排序和政策。新增产品、固定数据/政策/指标和测试在`0a66334`提交，随后进行正式验收。旧suite/card/oracle/candidate/live产品文件未修改。

| 尝试 | 来源与结果 | 保留的界限 |
|---|---|---|
| 固定C2C2 reader核验 | [historical-source.json](historical-source.json)：原完整delivery通过，旧公开report精确相等 | 仅本机原材料认证；不公开raw |
| 初始编译与导入探针 | 新3模块编译通过；`-I`忽略PYTHONPATH，旧安装没有新模块，ModuleNotFoundError | 实际命令及该源码hash在[补充开发记录](evidence/development-probes.json) |
| 源码路径有限探针 | 8/16/32、416组合及四个合成Gate通过 | 发生在机器可读freeze之前；属于过程顺序偏差，不算最终验收 |
| 数据/政策/指标封存 | [freeze](frozen-design/freeze.json)，数据hash固定；之后没有按探针结果调题或控制策略 | 设计文本先冻结，但不声称首次有限计算前已封存所有机器数据 |
| 正式源码纯测试 | [tests](evidence/tests-d4dd34039d2b.json)，7项通过 | 无旧慢期限/runtime/live矩阵复跑 |
| 首次CLI guard | [FAIL](evidence/cli-eadb83bc86b5.json)，误拦公开引用文件名 | 仅修改tooling guard，不修改产品合同/源码 |
| 修正后的CLI guard | [PASS](evidence/cli-b6e40881b375.json)，8个流程通过，移址报告相等 | 真实模块入口在受限子进程中执行，无worker/provider |
| 最小安装和literal CLI | [PASS](evidence/literal-cli-027c3161315a.json)，安装+4条`-m`命令 | 只复制纯导入闭包，不安装网络/runtime依赖 |

所有验收记录含运行时源码hash和argv；FAIL不会改标为最终PASS。公开包的产品source pins与纯测试及两类CLI一致。开发探针原快照保留在frozen-design，后续只补充CLI/封装/诊断说明。

C2C2 `local-acceptance.failed_attempts_retained=[]`不等于历史从无失败；其[DEVELOPMENT](../phase1c2c2/DEVELOPMENT.md)、[CLI开发失败](../phase1c2c2/evidence/cli-development-failure.json)和早期矩阵快照仍保留，没有刷新旧manifest或reader。

本轮未创建受管Worker/Job、HTTP服务或监听端口，真实模型/provider/目录/MCP调用0，原DB/账本/claim不改。最小venv和Python CLI子进程已正常退出，不混用历史197个Job的清理统计。

最终发布扫描仅在本地内存读取ignored凭据进行精确字节比对，并比对历史/本轮旧raw reasoning是否误入新增公开文件；不输出秘密及其长度/hash，不用于diagnostic CLI或任何网络调用。诊断运行本身credential_reads=0；发布扫描单列，避免将其误称全阶段没有读取凭据文件。
