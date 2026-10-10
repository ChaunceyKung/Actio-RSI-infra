# C2C4 开发记录

从已同步的 `dbb0f815c5d1baae28e37ddaeb8f68b6b442f0dc` 开始，原工作树干净，建立 `phase1c2c4-visible-rule-robustness`。初次fetch及一次普通重试出现schannel TLS握手失败，随后使用HTTP/1.1的普通fetch成功；未关闭TLS验证。C2C3交付与C2C2固定reader均为祖先。

首先以固定reader认证C2C2完整controlled delivery及关联v4原库，并以固定C3 reader核验原portable package；guard禁止key/env/network/process/runtime import/write。六项内容pins另从封存body/proposal/scaffold独立重算，均匹配。旧历史数据/决策/claim不改；历史raw reader使用代码选定固定Git版本，artifact无源码执行权限。

新v10/v6合同、完整TaskSpec、64/128计划、三类比较、类型化分母、v4快照/历史分派和公开CLI均在首次真实发送前实现。先有纯empty报告开发探针，随后干净离线bootstrap并安装当前产品；正式验收收据绑定产品逐文件hash和实际argv。C2C4要求的是首次真实发送前冻结；本机开发/合成验收在冻结前进行，未据合成或真实结果改数据/原候选。

验收分开记录：纯规则/映射/分母/原子claim与历史；实际DSH/Concordia行为错误和前驱处理；unknown/headers60超时/完整后缀；controller/verifier失败库存；完整64episode正常128seat预演；隐藏世界同A输入不同输出的独立fixture；公开CLI、只读guard及重新seal篡改拒绝。异常fixture产生的unknown被永久保留，不能在汇总时当作0发送或已释放费用。

`evidence/` 为追加记录，失败不删除或覆盖；每个record携带当时产品源码。完整预演与必要错误分支串行，live后不改冻结产品、不重跑。手算向量断言及隐藏世界输出不同的fixture属于验收补充；产品源码保持同一版本。最终local-acceptance引用与最终产品匹配的实际PASS记录，不能引用旧产品快照替代。

源v4复制使用SQLite backup，保留backup与完整行语义hash，源前后比对；追加evaluation不重置原候选decided/claimed。并发claim两调用只有一个赢家，改输出root和重复execute均不授予新资格。原六个candidate decision与C2C2 evaluation decision保持精确绑定。

清理脚本只汇总本轮explicit roots、全部失败/正常测试、预演和live。具名Job逐个查询inactive/reaped，服务join和端口监听独立核对，账本authorized/reserved/sending计数必须0。永久claim和历史active marker文件保留；失去运行进程的marker不等于仍有发送资格，unknown账务不会因清理而释放。历史139/目录GET1与本机及本轮live分列。

发布扫描在本机内存读取ignored凭据作精确比对，这是独立的发布检查，不初始化provider、不打印秘密及任何派生属性。solver注入只在专用execute通过发布Gate后进行。历史/本轮raw reasoning不公开，也不用作事后行为解释。完整raw材料留本地，Git只含脱敏事实/行动/谱系/审计摘要。

最终停止状态、计数、具体失败和测试收据见 [RESULTS](RESULTS.md)、[local acceptance](local-acceptance.json) 及 [manifest](evidence_manifest.json)。研究有效性、账单/上游身份、binary_source_mapping与full_controller_recovery的旧限制保持原义。

首次完整预演 `D:/actio-c2c4-rehearsal-v1` 的64 episodes/128 sent/128 admitted均完成，unknown=0；随后全目录凭据排除扫描尚未结束，验收包装器的7200秒整体时限终止了CLI。该次整包验收 **FAIL**，没有 delivery，也没有 C4 evaluation decision，不据128成功发送将整个验收改记PASS。[原失败收据](evidence/cli-1e6399a5e5e8.json)和全部本地材料保留。此时副本3 evaluations/1 evaluation decision，原6份candidate decision不变。

[中断清理核对](evidence/interruption-39c22b063622.json)确认128个具名Job全部reaped/inactive、控制进程退出、原loopback端口59337无监听、active发送状态0。服务因控制进程被终止，没有join收据；保留这个缺口，不伪造join。该128次本机发送归入失败开发预演，最终通过的主预演另列。unknown/claim与失败目录均不删除，full_controller_recovery仍unsupported。

只修正验收包装器：本机完整execute不再加与逐请求/Worker期限无关的整体截止时间，运行前先记录实际argv和包装器source hash。产品源码、任务、计划、费用规则和所有逐请求期限均未改变。受影响的完整CLI验收使用新目录 `D:/actio-c2c4-rehearsal-v2` 重新执行；旧失败不覆盖。清理辅助脚本首版误用了表名candidate_decision，SQLite拒绝；[工具失败记录](evidence/tooling-failure-5be3035617c6.json)保留当时源码与错误，随后按真实decision表核验通过。该工具错误没有发送或修改产品/权威库。

首次真实启动尝试在冻结提交 `2cebb025ad0424aafbe0d7c76bab1da48b162442` 下，于发送前的发布核对失败：包装器 clean_env 的 PATH 只有 System32，找不到 Git。未创建 live root/claim，未进入 solver 凭据解析或 campaign execute，真实发送0。[失败收据](evidence/launch-gate-failure-e87861a29554.json)保留实际 argv、原包装器源码与错误。修正仅在包装器隔离 PATH 加入本机解析的 Git 目录，不继承 provider 环境、不改变产品合同；相同隔离环境的 Git/version 与两个远端读取[验收通过](evidence/launch-git-admission.json)。重新提交并发布冻结后才允许首次 campaign；这次发送前失败不伪称已执行，也不删除任何 claim。

唯一真实campaign在修正后的冻结提交 `3750954ea7cc8dff64115039e27bb671fa618d01` 下运行。发布核对 2026-10-10T07:06:08.463Z 早于首个intent 2026-10-10T07:06:10.478Z。前16个episode技术完整；ep-16 / baseline / S-hidden-w0-reversed 的A为第33次发送，HTTP200的SSE出现冻结审计不支持的 event 字段，未产生可认证行动，账务保持unknown。控制器按合同停止，完整保留95个not_run seat、47个整episode后缀及本episode未运行的B；不将技术缺失当行为通过。实际33 response、32可信usage/admitted，无重试或第二批；主评估 infrastructure_failure。详见 [结构化停止证据](stop.json) 和 [实际启动收据](evidence/live-launch.json)。产品源码、合同与期限在首发后均未修改。
