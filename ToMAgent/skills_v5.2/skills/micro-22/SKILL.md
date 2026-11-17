---
name: micro-22
level: micro
layer: L3
family: "goal-action"
description: "Explain the purpose behind a behavior the character has ALREADY shown - a current or just-performed action, gaze, gesture, expression, wink, nudge, or other cue. Answer WHY this behavior is happening, not what the character will do next."
---

# Intention Recognition

## Use When
- Use when the question asks WHY a character is doing, looking at, pointing to, nudging, winking at, smiling at, signaling, or arranging something right now.
- Use when the answer is the immediate purpose or communicative function of a behavior that has already been observed in the scene.
- Use when a nonverbal cue - a glance, wink, nudge, smile, head shake, pause, or way of handling an object - must be read as a deliberate, goal-directed signal.
- Use when the question is what the actor is trying to make someone notice, understand, do, or avoid THROUGH the cue they just produced.

## Do Not Use When
- Do not use when the answer is what the character will do NEXT (their next move, choice, or destination) rather than why the present behavior occurred; use the next-action prediction capability instead - what the character is most likely to do next (micro-23).
- Do not use when the cue is a spoken hint or indirect utterance and the task is to recover the social action of the words ('Can't you find the cleaner?' = clean the bathroom); use the indirect-speech-act capability - the action performed by an utterance (micro-35).
- Do not use when the task is to rank long-term versus short-term versus local goals; use the goal-hierarchy capability (micro-21).
- Do not use when the variable is another person's stable likes or wants; use the other-person preference capability (micro-20).
- Do not use when the issue is which prior commitment, obligation, or scheduled plan should take priority; use the commitment-priority capability (micro-24).
- Do not use when the behavior is a mere physical event with no mental purpose to infer.

## Decision Variable
the immediate purpose behind the behavior

## Trigger Checklist
- There is a concrete, already-observed behavior or cue in the scene (a gaze, gesture, expression, or small action that has happened).
- The question word is WHY, or it asks what the actor means, is trying to say, or is trying to accomplish by that behavior.
- A correct answer can be stated as an immediate aim of the existing behavior, not as a later action the character has yet to take.
- Context reveals what the actor can see, knows, wants noticed, or wants changed at this moment.
- Competing explanations can be ranked from the ACTOR's perspective, not from the narrator's hindsight or a bystander's knowledge.

## Workflow
- Pin down the exact behavior to explain: who performs it, what form it takes (direction, timing, target), and who can perceive it.
- Confirm the question asks WHY this behavior occurs - not what happens next. If it asks for the character's following move or choice, switch to the next-action prediction capability (micro-23).
- List the immediate purposes the behavior could plausibly serve: drawing attention to something, prompting another person to act, warning, reassuring, concealing, teasing, requesting, or confirming shared understanding.
- Filter with the actor's perspective - what the actor can see, knows, and wants right now. Drop any purpose the actor could not intend (e.g. it relies on information the actor lacks).
- Use the cue's specific form (its direction and target, what it points at, who it is aimed at) to choose the single purpose it fits best; reject vague motives like 'to be friendly' when a sharper purpose is supported.
- State the answer as the immediate intention behind the existing behavior - never as a prediction of a later action.

## Special Case
**Directed nonverbal cue between two people**: When a glance, wink, nudge, smile, or head shake is aimed at a specific person, treat it as a signal meant to change that person's attention, belief, emotion, or behavior, and read its purpose from what the two share and who else is watching.

Scene: Xiao Hong and Xiao Fang are watching other children play. Xiao Hong gives Xiao Fang a look, glances toward the swing where a new child sits alone, then smiles at Xiao Fang. Xiao Fang nods.
Question: Why does Xiao Hong smile at Xiao Fang?
Answer logic: The smile is a directed signal that follows Xiao Hong's glance toward the swing. Its immediate purpose is to suggest to Xiao Fang that they go over and make a new friend together - it confirms a shared plan, not a feeling about the playground. The answer explains the existing cue; it does not predict the pair's next steps.

## Boundary Exit Rule
- If the answer must be the character's NEXT move - where they go, what they choose, or what they do after the cue - switch to the next-action prediction capability - what the character is most likely to do next (micro-23).
- If the cue is a spoken hint or indirect line and the task is to recover the social act the words perform (hinting, requesting, refusing, reminding), use the indirect-speech-act capability - the action performed by an utterance (micro-35).
- If the answer requires comparing a local action against a broader or longer-term aim, use the goal-hierarchy capability - long-term versus short-term versus local goals (micro-21).
- If the answer turns on what one person believes another person likes or wants, use the other-person preference capability (micro-20).
- If the answer depends on obligations, prior promises, scheduled plans, or task priority, use the commitment-priority capability (micro-24).
- If the scene can be solved from literal verbal meaning alone with no behavioral purpose to infer, do not use this unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this capability when an already-observed behavior is the evidence and the diagnostic question is WHY that behavior is happening - the immediate purpose it serves right now. If the question instead asks what the character does next, route to the next-action prediction capability (micro-23).
