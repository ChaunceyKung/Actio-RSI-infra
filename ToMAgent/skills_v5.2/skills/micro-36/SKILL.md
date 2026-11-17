---
name: micro-36
level: micro
layer: L5
family: "language-pragmatics"
description: "Infers the extra information a speaker communicates through context but does not explicitly say: the implicit proposition a cooperative listener recovers from the wording, the situation, and shared expectations."
---

# Conversational Implicature

## Use When
- Use when the question asks what extra meaning or information is communicated beyond the literal sentence.
- Use when the answer is an inferred PROPOSITION or quantity (e.g. 'not all of them', 'about four of five') that the words alone do not state but context makes recoverable.
- Use when the listener must combine the wording, a scalar or partial cue ('some', 'almost every', 'I looked at 3 of 5'), and the scene to fill in what is meant.
- Use when a literally true or incomplete utterance only fully answers the question once the implicit content is added.

## Do Not Use When
- Do not use when the question asks what social act the utterance performs, such as requesting, warning, refusing, reminding, or hinting; name and route to the social-action-of-an-utterance capability (Indirect Speech Act, micro-35).
- Do not use when the question asks only for the plain stated content of the words; name and route to the explicit-meaning capability (Literal Meaning, micro-34).
- Do not use when the question is whether the statement is true, false, or a lie; name and route to the truth-status capability (Truth, Lie, and Half-Truth, micro-37).
- Do not use when the issue is whether a true statement steers the listener to a false belief; name and route to the misleading-true-statement capability (Misleading and Selective Expression, micro-38).

## Decision Variable
the implicit information derived from context

## Trigger Checklist
- Is the utterance literally true but underinformative, so a cooperative listener is expected to read in more?
- Does the question ask what the speaker MEANT or what is IMPLIED beyond the words actually said?
- Is the correct answer an inferred fact or quantity, not a speech-act label and not a true/false verdict?
- Must the listener combine wording, a scalar cue, and scene expectations to recover the extra message?

## Workflow
- State the literal sentence meaning first (SAY), including any scalar or partial cue such as 'some', 'almost every', or 'I checked 3 of 5'.
- Ask what additional proposition a cooperative, informative speaker would expect the listener to infer (IMPLY).
- Apply the relevant inference: a weaker scalar term excludes the stronger one (e.g. 'some' implies 'not all'); a 'almost every / about half' cue plus a sample implies an estimated total.
- Confirm the inferred content is what the question wants, not the act being performed and not a truth verdict.
- Return only the implied proposition or quantity. If the question instead targets the act, the plain words, or the truth status, stop and route out to the matching capability.

## Special Case
**Quantity implicature from a scalar cue and a partial sample**: When the scene gives a scalar quantifier ('almost every', 'about a third') and a partial observation, the implicature is the estimated total derived from the quantifier, not the literal count of the sample alone.

Scene: Almost every letter to Laura's company contains a check. Today Laura receives 5 letters. She phones: 'I looked at 3 of the 5 letters; 2 of them have checks.'
Question: Before her call, how many of the 5 letters would you expect to contain checks?
Answer logic: Literally Laura states only that 2 of the 3 she opened had checks. The implicit information, recovered from 'almost every letter contains a check' applied to all 5, is that about 4 of the 5 contain checks. The target is this inferred quantity, not what act Laura performs (that would be the social-action capability, Indirect Speech Act, micro-35) and not whether she is truthful (the truth-status capability, Truth, Lie, and Half-Truth, micro-37). The correct reading is the implied count of about 4.

## Boundary Exit Rule
- If the question asks what social action the utterance performs (request, warning, reminder, refusal, hint), route to the social-action-of-an-utterance capability (Indirect Speech Act, micro-35).
- If the question asks only for the explicit content of the words, route to the explicit-meaning capability (Literal Meaning, micro-34).
- If the question asks whether the utterance is factually true or false, route to the truth-status capability (Truth, Lie, and Half-Truth, micro-37).
- If the question asks whether a literally true statement nudges the listener toward a false belief, route to the misleading-true-statement capability (Misleading and Selective Expression, micro-38).

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this unit when the diagnostic target is the extra information communicated implicitly, recovered by a cooperative listener from context, especially scalar or quantity implicatures where the words alone underdetermine the answer.
