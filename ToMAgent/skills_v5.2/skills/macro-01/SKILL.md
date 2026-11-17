---
name: macro-01
level: macro
layer: macro
family: "false-belief"
description: "Direct-route macro for predicting where or how a character will act from their own first-order false belief, especially after an object or situation changes while they are absent or unaware."
---

# Classic False-Belief Judgment

## Use When
- Use when the scene asks where a character will look, search, go, or act based on what they falsely believe.
- Use when a character had earlier access to a location or state, then the world changed without that character seeing or learning about the change.
- Use when the answer depends on the character's own belief rather than the real current state.
- Use when the case is a first-order mindreading problem: what X believes and does, not what X thinks Y believes.

## Do Not Use When
- Do not use when the question is really about what one character thinks ANOTHER character believes or will do (a nested, second-order belief, e.g. 'where does A think B will look'); that needs a second-order procedure that models the inner person's belief first and then the outer person's belief about it, not the single-character procedure here.
- Do not use when the main conflict is how something LOOKS versus what it really IS, or a misidentified object or person, with no action predicted from a false belief; that is an appearance-versus-reality or mistaken-identity problem, solved by tracking the true identity against the misleading appearance.
- Do not use when the question asks what is actually true rather than what the character will believe or do.
- Do not use when the character witnessed the change, was told about it, or otherwise had evidence that updates their belief.

## Decision Variable
where or how a character will act based on a false belief

## Direct Route Rule
Route immediately when the case is a first-order search-location belief after an unseen move.

## Expand With Micro Units
- Sensory Access: whether the character can directly perceive the information through a sensory channel (micro-05)
- Temporal Order and Event Updating: the event sequence and its updating effect (micro-08)
- Memory, Forgetting, and Misremembering: current memory content and fidelity (micro-09)
- First-Order Belief: the character's current factual belief (micro-11)
- False Belief: whether the character's belief mismatches the actual state (micro-12)
- Action Prediction: what the character is most likely to do next (micro-23)

## Trigger Checklist
- A single target character earlier observed or was told an initial location, container, label, owner, route, or state.
- The relevant object or situation changed AFTER that observation (an unseen move, swap, or relocation).
- The target character was absent or looking away and did not see, hear, infer, or receive a reliable message about the change.
- The question asks where the target character will look or go, what they will do, reach for, or expect, not what is really there now.
- The question involves only the target character's own (first-order) belief, not what one character thinks another believes.
- The real current location or state conflicts with the target character's belief, so reality and belief point to different options.

## Workflow
- Read the QUESTION first and name the exact target character whose action, search, or belief is asked. If the question nests one mind inside another ('where does A think B will look'), stop: solve it as a second-order belief problem (model B's belief first, then A's belief about B), not with this single-character procedure. If the question asks what is really/actually/now the case (no character's belief or search), this is a reality-recall question, not false belief: answer the true current state.
- Write down two separate facts: the REAL current location or state of the object, and the LAST state the target character personally observed or was reliably told. Do not merge these.
- Determine the target character's information access: did they see, hear, infer, or get a trustworthy message about the change? Count only evidence available to THAT character; ignore anything known to the reader, narrator, or another character.
- Decide the operative belief. If the target had NO access to the change, their belief is the old observed state (still false). If the target DID get reliable updating evidence (witnessed it or was told), their belief matches reality and this is no longer a false-belief case.
- Answer from the operative belief, not from reality: the character searches, goes, reaches, or expects according to that belief. When the belief is false, the correct option is the ORIGINAL location/content, which deliberately differs from the real current state.
- Before finalizing, run the two guard checks: (a) reality-bias guard, confirm you did not just pick the real current location the narrator revealed; (b) omniscience guard, confirm the character actually had access to every fact you credited them with. If either fails, revise.
- If the question secretly requires a nested belief (what A thinks B believes), switch to a second-order approach and model the inner belief before the outer one; if it is about what an object really is versus how it looks, or about a misidentified object or person, switch to an appearance-versus-reality approach that tracks the true identity against the misleading appearance.

## Special Case
**Unseen transfer or relocation**: When an object is moved while the target character is absent or unable to observe, the target will search in the original place they last believed the object to be, unless the scene gives them later updating evidence.

Scene: Wei and Nadia are in the bedroom with a handbag, a briefcase, and a backpack; they find a cabbage in the handbag. Nadia leaves the bedroom. While she is gone, Wei moves the cabbage from the handbag into the backpack. Nadia returns.
Question: After Nadia returns, where does she look for the cabbage?
Answer logic: Reality vs. belief: the cabbage is really in the backpack, but Nadia last saw it in the handbag and was absent for the move with no message, so her belief is unchanged and false. Answer from her belief: she looks in the handbag (the original place), not the backpack. Picking the backpack would be reality bias; crediting her with knowing the move would be an omniscience leak.

## Boundary Exit Rule
- Exit to a second-order belief approach when the answer requires modeling what one character thinks another character believes, knows, or will do: build the inner character's belief first, then the outer character's belief about that.
- Exit to an appearance-versus-reality approach when the core question is about the gap between how something looks and what it really is, a misidentified object or person, or what someone can know given limited information, rather than predicting belief-guided action.
- If who-saw-what is disputed, reason explicitly about sensory access: which character could directly see, hear, or touch the relevant information, and at what moment, before deciding whose belief is updated.
- If the failure risk is about memory or updating, track each character's last reliably known state and change it only when that specific character gains witnessing or trustworthy-message access to the change.
- If naming the believed location is not enough and you must predict a concrete action, connect the belief to the character's goal: state what they want, then the step they would take given that false belief.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
A character will search or act according to an outdated belief because a relevant change happened outside their awareness.
