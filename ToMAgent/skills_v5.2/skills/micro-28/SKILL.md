---
name: micro-28
level: micro
layer: L4
family: "emotion-appraisal"
description: "Detects when a character's outward emotional expression differs from their privately felt emotion."
---

# Hidden Emotion

## Use When
- Use when the question asks what a character REALLY feels despite a different facial expression, tone, posture, or statement (for example, 'What are X's real feelings?').
- Use when the scene gives evidence for both an internal appraisal and an external display, and they conflict, and you must report the hidden inner feeling.
- Use when the answer depends on separating private affect from public expression, and naming the true private emotion is all that is required.
- Use when a character smiles, laughs, says they are fine, stays calm, or acts pleased while the situation suggests sadness, anger, fear, disappointment, embarrassment, or worry.

## Do Not Use When
- Do not use when the task only asks what emotion naturally follows from an event and there is no conflicting outward display; use the basic event-to-emotion appraisal capability instead.
- Do not use when the true emotion itself is surprising or nonstandard, with no masking or mismatch; use the atypical-emotion capability instead.
- Do not use when the question asks WHY the character controls the display - because of politeness, professionalism, role, audience, culture, or etiquette; that is the social-display-rule capability - explaining the rule behind a managed display (micro-29).
- Do not use when the character actually CHANGES the inner feeling itself (reappraising the situation, calming down, redirecting attention) rather than merely masking it; that is the emotion-regulation capability (micro-33).
- Do not use when guilt, shame, pride, gratitude, blame, or responsibility appraisal is the core issue; use the moral-emotion capability (micro-30) instead.

## Decision Variable
internal emotion versus external expression

## Trigger Checklist
- A private emotional cause is present, such as loss, rejection, disappointment, threat, humiliation, or frustration.
- An outward display is described, such as smiling, laughing, staying calm, saying 'I'm fine,' congratulating someone, or acting cheerful.
- The outward display is not the emotion that the private situation would normally produce.
- The question asks for the real feeling, hidden feeling, or inner reaction - it wants the emotion itself, not the reason the display is managed.
- A social reason for masking may be mentioned, but answering the question does not require stating that rule; you only need to name the true inner feeling.

## Workflow
- Identify the event or information that affects the character privately.
- Infer the likely internal emotion from that private appraisal (use the goal, loss, threat, or concern - not the visible face).
- Identify the character's observable expression, words, or behavior.
- Compare the internal emotion with the external display; if they diverge, a hidden emotion is present.
- Check what the question actually asks. If it asks WHAT the character feels, answer with the private emotion and treat the display as unreliable evidence. If it instead asks WHY the character shows the other expression, this is the social-display-rule capability (micro-29); if the character actually talks themselves into a calmer feeling, it is the emotion-regulation capability (micro-33).
- Answer with the true inner feeling only; do not expand into a full account of etiquette, moral responsibility, or persuasion.

## Special Case
**Polite happy face hiding annoyance**: When a character keeps a pleasant display so as not to upset someone, treat the real emotion as the one supported by the private appraisal, not by the smile. The detection target is the inner feeling, even if a social motive for masking is mentioned.

Scene: Mingming finds visiting his grandfather boring, but he goes every week and this visit is long. He keeps a happy face so his grandfather will not be hurt.
Question: What are Mingming's real feelings?
Answer logic: The boring, drawn-out visit frustrates Mingming, so his private emotion is annoyance. The happy face is only the outward display, kept up to protect his grandfather. Because the question asks what he REALLY feels, the answer is annoyed - the hidden inner emotion, not the smile. (If the question had asked WHY he keeps the happy face, the answer would be the social reason, which belongs to the display-rule capability.)

## Boundary Exit Rule
- Exit to the basic event-to-emotion appraisal capability if there is only an event-to-emotion inference and no conflicting display.
- Exit to the atypical-emotion capability if the character's actual emotion is unusual but openly shown, with no masking.
- Exit to the social-display-rule capability - which explains the norm, role, or audience that drives a managed display - if the question asks WHY the character controls the expression rather than what they feel (micro-29).
- Exit to the emotion-regulation capability - which changes the inner feeling itself through reappraisal, calming, or attention shift - if the character actually alters how they feel rather than just masking it (micro-33).
- Exit to the moral-emotion capability if the hidden feeling is mainly produced by responsibility, blame, guilt, shame, pride, or gratitude (micro-30).

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when a scene contrasts a character's private emotional state with a different outward expression and the question asks what they truly feel.
