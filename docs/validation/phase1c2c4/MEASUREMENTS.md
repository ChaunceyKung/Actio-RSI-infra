# C2C4 指标覆盖

以下均从独立 verifier 返回的 metric cells 汇总；逐 seat 原记录见 [report](samples/report.json)。数值指标的 true/false 不适用，以破折号显示；missing 与 not_applicable 不填0。

| arm | metric | assigned | eligible | defined | true | false | missing | not_applicable |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | format_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | local_hard_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | format_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | local_hard_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | b_response_rule | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | joint | 32 | 32 | 8 | 3 | 5 | 24 | 0 |
| baseline | utility_A | 32 | 32 | 8 | — | — | 24 | 0 |
| baseline | utility_B | 32 | 32 | 8 | — | — | 24 | 0 |
| baseline | pareto | 32 | 32 | 8 | 4 | 4 | 24 | 0 |
| baseline | regret | 32 | 32 | 8 | — | — | 24 | 0 |
| baseline | conditional_offer_score | 32 | 32 | 8 | — | — | 24 | 0 |
| baseline | conditional_offer_gap | 32 | 32 | 8 | — | — | 24 | 0 |
| baseline | argmax_membership | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | joint_feasible | 32 | 32 | 32 | 28 | 4 | 0 | 0 |
| baseline | omniscient_upper_bound | 32 | 32 | 32 | — | — | 0 | 0 |
| baseline | public_hard_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | self_hard_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | public_hard_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | self_hard_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | text_verified_A | 32 | 32 | 9 | 8 | 1 | 23 | 0 |
| baseline | domain_executable_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | text_verified_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| baseline | domain_executable_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | format_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | local_hard_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | format_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | local_hard_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | b_response_rule | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | joint | 32 | 32 | 8 | 3 | 5 | 24 | 0 |
| candidate | utility_A | 32 | 32 | 8 | — | — | 24 | 0 |
| candidate | utility_B | 32 | 32 | 8 | — | — | 24 | 0 |
| candidate | pareto | 32 | 32 | 8 | 4 | 4 | 24 | 0 |
| candidate | regret | 32 | 32 | 8 | — | — | 24 | 0 |
| candidate | conditional_offer_score | 32 | 32 | 8 | — | — | 24 | 0 |
| candidate | conditional_offer_gap | 32 | 32 | 8 | — | — | 24 | 0 |
| candidate | argmax_membership | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | joint_feasible | 32 | 32 | 32 | 28 | 4 | 0 | 0 |
| candidate | omniscient_upper_bound | 32 | 32 | 32 | — | — | 0 | 0 |
| candidate | public_hard_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | self_hard_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | public_hard_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | self_hard_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | text_verified_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | domain_executable_A | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | text_verified_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |
| candidate | domain_executable_B | 32 | 32 | 8 | 8 | 0 | 24 | 0 |

assigned=eligible+not_applicable；eligible=defined+missing；布尔defined=true+false。
format/domain 相关，B local_hard/response_rule 同源；public/self 是原 hard 的组成，不将它们相加作为独立证据。条件得分不含接受概率，正 gap 或全知 regret 不能直接判原 hard 违规。
