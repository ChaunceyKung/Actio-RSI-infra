---
name: micro-42
level: micro
layer: L6
family: "norms-relationships"
description: "Judge whether a remark or act is a social faux pas: does it breach the tact of its setting and embarrass, hurt, or offend someone present? Use for 'did anyone say something inappropriate / which sentence was inappropriate' detection. NOT for who is to blame, how to apologize, or fitting a message to the listener's level."
---

# Faux Pas and Offense

## Use When
- The question asks whether anyone said or did something inappropriate, rude, awkward, embarrassing, or offensive in the scene.
- The question asks which specific sentence or act was the inappropriate one (identify the faux pas among several lines).
- The judgment turns on whether a remark breaches the tact of its setting because the speaker did not realize it would expose, belittle, or wound a listener present.

## Do Not Use When
- The main question is who caused harm, whether the act was intentional, or whether someone is blameworthy; route to harm and responsibility.
- The main task is how to apologize, repair, reconcile, or manage the relationship after the breach; route to relationship repair and apology.
- The act is simply adapting wording to the listener's expertise, age, or identity (e.g. simplifying for a novice); that is appropriate, so route to audience calibration.
- The issue is distribution, fairness, reciprocity, negotiation, or strategic influence; route to fairness and reciprocity or negotiation.
- The question asks WHY a non-literal remark was said (sarcasm, irony, hidden meaning) rather than whether it breached tact; that is non-literal comprehension, not a faux-pas judgment.

## Decision Variable
whether a remark or act breaches the tact of its setting and is likely to embarrass, hurt, or offend someone present

## Trigger Checklist
- Does the prompt ask 'did anyone say something inappropriate' or 'which sentence was inappropriate'?
- Is the test whether a remark was rude, tactless, embarrassing, or offensive in its specific setting?
- Is there a listener present who would be exposed, belittled, or wounded by the remark?
- Is the speaker's intent NOT the thing being asked about (a faux pas counts even when accidental and well-meant)?

## Workflow
- Confirm the question is a tact judgment: 'was it inappropriate / which line was inappropriate'. If it instead asks who is to blame, how to apologize, or why a remark was meant, jump to the matching exit rule and stop.
- List the candidate remarks/acts and, for each, the audience actually present (especially anyone the remark is about or could wound).
- For each candidate, test the tact line: does it expose private/sensitive facts, belittle or insult a person present, ignore the setting's decorum, or expose a fact that wounds someone present?
- A remark is a faux pas even if it is true, blunt, or unintentional — judge by likely embarrassment or offense to those present, not by truthfulness or intent. Honest-but-unsolicited put-downs and dismissals of someone present DO count.
- If exactly one candidate crosses the line, that is the faux pas (the inappropriate sentence). If none crosses it (e.g. the remark is a normal compliment, request, or polite reply), answer that no one said anything inappropriate.
- Return the tact verdict only. Do not assign blame, propose an apology, or recommend a next social move.

## Special Case
**Blunt-but-true or well-meant remark that still embarrasses**: A remark counts as a faux pas when it would embarrass or offend a listener present, even if it is factually true, merely blunt, or made with no bad intent. Do not let 'it's true' or 'they didn't mean it' talk you out of the faux-pas verdict. Truthfulness and intent are not the deciding variable; likely embarrassment to those present is. (If the question instead asks about blame, intent, or an apology, leave this unit.)

Scene: Xiaofang proudly hangs the new blue curtains she and her mother just bought. Her best friend Xiaolan comes over, looks at them, and says: 'Oh, the color of these curtains is too ugly, I think you should buy new ones.'
Question: If there is one, which sentence is inappropriate?
Answer logic: Xiaolan's remark is the faux pas. The judgment is about tact, not honesty: bluntly calling something Xiaofang just chose and is proud of 'too ugly' in front of her is likely to embarrass and hurt her, regardless of whether Xiaolan is sincere. The mother's earlier compliment and Xiaofang's follow-up question are normal and appropriate.

## Boundary Exit Rule
- Exit to harm and responsibility if the question turns on responsibility, intent, causation, or whether someone is to blame for harm.
- Exit to relationship repair and apology if the question is about how to apologize, repair, or restore the relationship after the breach.
- Exit to audience calibration if the act is fitting speech to a listener's expertise, age, identity, or stance, and the question is whether that adaptation was appropriate (it usually is, so it is not a faux pas).
- Exit to fairness and reciprocity or negotiation if the question is about negotiation, fairness, reciprocity, or strategic influence.
- Exit to non-literal comprehension if the question asks WHY a sarcastic/ironic remark was made rather than whether it breached tact.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when the question is 'did anyone say something inappropriate' or 'which sentence was inappropriate' — i.e. judging a remark or act for tact, embarrassment, or offense toward someone present.
