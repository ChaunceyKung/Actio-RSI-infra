# macro-14 Examples and Boundaries

## Decision Variable
Given a known total, a vague quantifier, and possibly a partial sample, what count or likelihood does the question ask for — and does it ask the pre-observation prior or the post-observation update?

## Route Signal
A total is stated, a vague quantity word maps it to a sub-count, and the question asks how many / how likely — frequently split into a BEFORE (pre-observation) and an AFTER (post-observation) version.

## Hard Boundary
- Not decoding what an utterance pragmatically implies as a meaning or request
- Not causal attribution
- Not belief tracking
- Not emotion inference
- Not viewpoint or visibility reasoning
- Not trust or relationship judgment

## Shortcut To Avoid
- Do not anchor on the small observed sample ("2 of the 3 I checked") when the question asks the BEFORE / pre-observation expectation — answer the prior from the quantifier instead.
- Do not read the vague quantifier loosely: pin it to a number over the total ('almost every of 5' = 4, 'almost half of 20' = 9, 'a third of 9' = about 2-3).
- Do not turn the count question into a story about motive, belief, or feeling.
- Do not ignore a clearly stated base rate / typicality just because a fresh observation is available.

## Common Failure Modes
- Anchoring on the small observed sample when the question asks the pre-observation prior — the dominant error on this scene; the gold for a BEFORE question is the quantifier-derived base rate, not the reported sample.
- Mis-mapping the vague quantifier: reading 'almost every' as 'all', 'most' as 'half', or 'almost half' as the rounded-up rather than the just-below whole number.
- Confusing the BEFORE and AFTER questions and giving the updated estimate when the prior was asked (or vice versa).
- In ranked multi-quantifier scenes, mis-ordering 'most' vs 'very few', or forgetting that 'almost none of X is sold/liked' means almost all of X remains.
- Giving an exact, falsely precise count when the quantifier only supports an approximate value, or picking an option that matches the sample number instead of the prior.

## Minimal Pair
- Case: Almost every letter contains a check; 5 arrived; someone checked 3 and 2 had checks; how many did you expect BEFORE the call? | Why: A vague quantifier over a known total, asked as a pre-observation expectation — the answer is the prior (4, from 'almost every of 5'), ignoring the sample. This is in-scope numeric base-rate estimation.
- Case: A tired traveler interrupts a host and says only 'I had a long, hot drive' (and later 'I'm thirsty'); what does he really want? | Why: Near miss: it looks like understanding a person, but the target is what the utterance IMPLIES as a request (a drink / a rest), i.e. conversational-meaning inference, not a count. It routes to indirect-meaning reasoning, not estimation.

## Boundary Stress Test
- If the scene asks what a remark secretly means or requests, it is conversational meaning, not this macro.
- If the scene asks why the person acted that way, it is causal attribution, not this macro.
- If a vague quantifier sits next to an exact number ('about 20 people', 'most of the 30'), keep it here: read the quantifier as a range or anchor the count on the stated total — the task is still estimation.
- If the scene asks for a count BEFORE observation and also reports a sample, answer the prior from the quantifier and discard the sample.
- If the scene asks what someone believes another person saw or knew, it is perspective/knowledge, not this macro.

## Generalization Note
Core skill: map a vague quantity word onto a number (when there is a known total) or a proportion (when there is not), decide whether the question wants the pre-observation prior (base rate) or the post-observation update (sample), and return the asked count, proportion, or likelihood. Some prompts of this kind are labeled 'scalar implicature' but are really numeric base-rate estimation; keep them distinct from genuine conversational-implicature ('some' meaning 'not all') reasoning, which is about implied meaning rather than counting.
