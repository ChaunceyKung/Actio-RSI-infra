---
name: micro-38
level: micro
layer: L5
family: "language-pragmatics"
description: "Diagnostic unit for cases where a true or selective expression steers the listener toward a false inference."
---

# Misleading and Selective Expression

## Use When
- Use when the question is whether a true expression causes the listener to draw the wrong conclusion.
- Use when the key issue is selective disclosure, framing, or emphasis that makes the audience infer something false.
- Use when the stated content may be accurate but the communicative effect is deceptive.

## Do Not Use When
- Do not use when the question is simply whether the words are factually true or false; route to the truth-status capability that compares a claim against the facts (micro-37). A plainly false statement is ordinary lying, not true-but-misleading.
- Do not use when the task is to recover an unstated meaning the speaker intends and the listener is meant to grasp correctly; route to the conversational-implicature capability (micro-36). This unit fires only when the inference the listener draws is FALSE.
- Do not use when the task is the speaker's reason or motive for choosing that wording; route to the speaker-motivation capability that asks why something was said (micro-39).
- Do not use when the issue is fitting the message to the listener's level or knowledge rather than producing a false impression; route to the audience-calibration capability (micro-40).

## Decision Variable
whether the expression leads the listener to a false inference

## Trigger Checklist
- The literal statement can be true.
- The listener is likely to infer more than the sentence strictly states.
- The wrong answer depends on whether the audience is misled, not on factual truth alone.
- A hidden omission, framing choice, or partial disclosure changes the listener's belief.

## Workflow
- First confirm the literal content is true (or at least not plainly false). If the words themselves conflict with the facts, this is ordinary lying — stop and route to the truth-status capability (micro-37).
- Identify what a reasonable listener would actually infer from the wording, emphasis, and especially what was left unsaid.
- Compare that inferred belief with the real situation: is the listener now closer to a FALSE understanding?
- Pinpoint the device doing the misleading — omission of a key fact, selective disclosure, framing, or misleading emphasis — and name it.
- If a true (or partly true) statement pushes the listener toward a false belief, classify it here as misleading. If the listener's inference is actually correct, it is not misleading — route to the conversational-implicature capability (micro-36) if the question is about recovered meaning, or to the speaker-motivation capability (micro-39) if it is about why the speaker spoke that way.

## Special Case
**True wording, false impression by omission**: A statement belongs here when each thing said is true (or not plainly false) yet a key detail is left out, so the listener forms a belief that is false. The test is the listener's resulting belief, not the literal sentence.

Scene: An antique dealer, Mr. Lin, has a jade piece that is really a modern replica he bought abroad. A buyer admires it. He tells later customers, truthfully, that it is 'the star product of the shop, drawing the attention of many collectors,' but never mentions it is not the antique relic buyers assume it to be.
Question: Does Mr. Lin's wording mislead the listener?
Answer logic: Yes. Taken literally, 'star product that draws many collectors' can be true, so this is not caught by a simple truth check. But by selecting flattering true facts and omitting that the piece is a modern replica, the wording leaves the listener believing it is a genuine valuable antique — a false belief. The misleading effect, not the literal truth, is the diagnostic.

## Boundary Exit Rule
- If the task asks whether the words are factually true or false rather than whether the listener is misled, exit to the truth-status capability that compares a claim against the facts (micro-37); an outright false statement is ordinary lying, not true-but-misleading.
- If the task asks what extra meaning was conveyed beyond the words and that recovered meaning is correct rather than false, exit to the conversational-implicature capability that recovers unstated intended meaning (micro-36).
- If the task asks why the speaker chose that wording rather than whether it misleads, exit to the speaker-motivation capability that asks why something was said (micro-39).
- If the main issue is adapting the message to the listener's level or background rather than producing a false impression, exit to the audience-calibration capability (micro-40).

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when a true statement, partial statement, or framing choice is judged by whether it misleads the listener into a false belief.
