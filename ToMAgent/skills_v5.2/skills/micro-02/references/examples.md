# micro-02 Examples and Boundaries

## Decision Variable
which evidence supports the conclusion

## Route Signal
This review lens checks whether a conclusion's support is real text, an inference, or commonsense completion.

## Hard Boundary
- No explanation comparison.
- No bias checking.
- No task routing.
- No scene-level prediction unless it is explicitly framed as evidence support.

## Shortcut To Avoid
- Do not pick the most plausible story and call it evidence.
- Do not treat background knowledge as if it were stated support.
- Do not answer from intuition before separating what is written from what is inferred.

## Common Failure Modes
- Confusing a likely inference with direct evidence.
- Choosing a completion that fits the story but is not text-based.
- Sliding into best-explanation reasoning instead of support tracing.
- Overlooking the difference between what is said and what must be added.

## Minimal Pair
- Case: A passage states that the boy grabbed a coat before leaving because the weather app showed snow. | Why: The question asks which detail supports the conclusion, so the unit identifies the evidence chain behind the conclusion.
- Case: Two possible reasons are given for why the woman left early, and the task asks which reason is more convincing. | Why: Weighing which reason is more convincing is the parallel alternative-explanation lens's job; this lens instead checks whether each cited reason is actually stated in the text.

## Boundary Stress Test
- If two explanations both fit, leave the contest to the alternative-explanation lens; here, just sort what the text states versus what is inferred.
- If the support comes from a clue plus commonsense completion, keep the clue and the completion separate.
- Whether the solver is biased is examined by the parallel bias-check lens; this lens stays focused on evidence sourcing.

## Generalization Note
This skill generalizes to any case where the main operation is tracing why an answer follows from evidence, especially when direct statements, inferences, and background knowledge are easy to blur.
