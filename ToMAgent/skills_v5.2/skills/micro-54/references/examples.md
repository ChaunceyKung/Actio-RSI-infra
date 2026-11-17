# micro-54 Examples and Boundaries

## Decision Variable
how an observed portion of a set should revise a prior quantity estimate of the whole (or of a remainder or proportion)

## Route Signal
Route here when a prior quantity over a set is followed by a partial observation and the task asks for the revised estimate; keep the observed part known, apply the prior over the unseen rest, and let sample size and representativeness set how far the estimate moves.

## Hard Boundary
- This unit revises an estimate after a portion is observed. Reading a vague quantifier with no observation belongs to the vague-quantity prior.
- This unit is about a quantity, not causal responsibility, blame, or motive.
- This unit needs a fresh partial observation; pure 'how common is this category' reasoning is base rate and typicality, not an update.

## Shortcut To Avoid
- Do not give the prior-only answer once a portion has been observed, nor an updated answer when nothing has been observed; the presence of an observation decides.
- Do not naively scale the observed rate straight up to the whole when the observed slice is a known count; only the unseen part is estimated from the prior.
- Do not move the estimate the same amount regardless of sample size; a small or biased sample should barely shift it, a large unbiased one should shift it a lot.
- Do not snap to the clean fraction when the prior says 'almost'; trim the estimate down by a little. And do not re-estimate cases already counted exactly.

## Common Failure Modes
- Answering with the prior-only number when an observation is available, or updating when no observation was actually made.
- Reporting the raw observed count as the whole-set total instead of adding the prior over the unseen remainder.
- Ignoring sample size and representativeness, moving the estimate too far on a tiny or biased sample or too little on a large unbiased one.
- Snapping to the exact round fraction when the prior said 'almost,' which should shave the count down.
- When categories are joint, forgetting to subtract the observed category and any small residual to back out an unobserved one, or treating a remainder question as a whole-set question and skipping the subtraction.

## Minimal Pair
- Case: A set has a prior of 'almost all,' a definite slice of it is observed and counted, and the question asks the revised whole-set total. | Why: An update: take the observed slice as known and add the prior over the unseen rest, trimmed by the 'almost' hedge. Stays in this unit.
- Case: The same set and the same 'almost all' prior, but nothing is observed and the question asks the expected total from the quantifier alone. | Why: Single-variable near-miss: only the observation is removed. With no observation to fold in, the answer is the prior over the whole set and routes to the vague-quantity prior, not here.

## Boundary Stress Test
- If the observed part already exhausts the relevant unseen cases, the revised estimate may equal the observed count because the prior adds nothing more.
- If a prior-only and an updated question share one story, answer each with its own logic; do not reuse the prior-only number for the updated question.
- If the observed sample is small or visibly biased, keep the estimate near the prior; only a large, representative sample justifies a large move.
- If the question asks 'who caused' or 'why' rather than 'how many,' leave this unit.

## Generalization Note
The same operation covers any set with a prior and a partial look at it: read the prior quantity over the whole, lock in the observed count, estimate only the unseen remainder from the prior, let the sample's size and representativeness govern how far to move when generalizing, apply any hedge such as 'almost,' and answer the revised quantity asked, whether a total, a remaining count, or an updated proportion.
