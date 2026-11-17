---
name: micro-55
level: micro
layer: L7
family: "quantity-probability"
description: "Judge the most likely or most natural answer from how common or typical a category, outcome, or reaction usually is, rather than from a vague quantifier word or a freshly observed sample count."
---

# Base Rate and Typicality

## Use When
- Use when the question asks which outcome, category, trait, role, or reaction is most likely, given how common or typical it usually is.
- Use when the answer is the default emotional or behavioral reaction a normal person has to an ordinary event (gift, win, loss, threat), and no twist makes the situation unusual.
- Use when a vivid individual description must be weighed against a stated population frequency or prior category prevalence.
- Use when the inference is about prior likelihood before any decisive direct observation settles the case.

## Do Not Use When
- Do not use when the task is to recover the approximate range a quantifier word implies (some, most, almost all, about half). That is about word meaning, not category likelihood. Handle that with the vague-quantity interpretation skill.
- Do not use when a specific sample, partial count, or newly seen subset was observed and the estimate must be revised on that data. Observed-sample updating is the closest neighbor and the main confusion; route it to the quantity-update-after-observation skill.
- Do not use when the question asks what caused an outcome rather than which outcome was more likely beforehand. Naming a cause is causal attribution.
- Do not use when the decisive variable is a character's belief, perception, or intention rather than objective base rate; use the matching belief, perception, or intention skill.
- Do not use when an explicit fact in the story already settles the answer, so the prior is irrelevant.

## Decision Variable
how common or typical the category, outcome, or reaction is by default, used as a prior with no specific sample observed

## Trigger Checklist
- The question asks what is most likely, most probable, typical, expected, natural, or common.
- The decisive cue is a prior: a stated population frequency, role frequency, ordinary prevalence, or the default reaction to a familiar event.
- No specific sample was observed in the scene that would force the estimate to be revised on that data.
- The answer is a default given what is usual, not a quantifier word's meaning and not a cause.
- Any vivid individual description present is representative or stereotype-like, not specifically diagnostic.

## Workflow
- Confirm the operation is a prior-likelihood judgment: no observed sample to update on, no quantifier word to decode, no cause to name. If any of those, exit (see Boundary Exit Rule).
- Name the candidate categories, outcomes, or reactions being compared.
- Find the prior: a stated frequency or population proportion if given, otherwise the default or most usual case for this ordinary situation.
- For a normal event with no twist, pick the typical reaction a normal person would have (a longed-for gift gives happiness, a win gives pride, a threat gives fear).
- If a vivid description is present, test it: is it specifically diagnostic of the rare category, or merely representative? If merely representative, keep the base rate central and do not switch to the rare category.
- Choose the higher-prior option. State it as more likely or expected, not certain, unless an explicit fact in the scene makes it decisive.

## Special Case
**Vivid or stereotypical description versus base rate**: When a vivid description resembles a rare category but the stated base rate strongly favors a common one, stay with the common category unless the description is specifically diagnostic rather than merely representative. Resemblance alone does not beat a strong prior.

Scene: At a conference there are 90 engineers and 10 poets. Alex is described as quiet, precise, and fond of notebooks.
Question: Is Alex more likely to be an engineer or a poet?
Answer logic: The quiet-notebook description feels poet-like, but it is representative, not diagnostic; many engineers fit it too. The 90-to-10 base rate dominates, so engineer is more likely. Note this is a pure prior judgment: nothing was sampled and no count needs revising, which is what separates it from updating-on-observed-data.

## Boundary Exit Rule
- If the core operation is mapping a quantifier word (many, few, most, about half) onto an approximate range, that is decoding word meaning, not comparing category likelihood; use the vague-quantity interpretation skill.
- If a specific sample, partial count, or newly seen subset was observed and the estimate must be revised on that data, that is updating a count from observation; use the quantity-update-after-observation skill. The tell: the scene reports something just seen (8 of 10 were flu) that should move the number.
- If the question asks what produced the result, that is causal attribution.
- If the issue is what a character thinks is likely rather than what is objectively likely from base rates, use the matching belief or knowledge skill.
- If the prior judgment is only one substep inside a larger negotiation, trust, false-belief, or communication scene, hand back to the macro route that owns that scene.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this unit when likelihood turns on a prior: commonness, category frequency, ordinary prevalence, or the default reaction to a familiar event, with no specific sample observed to update on.
