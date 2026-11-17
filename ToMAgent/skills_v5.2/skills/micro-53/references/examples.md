# micro-53 Examples and Boundaries

## Decision Variable
the approximate proportion or range implied by the vague quantifier

## Route Signal
Pick this unit when a question asks the amount or proportion a vague quantifier implies BEFORE any sample is observed: map the phrase to an approximate share, and scale to a count only if a set size is given.

## Hard Boundary
- This unit computes the prior from the quantifier (and stated size); it does NOT re-estimate from an observed sample (that is the after-observation quantity update).
- A situation may include a later observed count; if the question asks for the prior, that count is irrelevant to the answer.
- This unit does not solve negotiation, authority, typicality, or relationship scenes even when they contain words like "some" or "most."

## Shortcut To Avoid
- Do not pick an observed sample count as the prior. A prior derived from the quantifier stands on its own, regardless of what a later partial observation showed.
- Do not collapse "nearly all / almost every" into the exact total; it means short of all. Do not collapse "almost none" into exactly zero.
- Do not invent a specific count when no reference-set size is given; keep the answer to a qualitative proportion or range in that case.

## Common Failure Modes
- Answering a before/prior question with a later observed sample count instead of the quantifier-derived prior (the after-observation-update leak).
- Turning "nearly all" into the full total or "almost none" into exactly zero.
- Confusing typicality (is this kind common?) with how much of THIS situation the quantifier covers.
- Forcing a precise number when only a vague proportion is warranted, or refusing to scale even when a clear set size is provided.

## Minimal Pair
- Case: A teacher says "about half of the class finished the reading" and asks, before any tally, what proportion finished. (gold: roughly half) | Why: Pure prior: map "about half" to around 50%. No observed count is folded in. In scope for this unit. If the class size were stated, you could add an approximate count.
- Case: Later the teacher counts a sample of hands and asks how many in the whole class likely finished given that observed sample. (different answer) | Why: Near miss: the question is post-observation, so the estimate is re-derived from the sample, not from "about half." Route to the after-observation quantity update.

## Boundary Stress Test
- "Almost none" -> near zero but not necessarily exactly zero.
- "About half" -> around 50%; if a set size is given, round to a whole number near half.
- "Some" -> more than one but not all, often a context-shaped minority; keep it qualitative unless a size invites a count.
- "Nearly all / almost every" -> a near-total share just short of all, never the exact total and never zero.
- If the question asks for the estimate AFTER an observation rather than the prior, stop and route to the after-observation quantity update even though the same quantifier is present.

## Generalization Note
Vague quantifiers map to an approximate share; that share IS the prior. When a reference-set size is stated, the prior may be scaled to an approximate count; when none is stated, it stays a qualitative proportion. Keep it strictly separate from the post-sample re-estimate, from typicality, and from strategic uses.
