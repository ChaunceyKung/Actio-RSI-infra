# C2C4 结果

工程 **INCOMPLETE**；C1 本评估为 **infrastructure_failure**，eligible_for_activation=false。本轮继承合成诊断开发集，不是holdout、模型排名或能力准入。冻结产品提交 `3750954ea7cc8dff64115039e27bb671fa618d01`；最终交付提交通过Git提交本身与最终消息查验，不写自引用hash。

停止点为 **ep-16 / baseline / S-hidden-w0-reversed / A**，即第33次实际发送。响应HTTP200含 `event: error`；冻结审计拒绝不支持的SSE字段，适配层没有可认证的action文本。该请求保持unknown，未用作行动、B历史或行为评分；没有修合同、重试或补样。95个not_run包含该episode的B与后续47个完整episode。详见 [停止证据](stop.json)。最终离线核验PASS表示停止证据可验证，不表示真实campaign工程完整。

| 执行层次 | 实际 / assigned |
|---|---:|
| 技术完整 episodes | 16 / 64 |
| 执行已解决 episodes | 16 / 64 |
| attempted / sent / response / usage / admitted | 33 / 33 / 33 / 32 / 32 |
| assigned seats | 128 |
| unknown / protocol_error / not_run | 1 / 1 / 95 |
| 因可信非法A跳过B | 0 |
| 候选配对执行完整 | 8 / 32 |
| 至少一项defined指标delta非零的候选对 | 2 / 32 |

上述并列值是不同阶段的计数，不混为同一成功率。逐臂 [指标覆盖](MEASUREMENTS.md)、[具体约束错误](VIOLATIONS.md) 与 [三类比较摘要](COMPARISONS.md) 分别列出完整分母；完整数据见 [report](samples/report.json) 和 [三类比较](comparisons.json)。missing/not_applicable均为null，不用0替代。A条件得分保留所有同分argmax，正gap不自动判原hard违规；joint/regret也不直接判A错误。

| 描述性对照 | assigned | A行动相同 / defined | B行动相同 / defined | 执行完整 |
|---|---:|---:|---:|---:|
| hidden_world | 32 | 0/0 | 0/0 | 0 |
| presentation | 32 | 0/0 | 0/0 | 0 |

B同实际A子集在comparison中标为条件化描述，完整32个展示对照仍保留。隐藏世界A允许输入相同是Gate，输出相同不是Gate；展示同时改变两actor的options，A行动变化又改变B历史。单次差异可能混合采样和时间变化，不识别稳定位置偏好或因果收益。32展示只有16不同A视图，加入两臂32种输入条件，在两隐藏世界重复；独立研究单位和真人标签均0。

候选已观察格式/原hard违规记录 0 项，baseline 0 项。逐项单位和metric在report中保留；B local_hard与response_rule同源，format/domain也相关，不能当独立证据计数。没有capability pass，旧C1/C2C2决定保持不变。

权威副本谱系为 3 evaluations / 2 evaluation decisions，另保留6份原candidate decision。原Store identity、所有旧事件/plan/binding/policy/decision由固定C2C2 reader和代码信任表核验；schema仍为4。

历史生成尝试139，本轮实际sent 33，累计 **172**；历史目录GET1另列。无额外smoke、目录请求、补样、模型筛选或第二批。金额策略uncapped，费用cost原值与来源保留；币种/单位、供应商账单与上游权重身份UNVERIFIED，不估USD、未知不填0。

本机开发/错误分支及失败预演发送 145，其中unknown 2；最终完整预演发送 128，均为loopback合成响应，与真实费用分开。本轮共核查 306 个具名Job和 6 个服务；全部Job已reaped/inactive，相关端口无监听，active authorized/reserved/sending为0。5个服务有join收据；1个失败预演服务被包装器整体时限终止，未产生join收据，保留该缺口并单独核查进程退出/端口关闭。unknown账务与永久claim保留，不授予真实重跑资格。

[本机验收](local-acceptance.json) 绑定最终产品源码；[开发记录](DEVELOPMENT.md)保留所有失败与实际命令。固定C2C2完整delivery/v4原库和固定C3包分别通过；共享源码变化没有刷新历史pins。公开plan/preflight/analyze/verify/lineage实跑并加只读guard；execute通过公开CLI完成本机矩阵与本轮唯一真实campaign。

完整raw/adapter/native、数据库和reasoning只保存在 [受控交付引用](controlled-delivery.json) 指向的本地包；Git只发布行动、分母、测量、谱系及审计摘要。hash不是供应商签名或独立时标。binary_source_mapping=unproven，full_controller_recovery=unsupported。研究有效性UNESTABLISHED，训练/judge/真人校准/生产激活未解锁。

停止于C2C4；不自动启动C2C5或新批次。可信规则错误只定位本轮具体条件；零差值也不证明等效或无效。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [manifest](evidence_manifest.json)。
