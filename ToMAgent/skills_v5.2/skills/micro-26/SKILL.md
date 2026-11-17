---
name: micro-26
level: micro
layer: L4
family: "emotion-appraisal"
description: "Infer a character's basic emotion by appraising whether an event helps or harms that character's goals, interests, safety, possessions, or social standing."
---

# Basic Emotion Appraisal

## Use When
- Use when the question asks what a character feels after a straightforward success, failure, gain, loss, threat, relief, or disappointment.
- Use when the needed inference is how the event affects the character's goals or interests.
- Use when the character's outward expression can be treated as sincere or irrelevant to the question.
- Use when the answer can be derived from ordinary appraisal patterns such as goal achieved implies happiness, goal blocked implies frustration or sadness, danger implies fear, loss implies sadness, and threat removed implies relief.

## Do Not Use When
- Do not use when the main question is what the character will choose or do next; route to goal-action units such as Commitment Priority or Goal-Conflict Arbitration.
- Do not use when the emotion is surprising specifically because the character has unusual values, preferences, or appraisals; route to Atypical Emotion.
- Do not use when the character feels one thing but displays another; route to Hidden Emotion.
- Do not use when the emotion depends on guilt, shame, blame, responsibility, wrongdoing, or moral evaluation rather than basic goal impact.
- Do not use when the emotion depends mainly on imagining an alternative outcome, regret, relief about what could have happened, or counterfactual comparison.

## Decision Variable
event impact on the character's goals or interests

## Trigger Checklist
- A character experiences or learns about an event.
- The question asks for an emotion, feeling, or likely affective reaction.
- The event has a clear positive, negative, threatening, or relieving consequence for that character.
- No hidden display, deception, moral blame, or unusual emotional preference is central.
- The answer can be explained by the character's own goals, not the narrator's or another person's goals.

## Workflow
- Identify the character whose emotion is being asked about.
- List that character's active goal, interest, possession, relationship, safety concern, or expectation in the scene.
- Classify the event's impact on that target: helps, blocks, threatens, removes threat, causes loss, or gives gain.
- Map the appraisal to a basic emotion: gain or success to happiness, blocked goal to frustration or disappointment, loss to sadness, danger to fear, goal obstruction or frustration to anger (blame-focused anger, where a responsible agent is judged at fault, routes to the moral-emotion capability instead), threat removed to relief.
- Check whether the character knows about the event; if not, appraise only what the character believes happened.
- Return the emotion with a brief causal explanation tied to the character's goal impact.

## Special Case
**No contrary wish stated means use the default appraisal**: When the story gives the character a positive, negative, or threatening event and states no special wish, value, or expectation that would reverse it, answer with the ordinary emotion for that event. Only switch to a surprising emotion if the text supplies a reason for it.

Scene: Xiao Ming receives a bicycle on his birthday. The story says nothing about wanting a different present.
Question: What is Xiao Ming's emotion?
Answer logic: Receiving a desirable gift advances an ordinary goal, so the default appraisal is happiness. Because the story states no competing wish (such as hoping for a computer instead), there is nothing to make the feeling atypical, so the answer is Happy rather than Disappointed.

## Boundary Exit Rule
- If the task asks which action wins among competing plans or motives, exit to the goal-arbitration capabilities that pick an action rather than infer a feeling (micro-24, micro-25).
- If the genuine emotion is surprising because the character holds an unusual wish, value, belief, or expectation that reverses the ordinary reaction, exit to the atypical-emotion capability that explains why a real feeling deviates from the default (micro-27).
- If facial expression, politeness, concealment, or pretending hides a different inner feeling, exit to the hidden-emotion capability that reads the true feeling behind a managed display (micro-28).
- If blame, guilt, shame, apology, deservedness, or moral responsibility determines the feeling, exit to the moral-emotion capability that handles emotions arising from wrongdoing or moral evaluation (micro-30).
- If the answer depends mainly on imagining what could have happened but did not, exit to the reality-versus-alternative comparison capability that diagnoses regret, relief, disappointment, and pleasant surprise rather than appraising the actual event (micro-31).

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when an event's direct impact on a character's goal, interest, safety, or loss/gain is enough to infer the character's basic emotion.
