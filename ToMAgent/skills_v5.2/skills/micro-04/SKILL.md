---
name: micro-04
level: micro
layer: L0
family: "meta-control"
description: "A meta-control unit for checking whether a current judgment is being distorted by the solver's own perspective, emotional reaction, or moral intuition."
---

# Anti-Bias Check

## Use When
- Use when the task is to audit whether a judgment may be skewed by perspective bias, outcome bias, or a gut-level moral reaction.
- Use when you need to check whether the current reasoning is being distorted by the solver's own viewpoint, sympathies, or intuitive reaction.
- Use when the main question is whether the reasoning process is biased, not what the correct social inference is.

## Do Not Use When
- Do not use this lens to gather or sort evidence; that is the parallel evidence-chain review lens, which runs alongside it.
- Do not use it to compare which of several explanations fits best; that is the parallel alternative-explanation review lens.
- Do not use it to decide what a character can see, hear, know, or believe; the solver's substantive reasoning covers that.
- Do not replace the substantive answer with a bias verdict; this lens only flags distortion in the reasoning, after which the substantive answer stands or is recomputed.

## Decision Variable
presence of perspective-, outcome-, or moral-intuition distortion in the current reasoning

## Trigger Checklist
- Is the conclusion being driven by my own perspective instead of the scene facts?
- Is an emotional or moral reaction making the answer feel more certain than the evidence allows?
- Am I assuming the outcome should have been obvious just because I now know it?
- Am I checking the quality of the reasoning rather than generating a new explanation?
- Would the judgment change if I stripped away sympathy, blame, or hindsight?

## Workflow
- Identify the current conclusion or reaction that is under review.
- Separate scene facts from the solver's interpretation or gut reaction.
- Ask whether perspective, outcome knowledge, or moral intuition is pushing the answer.
- If bias is present, flag the distortion and suspend the judgment until the reasoning is cleaned up.
- Do not invent a new story; only assess whether the existing reasoning is biased.

## Special Case
**Outcome and perspective override**: If an answer feels obvious because of how things turned out or because the solver projects their own preference onto the character, first test whether that feeling is supported by the character's stated desire and viewpoint rather than a shortcut reaction.

Scene: Xiao Ming hopes for a computer or a new game for his birthday, but on his birthday he receives a bicycle.
Question: What is Xiao Ming's emotion at this time?
Answer logic: A naive solver feels the answer is obviously 'happy' because a gift arrived and because the solver would themselves be glad to get a bicycle. That pull is outcome bias blended with projecting one's own preference onto the character, not a reading grounded in Xiao Ming's stated desire for a computer or game. The unit's job stops here: flag 'happy' as outcome/projection bias, note that the gift does not match the stated desire, suspend that judgment, and route to emotion appraisal to determine the actual emotion. Do not let the pleasant ending or your own preference settle the answer.

## Boundary Exit Rule
- Deciding what a character saw, knew, or believed is the solver's substantive job, not this lens's.
- Comparing competing explanations is the parallel alternative-explanation lens's job.
- Inferring an intention, emotion, or social meaning from behavior is the solver's substantive job.
- This lens is complete once the reasoning has been checked for perspective, outcome, and moral-intuition distortion.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
This review lens asks whether the draft judgment is being distorted by the solver's own perspective, hindsight, emotion, or moral intuition.
