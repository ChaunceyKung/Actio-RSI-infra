---
name: micro-34
level: micro
layer: L5
family: "language-pragmatics"
description: "Determines what an utterance EXPLICITLY says: its plain semantic content, read off the actual words, without adding the speaker's hidden intention, the social act being performed, or any implied extra meaning."
---

# Literal Meaning

## Use When
- Use when the question asks what a sentence, sign, message, or spoken utterance explicitly says or states, in its plain dictionary sense.
- Use when the answer can be produced by parsing the actual words, their conventional meanings, and stated facts alone.
- Use when the task is to separate the literal stated content from what the speaker intended, hinted, requested, or implied.
- Use when checking whether a statement is literally compatible with a fact, label, instruction, or description.

## Do Not Use When
- Do not use when the question asks what social action the utterance performs, such as requesting, warning, refusing, reminding, or hinting; name and route to the social-action-of-an-utterance capability (Indirect Speech Act, micro-35).
- Do not use when the question asks what extra information is conveyed by context but not actually said; name and route to the implied-information capability (Conversational Implicature, micro-36).
- Do not use when the question is whether the statement is true, false, or deceptive; name and route to the truth-status capability (Truth, Lie, and Half-Truth, micro-37).
- Do not use when the question is how the listener feels, how the speaker manages emotion, or why the speaker chose those words.
- Do not use if the answer requires adding unstated motives, politeness norms, audience reaction, or relationship history beyond resolving who or what a word refers to.

## Decision Variable
the sentence's explicit semantic content

## Trigger Checklist
- Is there a quoted or clearly identifiable utterance, sign, or message?
- Does the question ask what the words SAY, rather than what the speaker is DOING or IMPLYING?
- Can the answer be produced from grammar, word meaning, reference, and stated facts alone?
- Would the answer stay the same even if the speaker secretly had a completely different motive?
- Are contextual facts needed only to fix reference (who 'she' or 'that box' is), not to recover a hidden message?

## Workflow
- Identify the exact utterance, sign, or message to interpret, word for word.
- Resolve only ordinary references using stated context: names, pronouns, time, place, objects. Do not import motives.
- Restate the utterance in plain, explicit terms: its literal assertion, question, command, or description, nothing more.
- Discard every candidate answer that adds a social act ('is requesting', 'is warning'), an implied proposition ('really means that not all...'), an emotion, or a truth verdict. Those belong to other capabilities.
- Pick the option that matches ONLY the conventional meaning of the words. If the question asks what the speaker is doing or implying, stop and route out to the matching capability.

## Special Case
**Literal question form versus the request it conventionally performs**: When an utterance is phrased as a question (e.g. 'Can you pass the salt?'), the literal content is the question it asks (whether the listener is able). Only convert it into a request when the task explicitly asks what social action is performed.

Scene: After a long hot trip George arrives at Angela's office and, as she starts pitching ideas, interrupts: 'Ah, I had a long and hot highway trip.'
Question: What does George's sentence literally state?
Answer logic: Literally it states one fact: George experienced a long, hot highway trip. Reading it as 'George wants to rest or have a drink' is the social act it performs in context, which belongs to the social-action-of-an-utterance capability (Indirect Speech Act, micro-35), not to literal meaning. The literal answer is just the reported fact about the trip.

## Boundary Exit Rule
- If the target answer says the speaker 'is hinting', 'is asking indirectly', 'is requesting', 'is warning', or 'is reminding', the question is about the social act performed; route to the social-action-of-an-utterance capability (Indirect Speech Act, micro-35).
- If the target answer is an extra unstated proposition the listener must infer ('this implies that not all of them...'), route to the implied-information capability (Conversational Implicature, micro-36).
- If the issue is whether the utterance is true, false, a lie, or a half-truth, route to the truth-status capability (Truth, Lie, and Half-Truth, micro-37).
- If the issue is whether a literally true statement steers the listener to a false belief, route to the misleading-true-statement capability (Misleading and Selective Expression, micro-38).
- If the answer depends on the listener's private knowledge, relationship history, or politeness norms beyond fixing a referent, exit this unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this unit when the diagnostic target is what the utterance EXPLICITLY says, the plain semantic content, independent of any hidden intention, social act, or implied extra meaning.
