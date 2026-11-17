---
name: macro-14
level: macro
layer: macro
family: "estimation"
description: "Direct-route macro for estimating a count or likelihood from a vague quantifier (almost-every, most, almost-half, few, almost-none) over a known total, combined with a base-rate prior and any partial sample. Crucial split: when the question asks the BEFORE/pre-observation expectation, answer the prior from the quantifier and ignore the small sample."
---

# Quantity, Probability, and Social Estimation

## Use When
- Use when a known total is given (e.g., 5 letters, 9 monkeys, 20 students) and a vague quantifier ("almost every", "most", "almost half", "a third", "a few", "very few", "almost none") describes how many have a property, and the question asks for the specific count or likelihood.
- Use when the question explicitly asks the expectation BEFORE someone looked/counted/sampled, versus AFTER they looked: the before answer is the prior from the quantifier; the after answer updates with the observation.
- Use when a partial sample is reported ("I looked at 3 of 5; 2 had checks") and you must decide whether to use the prior or the updated estimate for the asked quantity.
- Use when several ranked quantifiers partition one total ("most order fish, a small part shrimp, very few crab") and you must back out one category's count.
- Use when the answer is a number, proportion, or probability under incomplete evidence, not a story about why something happened or what someone felt.

## Do Not Use When
- Do not use when the task is to decode what an utterance pragmatically IMPLIES as a meaning (e.g., "some of the cookies are gone" hinting "not all", or "can't you find the cleaner?" meaning "please clean now"). That is conversational-meaning inference: read the speaker's intended request behind the literal words, not a count.
- Do not use when the real task is causal attribution: why an event happened or who caused it.
- Do not use when the scene is mainly about belief, intention, emotion, trust, or social repair.
- Do not use when spatial viewpoint, visibility, or who-could-see-what is the core problem.
- Do not use when the question is primarily about offense, embarrassment, or faux pas rather than estimation.

## Decision Variable
Given a known total, a vague quantifier, and possibly a partial sample, what count or likelihood does the question ask for — and does it ask the pre-observation prior or the post-observation update?

## Direct Route Rule
Route here whenever the scene gives a total plus a vague quantity word (almost-every, most, almost-half, a-third, a-few, very-few, almost-none) and asks how many / how likely. First decide before-vs-after, then read the quantifier as a number.

## Expand With Micro Units
- Vague Quantity Prior: the approximate proportion or range implied by the vague quantifier (micro-53)
- Quantity Update After Partial Observation: how an observed portion of a set should revise a prior quantity estimate of the whole (or of a remainder or proportion) (micro-54)
- Base Rate and Typicality: how common or typical the category, outcome, or reaction is by default, used as a prior with no specific sample observed (micro-55)

## Trigger Checklist
- A total count is stated (5 letters, 9 monkeys, 20 students, 40 customers).
- A vague quantifier maps that total to a sub-count: almost-every, most, almost-half, a-third, a-quarter, a-few, very-few, almost-none.
- The question asks an approximate number, proportion, or probability for one category.
- Often the question pins a time: BEFORE vs AFTER someone looked, counted, picked, or sampled.
- The scene does not hinge on what an utterance secretly means, who believes what, or who saw what.

## Workflow
- Identify the target category the question asks about, and whether the scene gives a clear fixed set with a known total N (for example 5 letters, 40 customers) or only a general population with no fixed count.
- Map the vague quantifier to a quantity. With a known total N, estimate a number or narrow range over N: 'almost all / the vast majority' is close to N (a little below it); 'most' is a clear majority (roughly two-thirds to four-fifths of N); 'about half' is near N/2; 'a third' about N/3; 'a quarter' about N/4; 'a few / a small part' is a small positive count; 'very few / almost none' is near zero (about 1-2). With no fixed set, give a qualitative proportion instead of a single number. Treat 'almost / nearly X' as a little below the round value of X and pick the option closest to that estimate; do not assume one rigid rounding rule, since conventions for 'almost' vary across sources.
- Decide whether the question asks the BEFORE (pre-observation) expectation or the AFTER (post-observation) estimate. This is the single most important step and the most common failure point.
- If it asks the BEFORE / prior expectation: answer from the quantifier (the base rate) ALONE. A partial sample the character reports later does not change what you would have expected beforehand, so do not let a small observed count override the prior.
- If it asks the AFTER / updated estimate: integrate the prior with what was actually observed, weighing the sample by how representative and how large it is - a tiny or skewed sample barely moves a strong prior, a large representative one moves it more. As one common special case, if items were physically removed (eaten, picked, sold, taken), subtract the removed amount from the prior to get what remains.
- When several ranked quantifiers split one total, assign the largest share to 'most', the smallest (near 1-2) to 'very few / almost none', and the middle to 'some / a part'; if one category is given exactly, recover the asked category by subtracting the others from N.
- Return the specific quantity the question names - the count or proportion for that one category, or the likelihood - and match it to the option closest to your estimate.

## Special Case
**Before-observation question: use the base-rate prior, not the small sample**: When the question asks what to expect BEFORE the character looked/counted/sampled, the correct answer is the prior implied by the vague quantifier over the total, and the partial sample the character reports must be ignored. The sample only matters for an AFTER question.

Scene: Almost every letter to a company contains a check. Today the office gets 5 letters. An employee phones: 'I looked at 3 of the 5; 2 of those had checks.'
Question: BEFORE the employee called, how many of the 5 letters did you think contained checks?
Answer logic: The question is the pre-observation expectation, so use the base rate, not the report. 'Almost every' of 5 = nearly all but not quite all = 4. Ignore the observed 2-of-3 sample; it belongs only to an after-the-call estimate. Answer: 4.

## Boundary Exit Rule
- If the task is to decode what a remark IMPLIES as meaning rather than to count (e.g., 'some are missing' suggesting 'not all', or an indirect request like 'can't you find the cleaner?' meaning 'clean it now'), solve it as conversational-meaning inference: identify the speaker's intended request or implication behind the literal words. Do not convert it into a quantity.
- If the question is why something happened or who caused it, treat it as causal attribution, not estimation.
- If the answer depends on what someone believes, intends, or feels, or on the meaning being repaired in a conversation, model that mental state rather than computing a number.
- If the answer depends on who could see, hear, or notice something, reason about perceptual access, not about a count.
- If the core issue is trust history, an apology, or embarrassment, handle the relationship or social-harm dimension instead of estimating.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
A total is stated, a vague quantity word maps it to a sub-count, and the question asks how many / how likely — frequently split into a BEFORE (pre-observation) and an AFTER (post-observation) version.
