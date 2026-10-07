# Concordia 与最小评估 envelope

固定 `b71d202750e23444ce1bf28d9f114bcd88aa41db` 的**真实 `Sequential` Engine** 经正常package import运行，未复制/重写调度loop。两个最小 external Entity 实现name/observe/act；`act`调用助手用的同一`runtime_adapter.Adapter`，经真实官方SDK与DSH TS loop。GM是明确的deterministic Entity输出fixture，未调用付费GM模型，也没有第二solver模型。

证据：[concordia.json](evidence/concordia.json)，包括start manifest、实际GM调用序列、step_callback、intent/session/seq关联与完整实际provider输入。

| 检查 | 结果 |
|---|---|
| 实际Engine调度 | PASS；每步走terminate/next GM/make observation/next acting/next ActionSpec/act/resolve；环境选择顺序B→A |
| ActionSpec | PASS；JSON spec经过真实 `action_spec_parser` 转为CHOICE；external Entity把spec传DSH，再用原生 `ActionSpec.validate`校验 |
| 非法action | PASS；DSH固定输出INVALID，validate抛错后没有进入resolve，GM world与resolution都为空 |
| 合法intent与resolved event | PASS；抓取GM `act(RESOLVE)`的实际结果和 `observe(EVENT)`写世界，不把Engine.resolve的None伪造成outcome |
| 观察隐私 | PASS；每个actual provider-input中包含自身PRIVATE_ONLY_A/B，排除另一Agent标记及GM_PRIVATE_FULL_LOG；检查输入而非只看答案 |
| 同步边界 | PASS；Entity.act用同步SDK桥，单独受管线程处理通知等待；没有嵌套asyncio.run；外层Job总期限及每run期限有界 |
| 关联 | PASS；act-A/act-B、native session A/B、seq列表、flush marker，与step和GM resolution对应 |
| 起点重执行 | PASS；独立短根/新session重新运行两次，world与行动顺序相同 |
| mid-run完整恢复 | unsupported/false；未保存完整Engine cursor/external Entity/GM/native session快照 |

本profile工具仍只有只读fixture MCP，social Agent此场景不发工具请求。对两个Agent分别保留观察上下文；GM拥有world、调度与裁决，DSH拥有native session，Python probe只记录domain关联，不设第二world/memory writer。ActionSpec边界检查是薄桥职责；不能假定Engine自己会检查所有external Entity输出。

start manifest覆盖source/engine/order/options/私有标记规则/fixture/model/maxsteps，并记录adapter/plugin hash；明确排除mid-run state、live模型响应和外部世界完整状态。结果仅证明当前确定性seam，不代表通用simulator adapter或非确定性社会实验可重复性。

P5使用 [eval_probe.py](../../../probes/phase1a/eval_probe.py) 的受控返回值验证，**没有运行SOTOPIA真实parser/evaluator，没有迁移Raven**。13个checks在 [evaluation.json](evidence/evaluation.json)。

| 输入/错误 | Envelope分类 |
|---|---|
| 正常两身份+goal/relationship有限数值且轨迹合法/完整/隔离/预算内 | valid_measurement（不是有效性/统计显著性证明） |
| []、错identity、缺维度、字符串/非有限值、judge异常 | invalid_measurement；保留原始原因，不计任务零分 |
| 合法执行但非法行动、观察泄漏或超请求预算 | task_failure（此分类只指受控任务约束） |
| worker/transport基础设施失败 | infrastructure_failure |
| partial轨迹、缺native barrier | insufficient_evidence |

score范围0–10和两个维度仅是这个fixture的schema，不是未来SOTOPIA研究rubric的冻结决定。live预算0、固定输出，不估价、不使用发现的keys，未声称真实模型能力、社会效度、统计功效或演化收益。

B09输入必须等下一slice运行/恢复验收后确定：pilot数据与invalid率、独立实验单元（episode/cluster而非消息条数）、baseline/candidate配对及干扰假设、train/validation/holdout隔离、主指标/约束/最小有意义差异、方差/power和judge校准、授权provider/model与总预算。没有预先承诺+3pp或特定样本量。
