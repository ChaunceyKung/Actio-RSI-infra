---
name: micro-01
level: micro
layer: L0
family: "meta-control"
description: "Identify the psychological or social variable the prompt is actually asking for, without solving the substantive scene."
---

# Task Routing

## Use When
- Use when the prompt is asking what kind of mental, social, or pragmatic variable must be identified before solving.
- Use when you need to name the entry capability such as belief, desire, intention, emotion, norm, trust, privacy, or audience.
- Use when the task is to route the question to the right capability rather than answer the scene directly.
- Use when the stem asks 'what is being tested' or 'which capability applies' rather than asking for a scene answer.

## Do Not Use When
- Do not use this step to produce the scene answer itself (what someone believes, feels, wants, says, knows, or will do); routing only names the variable and selects the capability that then solves it.
- Do not use it to weigh which evidence supports a conclusion or to compare which of several explanations fits best; those are review-stage checks that run on every item, not destinations routing sends work to.
- Do not use it to audit the reasoning for perspective, outcome, or moral bias; that is also a separate review-stage check.
- Do not over-route when the matching capability is already obvious; just name the variable and move straight to that capability.

## Decision Variable
which mental or social variable category the question targets, named before any scene reasoning

## Trigger Checklist
- The prompt is asking what kind of thing is being tested, not what happened.
- You can name the answer as a variable category before any scene reasoning.
- More than one substantive skill could apply, so the first job is to choose the right lens.
- The key choice is the capability entry point, not the scene outcome.

## Workflow
- Read the question stem and identify the requested output type.
- Strip away story details and ask what variable would make the answer possible.
- Match the requested output to one routable category: perception, attention, memory, knowledge, belief, desire, intention, action, emotion, norm or relation, pragmatic meaning, or quantity and cause.
- Label the target variable at the right abstraction level using that taxonomy, for example a belief about where an object is, the intention behind a gesture, the certainty of a claim, or an emotion triggered by an event.
- Once the variable is named, route to the substantive capability that solves it — for example a belief, intention, or emotion capability — or answer 'none' when no library capability fits; do not solve the scene here. Evidence sorting, explanation comparison, and bias checking are not routing targets; they run automatically in the later review stage.

## Special Case
**Meta-question about the task itself**: If the prompt asks what the question is asking, answer only with the target variable category and do not infer the scene content.

Scene: Xiao Hong and Xiao Fang watch other children play on the playground. Xiao Hong gives Xiao Fang a look, glances toward the swing, then smiles at Xiao Fang. Xiao Fang nods and the two stand up.
Question: To answer 'Why does Xiao Hong smile at Xiao Fang?', which variable must be identified first?
Answer logic: Do not solve why she smiled yet. The output type the question needs is the intention behind the action, so the target variable is intention. Name that category and route to intention recognition; do not jump to a belief, an emotion, or a moral judgment.

## Boundary Exit Rule
- Once the target variable is named, the routing step is done; pass control to the selected substantive capability.
- Send the item to the capability that matches the named variable — a belief, intention, emotion, norm, relation, or pragmatic-meaning capability — or answer 'none' when nothing in the library fits.
- Evidence sorting and explanation comparison are review-stage checks that always run later, not routing destinations, so routing never needs to send work to them.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
This step always runs first to select the right social-cognitive lens or capability entry point; it names the variable rather than solving the scene.
