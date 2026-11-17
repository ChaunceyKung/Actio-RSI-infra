---
name: micro-02
level: micro
layer: L0
family: "meta-control"
description: "Separates text evidence, inference, and commonsense completion to identify what supports a conclusion."
---

# Evidence-Chain Construction

## Use When
- Use when the task asks which statement or clue supports a conclusion from the text.
- Use when you must separate direct evidence, inferred support, and commonsense completion.
- Use when the main job is to trace the evidential chain behind an answer, not to choose among rival explanations.

## Do Not Use When
- Do not use this lens to choose the best of several explanations; that is the parallel alternative-explanation review lens, which runs alongside it.
- Do not use it to name the question's target variable; that is the routing step.
- Do not use it to audit for perspective, outcome, or moral bias; that is the parallel bias-check review lens.
- Do not skip it just because the question does not literally ask 'what supports this'; in review it always checks whether the cited cues are actually in the text.

## Decision Variable
which evidence supports the conclusion

## Trigger Checklist
- The question asks for support, proof, or backing for a conclusion.
- You can separate the prompt into text evidence, inference, and outside knowledge.
- The answer depends on whether a statement is directly stated, implied, or just commonsense completion.
- You are not being asked to compare competing narratives or judge which explanation is best.

## Workflow
- Identify the conclusion being tested.
- List what is directly stated in the text.
- Mark what is inferred from the text versus supplied by commonsense.
- Choose the evidence that actually supports the conclusion, not the explanation that feels most complete.
- If the support comes only from outside knowledge, treat it as completion, not textual evidence.

## Special Case
**Separate the stated cue, the inference, and the behavior being explained**: The direct textual evidence is what the text literally states. The conclusion about a mental state is an inference built on top of it. The action being explained is the behavior in question, not itself evidence for the mental state behind it.

Scene: Sanming sees from a distance that Lingling quietly gives Dehua a document, smiles, and gently pats Dehua's back. Dehua quickly checks the document, shows a smile, and carefully puts it into his file bag.
Question: Which is the direct textual evidence that Dehua gained an advantage, as opposed to an inference?
Answer logic: The stated textual cue is that Lingling, the supervisor, secretly handed Dehua a document and he filed it away. The conclusion that this is extra information helping his promotion is the inference. Dehua filing the document is the behavior being explained, not separate proof that he gained an advantage. Keep these three layers distinct: do not promote the inference or the explained action into stated evidence.

## Boundary Exit Rule
- Comparing which explanation fits best is the parallel alternative-explanation lens's job, not this one's.
- Naming the question's target variable is the routing step's job.
- Auditing for perspective, outcome, or moral bias is the parallel bias-check lens's job.
- This lens is complete once textual evidence, inference, and commonsense completion have been separated.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
This review lens checks whether a conclusion's support is real text, an inference, or commonsense completion.
