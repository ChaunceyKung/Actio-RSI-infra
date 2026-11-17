---
name: micro-31
level: micro
layer: L4
family: "emotion-appraisal"
description: "Diagnose regret, relief, disappointment, or pleasant surprise by comparing what happened with a salient alternative outcome."
---

# Counterfactual Emotion

## Use When
- Use when the question asks what emotion follows from comparing reality with a salient alternative outcome.
- Use when the answer depends on whether the actual outcome feels better or worse than what could have happened.
- Use when the scene is about regret, relief, disappointment, or pleasant surprise from a contrast case, not from responsibility or norm violation.

## Do Not Use When
- Do not use when the emotion is explained by blame, guilt, shame, pride, anger, or gratitude tied to responsibility or moral appraisal.
- Do not use when the issue is simple success, failure, happiness, or sadness with no explicit or implied alternative outcome.
- Do not use when the main question is outward display, suppression, empathy, or emotion regulation rather than the felt emotion itself.
- Do not use when the comparison is about probability, certainty, or evidence alone without an emotional counterfactual contrast.

## Decision Variable
actual outcome versus salient alternative outcome

## Trigger Checklist
- Is there a clear actual outcome?
- Is there a plausible alternative outcome that matters to the character?
- Is the emotion based on comparing those two outcomes?
- Is the alternative better or worse than reality from the character's point of view?
- Is the target emotion regret, relief, disappointment, or pleasant surprise?

## Workflow
- Pin down the actual outcome that occurred.
- Find the salient alternative the character is implicitly or explicitly weighing it against: what they hoped for, expected, nearly got, or narrowly avoided. If no such alternative is in play, this is not the right capability.
- Judge the direction of the comparison from the character's point of view: is reality WORSE than the alternative, or BETTER?
- Map worse-than-alternative to regret (when one's own choice could have changed it) or disappointment (when reality fell short of a hoped-for or expected alternative); map better-than-alternative to relief (a feared worse outcome was avoided) or pleasant surprise (reality beat a low expectation).
- Confirm the comparison is what produces the emotion: if removing the alternative leaves the same feeling, re-route to the basic-emotion-from-an-event capability (micro-26); if blame or a violated norm is really driving it, re-route to the responsibility/norm-appraisal capability (micro-30).

## Special Case
**The alternative may be hoped-for or feared, and may be only implied**: The salient alternative does not have to be stated. It can be what the character hoped for, expected, nearly got, or narrowly escaped. Use this capability whenever the emotion turns on that contrast, even when the alternative is implicit, and stand down when blame, a violated norm, or display style is the real driver.

Scene: Lan misses her usual bus by a few seconds and has to wait for the next one. Soon afterward she learns that the bus she just missed was in a minor crash on its route.
Question: What does Lan most likely feel?
Answer logic: The actual outcome (missing the bus) is contrasted with the salient alternative she nearly experienced (being on that bus during the crash). Reality turns out better than the worse outcome she narrowly avoided, so the emotion is relief. Missing a bus on its own would read as mild annoyance; it is the comparison against the worse alternative she escaped that produces the relief, and there is no fault or norm to make this a moral emotion.

## Boundary Exit Rule
- If the question can be answered from the event itself, with no alternative outcome being weighed, exit to the basic-emotion-from-an-event capability (micro-26).
- If the emotion is driven by responsibility, fault, credit, or a violated norm rather than by an outcome comparison, exit to the responsibility/norm-appraisal capability that diagnoses guilt, shame, pride, anger, and gratitude (micro-30).
- If the task asks how the person shows or hides the feeling, exit to the hidden-emotion capability (micro-28) or the emotional-display-rules capability (micro-29).
- If the question is about coping with, reframing, or recovering from the feeling after it arises, exit to the emotion-regulation capability (micro-33).

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when the scene asks for regret, relief, disappointment, or pleasant surprise based on a better-or-worse alternative outcome.
