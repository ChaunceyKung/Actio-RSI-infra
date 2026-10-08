# 人工校准交接

当前状态 **BLOCKED**，真实标签为 0。分发 [可读 Markdown](annotations/annotation.md)、[实际盲化 JSONL](annotations/cases.jsonl) 和 [空白输入模板](annotations/blank-labels.jsonl)。3 个 case 是两个卡与一次不同实际回应的工程样例，不是 3 个独立研究单位。

[internal.json](annotations/internal.json) 只供数据管理员保管，包含真实 agent 映射和证据来源。公开包只呈现稳定 seat_1 / seat_2、公开情境、各自目标/约束/初始关系、完整两步实际行动、ActionSpec 与维度 anchors。隐藏 provider/model、arm、历史评分、fixture 脚本和期望结果。Markdown 逐例展示实际 view JSON 与其 hash，JSONL 使用同一内容。模板包含 opaque task/episode/trace/rubric/view/alias/group 哈希绑定，无评分。

未来流程：

1. 在授权和招募完成后，为两名独立标注者分配不相互可见的副本。标注者不得看到 preset 评分或另一人的结果。记录 rater ID、日期/协议版本与真实来源；不要把“human”字符串当作真实性证明。
2. goal 单独评分 0..10；relationship 单独评分 -5..5。锚点来自 scheduling-rubric.v1，当前未校准。两步符号行动可能不足以判断关系变化，使用 `cannot_judge`、null score 和具体原因。`scored` 必须给整数及依据。不得由任务是否完成推导关系提升。
3. 每人提交一行每 case，填入显式 rater 与 provenance=`human`，保留全部绑定。导入报告逐项列出缺标、错 seat/version/binding、重复和冲突；拒绝静默覆盖或补零。`synthetic_label_fixture` 是独立来源，绝不可计入人工有效样本。
4. 保留两名原始标注；单列每维度可评分覆盖率、缺失率及 cannot_judge 原因，再比较有序分数一致性。预先约定 weighted kappa 或 ordinal Krippendorff alpha 的选择、权重和缺失处理，按 family 聚类，不以 repeat 作独立样本。连续误差/等级相关可作为补充，不能相互替代。
5. 分歧由第三位裁决者查看证据并记录理由和新版本，不能覆盖原始标签。重复/冲突导入不等于两人分歧；当前导入工具保留维度分歧，尚不实现裁决数据库。
6. 有足够真实标签之后，按目标与关系分别比较 judge 和人工分布、偏差、误差、排序及不能判断率。冻结模型、rubric 和分组后再决定扩大数据；所有指标报告原始分母与聚类方式。

本轮只验收空模板、绑定、显式合成来源、错绑定拒绝、缺标、重复/冲突和分歧保留。没有实测人工相关性、显著性、置信区间或校准通过结论，也没有自动联系标注者。
