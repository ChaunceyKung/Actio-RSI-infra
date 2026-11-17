---
name: micro-37
level: micro
layer: L5
family: "language-pragmatics"
description: "Evaluate whether an utterance's explicit content is true, false, or a mix of true and false clauses (a half-truth), judged against the known facts. A literally true statement that misleads only by omitting a key fact is handled by the misleading-expression capability, not here."
---

# Truth, Lie, and Half-Truth

## Use When
- Use when the question asks whether a stated claim matches the facts available in the scene.
- Use when the answer depends on classifying explicit utterance content as true, false, partly true, or unsupported.
- Use when a character says something and the task is to compare the wording against what actually happened or what is actually the case.
- Use when a half-truth must be identified because the utterance contains both accurate and inaccurate explicit content.

## Do Not Use When
- Do not use when the question asks WHY the speaker said it or whether the speaker meant to deceive; truth status alone never settles intent, so route to the speaker-motivation capability that asks why a true-or-false thing was said (micro-39).
- Do not use when every explicit word is literally true yet the wording still leads the listener to a false conclusion; route to the misleading-and-selective-expression capability that judges whether true wording creates a false impression (micro-38).
- Do not use when the question asks what the speaker implied beyond the literal words; route to the conversational-implicature capability that recovers unstated intended meaning (micro-36).
- Do not use when the question asks what social act the utterance performs, such as requesting, warning, refusing, or hinting; route to the indirect-speech-act capability that names the act being performed (micro-35).
- Do not use when the comparison is between what a character believes and reality rather than between a stated claim and reality; first route to the relevant belief-or-knowledge capability.

## Decision Variable
truth status of explicit content

## Trigger Checklist
- There is a specific utterance, claim, answer, promise, report, or description to evaluate.
- The scene provides facts that can be compared against the utterance.
- The question asks whether the utterance is true, false, accurate, inaccurate, a lie, or a half-truth.
- The needed judgment concerns the words stated, not the hidden motive or listener interpretation.
- The utterance can be decomposed into one or more explicit propositions.

## Workflow
- Isolate ONLY the explicit content asserted (quote or paraphrase the literal claim); ignore tone, motive, and what the listener concludes.
- If the utterance bundles several claims, split it into atomic factual propositions ('I returned the book' AND 'I borrowed nothing new').
- From the scene, list the matching ground-truth fact for each proposition.
- Compare each proposition with its fact and tag it: TRUE (matches), FALSE (conflicts), UNSUPPORTED (scene gives no fact to check it against), or PARTLY TRUE.
- Classify the whole utterance: TRUE if every central claim matches; FALSE if any central claim conflicts with the facts; HALF-TRUTH only if the explicit content itself mixes a true clause with a false clause; UNSUPPORTED if the scene never establishes the relevant fact.
- Do NOT downgrade truth to falsehood (or upgrade falsehood to lie) on the basis of the speaker's motive, sincerity, or whether the listener was fooled — those are separate questions; answer only the content-versus-fact comparison the question asked.

## Special Case
**False content stays false regardless of the speaker's mind**: A statement is FALSE here whenever its explicit content conflicts with the facts, whether the speaker lied on purpose, told a kind white lie, or sincerely misremembered. Truth status compares words to facts; it never reaches inside the speaker's head. Settle the content question first, then send any 'why did they say it' or 'did they mean to deceive' question to the speaker-motivation capability (micro-39).

Scene: Li Ming plays football in the park, then rushes home forgetting the ball at the field; he genuinely thinks it is in his backpack. At dinner his brother asks where the football is, and Li Ming replies, 'It is in my bag.'
Question: Is what Li Ming says true?
Answer logic: Compare the claim 'It is in my bag' against the fact: the ball is still at the field. The content conflicts with reality, so the truth status is FALSE. The fact that Li Ming sincerely believed it (so it was an honest mistake, not a deliberate lie) does NOT change the truth status — that is a separate intent question handled elsewhere.

## Boundary Exit Rule
- Once you have classified the words as true or false, if the remaining question is WHY the speaker said them or whether the speaker meant to deceive, exit to the speaker-motivation capability that asks why a statement was made (micro-39) — truth status alone cannot decide intent.
- If every explicit word is true yet the wording steers the listener to a wrong conclusion, exit to the misleading-and-selective-expression capability that judges whether true wording creates a false impression (micro-38).
- If answering requires reading meaning the speaker implied beyond the literal words, exit to the conversational-implicature capability that recovers unstated intended meaning (micro-36).
- If the utterance functions mainly as a request, warning, refusal, reminder, or invitation rather than a checkable claim, exit to the indirect-speech-act capability that names the act being performed (micro-35).
- If the comparison the question wants is between a character's belief and reality rather than between a stated claim and reality, route first to the appropriate belief-or-knowledge capability before using this unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when the diagnostic target is the factual accuracy of what was explicitly said.
