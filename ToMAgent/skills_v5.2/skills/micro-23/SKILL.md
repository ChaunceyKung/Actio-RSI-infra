---
name: micro-23
level: micro
layer: L3
family: "goal-action"
description: "Predict what the character will most likely DO NEXT by combining their current belief state with their active goal. The output is a future action - not an explanation of a behavior they have already shown."
---

# Action Prediction

## Use When
- Use when the question asks what the character will do next, where they will go, what they will choose, or what move they will make.
- Use when a question phrased 'What does X want to do?' is really asking for X's next concrete action given the situation (the answer is a move X makes, not a feeling or trait).
- Use when the prediction must follow the character's own BELIEF about the situation, even when that belief is false, rather than the real state of the world.
- Use when the character has an identifiable goal and the task is to pick the next outward behavior that serves it.
- Use inside larger false-belief, social-cue, preference, or commitment scenes when the final diagnostic variable is the next action.

## Do Not Use When
- Do not use when the question asks WHY the character is currently or has just been acting, looking, gesturing, or signaling; that explains an already-shown behavior, so use the intention-recognition capability - the purpose behind a current cue (micro-22).
- Do not use when the central task is to weigh competing goals against each other (which goal wins) rather than to name the single next action; use the goal-conflict arbitration capability - choosing among conflicting goals (micro-25).
- Do not use when the task is to rank an obligation, prior promise, or scheduled plan against a new invitation; use the commitment-priority capability (micro-24).
- Do not use when the task is to explain the hierarchy among long-term, short-term, and local goals; use the goal-hierarchy capability (micro-21).
- Do not use when the answer is purely what the character knows, believes, wants, or feels, with no observable next behavior to predict.

## Decision Variable
what the character is most likely to do next

## Trigger Checklist
- The question asks what the character will do, where they will go, what they will choose, or what they will try next - or asks 'what does X want to do?' where the answer is a next move.
- A current belief state can be identified for the character, including anything they saw, missed, misunderstood, or falsely believe.
- An active goal, desire, or task the character is pursuing can be identified.
- The predicted action follows from the character's OWN belief, even if that belief is false.
- The required output is an observable behavior, not an internal motive, emotion, or explanation of a prior cue.

## Workflow
- Identify the target character whose next action is to be predicted.
- Confirm the question is forward-looking: it asks what happens NEXT (or 'what does X want to do?' = X's next move), not WHY a behavior already occurred. If it asks WHY about a current cue, switch to the intention-recognition capability (micro-22).
- Separate reality from the character's belief state - what they actually saw versus what they missed, misunderstood, or falsely believe.
- Identify the active goal the character is trying to satisfy at this moment.
- List the actions available in the scene and select the one that best advances the active goal GIVEN the character's own belief - not given reality, when the two differ.
- If the scene pits one goal against another and the question is which goal wins, stop: that is the goal-conflict arbitration capability (micro-25). Use this unit only once a single active goal points to one next action.
- State the predicted next action, briefly justified by belief plus goal.

## Special Case
**False-belief action**: When the character holds a false belief, predict the action that makes sense IF that false belief were true, not the action that would work in reality.

Scene: Maya puts her keys in the blue bowl and leaves. While she is away, Leo moves the keys to the drawer. Maya returns wanting to drive home.
Question: Where will Maya look for her keys first?
Answer logic: Maya's goal is to get her keys; her belief is that they are still in the blue bowl (she did not see Leo move them). The next action that serves the goal under her belief is to look in the blue bowl first - even though the keys are really in the drawer. Predict from belief, not reality.

## Boundary Exit Rule
- If the question asks WHY a current or just-performed cue is happening (a smile, glance, nudge, point), use the intention-recognition capability - the purpose behind a current behavior (micro-22). That unit looks backward; this one looks forward.
- If the scene's core problem is which of two competing goals the character will favor, use the goal-conflict arbitration capability - choosing among conflicting goals (micro-25).
- If the question is whether an existing commitment, deadline, or promise overrides a new option, use the commitment-priority capability (micro-24).
- If the question is how local actions relate to broader or longer-term goals, use the goal-hierarchy capability (micro-21).
- If the only required answer is what the character thinks, knows, wants, or feels with no behavioral prediction, use the relevant belief, desire, or emotion capability instead.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this capability when the answer must be an observable NEXT behavior derived from the character's belief state plus active goal. If the question instead asks WHY a behavior already shown is happening, route to the intention-recognition capability (micro-22).
