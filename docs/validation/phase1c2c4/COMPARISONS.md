# C2C4 三类描述性比较

三类各 assigned=32，彼此相关，不合并为研究样本量。执行覆盖与逐指标覆盖分列；同输入的输出差异允许存在。

| comparison | assigned | execution defined | execution missing | A same / defined | B same / defined |
|---|---:|---:|---:|---|---|
| hidden_world | 32 | 0 | 32 | 0 / 0 | 0 / 0 |
| presentation | 32 | 0 | 32 | 0 / 0 | 0 / 0 |
| candidate | 32 | 8 | 24 | 见逐对行动和指标 | 见逐对行动和指标 |

| candidate metric | assigned | eligible | defined | missing | not_applicable | nonzero delta / defined |
|---|---:|---:|---:|---:|---:|---|
| format_A | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| local_hard_A | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| format_B | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| local_hard_B | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| b_response_rule | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| joint | 32 | 32 | 8 | 24 | 0 | 2 / 8 |
| utility_A | 32 | 32 | 8 | 24 | 0 | 2 / 8 |
| utility_B | 32 | 32 | 8 | 24 | 0 | 1 / 8 |
| pareto | 32 | 32 | 8 | 24 | 0 | 2 / 8 |
| regret | 32 | 32 | 8 | 24 | 0 | 2 / 8 |
| conditional_offer_score | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| conditional_offer_gap | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| argmax_membership | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| joint_feasible | 32 | 32 | 32 | 0 | 0 | 0 / 32 |
| omniscient_upper_bound | 32 | 32 | 32 | 0 | 0 | 0 / 32 |
| public_hard_A | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| self_hard_A | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| public_hard_B | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| self_hard_B | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| text_verified_A | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| domain_executable_A | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| text_verified_B | 32 | 32 | 8 | 24 | 0 | 0 / 8 |
| domain_executable_B | 32 | 32 | 8 | 24 | 0 | 0 / 8 |

| B conditioned on same actual A | assigned | eligible | defined | missing | not_applicable | B same | B different |
|---|---:|---:|---:|---:|---:|---:|---:|
| hidden_world | 32 | 32 | 0 | 32 | 0 | 0 | 0 |
| presentation | 32 | 32 | 0 | 32 | 0 | 0 | 0 |

B 同实际 A 子集是事后条件描述。展示比较同时改变两 actor 的 options；A 变化又改变 B 的公开历史，不把所有 B 差异归因于自身选项位置。
每组行动、允许输入检查、逐指标 null/delta 与原因见 [完整比较](comparisons.json)。单次差异可能混合采样与时间变化；零差值不证明等效，非零不证明泛化收益。

本轮8个完整候选配对中，6对的全部可比较指标delta为0；另2对如下。delta均为C1减B0，未运行的24对仍保留missing。

| card | B0 A / B | C1 A / B | joint delta | utility A delta | utility B delta | regret delta |
|---|---|---|---:|---:|---:|---:|
| H-tie-w1-reversed | apple for 1 coins / reject | banana for 1 coins / accept | 1 | 3 | 0 | -3 |
| S-tie-w1-normal | propose:afternoon / accept | propose:morning / decline | -1 | -5 | -2 | 7 |

两对的原format/hard/B响应规则均通过；A条件argmax集合成员均为true、条件gap均为0。联合结果一正一负，不能将同分中的实际行动或全知regret差异直接解释为原规则错误、稳定偏好或可泛化候选收益。
