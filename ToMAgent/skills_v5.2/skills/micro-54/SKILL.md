---
name: micro-54
level: micro
layer: L7
family: "quantity-probability"
description: "After observing part of a set, subset, or sample, revise a prior quantity estimate: keep what was directly observed as known, apply the prior to the still-unobserved remainder, and weigh how representative and large the observed portion is before reporting the asked-for total, remaining count, or revised proportion."
---

# Quantity Update After Partial Observation

## Use When
- Use when a prior gives a rough quantity over a set (a vague quantifier like 'most' or 'almost half,' a base rate, or a stated proportion), THEN a portion of that set is observed, counted, or checked, and the task asks for the revised estimate.
- Use when the answer requires combining what was directly seen in the observed portion with the prior applied to the part that was not seen.
- Use when the task is to generalize from a sample to a larger population and the sample's size and representativeness should adjust how far the estimate moves.
- Use when the question asks for a revised whole-set total, how many remain after some were removed or accounted for, or an updated proportion once a partial count is in hand.
- Use when a speaker first gives a vague quantifier about people's views (e.g. a manager says 'most of the 12-person team supports the plan'), then a portion is actually polled or checked (e.g. you ask 4 of them and all 4 support it), and the task asks for the revised count of supporters across the whole team.

## Do Not Use When
- Do not use when no portion has been observed and the answer rests only on reading a vague quantifier over the whole set; that is the vague-quantity prior, not an update.
- Do not use when there is no observation and the estimate rests purely on how common or typical a category usually is; that is base rate and typicality reasoning.
- Do not use when the central question is why an outcome happened or which factor produced it, even if quantities are mentioned; that is causal attribution.
- Do not use when the whole set is fully observed and the answer is exact arithmetic; that is direct counting, not estimate revision from a partial view.

## Decision Variable
how an observed portion of a set should revise a prior quantity estimate of the whole (or of a remainder or proportion)

## Trigger Checklist
- A prior fixes an initial quantity over the set: a vague quantifier, a base rate, or a stated proportion.
- A portion of the set is then observed, counted, or checked, yielding a concrete number for that portion.
- The observed portion is treated as known, while the rest of the set still follows the prior.
- The estimate must be moved from its prior value toward what the observation implies, by an amount that depends on how large and representative the observed portion is.
- The target is a quantity (a total, a remaining count, or a revised proportion), not blame, motive, social status, or the bare meaning of a vague word.

## Workflow
- Start from the prior expectation. Read the initial quantity over the whole set from whatever the prior is: a vague quantifier ('almost half of 20' is a bit under 10), a base rate, or a stated proportion. With no observation, this prior is the whole answer and the task belongs to the vague-quantity prior.
- Read the observation exactly: which part of the set was looked at, how large that part is, and what was found there. This observed portion is now KNOWN, not estimated.
- Incorporate the observation. The observed portion contributes its actual count; the still-unobserved remainder continues to follow the prior. Combine them rather than discarding either piece.
- PRIMARY method: when a definite slice has been observed and counted, lock that observed count as known and estimate ONLY the unseen remainder from the prior; do not re-weight the slice you already counted. SECONDARY branch (only when the task is to generalize a sample's RATE to a larger population that was not counted): weigh representativeness and sample size, letting a large, unbiased sample move the estimate substantially toward what was observed while a small or biased sample moves it only a little. Most items are the primary case; use the secondary branch only when no exact slice-count is available and you must project a rate.
- Decide which quantity is asked and do the matching arithmetic: for a whole-set total, add the known observed count to the prior applied over the remainder; for a remaining count, subtract what was removed or accounted for from the prior total; for a revised proportion, blend the observed rate with the prior in proportion to how much weight the observation deserves.
- When a vague quantifier carries a hedge such as 'almost,' trim the estimate away from the clean fraction (almost half of 20 is a little under 10, not exactly 10) before selecting the final answer.
- When several categories are named and one was observed, use the totals and the observed category to back out an unobserved category by subtraction.

## Special Case
**Known observed part plus the prior over the rest**: The PRIMARY and most common case: the question asks for a whole-set total when a definite slice of the set has been observed. Then the answer is the exact observed count for the part seen PLUS the prior applied only to the part not seen, rather than scaling the sample's rate up to the whole or ignoring the observation. The rate-generalization method (where representativeness and sample size govern how far the estimate moves) is a SECONDARY branch reserved for when there is no exact slice-count and you must project a sample's rate onto a larger uncounted population; do not reach for it when a definite slice has already been counted.

Scene: A box holds 10 light bulbs, and from past stock you expect almost all of them to work. You test 4 of the 10 and find all 4 work.
Question: How many of the 10 bulbs do you now expect to work?
Answer logic: The 4 tested bulbs work (known). For the 6 untested bulbs the prior still applies: 'almost all' makes each very likely to work, so expect nearly all of them too. Anchor the final number on the WHOLE-SET hedge: 'almost all' of 10 means just short of all 10, so the revised total is about 9, not 10 and not a sharp drop. The 4 known-good bulbs plus the prior over the 6 unseen land there: roughly 9 working, with the 'almost' trimming the count below the full 10.

## Boundary Exit Rule
- Exit to the vague-quantity prior when no portion has been observed and only a vague quantifier must be read over the whole set: that is the prior, not an update.
- Exit to base rate and typicality reasoning when there is no fresh observation and the estimate rests on how common or typical a category usually is.
- Exit to causal attribution when the central question is why an outcome happened or which factor caused it.
- Exit to a broader quantity route when one scene chains several operations, such as reading a prior, then updating from an observation, then comparing the prior and revised estimates against each other.
- Do not force this unit when the whole set is fully observed; a complete count needs direct arithmetic, not partial-observation updating.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when a prior quantity over a set is followed by a partial observation and the task asks for the revised estimate; keep the observed part known, apply the prior over the unseen rest, and let sample size and representativeness set how far the estimate moves.
