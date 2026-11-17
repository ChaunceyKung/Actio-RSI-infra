# micro-01 Examples and Boundaries

## Decision Variable
which mental or social variable category the question targets, named before any scene reasoning

## Route Signal
This step always runs first to select the right social-cognitive lens or capability entry point; it names the variable rather than solving the scene.

## Hard Boundary
- No scene solving.
- No evidence ranking.
- No explanation comparison.
- No final belief, emotion, intention, or action inference.

## Shortcut To Avoid
- Do not jump straight to the story outcome.
- Do not confuse variable selection with answer generation.
- Do not overfit to a rigid template label when the prompt only asks for the relevant mental or social factor.

## Common Failure Modes
- Answering the substantive question instead of naming the variable.
- Picking too broad a label like social reasoning when the prompt asks for a specific mental-state type.
- Trying to sort evidence or compare explanations during routing instead of just naming the variable and selecting a capability.

## Minimal Pair
- Case: The prompt asks whether a story is about belief, desire, or intention. | Why: The task is to identify the variable being tested before any scene reasoning.
- Case: The prompt asks where a character will search after an object was moved. | Why: Routing only names the variable (a belief about a location) and selects the false-belief capability, which then solves the scene; routing itself does not give the answer.

## Boundary Stress Test
- If the prompt asks only what kind of inference is needed, the answer is the variable label itself.
- If the prompt asks who knows what, who wants what, or what happened, name the variable and route it to the matching substantive capability to solve.
- If two capabilities seem plausible, name the variable first, then select the single best-matching capability.

## Generalization Note
This skill generalizes across both structured questions and naturalistic real-world scenes by selecting the correct mental or social variable before any deeper inference.
